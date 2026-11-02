import importlib.util
import contextlib
import io
import os
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
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertFalse(module.write_report(report,{'new':'evidence'}))
            self.assertEqual('previous safe evidence',report.read_text())
            self.assertEqual([report],list(Path(root).iterdir()))

    def test_known_not_applied_history_close_recovery_is_explicit_and_idempotent(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/48'
            remote={'state':'OPEN','updatedAt':'2026-11-02T00:00:00Z','events':[{'event':'labeled','id':1,'created_at':'2026-11-01T00:00:00Z'}],'closes':0,'lose_first':True}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    return __import__('json').dumps({'url':url,'number':48,'state':remote['state'],
                        'closedAt':None if remote['state']=='OPEN' else '2026-11-02T00:01:00Z','updatedAt':remote['updatedAt']})
                if argv[:3]==['gh','api','--method']:
                    return __import__('json').dumps([remote['events']])
                if argv[:3]==['gh','issue','close']:
                    remote['closes']+=1
                    if remote['lose_first']:
                        remote['lose_first']=False
                        raise RemoteFailure('resource')
                    remote['state']='CLOSED';remote['updatedAt']='2026-11-02T00:01:00Z'
                    return ''
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier):github.close_history(url)
                with self.assertRaises(Barrier):github.close_history(url)
                with self.assertRaises(Barrier):github.recover_close_history_known_not_applied(url)
                self.assertEqual({'url':url,'closed':True},
                                 github.recover_close_history_known_not_applied(url,known_not_applied=True))
                self.assertEqual({'url':url,'closed':True},
                                 github.recover_close_history_known_not_applied(url,known_not_applied=True))
            self.assertEqual(2,remote['closes'])
            with github.gate.journal.transaction() as db:
                self.assertEqual('complete',db.execute('select state from remote_operations').fetchone()[0])
                self.assertEqual(1,db.execute('select count(*) from remote_recoveries').fetchone()[0])
                self.assertEqual([('proved',), ('complete',)],
                                 [tuple(row) for row in db.execute('select kind from remote_recovery_events order by sequence')])

    def test_history_recovery_refuses_close_reopen_and_transport_uncertainty(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/49'
            remote={'state':'OPEN','events':[
                {'event':'closed','id':1,'created_at':'2026-11-01T00:00:00Z'},
                {'event':'reopened','id':2,'created_at':'2026-11-01T00:01:00Z'},
            ]}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    return __import__('json').dumps({'url':url,'number':49,'state':remote['state'],
                        'closedAt':None,'updatedAt':'2026-11-02T00:00:00Z'})
                if argv[:3]==['gh','api','--method']:return __import__('json').dumps([remote['events']])
                if argv[:3]==['gh','issue','close']:raise RemoteFailure('resource')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier):github.close_history(url)
                with self.assertRaises(Barrier):github.recover_close_history_known_not_applied(url,known_not_applied=True)
                remote['events']=[]
                with github.gate.journal.transaction() as db:
                    db.execute("insert into transports values('unknown','other',NULL)")
                with self.assertRaises(Barrier):github.recover_close_history_known_not_applied(url,known_not_applied=True)
                remote['events']=[{'event':'labeled','id':3,'created_at':'2026-11-01T00:02:00Z'}]
                with github.gate.journal.transaction() as db:
                    db.execute("delete from transports where identity='unknown'")
                    db.execute("insert into transports values('live','other',?)", (os.getpid(),))
                with self.assertRaises(Barrier):github.recover_close_history_known_not_applied(url,known_not_applied=True)

    def test_history_recovery_reconciles_lost_applied_close_without_a_retry(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/50'
            remote={'state':'OPEN','closes':0,'updatedAt':'2026-11-02T00:00:00Z'}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    return __import__('json').dumps({'url':url,'number':50,'state':remote['state'],
                        'closedAt':None if remote['state']=='OPEN' else '2026-11-02T00:01:00Z','updatedAt':remote['updatedAt']})
                if argv[:3]==['gh','api','--method']:return '[]'
                if argv[:3]==['gh','issue','close']:
                    remote['closes']+=1;remote['state']='CLOSED'
                    raise RemoteFailure('resource')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier):github.close_history(url)
                self.assertEqual({'url':url,'closed':True},
                                 github.recover_close_history_known_not_applied(url,known_not_applied=True))
            self.assertEqual(1,remote['closes'])

    def test_history_recovery_rejects_malformed_snapshots_without_write(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/52'
            remote={'invalid':False,'closes':0}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    if remote['invalid'] == 'list': return '[]'
                    updated = None if remote['invalid'] is True else ('not-a-time' if remote['invalid'] == 'timestamp' else '2026-11-02T00:00:00Z')
                    return __import__('json').dumps({'url':url,'number':52,'state':'OPEN',
                        'closedAt':None,'updatedAt':updated})
                if argv[:3]==['gh','issue','close']:
                    remote['closes']+=1
                    raise RemoteFailure('resource')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier): github.close_history(url)
                for invalid in (True, 'timestamp', 'list'):
                    remote['invalid']=invalid
                    with self.assertRaises(Barrier):
                        github.recover_close_history_known_not_applied(url,known_not_applied=True)
            self.assertEqual(1,remote['closes'])

    def test_history_recovery_refuses_incomplete_and_changed_absence_proof(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/51'
            remote={'pages':[],'views':0}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    remote['views']+=1
                    stamp='2026-11-02T00:00:00Z' if remote['views'] % 2 else '2026-11-02T00:01:00Z'
                    return __import__('json').dumps({'url':url,'number':51,'state':'OPEN','closedAt':None,'updatedAt':stamp})
                if argv[:3]==['gh','api','--method']: return __import__('json').dumps(remote['pages'])
                if argv[:3]==['gh','issue','close']: raise RemoteFailure('resource')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier): github.close_history(url)
                with self.assertRaises(Barrier): github.recover_close_history_known_not_applied(url,known_not_applied=True)

    def test_history_recovery_accepts_complete_zero_event_page_exactly_once(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub);github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/55'
            remote={'state':'OPEN','writes':0}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    return __import__('json').dumps({'url':url,'number':55,'state':remote['state'],
                        'closedAt':None if remote['state']=='OPEN' else '2026-11-02T00:01:00Z',
                        'updatedAt':'2026-11-02T00:00:00Z'})
                if argv[:3]==['gh','api','--method']: return '[[]]'
                if argv[:3]==['gh','issue','close']:
                    remote['writes']+=1
                    if remote['writes']==1: raise RemoteFailure('resource')
                    remote['state']='CLOSED';return ''
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier): github.close_history(url)
                result=github.recover_close_history_known_not_applied(url,known_not_applied=True)
                self.assertEqual(result,github.recover_close_history_known_not_applied(url,known_not_applied=True))
            self.assertEqual(({'url':url,'closed':True},2), (result,remote['writes']))

    def test_history_recovery_rechecks_stable_snapshot_before_close(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/53'
            remote={'views':0,'closes':0,'first_close':True}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    remote['views']+=1
                    stamp='2026-11-02T00:00:00Z' if remote['views'] < 4 else '2026-11-02T00:01:00Z'
                    return __import__('json').dumps({'url':url,'number':53,'state':'OPEN',
                        'closedAt':None,'updatedAt':stamp})
                if argv[:3]==['gh','api','--method']:
                    return __import__('json').dumps([[{'event':'labeled','id':1,'created_at':'2026-11-01T00:00:00Z'}]])
                if argv[:3]==['gh','issue','close']:
                    remote['closes']+=1
                    if remote['first_close']:
                        remote['first_close']=False
                        raise RemoteFailure('resource')
                    raise AssertionError('changed proof must fence the close')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier): github.close_history(url)
                with self.assertRaises(Barrier): github.recover_close_history_known_not_applied(url,known_not_applied=True)
            self.assertEqual(1,remote['closes'])

    def test_history_recovery_rejects_malformed_event_and_closed_timestamp_without_write(self):
        with tempfile.TemporaryDirectory() as root:
            github=GitHub.__new__(GitHub)
            github.repository='stemarie/context-foundry';github.checkout=Path(root)
            github.gate=Gate(Journal(Path(root)/'runtime.sqlite'),'shared')
            url='https://github.com/stemarie/context-foundry/issues/54'
            remote={'state':'OPEN','events':[{'event':'labeled','id':1,'created_at':'bad-time'}],
                    'closes':0,'closed_at':'2026-11-02T00:01:00Z'}
            def transport(argv,cwd):
                if argv[:3]==['gh','issue','view']:
                    return __import__('json').dumps({'url':url,'number':54,'state':remote['state'],
                        'closedAt':None if remote['state']=='OPEN' else remote['closed_at'],
                        'updatedAt':'2026-11-02T00:00:00Z'})
                if argv[:3]==['gh','api','--method']: return __import__('json').dumps([remote['events']])
                if argv[:3]==['gh','issue','close']:
                    remote['closes']+=1
                    raise RemoteFailure('resource')
                raise AssertionError(argv)
            with patch('foundry_runtime.remote.command',side_effect=transport):
                with self.assertRaises(Barrier): github.close_history(url)
                with self.assertRaises(Barrier): github.recover_close_history_known_not_applied(url,known_not_applied=True)
                remote['state']='CLOSED';remote['closed_at']='bad-time'
                with self.assertRaises(Barrier): github.recover_close_history_known_not_applied(url,known_not_applied=True)
            self.assertEqual(1,remote['closes'])

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
