#!/usr/bin/env python3
"""Final-source installed-Hermes version/body smoke in disposable state; no delivery."""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid

from foundry_runtime.core import Barrier, Journal
from foundry_runtime.runtime import Client, Launcher, local_git


def run(args):
    checkout=Path(__file__).resolve().parents[1]
    root=Path(tempfile.mkdtemp(prefix='cf-native-version-',dir='/private/tmp'));root.chmod(0o700)
    print('PRIVATE_FIXTURE',root,flush=True)
    spec=importlib.util.spec_from_file_location('native_version_mock',args.ai_contract_checkout/'scripts/mock_client.py')
    mock=importlib.util.module_from_spec(spec);spec.loader.exec_module(mock)
    server=mock.LocalServer(str(args.service_binary),str(root),15)
    journal=Journal(root/'runtime.sqlite');launcher=Launcher(journal,args.hermes_python,args.hermes_source)
    keys=[];trees=[];branches=[];pid=None;cid=None;work=None
    report={'scope':'Actual installed Hermes Worker and independent QA on a disposable fixture; no remote Git, native Done or deployment',
            'ai_contract_revision':local_git(args.ai_contract_checkout,'rev-parse','HEAD'),
            'hermes_revision':local_git(args.hermes_source,'rev-parse','HEAD'),
            'runtime_sha256':{str(p.relative_to(checkout)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((checkout/'foundry_runtime').glob('*.py'))},
            'status':'running'}
    def bound(job):
        return {'project_id':pid,'contract_id':cid,'revision':job['revision']['number'],'digest':job['revision']['digest'],'attempt_id':job['attempt']['id']}
    def wait(stages,key):
        deadline=time.monotonic()+300
        while time.monotonic()<deadline:
            job=work('get',{'contract_id':cid})['job']
            if job['stage'] in stages:return job
            if launcher.inspect(key)=='stopped':raise Barrier('native invocation stopped before required transition')
            time.sleep(.3)
        raise Barrier('native smoke transition timeout')
    try:
        for role,scopes in [('worker','read,write,writer'),('qa','read,write,auditor'),('coordinator','read,write,coordinator')]:
            issued=subprocess.run([str(args.service_binary),'token','issue','version-'+role,scopes],env=server.env,capture_output=True,text=True,check=True)
            server.tokens[role]=next(line[6:] for line in issued.stdout.splitlines() if line.startswith('token='))
        origin=server.start();api=mock.Client(origin,server.tokens,'http',15)
        def call(op,data,role='admin'):
            with contextlib.redirect_stdout(io.StringIO()):return api.call(op,data,role)
        project=call('project_create',{'title':'Disposable native version smoke','repository':'stemarie/context-foundry','delivery_policy':'Disposable fixture only; no push, integration, Done or deployment.'})['project'];pid=project['id']
        milestone=call('milestone_create',{'project_id':pid,'ordinal':1,'title':'Native semantic version','goal':'Verify current installed adapter model path','scope':'Local disposable fixture','acceptance_criteria':'Worker and independent QA consume checked semantic version and native body.'})['milestone']
        call('project_planning_boundary',{'project_id':pid,'through':1,'expected_revision':0})
        def workflow(op,data=None,role='coordinator'):
            data=dict(data or {},project_id=pid)
            if op not in ('get','history'):data['idempotency_key']=uuid.uuid4().hex
            return call('workflow_'+op,data,role)['workflow']
        work=workflow
        work('configure',{'queue_target':1},'admin')
        for role in ('worker','qa'):work('agent',{'agent':'version-'+role,'agent_role':role},'admin')
        marker='native-body-'+uuid.uuid4().hex
        ordinary=call('milestone_contract_create',{'project_id':pid,'milestone_id':milestone['id'],'title':'Disposable version fixture','body_markdown':'Historical ordinary body, not executable native instructions. Do not write the obsolete marker.'},'architect')['contract'];cid=ordinary['id']
        body=f'''# Objective
Create only `native_version_fixture.txt` in this disposable worktree. It must state the semantic contract version verified by your current assignment/prompt and include this exact native-body marker: {marker}.
# Authority and scope
This is an explicitly authorized local acceptance fixture, not repository product work. Read assignment to verify version and immutable native body. The ordinary original body is historical. No source changes, remote Git, integration, Done, issue publication or deployment.
# Acceptance and verification
Write the concise fixture, run the supplied check and submit a local candidate. Independent QA must read the exact candidate diff/file, inspect assignment's semantic version, run its own supplied check, and record an evidence-backed Accepted verdict only if all criteria pass. The Coordinator cancels this disposable fixture after both processes retire; nothing is delivered.
'''
        job=work('define',{'contract_id':cid,'expected_revision':0,'title':'Disposable version fixture','body_markdown':body,'dependencies':[],'conflicts':[]},'architect')['job']
        work('ready',{'contract_id':cid,'revision':job['revision']['number'],'digest':job['revision']['digest']},'architect')
        job=work('reserve',{'lease_seconds':300})['job']
        resolver=('from hermes_cli.runtime_provider import resolve_runtime_provider; import json; '
                  'r=resolve_runtime_provider(requested="openai-codex",target_model="gpt-5.6-terra"); '
                  'print(json.dumps({k:r[k] for k in ["provider","api_mode","api_key","base_url"]}))')
        result=subprocess.run([str(args.hermes_python),'-B','-c',resolver],env=dict(os.environ,PYTHONPATH=str(args.hermes_source),PYTHONDONTWRITEBYTECODE='1'),capture_output=True,text=True,check=True)
        runtime=json.loads(result.stdout)
        base=local_git(checkout,'rev-parse','HEAD')
        def launch(job,role,ref):
            branch='codex/version-'+role+'-'+uuid.uuid4().hex[:8];directory=root/role
            local_git(checkout,'worktree','add','-b',branch,str(directory),ref);trees.append(directory);branches.append(branch)
            home=root/('home-'+role);home.mkdir(mode=0o700);scratch=home/'scratch';scratch.mkdir(mode=0o700)
            binding=dict(bound(job),actor='version-'+role)
            if role=='qa':binding['candidate_id']=job['candidate']['id']
            instructions=(checkout/'skills'/('foundry-'+role)/'SKILL.md').read_text()
            for rel in ['skills/OPERATING_RULES.md','WORK_CONTRACT.md','docs/WORKFLOW.md']:instructions+='\n'+(checkout/rel).read_text()
            check='from pathlib import Path; t=Path("native_version_fixture.txt").read_text(); assert "Alpha 1.0" in t and '+repr(marker)+' in t'
            config={'origin':origin,'service_token':server.tokens[role],'binding':binding,'role':role,'workspace':str(directory),'base_sha':base,
                    'candidate_sha':job.get('candidate',{}).get('sha'),'home':str(home),'scratch':str(scratch),'model':'gpt-5.6-terra',
                    'role_instructions':instructions,'checks':['/Library/Developer/CommandLineTools/usr/bin/python3','-B','-E','-s','-c',check],
                    'heartbeat_seconds':2,'invocation_seconds':360}
            key=launcher.ensure(config,runtime);keys.append(key)
            assert launcher.ensure(config,runtime)==key
            work('record',{**bound(job),'evidence':json.dumps({'role':role,'runtime_launch':key,'pid':journal.get(key)['pid'],'source_runtime_sha256':report['runtime_sha256']})})
            print('LAUNCHED',role,flush=True)
            return key
        worker=launch(job,'worker','HEAD');submitted=wait(['QA'],worker)
        changed=local_git(root/'worker','diff','--name-only',base,submitted['candidate']['sha']).splitlines()
        assert changed==['native_version_fixture.txt']
        q=work('assign_qa',{'contract_id':cid})['job'];qa=launch(q,'qa',q['candidate']['sha'])
        accepted=wait(['QA accepted','Implementing','Blocked'],qa)
        if accepted['stage']!='QA accepted':raise Barrier('native QA did not accept fixture; inspect safe history')
        for key in (qa,worker):launcher.stop(key)
        assert all(launcher.inspect(key)=='stopped' for key in keys)
        current=work('cancel',{**bound(accepted),'stopped_confirmed':True,'evidence':'Actual installed Hermes Worker/QA proof complete; both owned processes stopped. Disposable fixture never delivered.'})['job']
        report.update(status='passed',project_id=pid,contract_id=cid,attempt_id=accepted['attempt']['id'],candidate_sha=accepted['candidate']['sha'],semantic_version='Alpha 1.0',
                      native_marker=marker,fixture_text=(root/'worker'/'native_version_fixture.txt').read_text(),stage_before_cleanup=accepted['stage'],final_stage=current['stage'])
    except Exception as exc:
        report.update(status='failed',failure_category=type(exc).__name__)
        raise
    finally:
        stopped=True
        for key in keys:
            try:launcher.stop(key)
            except Barrier:stopped=False
        if work is not None and cid:
            history={'events':[],'revisions':[]};after=0
            while True:
                page=work('history',{'contract_id':cid,'limit':100,'after':after},'reader')
                history['revisions']=page.get('revisions',[])
                events=page.get('events',[]);history['events'].extend(events)
                if len(events)<100:break
                assert events[-1]['id']>after
                after=events[-1]['id']
            report['history']=history
        report['runtime_events']=[json.loads(line) for file in sorted(root.glob('home-*/events.jsonl')) for line in file.read_text().splitlines()]
        report['runtime_hashes_unchanged']=all(hashlib.sha256((checkout/p).read_bytes()).hexdigest()==v for p,v in report['runtime_sha256'].items())
        server.stop()
        assert all(token not in (root/'server.log').read_text(errors='replace') for token in server.tokens.values())
        if stopped:
            for tree in trees:local_git(checkout,'worktree','remove','--force',str(tree))
            for branch in branches:local_git(checkout,'branch','-D',branch)
            shutil.rmtree(root)
        report['cleanup']={'owned_processes_stopped':stopped,'fixture_removed':not root.exists(),'service_stopped':True,'credential_log_scan':'passed'}
        args.report.write_text(json.dumps(report,indent=2)+'\n')
        assert stopped and report['runtime_hashes_unchanged']
    print('PASS actual Hermes Worker/QA version/native-body fixture; no delivery; owned state removed',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('ai-contract-checkout','service-binary','hermes-source','hermes-python','report'):parser.add_argument('--'+name,type=Path,required=True)
    run(parser.parse_args())
