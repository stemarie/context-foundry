import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from foundry_runtime.runtime import Tools


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
