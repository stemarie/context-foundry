#!/usr/bin/env python3
"""Bounded real installed-Hermes acceptance. Explicit local inputs; no deployment.

Private fixture data is kept outside the checkout. Safe evidence is exported
before local service cleanup. A failed scenario never fabricates a receipt.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from foundry_runtime.core import Barrier, Gate, Journal
from foundry_runtime.runtime import Client, Launcher, ServiceError, local_git
from foundry_runtime.remote import GitHub


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_report(path, report):
    """Keep the previous evidence intact if capacity or atomic publication fails."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', prefix='.acceptance-', dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(report, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        return True
    except OSError:
        print('REPORT_UNAVAILABLE private canonical fixture must be retained', flush=True)
        return False
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def run(args):
    checkout = Path(__file__).resolve().parents[1]
    root = Path(tempfile.mkdtemp(prefix='cf-real-agent-', dir='/private/tmp'))
    root.chmod(0o700)
    print('PRIVATE_FIXTURE', root, flush=True)
    mock = load('acceptance_mock', args.ai_contract_checkout / 'scripts/mock_client.py')
    server = mock.LocalServer(str(args.service_binary), str(root), 15)
    journal = Journal(root / 'runtime.sqlite')
    launcher = Launcher(journal, args.hermes_python, args.hermes_source)
    launches, worktrees, reports = [], [], []
    report = {'status': 'running', 'ai_contract_revision': local_git(args.ai_contract_checkout, 'rev-parse', 'HEAD'),
              'foundry_bootstrap': local_git(checkout, 'rev-parse', 'HEAD'),
              'hermes_revision': local_git(args.hermes_source, 'rev-parse', 'HEAD'),
              'backend': 'installed Hermes AIAgent; macOS sandbox-exec checks; local SQLite AI.Contract',
              'contracts': reports, 'delivery': [], 'limits': []}
    try:
        for actor, scopes in [('coordinator', 'read,write,coordinator'), ('worker-one', 'read,write,writer'),
                              ('worker-two', 'read,write,writer'), ('qa', 'read,write,auditor')]:
            result = subprocess.run([str(args.service_binary), 'token', 'issue', 'acceptance-' + actor, scopes],
                                    env=server.env, capture_output=True, text=True, check=True)
            server.tokens[actor] = next(line[6:] for line in result.stdout.splitlines() if line.startswith('token='))
        origin = server.start()
        report['origin'] = origin
        class QuietClient(mock.Client):
            def call(self, *values, **options):
                import contextlib,io
                with contextlib.redirect_stdout(io.StringIO()):
                    return super().call(*values, **options)
        api = QuietClient(origin, server.tokens, 'http', 15)
        project = api.call('project_create', {'title': 'Disposable real Hermes acceptance',
                          'repository': 'stemarie/context-foundry', 'delivery_policy':
                          'Direct main after independent exact-candidate QA, expected-head non-force delivery and postchecks. No deployment.'})['project']
        pid = project['id']; report['project_id'] = pid
        milestone = api.call('milestone_create', {'project_id': pid, 'ordinal': 1, 'title': 'Local real-agent acceptance',
                             'goal': 'Verify the bounded Context Foundry runtime using actual agents and delivery.',
                             'scope': 'Context Foundry runtime, focused operator documentation and disposable proofs. No AI.Contract runtime ownership changes.',
                             'acceptance_criteria': 'Real independent QA, remote delivery and native history; preserve boundaries.'})['milestone']
        report['milestone_id'] = milestone['id']
        api.call('project_planning_boundary', {'project_id': pid, 'through': 1, 'expected_revision': 0})

        def work(op, values=None, actor='coordinator', expected_error=None):
            command = dict(values or {}, project_id=pid)
            if op not in ('get', 'list', 'agents', 'assignments', 'history'):
                command['idempotency_key'] = uuid.uuid4().hex
            result = api.call('workflow_' + op, command, actor, expected_error)
            return result if expected_error else result['workflow']

        def bound(job):
            result = {'contract_id': job['contract_id'], 'revision': job['revision']['number'],
                      'digest': job['revision']['digest'], 'attempt_id': job['attempt']['id']}
            if job.get('candidate'):
                result.update(candidate_id=job['candidate']['id'], candidate_sha=job['candidate']['sha'])
            return result

        work('configure', {'queue_target': 2}, 'admin')
        for actor, role in [('worker-one', 'worker'), ('worker-two', 'worker'), ('qa', 'qa')]:
            work('agent', {'agent': 'acceptance-' + actor, 'agent_role': role}, 'admin')
        # Resolve the existing configured provider only in the operator context.
        resolver = ('from hermes_cli.runtime_provider import resolve_runtime_provider; import json; '
                    'r=resolve_runtime_provider(requested="openai-codex",target_model="gpt-5.6-terra"); '
                    'print(json.dumps({k:r[k] for k in ["provider","api_mode","api_key","base_url"]}))')
        result = subprocess.run([str(args.hermes_python), '-c', resolver], capture_output=True, text=True,
                                env=dict(os.environ, PYTHONPATH=str(args.hermes_source), PYTHONDONTWRITEBYTECODE='1'), check=True)
        runtime = json.loads(result.stdout)
        gate = Gate(journal, 'owner-github-context-foundry')
        github = GitHub(gate, checkout, 'stemarie/context-foundry')
        expected = github.head()
        assert local_git(checkout, 'merge-base', expected, 'HEAD') == expected

        def contract(name, path, terms):
            bootstrap_scope = ('The delivered candidate intentionally includes the operator-authored runtime prerequisites, tests, preflight and LOCAL_RUNTIME.md since the remote baseline. These are authorized prerequisite changes; QA must review those files as well as this guide. Worker writes only the guide.' if not report['delivery'] else 'The candidate may include operator-authored runtime prerequisites, focused compatibility fixes, tests and acceptance runner since the declared remote baseline; those are authorized and QA must inspect them. Worker writes only the guide.')
            body = f'''# Objective
Create `{path}` as a concise operator guide for {name} in the bounded local Hermes adapter.
# Authority
Read AGENTS.md, docs/LOCAL_RUNTIME.md, foundry_runtime/core.py, runtime.py, worker.py and remote.py.
The operator has prepared the initial runtime prerequisites. Review and preserve their safety properties.
# Scope and non-goals
Worker changes only `{path}`. Do not change code, tests, profiles, secrets or AI.Contract. Do not deploy.
{bootstrap_scope}
# Dependencies and conflicts
No prerequisites. Independent documentation file; no shared mutable code or target integration ownership.
# Acceptance criteria
The guide accurately explains these concepts: {', '.join(terms)}. Include one practical recovery or verification example grounded in source. Avoid unverified acceptance claims.
Worker runs the supplied checks and submits an actual commit. Independent QA inspects the exact candidate and relevant runtime safety controls, independently runs checks and records evidence. QA acceptance is not Done.
# Verification and delivery
Use the check capability. Coordinator integrates serially, verifies expected-head non-force main delivery and postchecks, then records native Done and historical issue. No deployment.
'''
            c = api.call('milestone_contract_create', {'project_id': pid, 'milestone_id': milestone['id'],
                         'title': name, 'body_markdown': body}, 'architect')['contract']
            job = work('define', {'contract_id': c['id'], 'title': name, 'body_markdown': body,
                                 'dependencies': [], 'conflicts': []}, 'architect')['job']
            work('ready', {'contract_id': c['id'], 'revision': job['revision']['number'], 'digest': job['revision']['digest']}, 'architect')
            return c['id'], path, terms

        def workspace(ref, label):
            directory = root / label
            local_git(checkout, 'worktree', 'add', '-b', 'codex/acceptance-' + label + '-' + uuid.uuid4().hex[:6], str(directory), ref)
            worktrees.append(directory)
            return directory

        def configuration(job, actor, directory, base, terms, path, role, barrier=None):
            home = root / ('home-' + uuid.uuid4().hex); home.mkdir(mode=0o700)
            scratch = home / 'scratch'; scratch.mkdir(mode=0o700)
            binding = {'project_id': pid, **bound(job), 'actor': 'acceptance-' + actor}
            if role == 'worker':
                binding.pop('candidate_id', None); binding.pop('candidate_sha', None)
            roletext = (checkout / 'skills' / ('foundry-' + role) / 'SKILL.md').read_text()
            for source in ('skills/OPERATING_RULES.md', 'WORK_CONTRACT.md', 'docs/WORKFLOW.md'):
                roletext += '\n\n' + (checkout / source).read_text()
            check = ('import pathlib,unittest; p=pathlib.Path(' + repr(path) + '); '
                     'assert p.is_file(); text=p.read_text().lower(); '
                     'assert all(t.lower() in text for t in ' + repr(terms) + '); '
                     'suite=unittest.TestSuite([unittest.defaultTestLoader.discover("tests",pattern="test_core.py"),unittest.defaultTestLoader.discover("tests",pattern="test_transport.py")]); '
                     'r=unittest.TextTestRunner(verbosity=1).run(suite); assert r.wasSuccessful()')
            return {'origin': origin, 'service_token': server.tokens[actor], 'binding': binding,
                    'role': role, 'workspace': str(directory), 'base_sha': base,
                    'candidate_sha': job.get('candidate', {}).get('sha'), 'home': str(home), 'scratch': str(scratch),
                    'model': 'gpt-5.6-terra', 'role_instructions': roletext,
                    'checks': ['/Library/Developer/CommandLineTools/usr/bin/python3', '-E', '-s', '-c', check],
                    'start_barrier': str(barrier) if barrier else None, 'invocation_seconds': 600}

        def launch(config):
            key = launcher.ensure(config, runtime); launches.append(key)
            assert launcher.ensure(config, runtime) == key
            restarted = Launcher(Journal(journal.path), args.hermes_python, args.hermes_source)
            assert restarted.ensure(config, runtime) == key
            assert restarted.inspect(key) == 'running'
            print('LAUNCHED', config['role'], config['binding']['actor'], key, flush=True)
            return key

        def wait_stage(cid, stages, key=None, timeout=240):
            until = time.monotonic() + timeout
            while time.monotonic() < until:
                job = work('get', {'contract_id': cid})['job']
                if job['stage'] in stages:
                    return job
                if key and launcher.inspect(key) == 'stopped':
                    raise Barrier('real invocation stopped before required stage: ' + cid)
                time.sleep(.5)
            raise Barrier('bounded acceptance stage wait timed out')

        def review(job, path, terms, base, worker_key):
            while True:
                q = work('assign_qa', {'contract_id': job['contract_id']})['job']
                assert q['contract_id'] == job['contract_id']
                worker_actor = q['attempt']['worker'].removeprefix('acceptance-')
                work('verdict', {**bound(q), 'verdict':'Accepted', 'evidence':'Prohibited self-QA probe.'}, worker_actor, 'forbidden')
                qa_client = Client(origin, server.tokens['qa'])
                for override, expected_code in [({'revision':q['revision']['number']+1},'stale_revision'),
                                                ({'attempt_id':str(uuid.uuid4())},'active_claim_conflict'),
                                                ({'candidate_id':str(uuid.uuid4())},'validation_failed')]:
                    try:
                        qa_client.workflow('verdict', {'project_id':pid, **bound(q), **override,
                            'verdict':'Accepted','evidence':'Stale binding rejection probe.','idempotency_key':uuid.uuid4().hex})
                    except ServiceError as rejected:
                        assert rejected.code==expected_code
                    else:
                        raise AssertionError('stale verdict binding accepted')
                report['self_qa_and_stale_bindings_rejected']=True
                directory = workspace(q['candidate']['sha'], 'qa-' + uuid.uuid4().hex[:6])
                config = configuration(q, 'qa', directory, base, terms, path, 'qa')
                key = launch(config)
                reviewed = wait_stage(job['contract_id'], ['QA accepted', 'Implementing', 'Blocked'], key)
                launcher.stop(key)
                if reviewed['stage'] == 'Blocked':
                    raise Barrier('independent QA requires Architect reassessment')
                if reviewed['stage'] == 'Implementing':
                    assert launcher.inspect(worker_key) == 'running'
                    job = wait_stage(job['contract_id'], ['QA'], worker_key)
                    continue
                until = time.monotonic() + 15
                while launcher.inspect(worker_key) != 'stopped' and time.monotonic() < until:
                    time.sleep(.1)
                assert launcher.inspect(worker_key) == 'stopped'
                assert reviewed['stage'] != 'Done'
                return reviewed

        def deliver(job, base):
            with github.integration():
                return deliver_owned(job, base)

        def deliver_owned(job, base):
            nonlocal expected
            if job['stage'] != 'Integrating':
                job = work('integrate', bound(job))['job']
            def authority():
                current = work('get', {'contract_id': job['contract_id']})['job']
                if current['stage'] != 'Integrating' or current['accepted_candidate_id'] != job['candidate']['id']:
                    raise Barrier('integration authority changed')
            if github.head() != expected:
                raise Barrier('remote target drift requires inspection')
            # A clean merge preserves the exact accepted immutable candidate; no rebase,
            # conflict resolution or candidate modification is performed here.
            local_git(checkout, '-c', 'user.name=acceptance-coordinator', '-c', 'user.email=acceptance-coordinator@localhost', 'merge', '--no-edit', job['candidate']['sha'])
            target = local_git(checkout, 'rev-parse', 'HEAD')
            checks = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=checkout,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR='/private/tmp'), capture_output=True, text=True)
            if checks.returncode:
                raise Barrier('operator integration checks failed; no Done')
            pushed = github.push(target, expected, authority)
            assert github.head() == target
            # Deliberate disposable acceptance check failure: delivery alone cannot
            # produce Done. Record the actual exit and rejected completion first.
            failed_probe = subprocess.run([sys.executable, '-c', 'raise SystemExit(1)'])
            assert failed_probe.returncode == 1
            work('record', {**bound(job), 'evidence': 'Deliberate local postcheck probe exited 1; delivery is not completion.'})
            work('complete', {**bound(job), 'target_sha': target, 'checks_passed': False,
                              'reference': 'https://github.com/stemarie/context-foundry/commit/' + target,
                              'evidence': 'Deliberate postcheck probe exited 1.'}, expected_error='project_conflict')
            assert work('get', {'contract_id': job['contract_id']})['job']['stage'] == 'Integrating'
            report['failed_postcheck_kept_unresolved'] = True
            post = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests', '-v'], cwd=checkout,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1', TMPDIR='/private/tmp'), capture_output=True, text=True)
            if post.returncode:
                work('record', {**bound(job), 'evidence': 'Actual post-integration checks failed; no Done.'})
                raise Barrier('actual post-integration checks failed')
            job = work('complete', {**bound(job), 'target_sha': target, 'checks_passed': True,
                                   'reference': 'https://github.com/stemarie/context-foundry/commit/' + target,
                                   'evidence': 'Actual non-force expected-head delivery and remote SHA read-back; host control suite passed before and after delivery.'})['job']
            assert job['stage'] == 'Done'
            marker = 'foundry-contract:' + pid + ':' + job['contract_id']
            history = github.historical_issue(marker, 'Delivered: ' + job['revision']['title'],
                'Completed bounded real-agent acceptance contract.\n\n'
                'Contract: ' + job['contract_id'] + '\nRevision: ' + str(job['revision']['number']) +
                '\nAttempt: ' + job['attempt']['id'] + '\nCandidate: ' + job['candidate']['sha'] +
                '\nDelivered commit: https://github.com/stemarie/context-foundry/commit/' + target +
                '\n\nActual installed Hermes Worker and separate QA; independent checks; expected-head non-force push and remote read-back; post-integration checks; native Done. Disposable local service. No deployment.')
            github.close_history(history['url'])
            job = work('publish_history', {**bound(job), 'reference': history['url']})['job']
            report['delivery'].append(dict(pushed, history=history['url']))
            expected = target
            print('DONE', job['contract_id'], target, flush=True)
            return job

        if args.scenario == 'single':
            first = contract('Local runtime quickstart', 'docs/RUNTIME_QUICKSTART.md', ['AI.Contract', 'unknown', 'independent QA', 'no deployment'])
            first_job = work('reserve', {'lease_seconds': 300})['job']
            directory = workspace('HEAD', 'worker-first')
            actor = first_job['attempt']['worker'].removeprefix('acceptance-')
            config = configuration(first_job, actor, directory, expected, first[2], first[1], 'worker')
            key = launch(config)
            submitted = wait_stage(first[0], ['QA'], key)
            accepted = review(submitted, first[1], first[2], expected, key)
            complete = deliver(accepted, expected)
            reports.append({'job': complete, 'history': work('history', {'contract_id': first[0]}), 'launch': key})
        elif args.scenario == 'parallel':
            # Prerequisites have already had independent QA and real main delivery.
            report['delivery'].append({'previously_verified_base': expected})
            first = contract('Runtime isolation guide', 'docs/RUNTIME_ISOLATION.md', ['actor', 'sandbox', 'credential', 'AI.Contract'])
            second = contract('Runtime recovery guide', 'docs/RUNTIME_RECOVERY.md', ['unknown', 'lease', 'independent QA', 'breaker'])
            barrier = root / 'start-workers'
            active = []
            baseline = expected
            for task in (first, second):
                job = work('reserve', {'lease_seconds': 300})['job']
                assert job['contract_id'] == task[0]
                actor = job['attempt']['worker'].removeprefix('acceptance-')
                directory = workspace('HEAD', actor)
                config = configuration(job, actor, directory, baseline, task[2], task[1], 'worker', barrier)
                key = launch(config)
                active.append((task, job, config, key))
            assert active[0][1]['attempt']['worker'] != active[1][1]['attempt']['worker']
            assert work('reserve')['idle']
            both = [work('get', {'contract_id': row[0][0]})['job'] for row in active]
            assert all(job['stage'] == 'Implementing' for job in both)
            report['simultaneous_attempts'] = [bound(job) for job in both]
            barrier.touch()
            submissions = []
            for task, job, config, key in active:
                submissions.append((wait_stage(task[0], ['QA'], key), task, config, key))
            intervals = []
            for _, task, config, key in active:
                until = time.monotonic() + 60
                while True:
                    events = [json.loads(line) for line in (Path(config['home'])/'events.jsonl').read_text().splitlines()]
                    if any(e['event']=='model_finished' for e in events):
                        break
                    if time.monotonic()>until:
                        raise Barrier('real model turn completion still pending')
                    time.sleep(.2)
                intervals.append((next(e['time'] for e in events if e['event']=='model_started'),
                                  next(e['time'] for e in events if e['event']=='model_finished')))
            assert max(i[0] for i in intervals) < min(i[1] for i in intervals)
            report['actual_model_overlap'] = intervals
            submissions.sort(key=lambda item:item[0]['candidate']['sequence'])
            accepted = []
            for job, task, config, key in submissions:
                accepted.append((review(job, task[1], task[2], baseline, key), task, key))
            one, task_one, key_one = accepted[0]
            two, task_two, key_two = accepted[1]
            # Native integration serialization is verified before delivery.
            integrating = work('integrate', bound(one))['job']
            work('integrate', bound(two), expected_error='project_conflict')
            # deliver accepts an already-owned integration for this assertion.
            complete = deliver(integrating, baseline)
            reports.append({'job': complete, 'history': work('history', {'contract_id': task_one[0]}), 'launch': key_one})
            assert launcher.inspect(key_two) == 'stopped'
            old_candidate = two['candidate']
            # Target changed: retain the old accepted evidence, restart this bounded
            # documentation assignment on current main and require an actual fresh QA.
            work('recover', {**bound(two), 'stopped_confirmed': True,
                             'evidence': 'Old accepted Worker process group confirmed stopped. Target advanced; renew attempt and exact-candidate QA on current main.'})
            renewed = work('reserve', {'lease_seconds': 300})['job']
            assert renewed['contract_id'] == task_two[0] and renewed['attempt']['id'] != two['attempt']['id']
            directory = workspace('HEAD', 'worker-after-drift')
            actor = renewed['attempt']['worker'].removeprefix('acceptance-')
            config = configuration(renewed, actor, directory, expected, task_two[2], task_two[1], 'worker')
            key = launch(config)
            submitted = wait_stage(task_two[0], ['QA'], key)
            refreshed = review(submitted, task_two[1], task_two[2], expected, key)
            assert refreshed['candidate']['id'] != old_candidate['id']
            complete = deliver(refreshed, expected)
            reports.append({'job': complete, 'history': work('history', {'contract_id': task_two[0]}), 'launch': key,
                            'superseded_accepted_candidate': old_candidate})
        elif args.scenario == 'recovery':
            from foundry_runtime.runtime import Tools
            task = contract('Disposable recovery probe', 'docs/NOT_DELIVERED_PROBE.md', ['lease', 'unknown'])
            job = work('reserve', {'lease_seconds': 300})['job']
            directory = workspace('HEAD', 'recovery-worker')
            actor = job['attempt']['worker'].removeprefix('acceptance-')
            config = configuration(job, actor, directory, expected, task[2], task[1], 'worker', root/'never-release')
            config['heartbeat'] = False
            key = launch(config)
            # The installed AIAgent has initialized and is alive at its start barrier.
            until = time.monotonic()+30
            while not (Path(config['home'])/'events.jsonl').exists() and time.monotonic()<until:
                time.sleep(.1)
            assert launcher.inspect(key)=='running'
            work('heartbeat', {**bound(job), 'lease_seconds': 1}, actor)
            time.sleep(1.2)
            assert launcher.inspect(key)=='running'
            assert work('reserve', {'worker': job['attempt']['worker']})['idle']
            try: Tools(config).invoke('write', {'path':task[1], 'content':'stale write'})
            except Barrier: pass
            else: raise AssertionError('expired local writer was not fenced')
            work('recover', {**bound(job), 'stopped_confirmed':False, 'evidence':'Expiry alone is not stop proof.'}, expected_error='project_conflict')
            stopped = launcher.stop(key)
            assert stopped['stopped_confirmed'] and launcher.inspect(key)=='stopped'
            recovered = work('recover', {**bound(job), 'stopped_confirmed':True, 'evidence':'Actual adapter-owned Hermes process group stopped and absence confirmed.'})['job']
            assert recovered['stage']=='Ready'
            revised=work('define', {'contract_id':job['contract_id'], 'expected_revision':job['revision']['number'],
                'title':job['revision']['title'], 'body_markdown':job['revision']['body_markdown']+
                '\nMaterial clarification: this is an execution recovery probe only; no document or Git delivery is required.'}, 'architect')['job']
            assert revised['stage']=='Draft' and revised['revision']['number']==job['revision']['number']+1
            assert revised['revision']['digest']!=job['revision']['digest']
            work('ready', {'contract_id':revised['contract_id'],'revision':revised['revision']['number'],
                           'digest':revised['revision']['digest']}, 'architect')
            report['material_revision_requires_renewed_readiness']=True
            renewed = work('reserve', {'worker':job['attempt']['worker']})['job']
            assert renewed['attempt']['id'] != job['attempt']['id']
            try: Tools(config).invoke('write', {'path':task[1], 'content':'stale write'})
            except Barrier: pass
            else: raise AssertionError('old attempt writer was not fenced')
            unknown,_=journal.intent({'origin':origin,'project_id':pid,'contract_id':task[0],'revision':1,'digest':'unknown-probe','attempt_id':'not-launched','actor':'acceptance-worker-one'})
            assert launcher.inspect(unknown['key'])=='unknown'
            try: launcher.stop(unknown['key'])
            except Barrier: pass
            else: raise AssertionError('unknown execution was falsely stopped')
            cancelled=work('cancel',{**bound(renewed),'stopped_confirmed':True,'evidence':'Renewed attempt was never launched; prior real Worker stopped. Disposable recovery proof complete.'})['job']
            reports.append({'job':cancelled,'history':work('history',{'contract_id':task[0]}),'launch':key,'unknown_launch':unknown['key']})
            report['expiry_while_real_hermes_alive']=True
        report['status'] = args.scenario + '_passed'
        report['limits'] = []
        write_report(args.report, report)
        print('PASS actual scenario',args.scenario,flush=True)

    except BaseException as exc:
        report['status'] = 'blocked'
        report['failure_category'] = type(exc).__name__
        write_report(args.report, report)
        raise
    finally:
        for key in set(launches) | set(launcher.children):
            try:
                launcher.stop(key)
            except Barrier:
                report.setdefault('cleanup_unknown', []).append(key)
        try:
            if 'work' in locals():
                report['all_history'] = [work('history', {'contract_id': job['contract_id'], 'limit':100})
                                         for job in work('list').get('jobs', [])]
            diagnostics = []
            for home in root.glob('home-*'):
                row = {'home': home.name}
                for name in ('failure.txt', 'events.jsonl', 'invocation.log'):
                    path = home / name
                    if path.exists():
                        value = path.read_text(errors='replace')[-24000:]
                        for secret in list(server.tokens.values()) + ([runtime.get('api_key', '')] if 'runtime' in locals() else []):
                            if secret:
                                value = value.replace(secret, '[REDACTED]')
                        row[name] = value
                diagnostics.append(row)
            report['diagnostics'] = diagnostics
        except Exception:
            report['history_export_failed'] = True
        finally:
            server.stop()  # Reporting/capacity errors must not leave a live service.
        saved = write_report(args.report, report)
        if report.get('cleanup_unknown') or report.get('history_export_failed') or not saved:
            report['preserved_private_fixture'] = str(root)
            write_report(args.report, report)
            raise Barrier('quiescence or evidence publication unresolved; private fixtures retained')
        for path in root.glob('home-*'):
            shutil.rmtree(path)
        shutil.rmtree(root / 'data', ignore_errors=True)
        for path in root.glob('*.sqlite*'):
            path.unlink()
        for directory in worktrees:
            local_git(checkout, 'worktree', 'remove', '--force', str(directory))
        report['cleanup'] = {'owned_processes_stopped':True,'native_homes_removed':True,
                             'database_removed_after_history_export':True,'owned_worktrees_removed':True}
        write_report(args.report, report)
        print('CLEANUP owned processes, worktrees, native homes and local database stopped/removed', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('ai-contract-checkout', 'service-binary', 'hermes-source', 'hermes-python', 'report'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--scenario',choices=['single','parallel','recovery'],default='single')
    run(parser.parse_args())

if __name__ == '__main__':
    main()
