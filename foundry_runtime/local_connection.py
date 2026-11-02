"""Operator-invoked private BEE1 connection and read-only stdio MCP bridge.

Role credentials remain files outside workspaces. This module grants no work
ownership and installs no background service or scheduler.
"""
from __future__ import annotations
import argparse
import contextlib
import json
import os
from pathlib import Path
import shutil
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time

from .core import Barrier
from .runtime import Client

READ_TOOLS = {'contract_get','contract_list_by_status','contract_backlinks','chain_frozen','chain_evidence',
              'project_get','project_list','milestone_get','milestone_list','milestone_contract_list',
              'contract_assignment','workflow_get','workflow_list','workflow_history','workflow_agents','workflow_assignments'}


def private_json(path):
    path=Path(path);info=path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.getuid() or info.st_mode & 0o077:
        raise Barrier('connection/credential file must be owned, regular and private')
    return json.loads(path.read_text())


def credential(config, role):
    if role not in {'reader','architect','coordinator','worker','qa'}:
        raise Barrier('role not configured for local execution')
    value=private_json(config['credentials'][role])
    expected={'reader':{'read'},'architect':{'read','write','architect'},'coordinator':{'read','write','coordinator'},
              'worker':{'read','write','writer'},'qa':{'read','write','auditor'}}[role]
    if set(value['scopes'])!=expected or 'admin' in value['scopes']:
        raise Barrier('role credential scopes do not match the configured capability')
    return value


@contextlib.contextmanager
def orderly_sigterm():
    """Turn routine SIGTERM into stack unwinding while owned cleanup is active."""
    if threading.current_thread() is not threading.main_thread():
        raise Barrier('SIGTERM lifecycle protection requires the main thread')
    previous = signal.getsignal(signal.SIGTERM)

    def terminate(signum, frame):
        raise SystemExit(128 + signum)

    try:
        signal.signal(signal.SIGTERM, terminate)
    except (OSError, ValueError) as exc:
        raise Barrier('SIGTERM lifecycle protection could not be established') from exc
    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def _stop_owned_tunnel(process, control, target):
    """Close only this Popen child, retaining its control identity on uncertainty."""
    try:
        if process.poll() is None:
            try:
                subprocess.run(['ssh','-S',control,'-O','exit',target],capture_output=True,timeout=5)
            except (OSError, subprocess.TimeoutExpired):
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        raise Barrier('owned SSH shutdown unconfirmed; reconciliation identity retained') from None
        if process.poll() is None:
            raise Barrier('owned SSH shutdown unconfirmed; reconciliation identity retained')
        return True
    except Barrier:
        raise
    except (OSError, subprocess.TimeoutExpired):
        raise Barrier('owned SSH shutdown unconfirmed; reconciliation identity retained') from None


@contextlib.contextmanager
def tunnel(config, port=0):
    ssh=config['ssh']
    if ssh['target']!='karell@192.168.1.176' or ssh['remote_host']!='127.0.0.1' or ssh['remote_port']!=18080:
        raise Barrier('connection does not match the commissioned private service')
    if not port:
        with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    name=tempfile.mkdtemp(prefix='cf-ssh-',dir='/private/tmp')
    confirmed=False
    control=str(Path(name)/'master')
    command=['ssh','-M','-S',control,'-o','ControlPersist=no','-o','ControlMaster=yes',
             '-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ExitOnForwardFailure=yes',
             '-o','ConnectTimeout=10','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
             '-i',ssh['identity_file'],'-N','-L',f'127.0.0.1:{port}:127.0.0.1:18080',ssh['target']]
    try:
        with orderly_sigterm(), tempfile.TemporaryFile() as log:
            process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=log)
            try:
                deadline=time.monotonic()+15
                while time.monotonic()<deadline:
                    if process.poll() is not None:raise Barrier('private SSH connection could not start')
                    if Path(control).exists():
                        checked=subprocess.run(['ssh','-S',control,'-O','check',ssh['target']],capture_output=True,timeout=5)
                        if checked.returncode==0:break
                    time.sleep(.05)
                else:raise Barrier('private SSH connection readiness unknown')
                yield 'http://127.0.0.1:'+str(port)
            finally:
                confirmed=_stop_owned_tunnel(process,control,ssh['target'])
    finally:
        if confirmed:
            shutil.rmtree(name)


def request_id(message):
    value=message.get('id') if isinstance(message,dict) and 'id' in message else None
    return value if isinstance(value,(int,str)) and not isinstance(value,bool) else None


def rpc(client, message):
    if not isinstance(message,dict) or message.get('jsonrpc')!='2.0':
        return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'invalid MCP request'}}
    if 'id' not in message:
        return None
    identifier=request_id(message)
    if identifier is None:
        return {'jsonrpc':'2.0','id':None,'error':{'code':-32600,'message':'invalid MCP request'}}
    response={'jsonrpc':'2.0','id':identifier}
    method=message.get('method');params=message.get('params') or {}
    if method=='tools/call' and (not isinstance(params,dict) or params.get('name') not in READ_TOOLS):
        return {**response,'result':{'isError':True,'content':[{'type':'text','text':'This local connection is read-only; use actor-bound Foundry execution for mutations.'}]}}
    if method not in {'initialize','ping','tools/list','tools/call'}:
        return {**response,'error':{'code':-32601,'message':'method unavailable on read-only connection'}}
    result=client.call('/mcp',message)
    if not isinstance(result,dict):
        raise Barrier('private service returned invalid MCP response')
    result['id']=identifier
    if method=='tools/list' and 'result' in result:
        result['result']['tools']=[t for t in result['result'].get('tools',[]) if t['name'] in READ_TOOLS]
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('operation',choices=['status','mcp-reader']);args=parser.parse_args()
    config=private_json(args.config);reader=credential(config,'reader')
    with tunnel(config) as origin:
        client=Client(origin,reader['token'])
        if args.operation=='status':
            project=client.call('/api/v1/projects/'+config['project_id'],method='GET')['project']
            agents=client.workflow('agents',{'project_id':config['project_id']})
            result={'repository':project['repository'],'project_id':project['id'],'planning_through':project['planning_through'],
                    'agents':agents.get('agents',[]),'queue_target':agents.get('queue_target'),'service_ready':client.call('/readyz',method='GET')['status']=='ok'}
            if config.get('last_contract_id'):
                result['job']=client.workflow('get',{'project_id':config['project_id'],'contract_id':config['last_contract_id']})['job']
            print(json.dumps(result))
        else:
            for line in sys.stdin:
                message=None
                try:
                    message=json.loads(line)
                    result=rpc(client,message)
                except Exception:
                    identifier=request_id(message)
                    result=None if isinstance(message,dict) and 'id' not in message else {'jsonrpc':'2.0','id':identifier,'error':{'code':-32603,'message':'private service request unavailable'}}
                if result is not None:print(json.dumps(result),flush=True)

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('Local Foundry connection failed: '+type(exc).__name__,file=sys.stderr);raise SystemExit(2)
