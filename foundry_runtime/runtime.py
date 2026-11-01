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
            raise ServiceError(code) from None
        except (OSError, ValueError):
            raise Barrier('service unavailable; no local transition inferred') from None

    def workflow(self, operation, command):
        return self.call('/api/v1/workflow/' + operation, command)['workflow']

    def authority(self, binding, role):
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
        return job


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
            'output': (result.stdout + result.stderr)[-12000:]}


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

    def invoke(self, operation, arguments):
        job = self.client.authority(self.binding, self.role)
        self.calls.append(operation)
        if operation == 'assignment':
            history = self.client.workflow('history', {'project_id': self.binding['project_id'], 'contract_id': self.binding['contract_id']})
            return {'job': job, 'history': history.get('events', [])[-10:], 'files': sorted(str(p.relative_to(self.workspace)) for p in self.workspace.rglob('*')
                                               if p.is_file() and not any(x.startswith('.git') for x in p.relative_to(self.workspace).parts))[:200]}
        if operation == 'read':
            path = checked_path(self.workspace, arguments['path'])
            return {'content': path.read_text()[:64000]}
        if operation == 'diff':
            return {'diff': local_git(self.workspace, 'diff', self.config['base_sha'], 'HEAD')[:64000]}
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
            if self.role != 'worker' or job['stage'] != 'Implementing' or not self.checks or not self.checks['passed']:
                raise Barrier('current checks and Worker authority required')
            if snapshot(self.workspace) != self.checked_snapshot:
                raise Barrier('candidate changed since verification')
            local_git(self.workspace, 'diff', '--check')
            local_git(self.workspace, 'add', '--all')
            local_git(self.workspace, '-c', 'user.name=' + self.binding['actor'], '-c',
                      'user.email=' + self.binding['actor'] + '@localhost', 'commit', '-m', arguments['summary'])
            sha = local_git(self.workspace, 'rev-parse', 'HEAD')
            evidence = json.dumps({'actor': self.binding['actor'], 'checks': self.checks,
                                   'workspace': str(self.workspace), 'base_sha': self.config['base_sha'],
                                   'candidate_sha': sha, 'summary': arguments['summary']})
            result = self.client.workflow('submit', {**command_binding(self.binding), 'candidate_sha': sha,
                                                   'evidence': evidence, 'idempotency_key': 'submit:' + sha})
            self.candidate = sha
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
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': config['home'],
               'HERMES_HOME': config['home'], 'PYTHONPATH': self.source + os.pathsep + str(Path(__file__).resolve().parent.parent),
               'PYTHONDONTWRITEBYTECODE': '1', 'TMPDIR': config['scratch']}
        stream = open(Path(config['home']) / 'invocation.log', 'w')
        entry = ('from run_agent import AIAgent; import sys,runpy; sys.path.insert(0,' +
                 repr(str(Path(__file__).resolve().parent.parent)) +
                 '); runpy.run_module("foundry_runtime.worker",run_name="__main__")')
        process = subprocess.Popen([self.python, '-c', entry, '--journal', self.journal.path,
                                    '--launch', row['key'], '--nonce', row['nonce']], env=env, cwd=config['workspace'],
                                   stdin=subprocess.PIPE, stdout=stream, stderr=stream, start_new_session=True, text=True)
        self.children[row['key']] = process
        stream.close()
        process.stdin.write(json.dumps({'config': config, 'model_runtime': model_runtime}))
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
