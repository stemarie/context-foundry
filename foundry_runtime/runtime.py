"""Actor-bound service access and restricted local invocation backend.

Only the operator launches processes. The journal contains identities, not a queue.
The selected macOS check backend denies network, forks and reads outside its roots.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import hashlib
import os
import re
from pathlib import Path
import subprocess
import sys
import time
import threading
import socket
import http.client
import urllib.error
import urllib.request

from .core import Barrier, Journal


def parse_service_time(value):
    # Go RFC3339Nano emits variable precision; Python 3.9 accepts only 3/6 digits.
    normalized = re.sub(r'\.(\d+)', lambda match: '.' + match[1][:6].ljust(6, '0'), value)
    return datetime.fromisoformat(normalized.replace('Z', '+00:00'))


class ServiceError(Barrier):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class ServiceUnavailable(Barrier):
    def __init__(self, category, code=None):
        self.category, self.code = category, code
        super().__init__('service unavailable; current authority must be revalidated')


def native_worker_command(python, source, adapter_root):
    """Only trusted roots enter Python's import path, including at interpreter startup."""
    source, adapter_root = str(Path(source).resolve()), str(Path(adapter_root).resolve())
    entry = ('import sys; sys.path[:0]=' + repr([source, adapter_root]) + '; '
             'from run_agent import AIAgent; import runpy; sys.path.insert(0,' + repr(adapter_root) + '); '
             'runpy.run_module("foundry_runtime.worker",run_name="__main__")')
    return [str(python), '-I', '-B', '-c', entry]


def text_page(text, arguments, field):
    offset, limit = arguments.get('offset', 0), arguments.get('limit', 64000)
    if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 64000:
        raise Barrier('invalid page bounds')
    version = hashlib.sha256(text.encode()).hexdigest()
    if arguments.get('version') and arguments['version'] != version:
        raise Barrier('content changed between pages; restart at offset zero')
    end = min(len(text), offset + limit)
    return {field: text[offset:end], 'offset': offset, 'total_characters': len(text),
            'next_offset': end if end < len(text) else None, 'truncated': end < len(text), 'version': version}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Client:
    def __init__(self, origin, token):
        self.origin, self.token = origin.rstrip('/'), token
        self.opener = urllib.request.build_opener(NoRedirect())

    def call(self, path, data=None, method='POST'):
        raw = None if data is None else json.dumps(data).encode()
        request = urllib.request.Request(self.origin + path, raw,
                                        {'Authorization': 'Bearer ' + self.token, 'Content-Type': 'application/json'}, method=method)
        try:
            with self.opener.open(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                code = json.load(exc).get('error', {}).get('code', 'service_rejected')
            except (ValueError, AttributeError):
                code = 'service_rejected'
            if exc.code >= 500:
                raise ServiceUnavailable('http_service_failure', code) from None
            raise ServiceError(code) from None
        except (OSError, ValueError, http.client.HTTPException) as exc:
            cause = getattr(exc, 'reason', exc)
            if isinstance(cause, TimeoutError): category = 'timeout'
            elif isinstance(cause, ConnectionRefusedError): category = 'connection_refused'
            elif isinstance(cause, ConnectionResetError): category = 'connection_reset'
            elif isinstance(cause, socket.gaierror): category = 'dns_failure'
            elif isinstance(cause, http.client.RemoteDisconnected): category = 'connection_closed'
            elif isinstance(cause, ValueError): category = 'invalid_response'
            else: category = 'connection_failure'
            raise ServiceUnavailable(category) from None

    def workflow(self, operation, command):
        return self.call('/api/v1/workflow/' + operation, command)['workflow']

    def authority(self, binding, role):
        contract = self.call('/api/v1/contracts/' + binding['contract_id'], method='GET').get('contract', {})
        if contract.get('id') != binding['contract_id'] or contract.get('contract_version') != 'Alpha 1.0':
            raise Barrier('unsupported or missing semantic contract version')
        job = self.workflow('get', {'project_id': binding['project_id'], 'contract_id': binding['contract_id']})['job']
        revision, attempt = job['revision'], job.get('attempt')
        if (revision['number'] != binding['revision'] or revision['digest'] != binding['digest'] or
                not attempt or attempt['id'] != binding['attempt_id'] or
                parse_service_time(attempt['expires_at']) <= datetime.now(timezone.utc)):
            raise Barrier('stale assignment or lease')
        assigned = self.workflow('assignments', {'project_id': binding['project_id']}).get('jobs', [])
        if not any(j['contract_id'] == binding['contract_id'] for j in assigned):
            raise Barrier('actor does not own current assignment')
        if role == 'worker' and (attempt['worker'] != binding['actor'] or job['stage'] not in ('Implementing', 'QA')):
            raise Barrier('Worker authority changed')
        if role == 'qa' and (job['stage'] != 'QA' or job['reviewer'] != binding['actor'] or
                             job['candidate']['id'] != binding['candidate_id']):
            raise Barrier('QA authority changed')
        return dict(job, contract_version=contract['contract_version'])


def command_binding(binding):
    return {k: binding[k] for k in ('project_id', 'contract_id', 'revision', 'digest', 'attempt_id')}


def local_git(workspace, *args):
    env = {k: v for k, v in os.environ.items() if not (k.startswith('GIT_') or 'TOKEN' in k or 'API_KEY' in k)}
    env.update(GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null', GIT_TERMINAL_PROMPT='0')
    result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *args],
                            cwd=workspace, env=env, capture_output=True, text=True)
    if result.returncode:
        raise Barrier('local Git command failed')
    return result.stdout.strip()


