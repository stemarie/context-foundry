"""Disposable regression proofs for the follow-up audit."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from foundry_runtime.core import Barrier, Gate, Journal
from foundry_runtime.runtime import Client


class FollowupRegressions(unittest.TestCase):
    def test_late_failure_preserves_longest_server_deadline(self):
        with tempfile.TemporaryDirectory() as root:
            gate = Gate(Journal(Path(root)/'gate.sqlite'), 'shared')
            first, second = gate.acquire(now=1000), gate.acquire(now=1000)
            gate.outcome(first, 'rate_limit', retry_after=3600, now=1000)
            gate.outcome(second, 'connection', now=1001)
            for now in (1062, 4599):
                with self.assertRaises(Barrier): gate.acquire(now=now)
                with self.assertRaises(Barrier): gate.operator_probe(now=now)
            permit = gate.acquire(now=4600)
            gate.outcome(permit, now=4600)
            self.assertIsNone(gate.acquire(now=4601))

    def test_dead_controller_does_not_release_live_transport_group(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            code = '''import sys
from pathlib import Path
from foundry_runtime.core import Gate,Journal
from foundry_runtime.remote import command
p=Path(sys.argv[1]);g=Gate(Journal(p/'gate.sqlite'),'shared')
g.outcome(g.acquire(now=0),'connection',now=0)
child="import os,time; from pathlib import Path; Path("+repr(str(p/'child.pid'))+").write_text(str(os.getpid())); time.sleep(60)"
g.run('probe',{},lambda: {'result':command([sys.executable,'-c',child],p)})
'''
            parent = subprocess.Popen([sys.executable, '-B', '-c', code, str(root)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            child = None
            try:
                deadline = time.monotonic()+10
                while not (root/'child.pid').exists():
                    self.assertIsNone(parent.poll(), 'controller exited before transport launch')
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(.02)
                child = int((root/'child.pid').read_text())
                parent.kill(); parent.wait(timeout=5)
                os.kill(child, 0)
                gate = Gate(Journal(root/'gate.sqlite'), 'shared')
                with self.assertRaises(Barrier): gate.operator_probe()
                with self.assertRaises(Barrier): gate.acquire()
            finally:
                if parent.poll() is None: parent.kill(); parent.wait(timeout=5)
                if child:
                    try: os.kill(child, signal.SIGTERM)
                    except ProcessLookupError: pass
                    deadline = time.monotonic()+5
                    while True:
                        try: os.kill(child, 0)
                        except ProcessLookupError: break
                        self.assertLess(time.monotonic(), deadline, 'owned transport did not stop')
                        time.sleep(.02)
            # Only established group quiescence permits dead-controller recovery.
            permit = gate.operator_probe()
            gate.outcome(permit)
            with gate.journal.transaction() as db:
                self.assertEqual('started', db.execute('select state from remote_operations').fetchone()[0])
            # Recovering the connection never blindly repeats the uncertain write.
            with self.assertRaises(Barrier): gate.run('probe', {}, lambda: self.fail('duplicate write'))

    def test_exited_transport_leader_does_not_hide_live_descendant(self):
        from foundry_runtime.remote import command
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            gate = Gate(Journal(root/'gate.sqlite'), 'shared')
            gate.outcome(gate.acquire(now=0), 'connection', now=0)
            code = ('import subprocess,sys; from pathlib import Path; '
                    'p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(60)"],'
                    'stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL); '
                    'Path(sys.argv[1]).write_text(str(p.pid))')
            child = None
            try:
                with self.assertRaises(Barrier):
                    gate.run('descendant', {}, lambda: {'result': command([sys.executable,'-c',code,str(root/'child.pid')],root)})
                child = int((root/'child.pid').read_text())
                os.kill(child, 0)
                with gate.journal.transaction() as db:
                    row = dict(db.execute('select * from connections').fetchone())
                    self.assertEqual('half_open', row['state'])
                    self.assertEqual(1, db.execute('select count(*) from transports').fetchone()[0])
                with self.assertRaises(Barrier): gate.operator_probe()
            finally:
                if child:
                    os.kill(child, signal.SIGTERM)
                    deadline = time.monotonic()+5
                    while True:
                        try: os.kill(child, 0)
                        except ProcessLookupError: break
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(.02)
            gate.release_probe(row['owner'])
            permit = gate.operator_probe(); gate.outcome(permit)

    def test_unknown_transport_start_stays_blocked(self):
        with tempfile.TemporaryDirectory() as root:
            gate = Gate(Journal(Path(root)/'gate.sqlite'), 'shared')
            gate.outcome(gate.acquire(now=0), 'connection', now=0)
            identity = gate.transport_intent()
            with self.assertRaises(Barrier): gate.acquire(now=31)
            with self.assertRaises(Barrier): gate.operator_probe(now=31)
            # Only a known failed spawn can discard its own unacknowledged intent.
            gate.transport_finished(identity, not_started=True)
            permit = gate.acquire(now=31); gate.outcome(permit)

    def test_legacy_probe_cannot_infer_transport_quiescence(self):
        with tempfile.TemporaryDirectory() as root:
            gate = Gate(Journal(Path(root)/'gate.sqlite'), 'shared')
            gate.outcome(gate.acquire(now=0), 'connection', now=0)
            gate.acquire(now=31)
            with gate.journal.transaction() as db:
                db.execute('update connections set transport_tracking=0')
            with patch('foundry_runtime.core.os.kill', side_effect=ProcessLookupError):
                with self.assertRaises(Barrier): gate.operator_probe(now=32)

    def test_unknown_version_blocks_launch_before_process_or_intent(self):
        from foundry_runtime.runtime import Launcher
        with tempfile.TemporaryDirectory() as root:
            journal = Journal(Path(root)/'runtime.sqlite')
            launcher = Launcher(journal,sys.executable,root)
            config = {'origin':'http://127.0.0.1:1','service_token':'fixture-only','role':'worker',
                      'binding':{'project_id':'p','contract_id':'c'}}
            with patch.object(Client,'call',return_value={'contract':{'id':'c','contract_version':'Alpha 99.0'}}), \
                    patch('foundry_runtime.runtime.subprocess.Popen') as spawn:
                with self.assertRaises(Barrier): launcher.ensure(config,{})
                spawn.assert_not_called()
            with journal.transaction() as db:
                self.assertEqual(0,db.execute('select count(*) from launches').fetchone()[0])

    def test_exec_failure_releases_probe_without_claiming_connection_health(self):
        from foundry_runtime.remote import command
        with tempfile.TemporaryDirectory() as root:
            gate = Gate(Journal(Path(root)/'gate.sqlite'), 'shared')
            gate.outcome(gate.acquire(now=0), 'connection', now=0)
            with self.assertRaises(Barrier):
                gate.run('missing-executable', {}, lambda: command([str(Path(root)/'absent')],root))
            with gate.journal.transaction() as db:
                self.assertEqual('open',db.execute('select state from connections').fetchone()[0])
                self.assertEqual(0,db.execute('select count(*) from transports').fetchone()[0])
            permit=gate.operator_probe();gate.outcome(permit)

    def test_semantic_version_read_precedes_native_authority(self):
        binding = dict(project_id='p', contract_id='c', revision=1, digest='d', attempt_id='a', actor='w')
        job = dict(contract_id='c', revision=dict(number=1, digest='d'), stage='Implementing',
                   attempt=dict(id='a', worker='w', expires_at=(datetime.now(timezone.utc)+timedelta(minutes=5)).isoformat()))
        client = Client('http://127.0.0.1:1', 'fixture-only')
        for version in ('Alpha 1.0', 'Alpha 99.0', None):
            calls = []
            def call(path, data=None, method='POST'):
                calls.append((path, method))
                if '/contracts/' in path: return {'contract': {'id':'c', 'contract_version':version}}
                return {'workflow': {'job':job}} if path.endswith('/get') else {'workflow': {'jobs':[job]}}
            with patch.object(client, 'call', side_effect=call):
                if version == 'Alpha 1.0':
                    self.assertEqual('Alpha 1.0', client.authority(binding,'worker')['contract_version'])
                else:
                    with self.assertRaises(Barrier): client.authority(binding,'worker')
                    self.assertEqual(1,len(calls))
            self.assertEqual(('/api/v1/contracts/c','GET'),calls[0])

if __name__ == '__main__': unittest.main()
