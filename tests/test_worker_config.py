import math
import unittest

from foundry_runtime.core import Barrier
from foundry_runtime.worker import (DEFAULT_SDK_CONFIG, pending_transition_prompt, remaining_turn_seconds,
                                    run_sdk_turn, sdk_config, turn_decision, validated_invocation_seconds)


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

    def test_fake_model_completion_is_reprompted_until_native_handoff(self):
        agent = FakeAgent([{'completed': True}, {'completed': True}])
        settings = sdk_config({'sdk': {'run_budget_seconds': 120}})
        first, cap = run_sdk_turn(agent, 'first', 110.9, settings, now=lambda: 10.1)
        self.assertEqual(100, cap)
        self.assertEqual('continue', turn_decision('worker', first, 'Implementing'))
        # A completed response has no service effect: the loop appends this continuation prompt.
        second, cap = run_sdk_turn(agent, 'second' + pending_transition_prompt('worker'), 110.9, settings, now=lambda: 10.1)
        self.assertEqual(100, cap)
        self.assertIn('native submission', agent.prompts[-1])
        self.assertEqual('handoff', turn_decision('worker', second, 'QA'))

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
        for value in (True, -1, 0, 1.0, 1.5, math.inf, '12', 49):
            with self.subTest(value=value):
                with self.assertRaises(Barrier):
                    sdk_config({'sdk': {'max_iterations': value}})
        with self.assertRaises(Barrier):
            sdk_config({'sdk': {'unknown': 1}})
        with self.assertRaises(Barrier):
            sdk_config({'sdk': []})


if __name__ == '__main__':
    unittest.main()