def checked_path(workspace, value):
    relative = Path(value)
    if relative.is_absolute() or '..' in relative.parts or any(p.startswith('.git') for p in relative.parts):
        raise Barrier('path is outside invocation capability')
    path = workspace / relative
    if not path.resolve().is_relative_to(workspace.resolve()):
        raise Barrier('path escapes invocation workspace')
    if any(p.is_symlink() for p in [path, *path.parents] if p != workspace.parent):
        raise Barrier('symlink is not an invocation file capability')
    return path


def check_descriptor(argv, cwd, backend='macos sandbox-exec'):
    """Return adapter-generated execution metadata that model summaries cannot replace."""
    descriptor = {'argv': [str(value) for value in argv], 'cwd': str(Path(cwd).resolve()), 'backend': backend}
    return {**descriptor, 'identity': hashlib.sha256(
        json.dumps(descriptor, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}


def restricted_check(workspace, argv, scratch, timeout=90):
    if sys.platform != 'darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        raise Barrier('this backend requires verified macOS sandbox-exec; no unsandboxed fallback')
    # JSON quoting is also valid for sandbox path strings. No user shell string.
    read_roots = ['/System', '/usr', '/bin', '/sbin', '/Library/Developer/CommandLineTools',
                  '/Library/Frameworks/Python3.framework', str(workspace), str(scratch)]
    allowed = '(literal "/") ' + ' '.join('(subpath ' + json.dumps(r) + ')' for r in read_roots)
    writable = ' '.join('(subpath ' + json.dumps(str(r)) + ')' for r in (workspace, scratch))
    profile = ('(version 1)(allow default)(deny network*)(deny process-fork)'
               '(deny file-read-data (require-not (require-any ' + allowed +
               ' (literal "/dev/null") (literal "/dev/urandom") (literal "/dev/random"))))'
               '(deny file-write* (require-not (require-any ' + writable +
               ' (literal "/dev/null"))))'
               '(deny file-write* (subpath ' + json.dumps(str(workspace / '.git')) + '))')
    env = {'PATH': '/usr/bin:/bin', 'HOME': str(scratch), 'TMPDIR': str(scratch), 'PYTHONDONTWRITEBYTECODE': '1'}
    result = subprocess.run(['/usr/bin/sandbox-exec', '-p', profile, *argv], cwd=workspace, env=env,
                            capture_output=True, text=True, timeout=timeout)
    return {'passed': result.returncode == 0, 'exit_code': result.returncode,
            'output': (result.stdout + result.stderr)[-12000:],
            'command': check_descriptor(argv, workspace)}


def snapshot(workspace):
    result = hashlib.sha256()
    for path in sorted(workspace.rglob('*')):
        if any(part.startswith('.git') for part in path.relative_to(workspace).parts):
            continue
        if path.is_symlink():
            raise Barrier('candidate contains unsupported symlink')
        if path.is_file():
            result.update(str(path.relative_to(workspace)).encode())
            result.update(b'\0' + path.read_bytes() + b'\0')
    return result.hexdigest()


class Tools:
    def __init__(self, config):
        self.config = config
        self.client = Client(config['origin'], config['service_token'])
        self.binding, self.role = config['binding'], config['role']
        self.workspace = Path(config['workspace']).resolve()
        self.checks = None
        self.candidate = None
        self.calls = []
        self.lock = threading.RLock()

    def invoke(self, operation, arguments):
        # Native batched tool calls must not race workspace mutation or commits.
        with self.lock:
            return self._invoke(operation, arguments)

    def submission_identity(self, content):
        return hashlib.sha256(json.dumps({'origin': self.config['origin'], 'binding': self.binding,
                                          'content': content}, sort_keys=True).encode()).hexdigest()

    def pending_submission(self):
        if not self.config.get('runtime_journal'):
            return None
        journal = Journal(self.config['runtime_journal'])
        identity = self.submission_identity(snapshot(self.workspace))
        with journal.transaction() as db:
            row = db.execute('SELECT intent,payload FROM submissions WHERE identity=?', (identity,)).fetchone()
        if not row:
            return None
        intent = json.loads(row['intent'])
        payload = json.loads(row['payload']) if row['payload'] else {}
        return {'summary': intent['summary'], 'candidate_sha': payload.get('candidate_sha'),
                'idempotency_key': payload.get('idempotency_key')}

    def _invoke(self, operation, arguments):
        job = self.client.authority(self.binding, self.role)
        self.calls.append(operation)
        if operation == 'assignment':
            events, after = [], 0
            while True:
                page = self.client.workflow('history', {'project_id': self.binding['project_id'],
                    'contract_id': self.binding['contract_id'], 'after': after, 'limit': 100}).get('events', [])
                events.extend(page)
                if len(page) < 100:
                    break
                if page[-1]['id'] <= after:
                    raise Barrier('history continuation did not advance')
                after = page[-1]['id']
            return {'job': job, 'pending_submission': self.pending_submission(), 'history': events[-10:], 'history_total': len(events),
                    'latest_review': next((e for e in reversed(events) if e['operation'] == 'verdict'
                        and e.get('job', {}).get('revision', {}).get('number') == self.binding['revision']
                        and e.get('job', {}).get('revision', {}).get('digest') == self.binding['digest']
                        and e.get('job', {}).get('attempt', {}).get('id') == self.binding['attempt_id']), None),
                    'files': sorted(str(p.relative_to(self.workspace)) for p in self.workspace.rglob('*')
                        if p.is_file() and not any(x.startswith('.git') for x in p.relative_to(self.workspace).parts))[:200]}
        if operation == 'history':
            after, limit = arguments.get('after', 0), arguments.get('limit', 100)
            if type(after) is not int or after < 0 or type(limit) is not int or not 1 <= limit <= 100:
                raise Barrier('invalid history page bounds')
            result = self.client.workflow('history', {'project_id': self.binding['project_id'],
                'contract_id': self.binding['contract_id'], 'after': after, 'limit': limit})
            events = result.get('events', [])
            return {**result, 'next_after': events[-1]['id'] if len(events) == limit else None}
        if operation == 'read':
            path = checked_path(self.workspace, arguments['path'])
            return text_page(path.read_text(), arguments, 'content')
        if operation == 'diff':
            return text_page(local_git(self.workspace, 'diff', self.config['base_sha'], 'HEAD'), arguments, 'diff')
        if operation == 'write':
            if self.role != 'worker' or job['stage'] != 'Implementing':
                raise Barrier('write capability denied')
            content = arguments['content']
            if len(content.encode()) > 128000:
                raise Barrier('write exceeds capability bound')
            path = checked_path(self.workspace, arguments['path'])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            self.checks = None
            return {'written': arguments['path']}
        if operation == 'check':
            if self.role == 'qa' and local_git(self.workspace, 'rev-parse', 'HEAD') != self.config['candidate_sha']:
                raise Barrier('QA snapshot no longer matches candidate')
            before = snapshot(self.workspace)
            self.checks = restricted_check(self.workspace, self.config['checks'], Path(self.config['scratch']))
            after = snapshot(self.workspace)
            if before != after:
                self.checks = None
                raise Barrier('check changed candidate files; rerun verification')
            self.checked_snapshot = after
            return self.checks
        if operation == 'submit':
            if self.role != 'worker' or job['stage'] not in ('Implementing', 'QA') or not self.checks or not self.checks['passed']:
                raise Barrier('current checks and Worker authority required')
            content_digest = snapshot(self.workspace)
            if content_digest != self.checked_snapshot:
                raise Barrier('candidate changed since verification')
            if not self.config.get('runtime_journal'):
                raise Barrier('durable transport journal is required for submission')
            journal = Journal(self.config['runtime_journal'])
            identity = self.submission_identity(content_digest)
            with journal.transaction() as db:
                row = db.execute('SELECT * FROM submissions WHERE identity=?', (identity,)).fetchone()
                if row:
                    intent = json.loads(row['intent'])
                else:
                    intent = {'parent': local_git(self.workspace, 'rev-parse', 'HEAD'),
                              'summary': arguments['summary'], 'workspace': str(self.workspace), 'checks': self.checks}
                    db.execute('INSERT INTO submissions VALUES(?,?,NULL)', (identity, json.dumps(intent)))
            if intent['summary'] != arguments['summary'] or intent['workspace'] != str(self.workspace):
                raise Barrier('prepared submission intent differs; inspect original summary/workspace')
            if row and row['payload']:
                command = json.loads(row['payload'])
            else:
                head = local_git(self.workspace, 'rev-parse', 'HEAD')
                if head == intent['parent']:
                    if job['stage'] != 'Implementing':
                        raise Barrier('candidate already submitted; reconcile assignment')
                    local_git(self.workspace, 'diff', '--check')
                    local_git(self.workspace, 'add', '--all')
                    local_git(self.workspace, '-c', 'user.name=' + self.binding['actor'], '-c',
                              'user.email=' + self.binding['actor'] + '@localhost', 'commit', '-m', intent['summary'])
                    head = local_git(self.workspace, 'rev-parse', 'HEAD')
                elif (local_git(self.workspace, 'rev-parse', 'HEAD^') != intent['parent'] or
                      local_git(self.workspace, 'log', '-1', '--format=%B') != intent['summary'] or
                      local_git(self.workspace, 'status', '--porcelain')):
                    raise Barrier('local commit outcome unknown; explicit reconciliation required')
                evidence = json.dumps({'actor': self.binding['actor'], 'checks': intent['checks'],
                    'workspace': str(self.workspace), 'branch': local_git(self.workspace, 'branch', '--show-current'),
                    'base_sha': self.config['base_sha'], 'candidate_sha': head, 'summary': intent['summary']})
                command = {**command_binding(self.binding), 'candidate_sha': head,
                           'evidence': evidence, 'idempotency_key': 'submit:' + head}
                with journal.transaction() as db:
                    db.execute('UPDATE submissions SET payload=? WHERE identity=?', (json.dumps(command), identity))
            if local_git(self.workspace, 'rev-parse', 'HEAD') != command['candidate_sha']:
                raise Barrier('workspace moved after candidate preparation')
            if job['stage'] == 'QA':
                if job['candidate']['sha'] != command['candidate_sha']:
                    raise Barrier('service candidate differs from prepared submission')
                return {'job': job, 'reconciled': True}
            if job.get('candidate', {}).get('sha') == command['candidate_sha']:
                raise Barrier('QA requested changes; change and verify the candidate before resubmitting')
            result = self.client.workflow('submit', command)
            self.candidate = command['candidate_sha']
            return result
        if operation == 'verdict':
            if self.role != 'qa':
                raise Barrier('QA capability denied')
            verdict = arguments['verdict']
            if verdict == 'Accepted' and (local_git(self.workspace, 'status', '--porcelain') or
                                          local_git(self.workspace, 'rev-parse', 'HEAD') != self.config['candidate_sha']):
                raise Barrier('QA candidate changed')
            if verdict == 'Accepted' and (not self.checks or not self.checks['passed']):
                raise Barrier('independent exact-candidate checks required')
            evidence = json.dumps({'actor': self.binding['actor'], 'candidate_sha': self.config['candidate_sha'],
                                   'checks': self.checks, 'summary': arguments['summary']})
            return self.client.workflow('verdict', {**command_binding(self.binding), 'candidate_id': self.binding['candidate_id'],
                                                    'verdict': verdict, 'evidence': evidence,
                                                    'idempotency_key': 'qa:' + self.binding['candidate_id'] + ':' + verdict})
        raise Barrier('tool not permitted')


class Launcher:
    def __init__(self, journal, python, source):
        self.journal, self.python, self.source = journal, str(python), str(source)
        self.children = {}

    def ensure(self, config, model_runtime):
        Client(config['origin'], config['service_token']).authority(config['binding'], config['role'])
        binding = {'origin': config['origin'], 'role': config['role'], **config['binding']}
        row, created = self.journal.intent(binding)
        if not created:
            return row['key']
        home = Path(config['home'])
        home.mkdir(mode=0o700, exist_ok=True)
        Path(config['scratch']).mkdir(mode=0o700, exist_ok=True)
        (home / 'config.yaml').write_text(json.dumps({'model': {'provider': model_runtime['provider'], 'default': config['model']},
                                                     'memory': {'enabled': False}, 'plugins': {'enabled': []},
                                                     'tools': {'tool_search': {'enabled': 'off'}}}))
        if Path(self.source).resolve().is_relative_to(Path(config['workspace']).resolve()) or Path(__file__).resolve().parent.parent.is_relative_to(Path(config['workspace']).resolve()):
            raise Barrier('trusted runtime source must be outside the candidate workspace')
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': config['home'],
               'HERMES_HOME': config['home'],
               'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': config['scratch'],
               'HERMES_DISABLE_LAZY_INSTALLS': '1'}
        stream = open(Path(config['home']) / 'invocation.log', 'w')
        command = native_worker_command(self.python, self.source, Path(__file__).resolve().parent.parent)
        process = subprocess.Popen([*command, '--journal', self.journal.path,
                                    '--launch', row['key'], '--nonce', row['nonce']], env=env, cwd=config['workspace'],
                                   stdin=subprocess.PIPE, stdout=stream, stderr=stream, start_new_session=True, text=True)
        self.children[row['key']] = process
        stream.close()
        process.stdin.write(json.dumps({'config': dict(config, runtime_journal=self.journal.path), 'model_runtime': model_runtime}))
        process.stdin.close()
        deadline = time.monotonic() + 90
        while self.journal.get(row['key'])['pid'] is None and time.monotonic() < deadline:
            if process.poll() is not None:
                raise Barrier('invocation exited before launch acknowledgement')
            time.sleep(0.03)
        if self.journal.get(row['key'])['pid'] is None:
            raise Barrier('launch response unknown; do not spawn a replacement')
        return row['key']

    def inspect(self, key):
        if key in self.children:
            self.children[key].poll()  # Reap an owned completed child before probing group identity.
        return self.journal.inspect(key)

    def stop(self, key, timeout=10):
        row = self.journal.get(key)
        state = self.inspect(key)
        if state == 'unknown':
            raise Barrier('unknown execution cannot be stopped by inference')
        if state == 'running':
            import signal
            os.killpg(row['pid'], signal.SIGTERM)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.inspect(key) == 'stopped':
                return {'stopped_confirmed': True, 'launch': key}
            time.sleep(.05)
        raise Barrier('termination not yet confirmed')
