"""Disposable command-admission and target-recovery proofs."""
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from foundry_runtime.core import Barrier, Gate, Journal
from foundry_runtime.remote import GitHub, command


class AdmissionRegressions(unittest.TestCase):
    def test_compound_operation_cannot_start_command_after_trip(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);gate=Gate(Journal(root/'gate.sqlite'),'shared')
            other=Gate(Journal(root/'gate.sqlite'),'shared')
            first_done=threading.Event();resume=threading.Event();errors=[]
            def callback():
                command([sys.executable,'-c','print("first fixture command")'],root)
                first_done.set()
                if not resume.wait(5):raise Barrier('fixture coordination timeout')
                command([sys.executable,'-c','from pathlib import Path; Path("second-ran").write_text("fixture")'],root)
                return {'fixture':'complete'}
            def caller():
                try:gate.run('compound',{},callback)
                except Barrier:errors.append('fenced')
            thread=threading.Thread(target=caller);thread.start()
            try:
                self.assertTrue(first_done.wait(5))
                other.outcome(other.acquire(),'rate_limit',retry_after=3600)
            finally:
                resume.set();thread.join(5)
            self.assertFalse(thread.is_alive())
            self.assertFalse((root/'second-ran').exists())
            self.assertEqual(['fenced'],errors)
            with gate.journal.transaction() as db:
                self.assertEqual('open',db.execute('select state from connections').fetchone()[0])
                self.assertEqual(0,db.execute('select count(*) from transports').fetchone()[0])

    def test_recovery_does_not_revive_an_old_command_grant(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);gate=Gate(Journal(root/'gate.sqlite'),'shared')
            other=Gate(Journal(root/'gate.sqlite'),'shared')
            ready=threading.Event();resume=threading.Event();errors=[]
            def callback():
                command([sys.executable,'-c','print("first fixture command")'],root)
                ready.set()
                if not resume.wait(5):raise Barrier('fixture coordination timeout')
                return command([sys.executable,'-c','print("stale command")'],root)
            def caller():
                try:gate.run('old',{},callback)
                except Barrier:errors.append('fenced')
            thread=threading.Thread(target=caller);thread.start()
            try:
                self.assertTrue(ready.wait(5))
                other.outcome(other.acquire(),'connection')
                probe=other.operator_probe();other.outcome(probe)
            finally:resume.set();thread.join(5)
            self.assertFalse(thread.is_alive());self.assertEqual(['fenced'],errors)
            result=other.run('fresh',{},lambda: {'output':command([sys.executable,'-c','print("fresh")'],root)})
            self.assertEqual({'output':'fresh'},result)

    def test_probe_owner_can_finish_a_valid_compound_operation(self):
        with tempfile.TemporaryDirectory() as name:
            gate=Gate(Journal(Path(name)/'gate.sqlite'),'shared')
            gate.outcome(gate.acquire(now=0),'connection',now=0)
            def callback():
                first=command([sys.executable,'-c','print("first")'],name)
                second=command([sys.executable,'-c','print("second")'],name)
                return {'outputs':[first,second]}
            self.assertEqual({'outputs':['first','second']},gate.run('probe',{},callback))
            self.assertIsNone(gate.acquire())

    def test_actual_transport_timeout_stops_owned_group(self):
        original=subprocess.Popen.communicate
        def shortened(process,*args,**kwargs):
            if kwargs.get('timeout')==90:kwargs['timeout']=.3
            return original(process,*args,**kwargs)
        with tempfile.TemporaryDirectory() as name:
            gate=Gate(Journal(Path(name)/'gate.sqlite'),'shared')
            gate.outcome(gate.acquire(now=0),'connection',now=0)
            with patch.object(subprocess.Popen,'communicate',shortened):
                with self.assertRaises(Barrier):
                    gate.run('timeout',{},lambda: command([sys.executable,'-c','import time; time.sleep(30)'],name))
            with gate.journal.transaction() as db:
                self.assertEqual(0,db.execute('select count(*) from transports').fetchone()[0])
                self.assertEqual('open',db.execute('select state from connections').fetchone()[0])

    def test_exited_leader_timeout_retains_descendant_fence(self):
        original=subprocess.Popen.communicate
        def shortened(process,*args,**kwargs):
            if kwargs.get('timeout')==90:kwargs['timeout']=.3
            return original(process,*args,**kwargs)
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);gate=Gate(Journal(root/'gate.sqlite'),'shared')
            gate.outcome(gate.acquire(now=0),'connection',now=0)
            code='import subprocess,sys; from pathlib import Path; p=subprocess.Popen([sys.executable,"-c","import time; time.sleep(30)"]); Path("child.pid").write_text(str(p.pid))'
            child=None
            try:
                with patch.object(subprocess.Popen,'communicate',shortened):
                    with self.assertRaises(Barrier):
                        gate.run('timeout',{},lambda: command([sys.executable,'-c',code],root))
                child=int((root/'child.pid').read_text());os.kill(child,0)
                with gate.journal.transaction() as db:
                    row=dict(db.execute('select * from connections').fetchone())
                    self.assertEqual('half_open',row['state'])
                    self.assertEqual(1,db.execute('select count(*) from transports').fetchone()[0])
            finally:
                if child:
                    os.kill(child,signal.SIGTERM);deadline=time.monotonic()+5
                    while True:
                        try:os.kill(child,0)
                        except ProcessLookupError:break
                        self.assertLess(time.monotonic(),deadline);time.sleep(.02)
            gate.release_probe(row['owner']);permit=gate.operator_probe();gate.outcome(permit)

    def test_dead_integration_controller_cannot_release_live_transport(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            code='''import sys
from pathlib import Path
from foundry_runtime.core import Gate,Journal
from foundry_runtime.remote import GitHub,command
p=Path(sys.argv[1]);g=Gate(Journal(p/'gate.sqlite'),'shared')
h=GitHub.__new__(GitHub);h.repository='stemarie/context-foundry';h.gate=g
child="import os,time; from pathlib import Path; Path("+repr(str(p/'child.pid'))+").write_text(str(os.getpid())); time.sleep(60)"
with h.integration():
 g.run('old-integration',{},lambda: {'result':command([sys.executable,'-c',child],p)})
'''
            parent=subprocess.Popen([sys.executable,'-B','-c',code,str(root)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            child=None
            try:
                deadline=time.monotonic()+10
                while not (root/'child.pid').exists():
                    self.assertIsNone(parent.poll());self.assertLess(time.monotonic(),deadline);time.sleep(.02)
                child=int((root/'child.pid').read_text());parent.kill();parent.wait(timeout=5)
                os.kill(child,0)
                h=GitHub.__new__(GitHub);h.repository='stemarie/context-foundry';h.gate=Gate(Journal(root/'gate.sqlite'),'shared')
                for alias in ('shared','another-connection'):
                    h.gate=Gate(Journal(root/'gate.sqlite'),alias)
                    with self.assertRaises(Barrier):
                        with h.integration():self.fail('second integration admitted before transport stop')
            finally:
                if parent.poll() is None:parent.kill();parent.wait(timeout=5)
                if child:
                    try:os.kill(child,signal.SIGTERM)
                    except ProcessLookupError:pass
                    deadline=time.monotonic()+5
                    while True:
                        try:os.kill(child,0)
                        except ProcessLookupError:break
                        self.assertLess(time.monotonic(),deadline);time.sleep(.02)
            with h.integration():pass
            with h.gate.journal.transaction() as db:
                self.assertEqual(0,db.execute('select count(*) from transports').fetchone()[0])
                self.assertEqual('started',db.execute('select state from remote_operations').fetchone()[0])

if __name__=='__main__':unittest.main()
