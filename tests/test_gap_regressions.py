"""Audit regressions. Host-only: local Git/process tests do not run in candidate checks."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from foundry_runtime import runtime
from foundry_runtime.core import Barrier, Gate, Journal, RemoteFailure
from foundry_runtime.remote import command


class GapRegressions(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root/'workspace'; self.workspace.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def tools(self, role='worker'):
        config={'origin':'http://127.0.0.1:1','service_token':'fixture-only','role':role,
                'binding':{'project_id':'p','contract_id':'c','revision':1,'digest':'d','attempt_id':'a','actor':'fixture'},
                'workspace':str(self.workspace),'base_sha':'base','runtime_journal':str(self.root/'runtime.sqlite')}
        return runtime.Tools(config)

    def test_candidate_modules_never_run_during_native_startup(self):
        factory=getattr(runtime,'native_worker_command',None)
        self.assertIsNotNone(factory,'startup needs an isolated trusted import path')
        source=self.root/'hermes';source.mkdir()
        adapter=self.root/'adapter';(adapter/'foundry_runtime').mkdir(parents=True)
        (source/'run_agent.py').write_text('class AIAgent: pass\n')
        (adapter/'foundry_runtime/__init__.py').write_text('')
        (adapter/'foundry_runtime/worker.py').write_text('import json,sys\np=json.load(sys.stdin)\nassert p["sentinel"]=="fixture-only"\nprint("trusted worker")\n')
        poison='raise RuntimeError("candidate module executed")\n'
        for name in ['run_agent.py','json.py','sitecustomize.py','usercustomize.py']:
            (self.workspace/name).write_text(poison)
        (self.workspace/'foundry_runtime').mkdir()
        (self.workspace/'foundry_runtime/__init__.py').write_text(poison)
        result=subprocess.run(factory(sys.executable,source,adapter),cwd=self.workspace,
                              input=json.dumps({'sentinel':'fixture-only'}),capture_output=True,text=True)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual('trusted worker',result.stdout.strip())

    def test_submission_retry_reuses_commit_and_identical_request_after_restart(self):
        git=lambda *args:runtime.local_git(self.workspace,*args)
        git('init','-q');(self.workspace/'work.txt').write_text('before')
        git('add','.');git('-c','user.name=fixture','-c','user.email=fixture@localhost','commit','-qm','base')
        tools=self.tools();tools.config['base_sha']=git('rev-parse','HEAD')
        class Service:
            calls=[]
            def authority(self,*args):return {'stage':'Implementing'}
            def workflow(self,operation,body):
                self.calls.append(body)
                if len(self.calls)==1:raise Barrier('fixture unavailable before acceptance')
                return {'job':{'stage':'QA','candidate':{'sha':body['candidate_sha']}}}
        service=Service();tools.client=service
        (self.workspace/'work.txt').write_text('after')
        tools.checks={'passed':True,'exit_code':0};tools.checked_snapshot=runtime.snapshot(self.workspace)
        with self.assertRaises(Barrier):tools.invoke('submit',{'summary':'fixture candidate'})
        sha=git('rev-parse','HEAD')
        # A successor process reconstructs transport intent, never another queue.
        restarted=runtime.Tools(tools.config);restarted.client=service
        restarted.checks={'passed':True,'exit_code':0};restarted.checked_snapshot=runtime.snapshot(self.workspace)
        result=restarted.invoke('submit',{'summary':'fixture candidate'})
        self.assertEqual('QA',result['job']['stage'])
        self.assertEqual(sha,git('rev-parse','HEAD'))
        self.assertEqual(2,len(service.calls));self.assertEqual(service.calls[0],service.calls[1])

    def test_assignment_finds_review_after_first_history_page(self):
        tools=self.tools()
        events=[{'id':i,'operation':'heartbeat'} for i in range(1,151)]
        events[105]={'id':106,'operation':'verdict','evidence':'current QA corrections','job':{'revision':{'number':1,'digest':'d'},'attempt':{'id':'a'}}}
        events[145]={'id':146,'operation':'verdict','evidence':'stale different attempt','job':{'revision':{'number':1,'digest':'d'},'attempt':{'id':'other'}}}
        class Service:
            def authority(self,*args):return {'stage':'Implementing'}
            def workflow(self,operation,body):
                return {'events':[e for e in events if e['id']>body.get('after',0)][:body.get('limit',50)]}
        tools.client=Service();result=tools.invoke('assignment',{})
        self.assertEqual(150,result['history'][-1]['id'])
        self.assertEqual(106,result['latest_review']['id'])

    def test_read_and_diff_pages_reconstruct_full_stable_content(self):
        tools=self.tools('qa')
        class Service:
            def authority(self,*args):return {'stage':'QA'}
        tools.client=Service();text='a'*64000+'important tail'
        (self.workspace/'large.txt').write_text(text)
        for operation in ['read','diff']:
            with patch('foundry_runtime.runtime.local_git',return_value=text):
                first=tools.invoke(operation,{'path':'large.txt'})
                self.assertTrue(first['truncated']);self.assertEqual(64000,first['next_offset'])
                second=tools.invoke(operation,{'path':'large.txt','offset':first['next_offset'],'version':first['version']})
                field='content' if operation=='read' else 'diff'
                self.assertEqual(text,first[field]+second[field]);self.assertIsNone(second['next_offset'])
                with self.assertRaises(Barrier):tools.invoke(operation,{'path':'large.txt','offset':1,'version':'wrong-version'})

    def test_local_rejection_releases_half_open_probe_without_claiming_health(self):
        gate=Gate(Journal(self.root/'gate.sqlite'),'shared')
        gate.outcome(gate.acquire(now=0),'connection',now=0)
        def rejected():raise Barrier('stale authority, no remote request made')
        with self.assertRaises(Barrier):gate.run('rejected',{},rejected)
        with gate.journal.transaction() as db:
            self.assertEqual('open',db.execute('select state from connections').fetchone()[0])
        permit=gate.operator_probe();gate.outcome(permit)
        self.assertIsNone(gate.acquire())

    def test_dead_probe_owner_can_be_recovered_but_live_owner_cannot(self):
        path=self.root/'dead-probe.sqlite'
        code="from foundry_runtime.core import Journal,Gate; import sys; g=Gate(Journal(sys.argv[1]),'shared'); g.outcome(g.acquire(now=0),'connection',now=0); g.acquire(now=31)"
        subprocess.run([sys.executable,'-c',code,str(path)],check=True)
        gate=Gate(Journal(path),'shared');permit=gate.operator_probe()
        with self.assertRaises(Barrier):gate.operator_probe()
        gate.outcome(permit)
        self.assertIsNone(gate.acquire())

    def test_server_reset_blocks_automatic_and_operator_early_probes(self):
        gate=Gate(Journal(self.root/'reset.sqlite'),'shared')
        gate.outcome(gate.acquire(now=1000),'rate_limit',retry_after=3600,now=1000)
        with self.assertRaises(Barrier):gate.acquire(now=2000)
        with self.assertRaises(Barrier):gate.operator_probe(now=2000)
        permit=gate.acquire(now=4600);gate.outcome(permit,now=4600)
        self.assertIsNone(gate.acquire(now=4601))

    def test_cached_result_race_releases_probe_without_claiming_network_health(self):
        gate=Gate(Journal(self.root/'race.sqlite'),'shared')
        gate.outcome(gate.acquire(now=0),'connection',now=0)
        from foundry_runtime.core import digest
        with gate.journal.transaction() as db:
            db.execute("INSERT INTO remote_operations VALUES(?,?,?,'started',NULL)",('race','shared',digest({})))
        acquire=gate.acquire
        def racing_acquire():
            permit=acquire()
            with gate.journal.transaction() as db:
                db.execute("UPDATE remote_operations SET state='complete',result=? WHERE identity='race'",(json.dumps({'sha':'cached'}),))
            return permit
        with patch.object(gate,'acquire',side_effect=racing_acquire):
            self.assertEqual({'sha':'cached'},gate.run('race',{},lambda:self.fail('duplicate operation')))
        with gate.journal.transaction() as db:
            self.assertEqual('open',db.execute('SELECT state FROM connections').fetchone()[0])
        permit=gate.operator_probe();gate.outcome(permit)

    def test_transport_diagnostics_are_classified_without_raw_error_text(self):
        import urllib.error
        from foundry_runtime.runtime import Client, ServiceUnavailable
        client=Client('http://127.0.0.1:1','fixture-only')
        cases=[(ConnectionRefusedError('secret driver detail'),'connection_refused'),
               (TimeoutError('secret driver detail'),'timeout'),
               (ConnectionResetError('secret driver detail'),'connection_reset')]
        for cause,expected in cases:
            with patch.object(client.opener,'open',side_effect=urllib.error.URLError(cause)):
                with self.assertRaises(ServiceUnavailable) as result:client.workflow('get',{})
                self.assertEqual(expected,result.exception.category)
                self.assertNotIn('secret driver detail',str(result.exception))

    def test_resource_status_and_server_reset_are_parsed_from_response_metadata(self):
        samples=[('HTTP 404: Not Found; request id abc401def','resource',None),
                 ('< HTTP/2 403\n< X-RateLimit-Remaining: 0\n< X-RateLimit-Reset: 4600\nAPI rate limit exceeded','rate_limit',3600),
                 ('< HTTP/2 403\n< X-RateLimit-Remaining: 0\n< X-RateLimit-Reset: 4600\ngh: API rate limit exceeded (HTTP 403)','rate_limit',3600),
                 ('HTTP 403: insufficient repository permission','resource',None)]
        for stderr,category,delay in samples:
            with patch('subprocess.run',return_value=subprocess.CompletedProcess([],1,'',stderr)),patch('foundry_runtime.remote.time.time',return_value=1000):
                with self.assertRaises(RemoteFailure) as caught:command(['gh','fixture'],self.workspace)
                self.assertEqual(category,caught.exception.category);self.assertEqual(delay,caught.exception.retry_after)


if __name__=='__main__':unittest.main()
