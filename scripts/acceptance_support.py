"""Shared acceptance mechanics; scenario assertions and cleanup stay with runners.

These helpers do not launch agents, judge acceptance, retry mutations, integrate,
or decide whether private evidence can be removed.
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import uuid

from foundry_runtime import constants as settings
from foundry_runtime.core import Barrier


READ_ONLY_WORKFLOW_OPERATIONS = frozenset({'get', 'list', 'agents', 'assignments', 'history'})


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def issue_actor_tokens(server, binary, actors, *, prefix, containerized=False):
    """Issue each explicitly selected actor; retain issued tokens on partial failure."""
    for actor, scopes in actors:
        if containerized:
            token = server.issue_token(prefix + actor, scopes)
        else:
            result = subprocess.run([str(binary), 'token', 'issue', prefix + actor, scopes],
                                    env=server.env, capture_output=True, text=True, check=True)
            token = next(line[6:] for line in result.stdout.splitlines() if line.startswith('token='))
        server.tokens[actor] = token


def resolve_provider(python, source, *, disable_bytecode=False):
    """Resolve the selected provider privately; preserve the virtualenv launcher path."""
    program = ('from hermes_cli.runtime_provider import resolve_runtime_provider; import json; '
               'r=resolve_runtime_provider(requested=' + repr(settings.ACCEPTANCE_PROVIDER) +
               ',target_model=' + repr(settings.ACCEPTANCE_MODEL) + '); '
               'print(json.dumps({k:r[k] for k in ["provider","api_mode","api_key","base_url"]}))')
    result = subprocess.run([str(python), *(['-B'] if disable_bytecode else []), '-c', program],
                            env=dict(os.environ, PYTHONPATH=str(source), PYTHONDONTWRITEBYTECODE='1'),
                            capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def quiet_call(api, operation, values, actor='admin', expected_error=None):
    with contextlib.redirect_stdout(io.StringIO()):
        if expected_error is not None:
            return api.call(operation, values, actor, expected_error)
        return api.call(operation, values, actor)


def workflow_call(api, project_id, operation, values=None, actor='coordinator', expected_error=None):
    command = dict(values or {}, project_id=project_id)
    if operation not in READ_ONLY_WORKFLOW_OPERATIONS:
        command['idempotency_key'] = uuid.uuid4().hex
    result = quiet_call(api, 'workflow_' + operation, command, actor, expected_error)
    return result if expected_error else result['workflow']


def job_binding(job, *, project_id=None, include_candidate=False):
    result = {'contract_id': job['contract_id'], 'revision': job['revision']['number'],
              'digest': job['revision']['digest'], 'attempt_id': job['attempt']['id']}
    if project_id is not None:
        result['project_id'] = project_id
    if include_candidate and job.get('candidate'):
        result.update(candidate_id=job['candidate']['id'], candidate_sha=job['candidate']['sha'])
    return result


def workflow_pages(work, operation, *, field, cursor_field, values=None, actor='reader'):
    """Yield complete pages; refuse a non-advancing cursor rather than loop forever."""
    after = 0
    while True:
        page = work(operation, dict(values or {}, after=after, limit=settings.HISTORY_PAGE_SIZE), actor)
        rows = page.get(field, [])
        yield page
        if len(rows) < settings.HISTORY_PAGE_SIZE:
            return
        next_after = rows[-1][cursor_field]
        if next_after <= after:
            raise Barrier('acceptance pagination did not advance')
        after = next_after


def history_snapshot(work, contract_id, *, actor='reader'):
    history = {'events': [], 'revisions': []}
    for page in workflow_pages(work, 'history', field='events', cursor_field='id',
                               values={'contract_id': contract_id}, actor=actor):
        history['events'].extend(page.get('events', []))
        history['revisions'] = page.get('revisions', [])
    return history
