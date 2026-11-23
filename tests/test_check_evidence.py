import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from foundry_runtime.core import Barrier
from foundry_runtime.runtime import Tools, local_git


class CheckEvidenceTests(unittest.TestCase):
    def make_tools(self, root, role, stage, candidate_sha=None):
        workspace = root / 'workspace'
        scratch = root / 'scratch'
        workspace.mkdir()
        scratch.mkdir()
        (workspace / 'candidate.txt').write_text('candidate')
        candidate_sha = candidate_sha or ('a' * 40)
        tools = Tools({
            'origin': 'https://fixture.invalid', 'service_token': 'fixture-only',
            'workspace': str(workspace), 'scratch': str(scratch),
            'runtime_journal': str(root / 'runtime.sqlite'),
            'base_sha': 'b' * 40, 'candidate_sha': candidate_sha,
            'checks': ['python3', '-m', 'unittest', 'tests.test_local_connection'],
            'role': role,
            'binding': {'project_id': 'project', 'contract_id': 'contract', 'revision': 2,
                        'digest': 'digest', 'attempt_id': 'attempt', 'actor': role,
                        **({'candidate_id': 'candidate-id'} if role == 'qa' else {})},
        })
        tools.client = Mock()
        tools.client.authority.return_value = {
            'stage': stage, 'reviewer': 'qa',
            'candidate': {'id': 'candidate-id', 'sha': candidate_sha},
        }
        return tools, workspace

    def run_check(self, tools):
        def run(argv, **kwargs):
            self.assertEqual('/usr/bin/sandbox-exec', argv[0])
            return Mock(returncode=0, stdout='pure check passed\n', stderr='')
        git = patch('foundry_runtime.runtime.local_git', return_value='a' * 40) if tools.role == 'qa' else patch('foundry_runtime.runtime.local_git')
        with patch('foundry_runtime.runtime.sys.platform', 'darwin'), \
             patch.object(Path, 'is_file', return_value=True), \
             patch('foundry_runtime.runtime.subprocess.run', side_effect=run), git:
            return tools.invoke('check', {})

    def init_candidate(self, tools, workspace):
        local_git(workspace, 'init', '-q')
        local_git(workspace, 'config', 'core.fileMode', 'true')
        local_git(workspace, 'add', '--all')
        local_git(workspace, '-c', 'user.name=fixture', '-c', 'user.email=fixture@localhost',
                  'commit', '-qm', 'candidate')
        sha = local_git(workspace, 'rev-parse', 'HEAD')
        tools.config.update(base_sha=sha, candidate_sha=sha)
        tools.client.authority.return_value['candidate']['sha'] = sha

    def test_interrupted_recheck_cannot_reuse_previous_pass(self):
        for role, stage, operation, arguments in (
                ('worker', 'Implementing', 'submit', {'summary': 'candidate'}),
                ('qa', 'QA', 'verdict', {'verdict': 'Accepted', 'summary': 'candidate'})):
            with self.subTest(role=role), tempfile.TemporaryDirectory() as temporary:
                tools, workspace = self.make_tools(Path(temporary), role, stage)
                self.init_candidate(tools, workspace)
                if role == 'worker':
                    (workspace / 'candidate.txt').write_text('ready to submit')
                with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                    tools.invoke('check', {})
                with patch('foundry_runtime.runtime.restricted_check',
                           side_effect=subprocess.TimeoutExpired(['fixture'], 1)):
                    with self.assertRaises(subprocess.TimeoutExpired):
                        tools.invoke('check', {})
                with self.assertRaises(Barrier):
                    tools.invoke(operation, arguments)
                tools.client.workflow.assert_not_called()
                with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                    tools.invoke('check', {})
                tools.invoke(operation, arguments)
                tools.client.workflow.assert_called_once()

    def test_worker_cannot_submit_executable_change_after_checks(self):
        with tempfile.TemporaryDirectory() as temporary:
            tools, workspace = self.make_tools(Path(temporary), 'worker', 'Implementing')
            path = workspace / 'candidate.txt'
            path.chmod(0o644)
            self.init_candidate(tools, workspace)
            original_sha = local_git(workspace, 'rev-parse', 'HEAD')
            with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                tools.invoke('check', {})
            path.chmod(0o755)
            self.assertIn('100644 => 100755', local_git(workspace, 'diff', '--summary'))
            with self.assertRaisesRegex(Barrier, 'changed since verification'):
                tools.invoke('submit', {'summary': 'unchecked executable change'})
            self.assertEqual(original_sha, local_git(workspace, 'rev-parse', 'HEAD'))
            tools.client.workflow.assert_not_called()

    def test_permission_change_during_check_requires_reverification(self):
        with tempfile.TemporaryDirectory() as temporary:
            tools, workspace = self.make_tools(Path(temporary), 'worker', 'Implementing')
            path = workspace / 'candidate.txt'
            path.chmod(0o644)
            def changed(*_args):
                path.chmod(0o755)
                return {'passed': True}
            with patch('foundry_runtime.runtime.restricted_check', side_effect=changed):
                with self.assertRaisesRegex(Barrier, 'check changed candidate'):
                    tools.invoke('check', {})
            self.assertIsNone(tools.checks)

    def test_worker_cannot_submit_repartitioned_binary_contents(self):
        with tempfile.TemporaryDirectory() as temporary:
            tools, workspace = self.make_tools(Path(temporary), 'worker', 'Implementing')
            self.init_candidate(tools, workspace)
            path = workspace / 'candidate.txt'
            path.write_bytes(b'left\0other.bin\0right')
            with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                tools.invoke('check', {})
            path.write_bytes(b'left')
            (workspace / 'other.bin').write_bytes(b'right')
            with self.assertRaisesRegex(Barrier, 'changed since verification'):
                tools.invoke('submit', {'summary': 'unchecked binary files'})
            tools.client.workflow.assert_not_called()

    def test_qa_cannot_accept_after_ignored_input_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            tools, workspace = self.make_tools(Path(temporary), 'qa', 'QA')
            (workspace / '.gitignore').write_text('check-input.txt\n')
            check_input = workspace / 'check-input.txt'
            check_input.write_text('checked input')
            self.init_candidate(tools, workspace)
            with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                tools.invoke('check', {})
            check_input.write_text('different input')
            self.assertEqual('', local_git(workspace, 'status', '--porcelain'))
            with self.assertRaisesRegex(Barrier, 'changed since verification'):
                tools.invoke('verdict', {'verdict': 'Accepted', 'summary': 'stale checks'})
            tools.client.workflow.assert_not_called()
            with patch('foundry_runtime.runtime.restricted_check', return_value={'passed': True}):
                tools.invoke('check', {})
            tools.invoke('verdict', {'verdict': 'Accepted', 'summary': 'fresh checks'})
            tools.client.workflow.assert_called_once()

    def test_worker_submit_persists_actual_check_descriptor_not_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tools, _workspace = self.make_tools(root, 'worker', 'Implementing')
            checks = self.run_check(tools)
            git = {'HEAD': 'c' * 40, 'branch': 'candidate'}
            def local_git(_workspace, *args):
                if args[:2] == ('rev-parse', 'HEAD'):
                    return git['HEAD']
                if args[:2] == ('rev-parse', 'HEAD^'):
                    return 'b' * 40
                if args[:2] == ('branch', '--show-current'):
                    return git['branch']
                if args[0] in ('diff', 'add') or 'commit' in args:
                    return ''
                raise AssertionError(args)
            with patch('foundry_runtime.runtime.local_git', side_effect=local_git):
                tools.invoke('submit', {'summary': 'model claims another command ran'})
            command = tools.client.workflow.call_args.args[1]
            evidence = json.loads(command['evidence'])
            self.assertEqual(checks['command'], evidence['checks']['command'])
            self.assertEqual('model claims another command ran', evidence['summary'])
            self.assertTrue((root / 'runtime.sqlite').is_file())

    def test_qa_verdict_persists_actual_check_descriptor_not_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            tools, _workspace = self.make_tools(Path(temporary), 'qa', 'QA')
            checks = self.run_check(tools)
            with patch('foundry_runtime.runtime.local_git', side_effect=lambda _workspace, *args: '' if args[0] == 'status' else 'a' * 40):
                tools.invoke('verdict', {'verdict': 'Accepted', 'summary': 'model claims another command ran'})
            command = tools.client.workflow.call_args.args[1]
            evidence = json.loads(command['evidence'])
            self.assertEqual(checks['command'], evidence['checks']['command'])
            self.assertEqual('model claims another command ran', evidence['summary'])


if __name__ == '__main__':
    unittest.main()
