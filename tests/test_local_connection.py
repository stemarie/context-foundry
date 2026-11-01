import json,os
from pathlib import Path
import signal
import tempfile
import unittest
from foundry_runtime.core import Barrier
from foundry_runtime.local_connection import credential,orderly_sigterm,private_json,rpc

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

    def test_sigterm_unwinds_and_restores_prior_handler(self):
        prior=signal.getsignal(signal.SIGTERM)
        restored=[]
        def previous(signum,frame):restored.append(signum)
        signal.signal(signal.SIGTERM,previous)
        try:
            with self.assertRaises(SystemExit) as stopped:
                with orderly_sigterm():
                    signal.raise_signal(signal.SIGTERM)
            self.assertEqual(128+signal.SIGTERM,stopped.exception.code)
            self.assertIs(signal.getsignal(signal.SIGTERM),previous)
            self.assertEqual([],restored)
        finally:
            signal.signal(signal.SIGTERM,prior)

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

if __name__=='__main__':unittest.main()
