import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/brainiac_learning.py"
QUALIFICATION_FIXTURE = ROOT / "tests/fixtures/brainiac/qualification_cases.json"
GITIGNORE = ROOT / ".gitignore"
BRAINIAC_CONFIG = ROOT / "profiles/foundry-brainiac/config.yaml"
spec = importlib.util.spec_from_file_location("brainiac_learning", SCRIPT)
assert spec and spec.loader
brainiac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brainiac)


class BrainiacLearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / "brainiac.sqlite"

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def incident(event_id, occurred_at, severity="normal", summary="worker timeout", revision="r1"):
        return {"event_id": event_id, "occurred_at": occurred_at, "severity": severity, "source": "kanban", "category": "dispatch", "summary": summary, "evidence_revision": revision}

    @staticmethod
    def proposal():
        return json.dumps({"proposal": "Bound retries.", "invariant": "One invocation per key.", "regression_test": "Replay the event.", "metric": "Repeat incidents."})

    def event_export(self, incident):
        return {"schema": brainiac.EVIDENCE_SCHEMA, "incident": incident}

    def test_no_qualifying_evidence_causes_no_astra_call(self):
        result = brainiac.process_incident(self.state, self.incident("one", "2026-01-01T00:00:00Z"))
        self.assertEqual(result["decision"], "not_qualified")
        self.assertFalse(result["astra_invoked"])

    def test_first_low_or_normal_occurrence_does_not_qualify(self):
        for severity in ("low", "normal"):
            with self.subTest(severity=severity):
                state = Path(self.temp.name) / f"{severity}.sqlite"
                result = brainiac.process_incident(state, self.incident(severity, "2026-01-01T00:00:00Z", severity))
                self.assertEqual(result["decision"], "not_qualified")

    def test_qualification_fixture_cases_have_deterministic_outcomes(self):
        cases = json.loads(QUALIFICATION_FIXTURE.read_text(encoding="utf-8"))
        for number, case in enumerate(cases):
            with self.subTest(case=case["incident"]["event_id"]):
                state = Path(self.temp.name) / f"fixture-{number}.sqlite"
                result = brainiac.process_incident(state, case["incident"])
                self.assertEqual(result["decision"], case["decision"])
                self.assertEqual(result["astra_invoked"], case["astra_invoked"])

    def test_high_severity_qualifies_exactly_once_and_duplicate_is_noop(self):
        event = self.incident("high", "2026-01-01T00:00:00Z", "high")
        first = brainiac.process_incident(self.state, event)
        second = brainiac.process_incident(self.state, event)
        self.assertTrue(first["astra_invoked"])
        self.assertEqual(first["decision"], "high_severity")
        self.assertFalse(second["astra_invoked"])
        self.assertEqual(second["decision"], "duplicate_noop")

    def test_second_same_fingerprint_within_30_days_qualifies_once(self):
        first = brainiac.process_incident(self.state, self.incident("first", "2026-01-01T00:00:00Z", "normal", "Timeout 100"))
        second = brainiac.process_incident(self.state, self.incident("second", "2026-01-30T23:59:59Z", "low", "Timeout 200"))
        self.assertFalse(first["astra_invoked"])
        self.assertTrue(second["astra_invoked"])
        self.assertEqual(second["decision"], "second_in_30_days")
        rerun = brainiac.process_incident(self.state, self.incident("second", "2026-01-30T23:59:59Z", "low", "Timeout 200"))
        self.assertEqual(rerun["decision"], "duplicate_noop")

    def test_outside_30_day_window_is_not_recurrence(self):
        brainiac.process_incident(self.state, self.incident("old", "2026-01-01T00:00:00Z"))
        result = brainiac.process_incident(self.state, self.incident("later", "2026-01-31T00:00:01Z"))
        self.assertEqual(result["decision"], "not_qualified")

    def test_weekly_synthesis_once_per_changed_revision_and_window(self):
        first = brainiac.record_weekly_synthesis(self.state, "r1", "2026-W01", "2026-01-05T00:00:00Z")
        duplicate = brainiac.record_weekly_synthesis(self.state, "r1", "2026-W01", "2026-01-05T00:00:00Z")
        changed = brainiac.record_weekly_synthesis(self.state, "r2", "2026-W01", "2026-01-05T00:00:00Z")
        self.assertTrue(first["synthesis_required"])
        self.assertFalse(duplicate["synthesis_required"])
        self.assertEqual(duplicate["decision"], "unchanged_noop")
        self.assertTrue(changed["synthesis_required"])

    def test_runtime_state_inside_checkout_is_rejected(self):
        with self.assertRaises(brainiac.BrainiacInputError):
            brainiac.process_incident(ROOT / "state" / "brainiac.sqlite", self.incident("bad", "2026-01-01T00:00:00Z"))

    def test_sensitive_incident_fields_are_rejected_before_persistence(self):
        for field in ("credentials", "accessToken", "session_id", "logs", "nested_cache"):
            with self.subTest(field=field):
                incident = self.incident(field, "2026-01-01T00:00:00Z")
                incident[field] = "must-not-persist"
                with self.assertRaisesRegex(brainiac.BrainiacInputError, "sensitive incident field is prohibited"):
                    brainiac.process_incident(self.state, incident)
        self.assertFalse(self.state.exists())

    def test_persistent_state_is_ignored_and_profile_remains_inactive(self):
        self.assertIn("*.sqlite", GITIGNORE.read_text(encoding="utf-8"))
        config = BRAINIAC_CONFIG.read_text(encoding="utf-8")
        self.assertIn("enabled: []", config)
        self.assertIn("dispatch_in_gateway: false", config)
        self.assertIn("cron_mode: deny", config)

    def test_bridge_low_normal_and_unchanged_weekly_noops_do_not_call_runner(self):
        calls = []
        runner = lambda command, prompt: calls.append((command, prompt)) or self.proposal()
        low = brainiac.process_board_event(self.state, self.event_export(self.incident("low", "2026-01-01T00:00:00Z")), runner)
        normal = brainiac.process_board_event(self.state, self.event_export(self.incident("normal", "2026-01-02T00:00:00Z", summary="separate incident")), runner)
        weekly = {"schema": brainiac.EVIDENCE_SCHEMA, "evidence_revision": "r1", "synthesis_window": "2026-W01", "observed_at": "2026-01-05T00:00:00Z"}
        first_weekly = brainiac.process_weekly_board_evidence(self.state, weekly, runner)
        unchanged_weekly = brainiac.process_weekly_board_evidence(self.state, weekly, runner)
        self.assertFalse(low["model_invoked"])
        self.assertFalse(normal["model_invoked"])
        self.assertTrue(first_weekly["model_invoked"])
        self.assertFalse(unchanged_weekly["model_invoked"])
        self.assertEqual(len(calls), 1)

    def test_bridge_high_event_invokes_exact_isolated_command_once_and_routes_receipt(self):
        calls = []
        runner = lambda command, prompt: calls.append((command, json.loads(prompt))) or self.proposal()
        export = self.event_export(self.incident("high-bridge", "2026-01-01T00:00:00Z", "high"))
        first = brainiac.process_board_event(self.state, export, runner)
        duplicate = brainiac.process_board_event(self.state, export, runner)
        self.assertTrue(first["model_invoked"])
        self.assertEqual(first["outcome"], "completed")
        self.assertEqual(first["route"], "architect_consideration")
        self.assertFalse(duplicate["model_invoked"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], brainiac.BRAINIAC_COMMAND)
        self.assertEqual(calls[0][0][1], "-p")
        self.assertEqual(calls[0][0][2], "foundry-brainiac")
        self.assertIn("openai-codex", calls[0][0])
        self.assertIn("gpt-6-astra", calls[0][0])
        self.assertEqual(calls[0][0][-2:], ("--toolsets", "bot_room"))
        self.assertNotIn("kanban", calls[0][0])
        with brainiac.connect(self.state) as db:
            route, proposal = db.execute("SELECT route, proposal_json FROM architect_outbox").fetchone()
        self.assertEqual(route, "architect_consideration")
        self.assertEqual(json.loads(proposal)["proposal"], "Bound retries.")

    def test_bridge_rejects_sensitive_or_unsupported_export_before_persistence_or_runner(self):
        calls = []
        runner = lambda command, prompt: calls.append((command, prompt)) or self.proposal()
        bad = self.event_export(self.incident("bad-export", "2026-01-01T00:00:00Z", "high"))
        bad["credentials"] = "never"
        with self.assertRaisesRegex(brainiac.BrainiacInputError, "sensitive incident field is prohibited"):
            brainiac.process_board_event(self.state, bad, runner)
        self.assertFalse(self.state.exists())
        self.assertEqual(calls, [])
        unsupported = self.event_export(self.incident("unsupported", "2026-01-01T00:00:00Z", "high"))
        unsupported["unapproved"] = "field"
        with self.assertRaisesRegex(brainiac.BrainiacInputError, "unsupported board evidence fields"):
            brainiac.process_board_event(self.state, unsupported, runner)
        self.assertEqual(calls, [])

    def test_failed_execution_is_terminal_and_never_retries(self):
        calls = []
        runner = lambda command, prompt: calls.append((command, prompt)) or "not-json"
        result = brainiac.execute_qualified(self.state, kind="event", invocation_key_value="fixed", evidence={"event_id": "one"}, observed_at="2026-01-01T00:00:00Z", runner=runner)
        retry = brainiac.execute_qualified(self.state, kind="event", invocation_key_value="fixed", evidence={"event_id": "one"}, observed_at="2026-01-01T00:00:00Z", runner=runner)
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(retry["decision"], "execution_duplicate_noop")
        self.assertEqual(len(calls), 1)

    def test_sensitive_proposal_is_not_routed_or_persisted_as_a_receipt(self):
        sensitive = json.dumps({"proposal": "Bound retries.", "invariant": "One invocation per key.", "regression_test": "Replay.", "metric": "Repeat incidents.", "accessToken": "never-store"})
        result = brainiac.execute_qualified(self.state, kind="event", invocation_key_value="sensitive", evidence={"event_id": "one"}, observed_at="2026-01-01T00:00:00Z", runner=lambda command, prompt: sensitive)
        self.assertEqual(result["outcome"], "failed")
        with brainiac.connect(self.state) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM architect_outbox").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
