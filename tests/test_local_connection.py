import contextlib,io,json,os
from pathlib import Path
import signal,subprocess,sys,tempfile,threading,unittest
from unittest.mock import Mock,patch
from foundry_runtime.core import Barrier
from foundry_runtime.local_connection import _stop_owned_tunnel,credential,main,orderly_sigterm,private_json,rpc
from foundry_runtime.runtime import Tools,check_descriptor

class LocalConnectionTests(unittest.TestCase):
    def test_reader_bridge_filters_discovery_and_blocks_mutations(self):
        class Service:
            calls=[]
            def call(self,path,body):
                self.calls.append(body)
                if body['method']=='tools/list':return {'jsonrpc':'2.0','id':body['id'],'result':{'tools':[{'name':'workflow_get'},{'name':'workflow_reserve'},{'name':'contract_delete'}]}}
                return {'jsonrpc':'2.0','id':body['id'],'result':{'content':[{'type':'text','text':'fixture'}]}}
        service=Service()
        response=rpc(service,{'jsonrpc':'2.0','id':1,'method':'tools/list'})
        self.assertEqual(['workflow_get'],[t['name'] for t in response['result']['tools']])
        for tool in ['workflow_reserve','workflow_submit','contract_delete','project_create']:
            self.assertTrue(rpc(service,{'jsonrpc':'2.0','id':2,'method':'tools/call','params':{'name':tool}})['result']['isError'])
        self.assertEqual(1,len(service.calls))
        self.assertIsNone(rpc(service,{'jsonrpc':'2.0','method':'notifications/initialized'}))
        rpc(service,{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'workflow_get'}})
        self.assertEqual(2,len(service.calls))

    def test_main_preserves_integer_and_string_ids_for_upstream_errors(self):
        client=Mock();client.call.side_effect=[RuntimeError('private fixture detail'),RuntimeError('private fixture detail'),{'jsonrpc':'2.0','id':'wrong','result':{}}]
        input_lines='\n'.join([json.dumps(message) for message in [
            {'jsonrpc':'2.0','id':7002,'method':'ping'},
            {'jsonrpc':'2.0','id':'string-id','method':'ping'},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':'next','method':'ping'},
        ]])+'\n'
        output=io.StringIO()
        with patch('foundry_runtime.local_connection.private_json',return_value={'credentials':{}}),\
             patch('foundry_runtime.local_connection.credential',return_value={'token':'fixture-only'}),\
             patch('foundry_runtime.local_connection.tunnel',return_value=contextlib.nullcontext('http://fixture')) ,\
             patch('foundry_runtime.local_connection.Client',return_value=client),\
             patch.object(sys,'argv',['connection','--config','fixture','mcp-reader']),\
             patch.object(sys,'stdin',io.StringIO(input_lines)),patch.object(sys,'stdout',output):main()
        responses=[json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(3,len(responses));self.assertEqual([7002,'string-id','next'],[response['id'] for response in responses])
        for response in responses[:2]:
            self.assertEqual('private service request unavailable',response['error']['message'])
            self.assertNotIn('fixture detail',response['error']['message'])

    def test_invalid_ids_are_bounded_and_notifications_do_not_reply(self):
        invalid=rpc(Mock(),{'jsonrpc':'2.0','id':False,'method':'invalid'})
        self.assertEqual(None,invalid['id']);self.assertEqual(-32600,invalid['error']['code'])
        self.assertEqual(None,rpc(Mock(),{'jsonrpc':'2.0','method':'notifications/initialized'}))
        self.assertEqual(-32600,rpc(Mock(),['not','a','message'])['error']['code'])

    def test_control_timeout_escalates_only_owned_child_and_confirms_exit(self):
        process=Mock();process.poll.side_effect=[None,0];process.wait.side_effect=[subprocess.TimeoutExpired(['ssh'],5),None]
        with patch('foundry_runtime.local_connection.subprocess.run',side_effect=subprocess.TimeoutExpired(['ssh'],5)):
            self.assertTrue(_stop_owned_tunnel(process,'/private/tmp/control','fixture@host'))
        process.terminate.assert_called_once_with();process.kill.assert_not_called();self.assertEqual(2,process.wait.call_count)

    def test_nonzero_control_exit_still_stops_owned_child(self):
        process=Mock();process.poll.side_effect=[None,0];process.wait.return_value=None
        with patch('foundry_runtime.local_connection.subprocess.run',return_value=Mock(returncode=255)):
            self.assertTrue(_stop_owned_tunnel(process,'/private/tmp/control','fixture@host'))
        process.wait.assert_called_once_with(timeout=5);process.terminate.assert_not_called();process.kill.assert_not_called()

    def test_unconfirmed_cleanup_fails_closed_without_unrelated_signal(self):
        process=Mock();process.poll.return_value=None;process.wait.side_effect=[subprocess.TimeoutExpired(['ssh'],5)]*3
        with patch('foundry_runtime.local_connection.subprocess.run',return_value=Mock(returncode=1)):
            with self.assertRaises(Barrier):_stop_owned_tunnel(process,'/private/tmp/control','fixture@host')
        process.terminate.assert_called_once_with();process.kill.assert_called_once_with()

    def test_sigterm_unwinds_and_restores_prior_handler(self):
        prior=signal.getsignal(signal.SIGTERM);restored=[]
        def previous(signum,frame):restored.append(signum)
        signal.signal(signal.SIGTERM,previous)
        try:
            with self.assertRaises(SystemExit) as stopped:
                with orderly_sigterm():signal.raise_signal(signal.SIGTERM)
            self.assertEqual(128+signal.SIGTERM,stopped.exception.code)
            self.assertIs(signal.getsignal(signal.SIGTERM),previous);self.assertEqual([],restored)
        finally:signal.signal(signal.SIGTERM,prior)

    def test_private_role_credentials_reject_admin_and_insecure_files(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/'reader.json';path.write_text(json.dumps({'token':'fixture-only','scopes':['read']}));path.chmod(0o600)
            config={'credentials':{'reader':str(path)}}
            self.assertEqual('fixture-only',credential(config,'reader')['token'])
            path.chmod(0o644)
            with self.assertRaises(Barrier):private_json(path)
            path.chmod(0o600);path.write_text(json.dumps({'token':'fixture-only','scopes':['admin']}))
            with self.assertRaises(Barrier):credential(config,'reader')
            link=Path(root)/'link';link.symlink_to(path)
            with self.assertRaises(Barrier):private_json(link)

    def test_check_descriptor_is_deterministic_and_binds_actual_execution_context(self):
        base=check_descriptor(['/usr/bin/python3','-m','unittest'],'/private/tmp/candidate')
        self.assertEqual(['/usr/bin/python3','-m','unittest'],base['argv']);self.assertEqual('macos sandbox-exec',base['backend'])
        self.assertEqual(base,check_descriptor(base['argv'],base['cwd']))
        self.assertNotEqual(base['identity'],check_descriptor(['/usr/bin/python3','-m','other'],'/private/tmp/candidate')['identity'])
        self.assertNotEqual(base['identity'],check_descriptor(base['argv'],'/private/tmp/other')['identity'])
        self.assertNotEqual(base['identity'],check_descriptor(base['argv'],base['cwd'],'other backend')['identity'])

    def test_qa_verdict_persists_adapter_check_descriptor_not_model_summary(self):
        candidate='a'*40
        tools=Tools.__new__(Tools)
        tools.role='qa';tools.binding={'project_id':'project','contract_id':'contract','revision':1,'digest':'digest','attempt_id':'attempt','actor':'qa','candidate_id':'candidate-id'}
        tools.config={'candidate_sha':candidate};tools.workspace=Path('/private/tmp/candidate')
        tools.checks={'passed':True,'command':check_descriptor(['python3','-m','unittest'],'/private/tmp/candidate')}
        tools.calls=[];tools.lock=threading.RLock();tools.client=Mock()
        tools.client.authority.return_value={'stage':'QA','reviewer':'qa','candidate':{'id':'candidate-id'}}
        with patch('foundry_runtime.runtime.local_git',side_effect=lambda workspace,*args: '' if args[0]=='status' else candidate):
            Tools._invoke(tools,'verdict',{'verdict':'Accepted','summary':'ran a different command'})
        payload=tools.client.workflow.call_args.args[1]
        evidence=json.loads(payload['evidence'])
        self.assertEqual(tools.checks['command'],evidence['checks']['command'])
        self.assertEqual('ran a different command',evidence['summary'])

if __name__=='__main__':unittest.main()
