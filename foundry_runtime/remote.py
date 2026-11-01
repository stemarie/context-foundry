"""Operator-only GitHub transport. Children receive none of these capabilities."""
import json
import contextlib
import fcntl
import os
import re
from email.utils import parsedate_to_datetime
import time
from pathlib import Path
import subprocess
import signal
import sys
import tempfile
import uuid

from .core import Barrier, RemoteFailure, active_gate
from .runtime import local_git


def response_metadata(stderr, now=None):
    """Parse response/status lines, never numeric substrings in IDs or bodies."""
    now = time.time() if now is None else now
    statuses, headers = [], {}
    for raw in stderr.splitlines():
        line = raw.strip()
        trace = re.search(r'<=\s*Recv header:\s*(.*)$', line, re.IGNORECASE)
        if trace:
            line = trace[1]
        elif line.startswith('< '):
            line = line[2:].strip()
        status = re.match(r'^HTTP(?:/\d+(?:\.\d+)?)?\s+([1-5]\d{2})(?:\s|:|$)', line, re.IGNORECASE)
        header_status = status
        if not status:
            status = re.search(r'\(HTTP\s+([1-5]\d{2})\)\s*$', line, re.IGNORECASE)
        if status and (header_status or not statuses or statuses[-1] != int(status[1])):
            statuses.append(int(status[1])); headers = {}
        header = re.match(r'^(Retry-After|X-RateLimit-Reset|X-RateLimit-Remaining):\s*(.*?)\s*$', line, re.IGNORECASE)
        if header:
            headers[header[1].lower()] = header[2]
    status = statuses[-1] if statuses else None
    message = stderr.lower()
    if status == 401:
        category = 'authentication'
    elif status == 429 or (status == 403 and (headers.get('x-ratelimit-remaining') == '0' or
            'retry-after' in headers or 'api rate limit exceeded' in message or 'secondary rate limit' in message)):
        category = 'rate_limit'
    elif status is not None:
        category = 'service' if status >= 500 else 'resource'
    elif any(value in message for value in ('authentication failed', 'could not read username')):
        category = 'authentication'
    elif any(value in message for value in ('could not resolve', 'unable to access', 'connection refused',
             'connection reset', 'timed out', 'failed to connect', "couldn't resolve host")):
        category = 'connection'
    elif 'rate limit' in message:
        category = 'rate_limit'
    else:
        category = 'resource'
    hints = []
    value = headers.get('retry-after')
    if value:
        try:
            hints.append(max(0, float(value)))
        except ValueError:
            try: hints.append(max(0, parsedate_to_datetime(value).timestamp() - now))
            except (TypeError, ValueError, OverflowError): pass
    if category == 'rate_limit' and headers.get('x-ratelimit-reset'):
        try: hints.append(max(0, float(headers['x-ratelimit-reset']) - now))
        except ValueError: pass
    return category, max(hints) if hints else None


def command(argv, cwd):
    env = dict(os.environ, GIT_TRACE_CURL='1', GIT_TRACE_CURL_NO_DATA='1', GH_DEBUG='api')
    try:
        gate = active_gate.get()
        if gate is None:
            result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=90)
        else:
            result = tracked_command(gate, argv, cwd, env)
    except subprocess.TimeoutExpired:
        raise RemoteFailure('connection') from None
    if result.returncode:
        category, delay = response_metadata(result.stderr)
        raise RemoteFailure(category, delay)
    return result.stdout.strip()


def tracked_command(gate, argv, cwd, env):
    identity = gate.transport_intent()
    # Before exec, this trusted isolated trampoline durably acknowledges its new
    # session/group. No argv, environment, output or credential enters the journal.
    entry = ('import os,sqlite3,sys\n'
             'db=sqlite3.connect(sys.argv[1],timeout=15)\n'
             'db.execute("UPDATE transports SET pid=? WHERE identity=?",(os.getpid(),sys.argv[2]))\n'
             'db.commit(); db.close()\n'
             'try: os.execvpe(sys.argv[3],sys.argv[3:],os.environ)\n'
             'except OSError: sys.exit(125)\n')
    try:
        process = subprocess.Popen([sys.executable, '-I', '-B', '-c', entry,
                                    gate.journal.path, identity, *argv], cwd=cwd, env=env,
                                   stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True, start_new_session=True)
    except OSError:
        gate.transport_finished(identity, not_started=True)
        raise
    try:
        try:
            stdout, stderr = process.communicate(timeout=90)
        except subprocess.TimeoutExpired:
            # Only an un-reaped, still-running owned leader can be signalled safely.
            if process.poll() is not None:
                raise Barrier('transport leader exited; descendant quiescence requires reconciliation') from None
            os.killpg(process.pid, signal.SIGKILL)
            try:
                process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                raise Barrier('transport stop not confirmed') from None
            gate.transport_finished(identity)
            raise
        gate.transport_finished(identity)
        if process.returncode == 125:
            raise Barrier('transport command could not start; connection health unestablished')
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)
    finally:
        process.stdout.close()
        process.stderr.close()



