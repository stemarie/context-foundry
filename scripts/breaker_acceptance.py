#!/usr/bin/env python3
"""Two actual disposable service projects; simulated GitHub failures, never a live outage."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
from urllib.parse import urlparse

from foundry_runtime.core import Barrier, Gate, Journal, RemoteFailure
from foundry_runtime.runtime import local_git, restricted_check


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ai-contract-checkout', type=Path, required=True)
    parser.add_argument('--service-binary', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('breaker_mock', args.ai_contract_checkout/'scripts/mock_client.py')
    mock = importlib.util.module_from_spec(spec); spec.loader.exec_module(mock)
    root = Path(tempfile.mkdtemp(prefix='cf-breaker-', dir='/private/tmp'))
    servers, projects = [], []
    report = {'scope':'Actual local service projects and durable gate; simulated GitHub transport/clock. No production failure injection.'}
    try:
        for number in (1, 2):
            directory = root/str(number); directory.mkdir()
            server = mock.LocalServer(str(args.service_binary), str(directory), 15); servers.append(server)
            origin = server.start(); client = mock.Client(origin, server.tokens, 'http', 15)
            project = client.call('project_create', {'title':'Disposable shared-breaker project '+str(number),
                'repository':'stemarie/context-foundry', 'delivery_policy':'Transport failure fixture only; no repository changes or deployment.'})['project']
            assert client.call('project_get', {'id':project['id']}, 'reader')['project']['id']==project['id']
            projects.append({'origin':origin,'project':project})
        path=root/'shared-runtime.sqlite'
        one,two=[Gate(Journal(path),'same-approved-github-connection') for _ in projects]
        now=time.time()
        one.outcome(one.acquire(now=now),'rate_limit',retry_after=90,now=now)
        for gate, project in zip((one,two),projects):
            try:gate.run('blocked:'+project['project']['id'],{},lambda: (_ for _ in ()).throw(AssertionError('transport bypass')))
            except Barrier:pass
            else:raise AssertionError('project bypassed open gate')
        local_git(Path(__file__).resolve().parents[1], 'diff', '--check')
        permits=[];lock=threading.Lock()
        def race(gate):
            try:
                permit=gate.acquire(now=now+91)
                with lock:permits.append(permit)
            except Barrier:pass
        threads=[threading.Thread(target=race,args=(gate,)) for gate in (one,two)]
        for thread in threads:thread.start()
        for thread in threads:thread.join()
        assert len(permits)==1
        one.outcome(permits[0],'connection',now=now+91)
        probe=two.operator_probe(now=now+92);two.outcome(probe,now=now+92)
        def missing():raise RemoteFailure('resource')
        try:one.run('ordinary-missing-resource',{},missing)
        except Barrier:pass
        assert two.acquire() is None
        fixture=[]
        def lost_response():
            fixture.append({'issue':1})
            raise RemoteFailure('connection')
        try:one.run('history-fixture',{'project_id':projects[0]['project']['id']},lost_response)
        except Barrier:pass
        probe=two.operator_probe();two.outcome(probe)
        result=two.run('history-fixture',{'project_id':projects[0]['project']['id']},lost_response,reconcile=lambda:fixture[0])
        assert result=={'issue':1} and len(fixture)==1
        workspace=root/'workspace';scratch=root/'scratch';workspace.mkdir();scratch.mkdir()
        port=urlparse(projects[0]['origin']).port
        check=restricted_check(workspace,['/Library/Developer/CommandLineTools/usr/bin/python3','-c',
            f"import socket\ntry:socket.create_connection(('127.0.0.1',{port}))\nexcept PermissionError:print('kernel denied connection to known live service')\nelse:raise AssertionError('raw transport bypass')"],scratch)
        assert check['passed'],check
        report.update(status='passed',projects=projects,shared_alias='same-approved-github-connection',
            both_projects_paused=True,local_git_continued=True,one_half_open_probe=True,
            failed_probe_reopened=True,operator_recovery=True,ordinary_resource_error_local=True,
            lost_issue_response_deduplicated=True,known_live_raw_network_denied=check)
    finally:
        for server in servers:server.stop()
        # Project records are preserved in the safe report; there are no work contracts in this fixture.
        args.report.write_text(json.dumps(report,indent=2)+'\n')
        shutil.rmtree(root)
    print('PASS actual two-project shared-gate fixture, simulated failures and owned cleanup')

if __name__=='__main__':main()
