import io
import json
import math
from pathlib import Path
import sys
import tempfile
import types
import unittest

from foundry_runtime.core import Barrier
from foundry_runtime.worker import (DEFAULT_SDK_CONFIG, complete_turn, pending_transition_prompt, reconcile_turn,
                                    remaining_turn_seconds, run_sdk_turn, sdk_config, turn_decision,
                                    validated_invocation_seconds)
from unittest.mock import Mock, patch


class FakeAgent:
    def __init__(self, results):
        self.results = iter(results)
        self.prompts = []
        self.run_budget_seconds = None

    def run_conversation(self, prompt):
        self.prompts.append(prompt)
        return next(self.results)


class WorkerConfigTests(unittest.TestCase):
    def test_defaults_and_valid_operator_overrides_are_bounded(self):
        self.assertEqual(DEFAULT_SDK_CONFIG, sdk_config({}))
        self.assertEqual({'max_iterations': 48, 'max_tokens': 12000, 'run_budget_seconds': 1200}, sdk_config({
            'sdk': {'max_iterations': 48, 'max_tokens': 12000, 'run_budget_seconds': 1200}}))

    def test_completion_continuation_explicitly_demands_the_native_transition(self):
        self.assertIn('native submission', pending_transition_prompt('worker'))
        self.assertIn('native verdict', pending_transition_prompt('qa'))

    def test_runtime_turn_decisions_cover_completion_exhaustion_handoff_and_authority_fencing(self):
        # The same decision helper is used by the invocation loop after a fresh native read.
        self.assertEqual('continue', turn_decision('worker', {'completed': True}, 'Implementing'))
        self.assertEqual('retry', turn_decision('worker', {'completed': False}, 'Implementing'))
        self.assertEqual('retry', turn_decision('qa', {'completed': True, 'error': 'iteration limit'}, 'QA'))
        self.assertEqual('handoff', turn_decision('worker', {'completed': True}, 'QA'))
        self.assertEqual('handoff', turn_decision('qa', {'completed': True}, 'Implementing'))

    def test_runtime_reconciliation_fences_continuation_and_skips_handoff_authority(self):
        tools = Mock()
        tools.role = 'worker'
        tools.binding = {'contract_id': 'contract'}
        tools.client.authority.return_value = {'stage': 'Implementing'}
        decision, current = reconcile_turn(tools, {'completed': True}, 'Implementing')
        self.assertEqual(('continue', {'stage': 'Implementing'}), (decision, current))
        tools.client.authority.assert_called_once_with(tools.binding, 'worker')
        tools.client.authority.reset_mock()
        decision, current = reconcile_turn(tools, {'completed': True}, 'QA')
        self.assertEqual(('handoff', None), (decision, current))
        tools.client.authority.assert_not_called()

    def test_fake_model_completion_is_reprompted_until_native_handoff(self):
        # complete_turn is the invocation-loop path: it runs the model, rereads
        # native state, and fences the result before the next continuation prompt.
        agent = FakeAgent([{'completed': True}, {'completed': True}])
        settings = sdk_config({'sdk': {'run_budget_seconds': 120}})
        tools = Mock()
        tools.role = 'worker'
        tools.binding = {'project_id': 'project', 'contract_id': 'contract'}
        tools.client.workflow.side_effect = [
            {'job': {'stage': 'Implementing'}}, {'job': {'stage': 'QA'}}]
        tools.client.authority.return_value = {'stage': 'Implementing'}
        first, cap, decision, current, refreshed = complete_turn(
            tools, agent, 'first', 110.9, settings, now=lambda: 10.1)
        self.assertEqual(({'completed': True}, 100, 'continue', {'stage': 'Implementing'}),
                         (first, cap, decision, current))
        self.assertEqual('Implementing', refreshed['stage'])
        self.assertEqual('continue', decision)
        # A completed response has no service effect: the loop appends this continuation prompt.
        second, cap, decision, current, refreshed = complete_turn(
            tools, agent, 'second' + pending_transition_prompt('worker'), 110.9, settings, now=lambda: 10.1)
        self.assertEqual(100, cap)
        self.assertIn('native submission', agent.prompts[-1])
        self.assertEqual(('handoff', None, 'QA'), (decision, current, refreshed['stage']))
        self.assertEqual(2, tools.client.workflow.call_count)

    def test_fake_model_turn_is_capped_by_actual_remaining_deadline_and_expires(self):
        agent = FakeAgent([{'completed': False, 'error': 'iteration limit'}])
        settings = sdk_config({'sdk': {'run_budget_seconds': 1200}})
        result, cap = run_sdk_turn(agent, 'bounded', 12.9, settings, now=lambda: 10.1)
        self.assertEqual({'completed': False, 'error': 'iteration limit'}, result)
        self.assertEqual(2, cap)
        self.assertEqual('retry', turn_decision('worker', result, 'Implementing'))
        with self.assertRaises(Barrier):
            run_sdk_turn(agent, 'expired', 10.1, settings, now=lambda: 10.2)

    def test_outer_deadline_and_actual_remaining_turn_cap_are_bounded(self):
        self.assertEqual(1, validated_invocation_seconds({'invocation_seconds': 1}))
        self.assertEqual(1200, validated_invocation_seconds({'invocation_seconds': 1200}))
        for value in (True, 0, -1, 1201, math.inf, '600'):
            with self.subTest(value=value):
                with self.assertRaises(Barrier):
                    validated_invocation_seconds({'invocation_seconds': value})
        self.assertEqual(2, remaining_turn_seconds(12.9, now=lambda: 10.1))
        self.assertEqual(0, remaining_turn_seconds(10.1, now=lambda: 10.2))

    def test_sdk_rejects_boolean_nonfinite_fractional_and_excessive_values(self):
        invalid = {
            'max_iterations': (True, -1, 0, 1.0, 1.5, math.inf, '12', 49),
            'max_tokens': (True, -1, 0, 256.0, math.inf, '3000', 12001),
            'run_budget_seconds': (True, -1, 0, 1.0, math.inf, '180', 1201),
        }
        for name, values in invalid.items():
            for value in values:
                with self.subTest(name=name, value=value):
                    with self.assertRaises(Barrier):
                        sdk_config({'sdk': {name: value}})
        with self.assertRaises(Barrier):
            sdk_config({'sdk': {'unknown': 1}})
        with self.assertRaises(Barrier):
            sdk_config({'sdk': []})

    def test_actual_main_blocks_authority_loss_and_exhausted_deadline(self):
        from foundry_runtime import worker

        class Registry:
            def register(self, *_args):
                pass
            def get_all_tool_names(self):
                return ['foundry_action']
            def get_entry(self, _name):
                return None
            def current_scope_key(self):
                return 'fixture'
            def deregister(self, *_args, **_kwargs):
                pass

        class Flags:
            def __init__(self, original):
                self.original, self.isolated = original, 1
            def __getattr__(self, key):
                return getattr(self.original, key)

        for kind in ('authority_lost', 'deadline', 'deadline_after_authority', 'normal_pending_verdict', 'service_recovered'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as folder:
                root, calls, finished = Path(folder), [], []
                test_case = self
                class Client:
                    reads = 0
                    stage = 'QA'
                    def workflow(self, *_args):
                        return {'job': {'stage': self.stage, 'contract_version': 'Alpha 1.0', 'revision': {'body_markdown': 'fixture'}}}
                    def authority(self, *_args):
                        self.reads += 1
                        if kind == 'authority_lost' and self.reads > 1:
                            raise Barrier('fixture authority revoked after model turn')
                        if kind == 'service_recovered' and self.reads == 2:
                            raise worker.ServiceUnavailable('timeout')
                        return {'stage': self.stage, 'contract_version': 'Alpha 1.0', 'revision': {'body_markdown': 'fixture'}}
                client = Client()
                class Tools:
                    def __init__(self, _config):
                        self.role = 'qa'; self.workspace = root; self.client = client
                        self.binding = {'project_id': 'p', 'contract_id': 'c', 'actor': 'qa', 'attempt_id': 'a'}
                class Agent:
                    def __init__(self, **kwargs):
                        self.tools = [{'function': {'name': 'foundry_action'}}]
                        self.run_budget_seconds = kwargs['run_budget_seconds']
                    def run_conversation(self, prompt):
                        calls.append((self.run_budget_seconds, prompt))
                        events = [json.loads(line) for line in (root/'home/events.jsonl').read_text().splitlines()]
                        test_case.assertEqual('model_started', events[-1]['event'])
                        test_case.assertEqual(self.run_budget_seconds, events[-1]['turn_seconds'])
                        if kind in ('normal_pending_verdict', 'service_recovered') and len(calls) == 2:
                            client.stage = 'Implementing'
                        return {'completed': True}
                class Journal:
                    def __init__(self, *_args):
                        pass
                    def acknowledge(self, *_args):
                        pass
                    def finish(self, *_args):
                        finished.append(True)
                payload = {'config': {'role': 'qa', 'home': str(root/'home'), 'model': 'fixture',
                                      'role_instructions': 'fixture', 'invocation_seconds': 30 if kind in ('authority_lost', 'deadline_after_authority', 'normal_pending_verdict', 'service_recovered') else 1},
                           'model_runtime': {'provider': 'fixture', 'api_mode': 'fixture', 'api_key': 'fixture', 'base_url': 'fixture'}}
                agent_module = types.ModuleType('run_agent'); agent_module.AIAgent = Agent
                tools_module = types.ModuleType('tools'); tools_module.__path__ = []
                registry_module = types.ModuleType('tools.registry'); registry_module.registry = Registry()
                real_monotonic = worker.time.monotonic
                ticks = iter((0, 0, 31))
                def monotonic():
                    if kind == 'deadline':
                        return next(ticks)
                    return next(ticks) if kind == 'deadline_after_authority' else real_monotonic()
                with patch.dict(sys.modules, {'run_agent': agent_module, 'tools': tools_module, 'tools.registry': registry_module}), \
                        patch.object(worker, 'Tools', Tools), patch.object(worker, 'Journal', Journal), \
                        patch.object(worker.time, 'monotonic', side_effect=monotonic), \
                        patch.object(sys, 'flags', Flags(sys.flags)), patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                        patch.object(worker.argparse.ArgumentParser, 'parse_args', return_value=types.SimpleNamespace(journal='j', launch='l', nonce='n')):
                    try:
                        worker.main()
                    except SystemExit as caught:
                        exit_code = caught.code
                    else:
                        exit_code = 0
                events = [json.loads(line)['event'] for line in (root/'home/events.jsonl').read_text().splitlines()]
                failure = (root/'home/failure.txt').read_text() if (root/'home/failure.txt').exists() else ''
                self.assertTrue(finished)
                if kind == 'authority_lost':
                    self.assertEqual(2, exit_code)
                    self.assertIn('blocked', events); self.assertNotIn('retired', events)
                    self.assertEqual(1, len(calls))
                    self.assertGreater(calls[0][0], 0)
                    self.assertLessEqual(calls[0][0], 30)
                    self.assertIn('fixture authority revoked after model turn', failure)
                elif kind.startswith('deadline'):
                    self.assertEqual(2, exit_code)
                    self.assertIn('blocked', events); self.assertNotIn('retired', events)
                    self.assertEqual([], calls); self.assertNotIn('model_started', events)
                    self.assertIn('deadline', failure)
                else:
                    self.assertEqual(0, exit_code)
                    self.assertEqual(2, len(calls)); self.assertIn('retired', events)
                    self.assertNotIn('blocked', events); self.assertFalse((root/'home/failure.txt').exists())
                    if kind == 'normal_pending_verdict':
                        self.assertIn('native verdict', calls[1][1])
                    if kind == 'service_recovered':
                        self.assertIn('authority_unavailable', events)
                        self.assertIn('authority_recovered', events)
                        self.assertGreaterEqual(client.reads, 3)

    def test_actual_main_retires_when_worker_is_released_during_model_return(self):
        from foundry_runtime import worker

        class Registry:
            def register(self, *_args): pass
            def get_all_tool_names(self): return ['foundry_action']
            def get_entry(self, _name): return None
            def current_scope_key(self): return 'fixture'
            def deregister(self, *_args, **_kwargs): pass

        class Flags:
            def __init__(self, original): self.original, self.isolated = original, 1
            def __getattr__(self, key): return getattr(self.original, key)

        with tempfile.TemporaryDirectory() as folder:
            root, calls, finished = Path(folder), [], []
            active = {'stage': 'Implementing', 'contract_version': 'Alpha 1.0',
                      'revision': {'number': 1, 'digest': 'd', 'body_markdown': 'fixture'}, 'attempt': {'id': 'a'}}
            pending = {**active, 'stage': 'QA'}
            accepted = {**active, 'stage': 'QA accepted'}
            class Client:
                def __init__(self): self.gets = 0
                def workflow(self, operation, _body):
                    if operation == 'get':
                        self.gets += 1
                        return {'job': active if self.gets == 1 else pending if self.gets == 2 else accepted}
                    raise AssertionError(operation)
                def authority(self, *_args):
                    if self.gets >= 2:
                        raise Barrier('worker assignment released after matching QA acceptance')
                    return active
            client = Client()
            class Tools:
                def __init__(self, _config):
                    self.role = 'worker'; self.workspace = root; self.client = client
                    self.binding = {'project_id': 'p', 'contract_id': 'c', 'actor': 'worker', 'attempt_id': 'a',
                                    'revision': 1, 'digest': 'd'}
            class Agent:
                def __init__(self, **kwargs):
                    self.tools = [{'function': {'name': 'foundry_action'}}]; self.run_budget_seconds = kwargs['run_budget_seconds']
                def run_conversation(self, _prompt):
                    calls.append(self.run_budget_seconds)
                    return {'completed': True}
            class Journal:
                def __init__(self, *_args): pass
                def acknowledge(self, *_args): pass
                def finish(self, *_args): finished.append(True)
            payload = {'config': {'role': 'worker', 'home': str(root/'home'), 'model': 'fixture',
                                  'role_instructions': 'fixture', 'invocation_seconds': 30, 'heartbeat': False},
                       'model_runtime': {'provider': 'fixture', 'api_mode': 'fixture', 'api_key': 'fixture', 'base_url': 'fixture'}}
            agent_module = types.ModuleType('run_agent'); agent_module.AIAgent = Agent
            tools_module = types.ModuleType('tools'); tools_module.__path__ = []
            registry_module = types.ModuleType('tools.registry'); registry_module.registry = Registry()
            with patch.dict(sys.modules, {'run_agent': agent_module, 'tools': tools_module, 'tools.registry': registry_module}), \
                    patch.object(worker, 'Tools', Tools), patch.object(worker, 'Journal', Journal), \
                    patch.object(sys, 'flags', Flags(sys.flags)), patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                    patch.object(worker.argparse.ArgumentParser, 'parse_args', return_value=types.SimpleNamespace(journal='j', launch='l', nonce='n')):
                worker.main()
            events = [json.loads(line)['event'] for line in (root/'home/events.jsonl').read_text().splitlines()]
            self.assertEqual(1, len(calls))
            self.assertIn('retired', events); self.assertNotIn('blocked', events)
            self.assertFalse((root/'home/failure.txt').exists())
            self.assertTrue(finished)

    def test_actual_main_retires_when_first_post_model_read_is_matching_accepted(self):
        from foundry_runtime import worker

        class Registry:
            def register(self, *_args): pass
            def get_all_tool_names(self): return ['foundry_action']
            def get_entry(self, _name): return None
            def current_scope_key(self): return 'fixture'
            def deregister(self, *_args, **_kwargs): pass

        class Flags:
            def __init__(self, original): self.original, self.isolated = original, 1
            def __getattr__(self, key): return getattr(self.original, key)

        with tempfile.TemporaryDirectory() as folder:
            root, calls, finished = Path(folder), [], []
            binding = {'project_id': 'p', 'contract_id': 'c', 'actor': 'worker', 'attempt_id': 'a',
                       'revision': 1, 'digest': 'd'}
            active = {'stage': 'Implementing', 'contract_version': 'Alpha 1.0',
                      'revision': {'number': 1, 'digest': 'd', 'body_markdown': 'fixture'}, 'attempt': {'id': 'a'}}
            accepted = {**active, 'stage': 'QA accepted'}
            class Client:
                def __init__(self): self.gets = 0
                def workflow(self, operation, _body):
                    if operation == 'get':
                        self.gets += 1
                        return {'job': active if self.gets == 1 else accepted}
                    raise AssertionError(operation)
                def authority(self, *_args):
                    if self.gets >= 2:
                        raise Barrier('worker assignment released after matching QA acceptance')
                    return active
            client = Client()
            class Tools:
                def __init__(self, _config): self.role, self.workspace, self.client, self.binding = 'worker', root, client, binding
            class Agent:
                def __init__(self, **kwargs):
                    self.tools = [{'function': {'name': 'foundry_action'}}]; self.run_budget_seconds = kwargs['run_budget_seconds']
                def run_conversation(self, _prompt): calls.append(self.run_budget_seconds); return {'completed': True}
            class Journal:
                def __init__(self, *_args): pass
                def acknowledge(self, *_args): pass
                def finish(self, *_args): finished.append(True)
            payload = {'config': {'role': 'worker', 'home': str(root/'home'), 'model': 'fixture',
                                  'role_instructions': 'fixture', 'invocation_seconds': 30, 'heartbeat': False},
                       'model_runtime': {'provider': 'fixture', 'api_mode': 'fixture', 'api_key': 'fixture', 'base_url': 'fixture'}}
            agent_module = types.ModuleType('run_agent'); agent_module.AIAgent = Agent
            tools_module = types.ModuleType('tools'); tools_module.__path__ = []
            registry_module = types.ModuleType('tools.registry'); registry_module.registry = Registry()
            with patch.dict(sys.modules, {'run_agent': agent_module, 'tools': tools_module, 'tools.registry': registry_module}), \
                    patch.object(worker, 'Tools', Tools), patch.object(worker, 'Journal', Journal), \
                    patch.object(sys, 'flags', Flags(sys.flags)), patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                    patch.object(worker.argparse.ArgumentParser, 'parse_args', return_value=types.SimpleNamespace(journal='j', launch='l', nonce='n')):
                worker.main()
            events = [json.loads(line)['event'] for line in (root/'home/events.jsonl').read_text().splitlines()]
            self.assertEqual(1, len(calls))
            self.assertIn('retired', events); self.assertNotIn('blocked', events)
            self.assertFalse((root/'home/failure.txt').exists())
            self.assertTrue(finished)


    def test_actual_main_blocks_stale_terminal_worker_handoff(self):
        from foundry_runtime import worker

        class Registry:
            def register(self, *_args): pass
            def get_all_tool_names(self): return ['foundry_action']
            def get_entry(self, _name): return None
            def current_scope_key(self): return 'fixture'
            def deregister(self, *_args, **_kwargs): pass

        class Flags:
            def __init__(self, original): self.original, self.isolated = original, 1
            def __getattr__(self, key): return getattr(self.original, key)

        with tempfile.TemporaryDirectory() as folder:
            root, calls, finished = Path(folder), [], []
            binding = {'project_id': 'p', 'contract_id': 'c', 'actor': 'worker', 'attempt_id': 'a',
                       'revision': 1, 'digest': 'd'}
            active = {'stage': 'Implementing', 'contract_version': 'Alpha 1.0',
                      'revision': {'number': 1, 'digest': 'd', 'body_markdown': 'fixture'}, 'attempt': {'id': 'a'}}
            stale_terminal = {**active, 'stage': 'QA accepted', 'attempt': {'id': 'other'}}

            class Client:
                def __init__(self): self.gets = 0
                def workflow(self, operation, _body):
                    if operation == 'get':
                        self.gets += 1
                        return {'job': active if self.gets == 1 else stale_terminal}
                    raise AssertionError(operation)
                def authority(self, *_args):
                    if self.gets >= 2:
                        raise Barrier('worker assignment belongs to another attempt')
                    return active
            client = Client()

            class Tools:
                def __init__(self, _config): self.role, self.workspace, self.client, self.binding = 'worker', root, client, binding
            class Agent:
                def __init__(self, **kwargs):
                    self.tools = [{'function': {'name': 'foundry_action'}}]; self.run_budget_seconds = kwargs['run_budget_seconds']
                def run_conversation(self, _prompt): calls.append(self.run_budget_seconds); return {'completed': True}
            class Journal:
                def __init__(self, *_args): pass
                def acknowledge(self, *_args): pass
                def finish(self, *_args): finished.append(True)
            payload = {'config': {'role': 'worker', 'home': str(root/'home'), 'model': 'fixture',
                                  'role_instructions': 'fixture', 'invocation_seconds': 30, 'heartbeat': False},
                       'model_runtime': {'provider': 'fixture', 'api_mode': 'fixture', 'api_key': 'fixture', 'base_url': 'fixture'}}
            agent_module = types.ModuleType('run_agent'); agent_module.AIAgent = Agent
            tools_module = types.ModuleType('tools'); tools_module.__path__ = []
            registry_module = types.ModuleType('tools.registry'); registry_module.registry = Registry()
            with patch.dict(sys.modules, {'run_agent': agent_module, 'tools': tools_module, 'tools.registry': registry_module}), \
                    patch.object(worker, 'Tools', Tools), patch.object(worker, 'Journal', Journal), \
                    patch.object(sys, 'flags', Flags(sys.flags)), patch.object(sys, 'stdin', io.StringIO(json.dumps(payload))), \
                    patch.object(worker.argparse.ArgumentParser, 'parse_args', return_value=types.SimpleNamespace(journal='j', launch='l', nonce='n')):
                with self.assertRaises(SystemExit) as caught:
                    worker.main()
            events = [json.loads(line)['event'] for line in (root/'home/events.jsonl').read_text().splitlines()]
            self.assertEqual(2, caught.exception.code)
            self.assertEqual(1, len(calls))
            self.assertIn('blocked', events); self.assertNotIn('retired', events)
            self.assertIn('worker assignment belongs to another attempt', (root/'home/failure.txt').read_text())
            self.assertTrue(finished)


if __name__ == '__main__':
    unittest.main()
