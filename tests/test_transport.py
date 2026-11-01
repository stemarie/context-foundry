import contextlib
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