class GitHub:
    def __init__(self, gate, checkout, repository):
        self.gate, self.checkout, self.repository = gate, Path(checkout), repository
        if repository != 'stemarie/context-foundry':
            raise Barrier('this acceptance delivery target is not authorized')
        remote = local_git(self.checkout, 'remote', 'get-url', 'origin')
        if remote not in ('https://github.com/' + repository + '.git', 'https://github.com/' + repository):
            raise Barrier('unexpected remote transport or repository')

    @contextlib.contextmanager
    def integration(self):
        # One shared runtime journal is mandatory across all projects on this host.
        # The lock covers ownership, target inspection, push, checks and native Done.
        from .core import digest
        path = Path(self.gate.journal.path).parent / ('integration-' + digest(self.repository + ':main') + '.lock')
        with path.open('a') as stream:
            os.chmod(path, 0o600)
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Barrier('target integration busy; wait for current owner') from None
            try:
                # A dead controller releases flock, but its Git process can live
                # on. Inspect all connection aliases in this shared journal while
                # holding the target lock, before admitting another integration.
                with self.gate.journal.transaction() as db:
                    self.gate.quiescent(db, all_connections=True)
                yield
            finally:
                fcntl.flock(stream, fcntl.LOCK_UN)

    def _head(self):
        output = command(['git', 'ls-remote', '--exit-code', 'origin', 'refs/heads/main'], self.checkout)
        return output.split()[0]

    def head(self):
        def read():
            return {'sha': self._head()}
        return self.gate.run('read:' + uuid.uuid4().hex, {'operation': 'head'}, read)['sha']

    def fetch(self):
        return self.gate.run('fetch:' + uuid.uuid4().hex, {'operation': 'fetch'},
                             lambda: {'completed': command(['git', '-c', 'core.hooksPath=/dev/null', 'fetch', 'origin', 'main'], self.checkout) == ''})

    def push(self, sha, expected, authority):
        intent = {'operation': 'push', 'repository': self.repository, 'sha': sha, 'expected': expected}

        def reconcile():
            head = self._head()
            return {'sha': sha, 'reconciled': True} if head == sha else None

        def write():
            authority()
            if self._head() != expected:
                raise Barrier('target advanced; inspect and obtain fresh QA for candidate changes')
            if subprocess.run(['git', 'merge-base', '--is-ancestor', expected, sha], cwd=self.checkout).returncode:
                raise Barrier('delivery must fast-forward')
            # Git's advertised expected head is checked again by the pre-push hook.
            # The push itself has no force option. A receive-side race is rejected by Git.
            with tempfile.TemporaryDirectory(prefix='cf-push-', dir=Path(self.gate.journal.path).parent) as root:
                hook = Path(root) / 'pre-push'
                hook.write_text('#!/usr/bin/python3\nimport sys\nrows=[line.split() for line in sys.stdin]\n'
                                'assert len(rows)==1\nr=rows[0]\nassert r[1]==' + repr(sha) +
                                ' and r[2]=="refs/heads/main" and r[3]==' + repr(expected) + '\n')
                hook.chmod(0o700)
                command(['git', '-c', 'core.hooksPath=' + root, 'push', 'origin', sha + ':refs/heads/main'], self.checkout)
            if self._head() != sha:
                raise Barrier('delivery response requires authoritative reconciliation')
            return {'sha': sha, 'expected': expected, 'non_force': True}

        return self.gate.run('push:' + self.repository + ':' + sha, intent, write, reconcile)

    def historical_issue(self, marker, title, body):
        # A deterministic marker is used by both creation and uncertain-response recovery.
        def reconcile():
            raw = command(['gh', 'issue', 'list', '--repo', self.repository, '--state', 'all',
                           '--limit', '1000', '--json', 'url,body'], self.checkout)
            matches = [row['url'] for row in json.loads(raw) if marker in row['body']]
            if len(matches) > 1:
                raise Barrier('duplicate historical records require reconciliation')
            return {'url': matches[0]} if matches else None

        def write():
            prior = reconcile()
            if prior:
                return prior
            with tempfile.NamedTemporaryFile(mode='w', prefix='cf-issue-', suffix='.md', dir=Path(self.gate.journal.path).parent) as stream:
                stream.write(body + '\n\n' + marker + '\n')
                stream.flush()
                url = command(['gh', 'issue', 'create', '--repo', self.repository, '--title', title,
                               '--body-file', stream.name], self.checkout)
            if not url.startswith('https://github.com/' + self.repository + '/issues/'):
                raise Barrier('historical issue response requires reconciliation')
            raw = command(['gh', 'issue', 'view', url, '--repo', self.repository, '--json', 'url,body'], self.checkout)
            verified = json.loads(raw)
            if verified.get('url') != url or marker not in verified.get('body', ''):
                raise Barrier('historical issue response requires reconciliation')
            return {'url': url}

        return self.gate.run('history:' + marker, {'title': title, 'body': body, 'repository': self.repository}, write, reconcile)

    def close_history(self, url):
        if not url.startswith('https://github.com/' + self.repository + '/issues/'):
            raise Barrier('unexpected historical reference')
        number = url.rsplit('/', 1)[1]
        if not number.isdigit():
            raise Barrier('invalid historical reference')
        def reconcile():
            state = command(['gh', 'issue', 'view', number, '--repo', self.repository, '--json', 'state'], self.checkout)
            return {'url': url, 'closed': True} if json.loads(state)['state'] == 'CLOSED' else None
        def close():
            if not reconcile():
                command(['gh', 'issue', 'close', number, '--repo', self.repository, '--reason', 'completed'], self.checkout)
            result = reconcile()
            if not result:
                raise Barrier('historical closure requires reconciliation')
            return result
        return self.gate.run('close:' + url, {'url': url, 'outcome': 'completed'}, close, reconcile)
