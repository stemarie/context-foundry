#!/usr/bin/env python3
"""V2 Architect adapter: activate one AI.Contract record, then create one tracker."""
from __future__ import annotations
import hashlib, json, os, re, subprocess, sys, tempfile, urllib.error, urllib.request
from pathlib import Path
from typing import Any, Callable

PROFILE="foundry-architect"; BOARD="context-foundry"
AUTH_START="<!-- FOUNDRY_ARCHITECT_CONTRACT_ISSUE_AUTHORIZATION_V2\n"; AUTH_END="\n-->"
TASK=re.compile(r"^t_[0-9a-f]{8}$"); UUID=re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"); SHA=re.compile(r"^[0-9a-f]{40}$"); REPO=re.compile(r"^stemarie/[A-Za-z0-9][A-Za-z0-9._-]*$")
MARKER="FOUNDRY-ARCHITECT-CONTRACT-ISSUE-V2"
class ContractIssueError(RuntimeError): pass

def digest_for(contract_id:str,title:str,body:str)->str: return hashlib.sha256((contract_id+"\0"+"1\0"+title+"\0"+body).encode()).hexdigest()
def key(card:dict[str,Any], suffix:str)->str: return f"foundry:{card['id']}:{authorization(card)['contract']['id']}:{suffix}"
def marker_for(card:dict[str,Any])->str: return f"<!-- {MARKER}:{card['id']}:{authorization(card)['contract']['id']} -->"
def exact(value:Any, keys:set[str], label:str)->dict[str,Any]:
 if not isinstance(value,dict) or set(value)!=keys: raise ContractIssueError(label+" has unsupported or missing fields")
 return value

def authorization(card:dict[str,Any])->dict[str,Any]:
 if card.get('assignee')!=PROFILE or not str(card.get('title','')).startswith('Architect:'): raise ContractIssueError('card is not an assigned Architect card')
 if not isinstance(card.get('id'),str) or not TASK.fullmatch(card['id']): raise ContractIssueError('card task ID is invalid')
 body=card.get('body')
 if not isinstance(body,str) or body.count(AUTH_START)!=1 or body.count(AUTH_END)!=1: raise ContractIssueError('card requires exactly one V2 contract authorization block')
 try: scope=json.loads(body.split(AUTH_START,1)[1].split(AUTH_END,1)[0])
 except json.JSONDecodeError as e: raise ContractIssueError('V2 authorization is invalid JSON') from e
 scope=exact(scope,{'contract','target'},'V2 authorization')
 c=exact(scope['contract'],{'id','title','body_markdown'},'contract')
 t=exact(scope['target'],{'repository','origin','api_target','branch','worktree_path','base_sha','issue_title','issue_body'},'target')
 if not isinstance(c['id'],str) or not UUID.fullmatch(c['id']): raise ContractIssueError('contract ID is not a canonical UUID')
 for k in ('title','body_markdown'):
  if not isinstance(c[k],str) or not c[k].strip() or len(c[k])>60000: raise ContractIssueError('contract content is invalid')
 if not isinstance(t['repository'],str) or not REPO.fullmatch(t['repository']): raise ContractIssueError('target repository is invalid')
 if t['origin']!=f"https://github.com/{t['repository']}.git" or t['api_target']!=f"https://api.github.com/repos/{t['repository']}" or t['branch']!='main': raise ContractIssueError('target derivations are invalid')
 if not isinstance(t['worktree_path'],str) or not t['worktree_path'].startswith('/') or not isinstance(t['base_sha'],str) or not SHA.fullmatch(t['base_sha']): raise ContractIssueError('target worktree or base SHA is invalid')
 for k in ('issue_title','issue_body'):
  if not isinstance(t[k],str) or not t[k].strip() or len(t[k])>60000: raise ContractIssueError('tracker content is invalid')
 return scope

def validate_workspace(card:dict[str,Any], scope:dict[str,Any], git:Callable[...,str])->None:
 t=scope['target']; ws=card.get('workspace_path')
 base=os.path.realpath(t['worktree_path'])
 expected=os.path.join(base,'.worktrees',card['id'])
 if not isinstance(ws,str) or os.path.realpath(ws)!=expected: raise ContractIssueError('card workspace is not the authorized task worktree')
 if os.path.realpath(git(ws,'rev-parse','--show-toplevel'))!=os.path.realpath(ws): raise ContractIssueError('workspace is not its authorized Git root')
 if git(ws,'remote','get-url','origin')!=t['origin'] or git(ws,'status','--porcelain') or git(ws,'rev-parse','HEAD')!=t['base_sha']: raise ContractIssueError('workspace origin, cleanliness, or head differs from authorization')
 remote=git(ws,'ls-remote','origin','refs/heads/main').split()
 if len(remote)!=2 or remote[0]!=t['base_sha'] or remote[1]!='refs/heads/main': raise ContractIssueError('remote main differs from authorized base')
def credential_file() -> Path:
 return Path(os.environ.get('HERMES_REAL_HOME',str(Path.home()))) / '.hermes/profiles/foundry-architect/.env'
def github_token() -> str:
 env=credential_file(); token=next((x.split('=',1)[1].strip().strip('"').strip("'") for x in env.read_text().splitlines() if x.startswith('GITHUB_TOKEN=')), '')
 if not token: raise ContractIssueError('GitHub credential helper lacks token')
 return token
def git_output(ws:str,*args:str)->str:
 env=dict(os.environ); askpass=None
 if args and args[0]=='ls-remote':
  askpass=tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False)
  askpass.write('#!/bin/sh\nprintf "%s\\n" "$GITHUB_TOKEN"\n'); askpass.close(); os.chmod(askpass.name,0o700)
  env.update({'GITHUB_TOKEN':github_token(),'GIT_ASKPASS':askpass.name,'GIT_TERMINAL_PROMPT':'0'})
 try: r=subprocess.run(['git','-C',ws,*args],capture_output=True,text=True,timeout=30,env=env)
 finally:
  if askpass: Path(askpass.name).unlink(missing_ok=True)
 if r.returncode: raise ContractIssueError('could not read target Git state')
 return r.stdout.strip()
