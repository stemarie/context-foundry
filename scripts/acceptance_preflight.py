#!/usr/bin/env python3
"""Available prerequisites only: never starts an agent or asserts native Done."""
import argparse,importlib.util,json,os,pathlib,subprocess,tempfile,shutil
parser=argparse.ArgumentParser(description="Run disposable service/skill prerequisites only; this is not real-agent acceptance.")
parser.add_argument('--ai-contract-checkout',required=True,type=pathlib.Path)
parser.add_argument('--service-binary',required=True,type=pathlib.Path)
parser.add_argument('--hermes-source',required=True,type=pathlib.Path)
parser.add_argument('--hermes-python',required=True,type=pathlib.Path)
args=parser.parse_args()
AIC=args.ai_contract_checkout.resolve()
BINARY=args.service_binary.resolve()
FOUNDRY=pathlib.Path(__file__).resolve().parents[1]
HERMES=args.hermes_source.resolve()
# Preserve the virtualenv launcher path; resolving its symlink loses that environment.
PYTHON=args.hermes_python.absolute()
for path in [BINARY,PYTHON,AIC/'scripts/mock_client.py',AIC/'cmd/aicontract/hermes_native_mcp_container_proof.py',HERMES/'tools/mcp_tool.py']:
 if not path.is_file():parser.error('required local acceptance prerequisite is absent')
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
mock=load('cf_mock',AIC/'scripts/mock_client.py')
native=load('cf_native',AIC/'cmd/aicontract/hermes_native_mcp_container_proof.py')
fixture=pathlib.Path(tempfile.mkdtemp(prefix='cf-service-preflight-',dir='/private/tmp'))
server=None
try:
 server=mock.LocalServer(str(BINARY),str(fixture),15)
 tokens=server.tokens
 for actor,scopes in [('coordinator','read,write,coordinator'),('worker','read,write,writer'),('qa','read,write,auditor')]:
  result=subprocess.run([str(BINARY),'token','issue','acceptance-'+actor,scopes],env=server.env,text=True,capture_output=True,check=True)
  tokens[actor]=next(line[6:] for line in result.stdout.splitlines() if line.startswith('token='))
 url=server.start();client=mock.Client(url,tokens,'http',10)
 project=client.call('project_create',{'title':'Disposable real-agent acceptance','repository':'stemarie/context-foundry','delivery_policy':'Direct main only after actual independent QA and verified non-force delivery; no deployment.'})['project']
 pid=project['id']
 milestone=client.call('milestone_create',{'project_id':pid,'ordinal':1,'title':'Real-agent acceptance','goal':'Verify the existing service and identify required external runtime prerequisites.','scope':'Disposable local acceptance; do not fabricate runtime assignment or completion.','acceptance_criteria':'Current skill and native service discovery; subsequent runtime/real-Git gates require their actual adapter implementation.'})['milestone']
 client.call('project_planning_boundary',{'project_id':pid,'through':1,'expected_revision':0})
 client.call('workflow_configure',{'project_id':pid,'queue_target':2,'idempotency_key':'preflight-config'})
 for actor,role in [('worker','worker'),('qa','qa')]:
  client.call('workflow_agent',{'project_id':pid,'agent':'acceptance-'+actor,'agent_role':role,'idempotency_key':'preflight-agent-'+actor})
 for actor in ['coordinator','worker','qa']:
  home=fixture/('home-'+actor);home.mkdir(mode=0o700)
  native.write_native_home(home,url,tokens[actor])
  config=json.loads((home/'config.yaml').read_text());config['skills']={'external_dirs':[str(FOUNDRY/'skills')]};(home/'config.yaml').write_text(json.dumps(config));(home/'config.yaml').chmod(0o600)
  result=native.native_call(HERMES,PYTHON,home,'mcp__ai_contract_test__workflow_agents',{'project_id':pid})
  assert {(a['actor'],a['role']) for a in result['workflow']['agents']}=={('acceptance-worker','worker'),('acceptance-qa','qa')}
  print('PASS native Hermes workflow_agents:',actor)
  if actor!='coordinator':
   denial_script=r"""
import json
from tools.mcp_tool_discovery import discover_mcp_tools
from tools.mcp_tool_lifecycle import shutdown_mcp_servers
from tools.registry import registry
import sys
name='mcp__ai_contract_test__workflow_reserve'
try:
 assert name in discover_mcp_tools()
 entry=registry.get_entry(name);assert entry is not None
 result=json.loads(entry.handler(json.loads(sys.argv[1])))
 assert 'error' in result and 'forbidden' in str(result['error']), 'native prohibited action was not rejected'
 print('PASS actual native Hermes prohibited Coordinator action')
finally:shutdown_mcp_servers()
"""
   denial_env={k:v for k,v in os.environ.items() if not k.startswith('HERMES_')};denial_env.update(HERMES_HOME=str(home),PYTHONPATH=str(HERMES),PYTHONDONTWRITEBYTECODE='1')
   subprocess.run([str(PYTHON),'-c',denial_script,json.dumps({'project_id':pid,'idempotency_key':'prohibited-'+actor})],env=denial_env,check=True)
   assignments=native.native_call(HERMES,PYTHON,home,'mcp__ai_contract_test__workflow_assignments',{'project_id':pid})
   assert not assignments['workflow'].get('jobs')
   print('PASS actor-bound empty assignments and prohibited Coordinator action:',actor)
 home=fixture/'home-worker'
 env={k:v for k,v in os.environ.items() if not k.startswith('HERMES_')};env.update(HERMES_HOME=str(home),PYTHONPATH=str(HERMES),PYTHONDONTWRITEBYTECODE='1')
 script=r'''
import json,sys
from pathlib import Path
from tools.skills_tool import _skill_catalog,skill_view
from tools.mcp_tool_discovery import discover_mcp_tools
from tools.mcp_tool_lifecycle import shutdown_mcp_servers
try:
 required={'mcp__ai_contract_test__workflow_'+op for op in ['get','define','ready','reserve','assignments','submit','verdict','integrate','complete']}
 assert required <= set(discover_mcp_tools())
 print('PASS actual Hermes required native workflow tool discovery')
finally:shutdown_mcp_servers()
root=Path(sys.argv[1]);names=['foundry-architect','foundry-coordinator','foundry-worker','foundry-qa']
for name in names:
 rows=[s for s in _skill_catalog() if s['name']==name and s['load_name']==name]
 assert len(rows)==1 and rows[0]['path'].resolve()==root/'skills'/name/'SKILL.md',name
 data=json.loads(skill_view(name,preprocess=False));assert data['success'] and data['content'],name
 print('PASS actual Hermes skill discovery/read:',name)
for rel in ['WORK_CONTRACT.md','docs/WORKFLOW.md','skills/OPERATING_RULES.md','skills/AI_CONTRACT_INTERFACE.md']:
 assert (root/rel).read_text().strip()
print('PASS all shared references readable in owning checkout')
'''
 subprocess.run([str(PYTHON),'-c',script,str(FOUNDRY)],env=env,check=True)
 print('PASS disposable preflight; no contract reserved, no agent/model launched, no Done or Git delivery asserted')
finally:
 if server is not None:server.stop()
 if fixture.exists():
  logs=(fixture/'server.log').read_text(errors='replace') if (fixture/'server.log').exists() else ''
  if server is not None:assert all(t not in logs for t in server.tokens.values())
  shutil.rmtree(fixture)
 assert not fixture.exists()
 print('PASS service process, local credentials, native homes and SQLite fixture removed')
