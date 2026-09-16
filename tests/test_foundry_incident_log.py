import argparse
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "profiles/foundry-watchdog/scripts/foundry_incident_log.py"
spec = importlib.util.spec_from_file_location("foundry_incident_log", SCRIPT)
assert spec and spec.loader
incident_log = importlib.util.module_from_spec(spec)
spec.loader.exec_module(incident_log)


class FoundryIncidentLogTests(unittest.TestCase):
    def args(self, **overrides):
        values = {
            "occurrence_key": "soft-nudge:contract-1:1:t_terminal:t_blocked",
            "source": "watchdog",
            "severity": "normal",
            "category": "lifecycle_routing",
            "summary": "A terminal milestone had no live successor.",
            "trigger_card_id": "t_terminal",
            "contract_id": "contract-1",
            "contract_revision": "1",
            "affected_role": "Integration Auditor",
            "action": "soft_nudge",
            "replacement_card_id": "t_reconcile",
            "evidence_revision": "board-event-42",
            "evidence_json": json.dumps({"terminal_card_id": "t_terminal", "successor_card_id": "t_blocked"}),
            "occurred_at": "2026-09-16T17:00:00Z",
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_record_has_deterministic_id_and_allowlisted_brainiac_shape(self):
        incident = incident_log.build_incident(self.args())
        self.assertEqual(incident["incident_id"], incident_log.stable_id(incident["occurrence_key"]))
        export = incident_log.row_to_evidence({
            "incident_id": incident["incident_id"], "occurred_at": incident["occurred_at"],
            "severity": incident["severity"], "detection_source": incident["detection_source"],
            "category": incident["category"], "summary": incident["summary"],
            "evidence_revision": incident["evidence_revision"],
        })
        self.assertEqual(set(export), {"schema", "incident"})
        self.assertEqual(set(export["incident"]), {"event_id", "occurred_at", "severity", "source", "category", "summary", "evidence_revision"})
        self.assertEqual(export["schema"], "foundry-watchdog-evidence-v1")

    def test_sensitive_evidence_is_refused_before_database_access(self):
        with self.assertRaisesRegex(incident_log.IncidentLogError, "sensitive field"):
            incident_log.build_incident(self.args(evidence_json=json.dumps({"accessToken": "never-store"})))

    def test_incident_log_schema_preserves_evidence_and_processing_receipts(self):
        migration = (ROOT / "migrations/20260916_foundry_incident_log.sql").read_text(encoding="utf-8")
        for token in ("CREATE TABLE IF NOT EXISTS foundry_incident_log", "UNIQUE KEY foundry_incident_log_occurrence_key", "evidence_json", "brainiac_state", "brainiac_receipt_json"):
            self.assertIn(token, migration)

    def test_watchdog_and_brainiac_profiles_receive_distinct_scoped_paths(self):
        helper = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("foundry-watchdog/.secrets/foundry_incident_log.env", helper)
        self.assertIn("foundry-brainiac/.secrets/foundry_incident_log.env", helper)
        self.assertIn("bridge_pending", helper)
        self.assertIn("brainiac_learning.py", helper)


if __name__ == "__main__":
    unittest.main()