def service(method:str,path:str,payload:dict[str,Any]|None=None)->Any:
 client=os.environ.get('AI_CONTRACT_CLIENT','/home/karell/.hermes/scripts/aicontract_book_client.sh')
 if method not in {'GET','POST'} or not path.startswith('/api/v1/'): raise ContractIssueError('AI.Contract operation is outside adapter authority')
 with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',delete=False) as f:
  if payload is not None: json.dump(payload,f)
  payload_path=f.name
 try:
  r=subprocess.run([client,'architect',method,path]+([payload_path] if payload is not None else []),capture_output=True,text=True,timeout=45)
 finally: Path(payload_path).unlink(missing_ok=True)
 if r.returncode: raise ContractIssueError('AI.Contract request failed')
 try:return json.loads(r.stdout)
 except json.JSONDecodeError as e: raise ContractIssueError('AI.Contract returned invalid JSON') from e
def github(method:str,url:str,payload:dict[str,Any]|None=None)->Any:
 token=github_token()
 req=urllib.request.Request(url,data=None if payload is None else json.dumps(payload).encode(),method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=30) as x:return json.load(x)
 except urllib.error.HTTPError as e: raise ContractIssueError(f'GitHub returned HTTP {e.code}') from e
def issue_body(card:dict[str,Any],scope:dict[str,Any])->str:
 c=scope['contract']; return f"{marker_for(card)}\nAI.Contract: `{c['id']}` revision 1, digest `{digest_for(c['id'],c['title'],c['body_markdown'])}`.\n\n{scope['target']['issue_body']}"
def contract_readback(value:Any,scope:dict[str,Any])->None:
 c=scope['contract']; v=value.get('contract',value) if isinstance(value,dict) else {}
 if not isinstance(v,dict) or any(v.get(k)!=c[k] for k in ('id','title','body_markdown')) or v.get('contract_version')!='Alpha 1.0' or v.get('status')!='In Progress': raise ContractIssueError('AI.Contract read-back differs from authorization')
def execute(card:dict[str,Any],service_request:Callable[[str,str,dict[str,Any]|None],Any]=service,github_request:Callable[[str,str,dict[str,Any]|None],Any]=github,git:Callable[...,str]=git_output)->dict[str,Any]:
 scope=authorization(card); validate_workspace(card,scope,git); c=scope['contract']; t=scope['target']; digest=digest_for(c['id'],c['title'],c['body_markdown'])
 service_request('POST','/api/v1/chains',{'role':'architect','idempotency_key':key(card,'precreate'),'contracts':[{'id':c['id'],'title':c['title'],'body_markdown':c['body_markdown'],'status':'New'}]})
 service_request('POST',f"/api/v1/chain-contracts/{c['id']}/activate",{'role':'architect','revision':1,'digest':digest,'idempotency_key':key(card,'activate')})
 frozen=service_request('GET',f"/api/v1/chain-contracts/{c['id']}/frozen",None).get('frozen_revision',{})
 if frozen.get('revision')!=1 or frozen.get('digest')!=digest: raise ContractIssueError('frozen revision differs from authorization')
 contract_readback(service_request('GET',f"/api/v1/contracts/{c['id']}",None),scope)
 base=t['api_target']; repo=github_request('GET',base,None)
 if not isinstance(repo,dict) or repo.get('full_name')!=t['repository'] or repo.get('default_branch')!='main': raise ContractIssueError('GitHub target read-back differs from authorization')
 matches=[x for x in github_request('GET',base+'/issues?state=all&per_page=100',None) if marker_for(card) in str(x.get('body',''))]
 if len(matches)>1: raise ContractIssueError('multiple tracker Issues match contract marker')
 if matches: issue=github_request('GET',base+f"/issues/{matches[0]['number']}",None); operation='contract-activated-and-tracker-read-back'
 else: issue=github_request('POST',base+'/issues',{'title':t['issue_title'],'body':issue_body(card,scope)}); operation='contract-activated-and-tracker-created'
 if issue.get('title')!=t['issue_title'] or issue.get('body')!=issue_body(card,scope) or not isinstance(issue.get('number'),int): raise ContractIssueError('tracker read-back differs from authorization')
 return {'operation':operation,'contract_id':c['id'],'revision':1,'issue':issue['number'],'repository':t['repository']}
def live_card(task_id:str)->dict[str,Any]:
 r=subprocess.run(['hermes','kanban','--board',BOARD,'show',task_id,'--json'],capture_output=True,text=True,timeout=30)
 if r.returncode: raise ContractIssueError('could not read assigned Architect card')
 try: value=json.loads(r.stdout)
 except json.JSONDecodeError as e: raise ContractIssueError('assigned Architect card read-back is invalid') from e
 if not isinstance(value,dict) or not isinstance(value.get('task'),dict) or value['task'].get('id')!=task_id: raise ContractIssueError('assigned Architect card read-back is malformed')
 return value['task']
def main()->None:
 task_id=os.environ.get('HERMES_KANBAN_TASK')
 if not isinstance(task_id,str) or not TASK.fullmatch(task_id): raise ContractIssueError('adapter requires its assigned canonical HERMES_KANBAN_TASK')
 print(json.dumps(execute(live_card(task_id)),sort_keys=True))
if __name__=='__main__':
 try: main()
 except ContractIssueError as error:
  print(str(error),file=sys.stderr); raise SystemExit(2)
