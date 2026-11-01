"""Operator-only GitHub transport. Children receive none of these capabilities."""
import json
from pathlib import Path
import subprocess
import tempfile
import uuid

from .core import Barrier, RemoteFailure
from .runtime import local_git


def command(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=90)
    if result.returncode:
        message = result.stderr.lower()
        if any(value in message for value in ('401', 'authentication failed', 'could not read username')):
            category = 'authentication'
        elif any(value in message for value in ('429', 'rate limit')):
            category = 'rate_limit'
        elif any(value in message for value in ('could not resolve', 'unable to access', 'connection refused', 'timed out')):
            category = 'connection'
        elif any(value in message for value in ('502', '503', '500 internal')):
            category = 'service'
        else:
            category = 'resource'
        raise RemoteFailure(category)
    return result.stdout.strip()


class GitHub:
    def __init__(self, gate, checkout, repository):
        self.gate, self.checkout, self.repository = gate, Path(checkout), repository
        if repository != 'stemarie/context-foundry':
            raise Barrier('this acceptance delivery target is not authorized')
        remote = local_git(self.checkout, 'remote', 'get-url', 'origin')
        if remote not in ('https://github.com/' + repository + '.git', 'https://github.com/' + repository):
            raise Barrier('unexpected remote transport or repository')

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
            with tempfile.TemporaryDirectory(prefix='cf-push-', dir='/private/tmp') as root:
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
                           '--search', marker + ' in:body', '--json', 'url,body'], self.checkout)
            matches = [row['url'] for row in json.loads(raw) if marker in row['body']]
            if len(matches) > 1:
                raise Barrier('duplicate historical records require reconciliation')
            return {'url': matches[0]} if matches else None

        def write():
            prior = reconcile()
            if prior:
                return prior
            with tempfile.NamedTemporaryFile(mode='w', prefix='cf-issue-', suffix='.md', dir='/private/tmp') as stream:
                stream.write(body + '\n\n' + marker + '\n')
                stream.flush()
                url = command(['gh', 'issue', 'create', '--repo', self.repository, '--title', title,
                               '--body-file', stream.name], self.checkout)
            verified = reconcile()
            if not verified or verified['url'] != url:
                raise Barrier('historical issue response requires reconciliation')
            return verified

        return self.gate.run('history:' + marker, {'title': title, 'body': body, 'repository': self.repository}, write, reconcile)
