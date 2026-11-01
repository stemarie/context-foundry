#!/usr/bin/env python3
"""Disposable real-service semantic-version proof; no model, delivery or deployment."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import uuid

from foundry_runtime.runtime import Client, command_binding, local_git


def run(args):
    spec = importlib.util.spec_from_file_location('followup_mock', args.ai_contract_checkout/'scripts/mock_client.py')
    mock = importlib.util.module_from_spec(spec); spec.loader.exec_module(mock)
    report = {'scope':'Actual local service and actor-bound adapter reads; no model/QA execution, remote delivery or deployment',
              'ai_contract_revision':local_git(args.ai_contract_checkout,'rev-parse','HEAD'),
              'service_binary_sha256':hashlib.sha256(args.service_binary.read_bytes()).hexdigest()}
    with tempfile.TemporaryDirectory(prefix='cf-followup-service-',dir='/private/tmp') as fixture:
        root = Path(fixture); root.chmod(0o700)
        server = mock.LocalServer(str(args.service_binary), str(root), 15)
        try:
            for role, scopes in [('worker','read,write,writer'),('qa','read,write,auditor'),('coordinator','read,write,coordinator')]:
                result = subprocess.run([str(args.service_binary),'token','issue','followup-'+role,scopes],
                                        env=server.env,capture_output=True,text=True,check=True)
                server.tokens[role] = next(line[6:] for line in result.stdout.splitlines() if line.startswith('token='))
            origin = server.start()
            api = mock.Client(origin,server.tokens,'http',15)
            def call(name, body, role='admin'):
                with contextlib.redirect_stdout(io.StringIO()): return api.call(name,body,role)
            project = call('project_create',{'title':'Disposable version proof','repository':'stemarie/context-foundry','delivery_policy':'No delivery or deployment.'})['project']
            pid = project['id']
            milestone = call('milestone_create',{'project_id':pid,'ordinal':1,'title':'Version reads','goal':'Verify semantic interpretation','scope':'Disposable local authority reads','acceptance_criteria':'Worker and QA read Alpha 1.0 independently of native revision.'})['milestone']
            call('project_planning_boundary',{'project_id':pid,'through':1,'expected_revision':0})
            def work(op, values=None, role='coordinator'):
                data = dict(values or {},project_id=pid)
                if op not in ('get','history'):data['idempotency_key']=uuid.uuid4().hex
                return call('workflow_'+op,data,role)['workflow']
            work('configure',{'queue_target':1},'admin')
            for role in ('worker','qa'):work('agent',{'agent':'followup-'+role,'agent_role':role},'admin')
            ordinary = call('milestone_contract_create',{'project_id':pid,'milestone_id':milestone['id'],'title':'Version authority fixture','body_markdown':'Ordinary original body; not native executable instructions.'},'architect')['contract']
            cid = ordinary['id']
            job = work('define',{'contract_id':cid,'expected_revision':0,'title':'Version authority fixture','body_markdown':'Native current body; read this separately from semantic version.','dependencies':[],'conflicts':[]},'architect')['job']
            work('ready',{'contract_id':cid,'revision':job['revision']['number'],'digest':job['revision']['digest']},'architect')
            job = work('reserve',{'lease_seconds':300})['job']
            binding = {'project_id':pid,'contract_id':cid,'revision':job['revision']['number'],'digest':job['revision']['digest'],'attempt_id':job['attempt']['id'],'actor':'followup-worker'}
            worker = Client(origin,server.tokens['worker'])
            actual = worker.authority(binding,'worker')
            assert actual['contract_version']=='Alpha 1.0' and actual['revision']['body_markdown']!=ordinary['body_markdown']
            # Real disposable local commit; this is a transport fixture, not model implementation or QA evidence.
            workspace = root/'candidate';workspace.mkdir()
            local_git(workspace,'init','-q');(workspace/'fixture.txt').write_text('Disposable version proof\n')
            local_git(workspace,'add','.');local_git(workspace,'-c','user.name=fixture','-c','user.email=fixture@localhost','commit','-qm','Disposable fixture')
            sha = local_git(workspace,'rev-parse','HEAD')
            worker.workflow('submit',{**command_binding(binding),'candidate_sha':sha,'evidence':'Actual local fixture commit; no model or independent QA execution claimed.','idempotency_key':'fixture-submit'})
            qa_job = work('assign_qa',{'contract_id':cid})['job']
            qa_binding = dict(binding,actor='followup-qa',candidate_id=qa_job['candidate']['id'])
            qa = Client(origin,server.tokens['qa']).authority(qa_binding,'qa')
            assert qa['contract_version']=='Alpha 1.0' and qa['candidate']['sha']==sha
            report.update(status='passed',worker_version=actual['contract_version'],qa_version=qa['contract_version'],native_body_remains_authoritative=True,
                          history=work('history',{'contract_id':cid,'limit':100},'reader'))
        finally:
            server.stop()
            log = (root/'server.log').read_text(errors='replace')
            assert all(token not in log for token in server.tokens.values())
    assert not root.exists()
    report['cleanup']={'service_stopped':True,'disposable_state_removed':True,'credential_log_scan':'passed'}
    args.report.write_text(json.dumps(report,indent=2)+'\n')
    print('PASS actual service Worker/QA semantic-version reads; canonical native body retained; owned state removed')

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('ai-contract-checkout','service-binary','report'):parser.add_argument('--'+name,type=Path,required=True)
    run(parser.parse_args())
