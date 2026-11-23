"""Behavioral coverage for shared helpers without a live service or model."""
import contextlib
from functools import partial
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from foundry_runtime import constants as settings
from foundry_runtime.core import Barrier
from scripts.acceptance_support import (history_snapshot, issue_actor_tokens, job_binding,
                                        load_module, resolve_provider, workflow_call, workflow_pages)


class AcceptanceSupportTests(unittest.TestCase):
    def test_module_loading_reads_selected_file_without_running_a_scenario(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / 'fixture.py'
            path.write_text('VALUE = 17\n')
            self.assertEqual(17, load_module('acceptance_fixture', path).VALUE)

    def test_token_setup_preserves_actor_selection_and_partial_failure(self):
        server = SimpleNamespace(tokens={}, env={'FIXTURE': 'private'})
        actors = [('worker', 'read,write,writer'), ('qa', 'read,write,auditor')]
        output = io.StringIO()
        with patch('scripts.acceptance_support.subprocess.run', side_effect=[
                SimpleNamespace(stdout='issued\ntoken=fixture-worker\n'), RuntimeError('issuance failed')]) as run, \
             contextlib.redirect_stdout(output):
            with self.assertRaisesRegex(RuntimeError, 'issuance failed'):
                issue_actor_tokens(server, '/fixture/service', actors, prefix='proof-')
        self.assertEqual({'worker': 'fixture-worker'}, server.tokens)
        self.assertEqual(['/fixture/service', 'token', 'issue', 'proof-qa', 'read,write,auditor'],
                         run.call_args.args[0])
        self.assertIs(server.env, run.call_args.kwargs['env'])
        self.assertEqual('', output.getvalue())

    def test_container_tokens_use_the_supplied_fixture_without_a_local_cli(self):
        server = SimpleNamespace(tokens={}, issue_token=Mock(return_value='fixture-token'))
        with patch('scripts.acceptance_support.subprocess.run') as run:
            issue_actor_tokens(server, '/unused', [('qa', 'read,write,auditor')],
                               prefix='container-', containerized=True)
        server.issue_token.assert_called_once_with('container-qa', 'read,write,auditor')
        run.assert_not_called()
        self.assertEqual({'qa': 'fixture-token'}, server.tokens)

    def test_provider_resolution_executes_selected_program_without_logging_credentials(self):
        with tempfile.TemporaryDirectory() as root:
            package = Path(root) / 'hermes_cli'
            package.mkdir()
            (package / '__init__.py').write_text('')
            (package / 'runtime_provider.py').write_text(
                'def resolve_runtime_provider(requested, target_model):\n'
                '    return {"provider": requested, "api_mode": target_model, "api_key": "fixture-private",\n'
                '            "base_url": "http://fixture.invalid", "ignored": True}\n')
            provider = "fixture-provider';raise RuntimeError('injected')#"
            model = 'fixture-model"with-quotes'
            captured = io.StringIO()
            with patch.multiple(settings, ACCEPTANCE_PROVIDER=provider, ACCEPTANCE_MODEL=model), \
                 contextlib.redirect_stdout(captured):
                result = resolve_provider(sys.executable, root, disable_bytecode=True)
            self.assertEqual({'provider': provider, 'api_mode': model, 'api_key': 'fixture-private',
                              'base_url': 'http://fixture.invalid'}, result)
            self.assertEqual('', captured.getvalue())

    def test_provider_uses_virtualenv_launcher_without_resolving_its_symlink(self):
        response = {'provider': 'fixture', 'api_mode': 'fixture', 'api_key': 'private', 'base_url': 'fixture'}
        with patch('scripts.acceptance_support.subprocess.run', return_value=SimpleNamespace(stdout=json.dumps(response))) as run:
            resolve_provider('/fixture/venv/bin/python', '/fixture/hermes')
        self.assertEqual('/fixture/venv/bin/python', run.call_args.args[0][0])
        self.assertEqual('-c', run.call_args.args[0][1])
        self.assertEqual('/fixture/hermes', run.call_args.kwargs['env']['PYTHONPATH'])

    def test_workflow_preserves_project_actor_errors_and_input_data(self):
        class API:
            def __init__(self):
                self.calls = []

            def call(self, operation, values, actor, expected_error=None):
                print('fixture-private-client-output')
                self.calls.append((operation, values, actor, expected_error))
                return {'error': expected_error} if expected_error else {'workflow': {'ok': True}}

        api = API()
        work = partial(workflow_call, api, 'project')
        original = {'project_id': 'foreign-project', 'contract_id': 'contract'}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual({'ok': True}, work('get', original, 'reader'))
            self.assertEqual({'ok': True}, work('submit', original, 'worker'))
            self.assertEqual({'error': 'project_conflict'}, work('complete', original, expected_error='project_conflict'))
        self.assertNotIn('idempotency_key', api.calls[0][1])
        self.assertTrue(api.calls[1][1]['idempotency_key'])
        self.assertEqual('worker', api.calls[1][2])
        self.assertEqual('project', api.calls[1][1]['project_id'])
        self.assertEqual({'project_id': 'foreign-project', 'contract_id': 'contract'}, original)
        self.assertEqual('', output.getvalue())
        for operation in ('list', 'agents', 'assignments', 'history'):
            work(operation)
            self.assertNotIn('idempotency_key', api.calls[-1][1])

    def test_bindings_keep_attempt_revision_and_optional_candidate_distinct(self):
        job = {'contract_id': 'contract', 'revision': {'number': 2, 'digest': 'digest'},
               'attempt': {'id': 'attempt'}, 'candidate': {'id': 'candidate', 'sha': 'sha'}}
        worker = job_binding(job, project_id='project')
        accepted = job_binding(job, include_candidate=True)
        self.assertEqual({'project_id': 'project', 'contract_id': 'contract', 'revision': 2,
                          'digest': 'digest', 'attempt_id': 'attempt'}, worker)
        self.assertNotIn('project_id', accepted)
        self.assertEqual('candidate', accepted['candidate_id'])
        self.assertEqual('sha', accepted['candidate_sha'])
        worker['revision'] = 99
        self.assertEqual(2, job['revision']['number'])

    def test_explicit_mutation_identity_survives_a_retry(self):
        api = Mock()
        api.call.return_value = {'workflow': {'ok': True}}
        values = {'idempotency_key': 'original-operation', 'contract_id': 'contract'}
        for _ in range(2):
            workflow_call(api, 'project', 'submit', values, 'worker')
        self.assertEqual(['original-operation', 'original-operation'],
                         [call.args[1]['idempotency_key'] for call in api.call.call_args_list])
        self.assertEqual('original-operation', values['idempotency_key'])

    def test_invalid_explicit_mutation_identity_never_reaches_service(self):
        for key in (None, '', '   ', False, 7, []):
            with self.subTest(key=key):
                api = Mock()
                with self.assertRaisesRegex(ValueError, 'idempotency_key'):
                    workflow_call(api, 'project', 'submit', {'idempotency_key': key})
                api.call.assert_not_called()

    def test_new_mutations_get_independent_keys_when_none_was_supplied(self):
        api = Mock()
        api.call.return_value = {'workflow': {'ok': True}}
        workflow_call(api, 'project', 'record')
        workflow_call(api, 'project', 'record')
        keys = [call.args[1]['idempotency_key'] for call in api.call.call_args_list]
        self.assertTrue(all(keys))
        self.assertNotEqual(keys[0], keys[1])

    def test_history_keeps_all_pages_and_the_final_revision_snapshot(self):
        calls = []

        def work(operation, values, actor):
            calls.append((operation, values, actor))
            events = [{'id': n} for n in range(values['after'] + 1, min(values['after'] + 3, 6))]
            return {'events': events, 'revisions': [values['after']]}

        with patch.object(settings, 'HISTORY_PAGE_SIZE', 2):
            history = history_snapshot(work, 'contract', actor='coordinator')
        self.assertEqual([1, 2, 3, 4, 5], [row['id'] for row in history['events']])
        self.assertEqual([4], history['revisions'])
        self.assertEqual([0, 2, 4], [call[1]['after'] for call in calls])
        self.assertTrue(all(call[1]['contract_id'] == 'contract' and call[2] == 'coordinator' for call in calls))

    def test_exact_page_boundary_fetches_empty_tail_and_stalled_cursor_fails(self):
        pages = Mock(side_effect=[{'jobs': [{'queue_sequence': 1}, {'queue_sequence': 2}]}, {'jobs': []}])
        with patch.object(settings, 'HISTORY_PAGE_SIZE', 2):
            result = list(workflow_pages(pages, 'list', field='jobs', cursor_field='queue_sequence'))
            self.assertEqual(2, len(result))
            self.assertEqual(2, pages.call_args.args[1]['after'])
            stalled = Mock(return_value={'events': [{'id': 0}, {'id': 0}]})
            with self.assertRaisesRegex(Barrier, 'did not advance'):
                history_snapshot(stalled, 'contract')
            self.assertEqual(1, stalled.call_count)


if __name__ == '__main__':
    unittest.main()
