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

    def test_persistent_state_is_ignored_and_profile_remains_inactive(self):
        self.assertIn("*.sqlite", GITIGNORE.read_text(encoding="utf-8"))
        config = BRAINIAC_CONFIG.read_text(encoding="utf-8")
        self.assertIn("enabled: []", config)
        self.assertIn("dispatch_in_gateway: false", config)
        self.assertIn("cron_mode: deny", config)


if __name__ == "__main__":
    unittest.main()
