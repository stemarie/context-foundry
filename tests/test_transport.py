import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from foundry_runtime.core import Barrier, Gate, Journal, RemoteFailure
from foundry_runtime.remote import GitHub, command

class TransportTests(unittest.TestCase):
    def test_cli_rate_hint_and_resource_error_classification(self):
        for stderr, category, delay in [('< HTTP/2 429\n< Retry-After: 95\nrate limit','rate_limit',95),
                                        ('HTTP 404: Not Found','resource',None),('authentication failed','authentication',None)]:
            with patch('subprocess.run',return_value=subprocess.CompletedProcess([],1,'',stderr)):
                with self.assertRaises(RemoteFailure) as caught: command(['gh','issue','view','0'],'.')
                self.assertEqual(category,caught.exception.category)
                self.assertEqual(delay,caught.exception.retry_after)

    def test_cached_write_does_not_close_open_breaker(self):
        with tempfile.TemporaryDirectory() as root:
            gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            self.assertEqual({'sha':'delivered'},gate.run('push',{},lambda:{'sha':'delivered'}))
            gate.outcome(gate.acquire(),'service')
            self.assertEqual({'sha':'delivered'},gate.run('push',{},lambda: self.fail('duplicate write')))
            with self.assertRaises(Barrier):gate.acquire()

    def test_two_project_callers_share_gate_and_resource_errors_stay_local(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'runtime.sqlite'
            project_one=Gate(Journal(path),'same-credential-reference')
            project_two=Gate(Journal(path),'same-credential-reference')
            def missing():raise RemoteFailure('resource')
            with self.assertRaises(Barrier):project_one.run('project-one:missing',{},missing)
            self.assertIsNone(project_two.acquire())
            project_one.outcome(None,'connection')
            with self.assertRaises(Barrier):project_two.acquire()
            probe=project_two.operator_probe()
            with self.assertRaises(Barrier):project_one.acquire()
            project_two.outcome(probe)
            self.assertIsNone(project_one.acquire())

    def test_lost_git_push_response_reconciles_without_another_push(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            expected,sha='a'*40,'b'*40
            remote={'head':expected,'pushes':0}
            def transport(argv,cwd):
                if 'ls-remote' in argv:return remote['head']+' refs/heads/main'
                if 'push' in argv:
                    self.assertFalse(any(arg.startswith('--force') for arg in argv))
                    remote['head']=sha;remote['pushes']+=1
                    raise RemoteFailure('connection')  # Remote committed; response was lost.
                raise AssertionError('unexpected transport')
            with patch('foundry_runtime.remote.command',side_effect=transport), patch('subprocess.run',return_value=subprocess.CompletedProcess([],0)):
                with self.assertRaises(Barrier):github.push(sha,expected,lambda:None)
                probe=github.gate.operator_probe();github.gate.outcome(probe)
                result=github.push(sha,expected,lambda:self.fail('uncertain push repeated'))
            self.assertTrue(result['reconciled'])
            self.assertEqual(1,remote['pushes'])

    def test_report_capacity_error_preserves_previous_evidence(self):
        path=Path(__file__).resolve().parents[1]/'scripts/real_agent_acceptance.py'
        spec=importlib.util.spec_from_file_location('acceptance_runner_test',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as root:
            report=Path(root)/'report.json';report.write_text('previous safe evidence')
            with patch.object(module.json,'dump',side_effect=OSError('fixture capacity failure')):
                self.assertFalse(module.write_report(report,{'new':'evidence'}))
            self.assertEqual('previous safe evidence',report.read_text())
            self.assertEqual([report],list(Path(root).iterdir()))

    def test_target_lock_excludes_another_project_caller(self):
        with tempfile.TemporaryDirectory() as root:
            one=GitHub.__new__(GitHub);two=GitHub.__new__(GitHub)
            for item in (one,two):
                item.repository='stemarie/context-foundry'
                item.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            with one.integration():
                with self.assertRaises(Barrier):
                    with two.integration():self.fail('overlapping target integration')
            with two.integration():pass

if __name__=='__main__':unittest.main()
