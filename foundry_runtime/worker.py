"""Isolated installed-Hermes process. No generic terminal, network or remote Git tool."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import threading
import time

from .core import Barrier, Journal
from .runtime import Tools, ServiceUnavailable, command_binding, parse_service_time


def main():
    # Hermes may re-exec while preparing an isolated home's dependencies.
    # Import before consuming stdin or acknowledging the durable launch.
    if not sys.flags.isolated:
        raise Barrier('native startup requires isolated Python')
    from run_agent import AIAgent
    parser = argparse.ArgumentParser()
    parser.add_argument('--journal', required=True)
    parser.add_argument('--launch', required=True)
    parser.add_argument('--nonce', required=True)
    args = parser.parse_args()
    journal = Journal(args.journal)
    journal.acknowledge(args.launch, args.nonce)  # Before reading stdin: uncertain parent starts are discoverable.
    payload = json.load(sys.stdin)
    config, runtime = payload['config'], payload['model_runtime']
    home = Path(config['home'])
    home.mkdir(mode=0o700, exist_ok=True)
    events = home / 'events.jsonl'

    def event(kind, **fields):
        with events.open('a') as stream:
            stream.write(json.dumps({'time': time.time(), 'event': kind, **fields}) + '\n')

    stop = threading.Event()
    unsafe = threading.Event()
    terminal = threading.Event()
    tools = Tools(config)

    def unavailable(exc):
        unsafe.set()
        event('authority_unavailable', error_category=type(exc).__name__,
              transport_category=getattr(exc, 'category', None), service_code=getattr(exc, 'code', None))

    def heartbeat():
        while not stop.wait(config.get('heartbeat_seconds', 5)):
            try:
                job = tools.client.workflow('get', {'project_id': tools.binding['project_id'], 'contract_id': tools.binding['contract_id']})['job']
                if job['stage'] not in ('Implementing', 'QA'):
                    return
                tools.client.authority(tools.binding, tools.role)
                renewed = tools.client.workflow('heartbeat', {**command_binding(tools.binding),
                    'lease_seconds': config.get('lease_seconds', 300),
                    'idempotency_key': 'heartbeat:' + args.launch + ':' + str(time.time_ns())})['job']
                was_unsafe = unsafe.is_set()
                unsafe.clear()
                if was_unsafe:
                    event('authority_recovered', attempt=renewed['attempt']['id'])
            except ServiceUnavailable as exc:
                unavailable(exc)  # Fence writes; retry only against actual current authority.
            except Exception as exc:
                unavailable(exc)
                terminal.set()  # Expiry, stale binding, revoked credentials: never renew by inference.
                return

    if tools.role == 'worker' and config.get('heartbeat', True):
        threading.Thread(target=heartbeat, daemon=True).start()
    try:
        from tools.registry import registry
        operations = ['assignment', 'history', 'read', 'diff', 'check'] + (['write', 'submit'] if tools.role == 'worker' else ['verdict'])

        def action(values, **_kwargs):
            try:
                if unsafe.is_set():
                    raise Barrier('authority unavailable; writes fenced')
                op = values.get('operation')
                if op not in operations:
                    raise Barrier('operation not exposed to this actor')
                event('tool', operation=op)
                return json.dumps(tools.invoke(op, values))
            except ServiceUnavailable as exc:
                unavailable(exc)
                return json.dumps({'error': str(exc), 'transport_category': exc.category})
            except Exception as exc:
                # Fixed authority errors and local file errors only; no raw HTTP/provider response.
                return json.dumps({'error': str(exc) if isinstance(exc, Barrier) else type(exc).__name__})

        schema = {'name': 'foundry_action', 'description': 'Use your current assignment and isolated workspace. No shell or remote Git access.',
                  'parameters': {'type': 'object', 'properties': {
                      'operation': {'type': 'string', 'enum': operations}, 'path': {'type': 'string'},
                      'content': {'type': 'string'}, 'summary': {'type': 'string'},
                      'offset': {'type': 'integer', 'minimum': 0}, 'limit': {'type': 'integer', 'minimum': 1, 'maximum': 64000},
                      'after': {'type': 'integer', 'minimum': 0}, 'version': {'type': 'string'},
                      'verdict': {'type': 'string', 'enum': ['Accepted', 'Changes requested', 'Blocked']}},
                      'required': ['operation'], 'additionalProperties': False}}
        registry.register('foundry_action', 'cf_invocation', schema, action)
        agent = AIAgent(model=config['model'], provider=runtime['provider'], api_mode=runtime['api_mode'],
                        api_key=runtime['api_key'], base_url=runtime['base_url'], max_iterations=12,
                        enabled_toolsets=['cf_invocation'], quiet_mode=True, skip_context_files=True,
                        skip_memory=True, skip_background_review=True, load_soul_identity=False,
                        save_trajectories=False, side_agent=True, run_budget_seconds=180, max_tokens=3000,
                        cwd=str(tools.workspace))
        for name in list(registry.get_all_tool_names()):
            if name != 'foundry_action':
                registry.deregister(name)
                registry.deregister(name, scope=registry.current_scope_key())
        exposed = {t['function']['name'] for t in agent.tools}
        event('capability_probe', exposed=sorted(exposed), registry=sorted(registry.get_all_tool_names()))
        if exposed != {'foundry_action'} or set(registry.get_all_tool_names()) != {'foundry_action'}:
            raise Barrier('native tool isolation could not be established')
        for prohibited in ('terminal', 'execute_code', 'delegate_task', 'web_extract', 'web_search'):
            if registry.get_entry(prohibited) is not None:
                raise Barrier('unexpected inherited capability')
        event('startup_isolation', isolated=bool(sys.flags.isolated))
        event('capabilities', tools=sorted(exposed), actor=tools.binding['actor'], role=tools.role)
        barrier = config.get('start_barrier')
        if barrier:
            until = time.monotonic() + config.get('start_barrier_seconds', 120)
            while not Path(barrier).exists():
                if time.monotonic() > until:
                    raise Barrier('operator start barrier timed out')
                time.sleep(.05)
        deadline = time.monotonic() + config.get('invocation_seconds', 600)
        while time.monotonic() < deadline:
            try:
                job = tools.client.workflow('get', {'project_id': tools.binding['project_id'], 'contract_id': tools.binding['contract_id']})['job']
                if tools.role == 'worker' and job['stage'] in ('QA accepted', 'Integrating', 'Done', 'Cancelled', 'Blocked'):
                    break
                if tools.role == 'qa' and job['stage'] != 'QA':
                    break
                tools.client.authority(tools.binding, tools.role)
            except ServiceUnavailable as exc:
                unavailable(exc)
                stop.wait(.5)
                continue
            if terminal.is_set():
                raise Barrier('lease expired, revoked or stale; recovery requires confirmed stop')
            if unsafe.is_set():
                if tools.role == 'qa':
                    unsafe.clear()  # Full current QA authority was just revalidated.
                    event('authority_recovered', attempt=tools.binding['attempt_id'])
                else:
                    stop.wait(.2)  # Only a validated, successful owning heartbeat clears this fence.
                    continue
            if tools.role == 'worker' and job['stage'] == 'QA':
                stop.wait(.2)
                continue
            prompt = config['role_instructions'] + '\n\nAssigned immutable work:\n' + job['revision']['body_markdown']
            if tools.role == 'worker':
                prompt += '\nUse assignment/read/write/check tools. After successful checks, submit with a concise commit summary. Do not integrate, approve yourself or invoke a remote transport. If QA requested corrections, inspect current history and correct this same assignment.'
            else:
                prompt += '\nIndependently inspect assignment, exact candidate diff and relevant files; run check yourself. Record an evidence-backed verdict with verdict/summary. Do not write, commit, integrate, or mark Done.'
            prompt += '\nUse history continuation and read/diff next_offset/version until the required evidence is fully inspected. Assignment includes the latest QA verdict even after many heartbeats. A pending_submission identifies a prepared immutable commit; retry its original summary after revalidation. Never claim a truncated prefix is a full review.'
            event('model_started')
            result = agent.run_conversation(prompt)
            event('model_finished', completed=bool(result.get('completed')), api_calls=result.get('api_calls', 0))
            try:
                refreshed = tools.client.workflow('get', {'project_id': tools.binding['project_id'], 'contract_id': tools.binding['contract_id']})['job']
            except ServiceUnavailable as exc:
                unavailable(exc)
                continue
            if tools.role == 'worker' and refreshed['stage'] == 'QA':
                # A successful service submission survives model iteration exhaustion.
                # Keep this process and heartbeat through QA and corrections.
                continue
            if tools.role == 'qa' and refreshed['stage'] != 'QA':
                break  # Reconcile the actual verdict even if the final model reply was cut short.
            if result.get('error') or not result.get('completed'):
                event('turn_reconciled', stage=refreshed['stage'])
                continue  # Current authority is checked again; bounded invocation still applies.
            raise Barrier('actor returned without its required service transition')

        else:
            raise Barrier('bounded invocation ended; current assignment retained')
        event('retired')
    except BaseException as exc:
        event('blocked', category=type(exc).__name__)
        # This file is private operator diagnostics; never publish provider/credential details.
        (home / 'failure.txt').write_text(type(exc).__name__ + ': ' + str(exc)[:1000])
        os.chmod(home / 'failure.txt', 0o600)
        raise SystemExit(2)
    finally:
        stop.set()
        journal.finish(args.launch)


if __name__ == '__main__':
    main()
