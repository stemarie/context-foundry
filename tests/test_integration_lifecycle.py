import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-auditor/adapters/integration_lifecycle.py"
FIXTURE_PATH = ROOT / "tests/fixtures/integration_lifecycle/mentorship_sibling_candidates.json"
spec = importlib.util.spec_from_file_location("integration_lifecycle", ADAPTER_PATH)
assert spec and spec.loader
integration_lifecycle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(integration_lifecycle)


BASE = "a" * 40
FOUNDATION = "b" * 40
PERMISSIONS = "c" * 40
MERGED = "d" * 40


def record(**overrides):
    value = {
        "source_change": True,
        "disposition": "merge_required",
        "repository": "stemarie/example",
        "default_branch": "main",
        "base_sha": BASE,
        "candidate_sha": FOUNDATION,
        "candidate_branch": "phase-0/foundation",
        "candidate_audit_verdict": "PASS",
        "candidate_audit_sha": FOUNDATION,
        "candidate_audit_disclaimer": integration_lifecycle.CANDIDATE_AUDIT_DISCLAIMER,
        "disposition_owner": "architect",
        "next_decision": "Open and independently audit the integration pull request.",
        "candidate_only_reason": None,
        "approval_request": None,
        "approval_owner": None,
        "pull_request_url": None,
        "pull_request_head_sha": None,
        "pull_request_merged": False,
        "merged_sha": None,
        "default_branch_head_sha": BASE,
        "default_branch_contains_merged": False,
        "post_merge_checks": [],
        "tracker_state": "open",
    }
    value.update(overrides)
    return value


class IntegrationLifecycleTests(unittest.TestCase):
    def test_merge_required_candidate_pass_without_pr_is_integration_pending(self):
        result = integration_lifecycle.evaluate(record())
        self.assertEqual(result["state"], "integration_pending")
        self.assertFalse(result["milestone_closable"])
        self.assertIn("pull_request_url", result["missing"])

    def test_candidate_only_requires_reason_owner_and_concrete_next_decision(self):
        invalid = record(
            disposition="candidate_only",
            candidate_only_reason=None,
            disposition_owner=None,
            next_decision=None,
        )
        result = integration_lifecycle.evaluate(invalid)
        self.assertEqual(result["state"], "invalid")
        self.assertCountEqual(
            result["errors"],
            ["candidate_only_reason", "disposition_owner", "next_decision"],
        )

    def test_candidate_only_can_close_only_a_candidate_record_not_a_milestone(self):
        result = integration_lifecycle.evaluate(
            record(
                disposition="candidate_only",
                candidate_only_reason="Awaiting explicit product-scope approval.",
                next_decision="Karell decides whether to authorize a merge-required integration tranche by 2026-10-01.",
            )
        )
        self.assertEqual(result["state"], "candidate_verified")
        self.assertTrue(result["candidate_record_closable"])
        self.assertFalse(result["milestone_closable"])
        self.assertNotIn("closable", result)

    def test_normalized_merge_evidence_is_advisory_until_authenticated_by_closure(self):
        result = integration_lifecycle.evaluate(
            record(
                pull_request_url="https://github.com/stemarie/example/pull/7",
                pull_request_head_sha=FOUNDATION,
                pull_request_merged=True,
                merged_sha=MERGED,
                default_branch_head_sha=MERGED,
                default_branch_contains_merged=True,
                post_merge_checks=[{"command": "go test ./...", "outcome": "PASS", "revision": MERGED}],
            )
        )
        self.assertEqual(result["state"], "integration_evidence_declared")
        self.assertFalse(result["milestone_closable"])
        self.assertNotIn("closable", result)

    def test_merge_required_merged_pr_without_main_readback_is_rejected(self):
        result = integration_lifecycle.evaluate(
            record(
                pull_request_url="https://github.com/stemarie/example/pull/7",
                pull_request_head_sha=FOUNDATION,
                pull_request_merged=True,
                merged_sha=MERGED,
            )
        )
        self.assertEqual(result["state"], "integration_pending")
        self.assertFalse(result["milestone_closable"])
        self.assertIn("default_branch_readback", result["missing"])
        self.assertIn("post_merge_checks", result["missing"])

    def test_merge_required_normalized_evidence_does_not_certify_authenticated_integration(self):
        result = integration_lifecycle.evaluate(
            record(
                pull_request_url="https://github.com/stemarie/example/pull/7",
                pull_request_head_sha=FOUNDATION,
                pull_request_merged=True,
                merged_sha=MERGED,
                default_branch_head_sha=MERGED,
                default_branch_contains_merged=True,
                post_merge_checks=[{"command": "go test ./...", "outcome": "PASS", "revision": MERGED}],
            )
        )
        self.assertEqual(result["state"], "integration_evidence_declared")
        self.assertFalse(result["candidate_record_closable"])
        self.assertFalse(result["milestone_closable"])

    def test_merge_required_rejects_failed_or_wrong_revision_post_merge_check(self):
        for checks in (
            [{"command": "go test ./...", "outcome": "FAIL", "revision": MERGED}],
            [{"command": "go test ./...", "outcome": "PASS", "revision": FOUNDATION}],
        ):
            result = integration_lifecycle.evaluate(
                record(
                    pull_request_url="https://github.com/stemarie/example/pull/7",
                    pull_request_head_sha=FOUNDATION,
                    pull_request_merged=True,
                    merged_sha=MERGED,
                    default_branch_head_sha=MERGED,
                    default_branch_contains_merged=True,
                    post_merge_checks=checks,
                )
            )
            self.assertEqual(result["state"], "integration_pending")
            self.assertIn("post_merge_checks", result["missing"])

    def test_milestone_receipt_rejects_boolean_pr_number(self):
        receipt = {
            "schema_version": "closure_integration_receipt_v1",
            "outcome": "DELIVERED",
            "disposition": "merge_required",
            "closure_scope": "product_milestone",
            "repository": "stemarie/example",
            "origin": "https://github.com/stemarie/example.git",
            "api_target": "https://api.github.com/repos/stemarie/example",
            "issue": 7,
            "branch": "main",
            "candidate_sha": FOUNDATION,
            "candidate_auditor_task_id": "t_1234abcd",
            "integration_pr_number": True,
            "integration_head_sha": PERMISSIONS,
            "integration_auditor_task_id": "t_abcd1234",
            "merged_sha": MERGED,
            "default_branch_readback_sha": MERGED,
            "post_merge_checks": [{"command": "go test ./...", "outcome": "PASS", "revision": MERGED}],
        }
        with self.assertRaises(ValueError):
            integration_lifecycle.validate_milestone_merge_receipt(receipt)

    def test_human_approval_requires_merge_ready_pr_and_named_approver(self):
        result = integration_lifecycle.evaluate(
            record(
                disposition="human_approval_required",
                pull_request_url="https://github.com/stemarie/example/pull/7",
                pull_request_head_sha=FOUNDATION,
                approval_request="Approve non-force merge of PR #7 to main.",
                approval_owner=None,
            )
        )
        self.assertEqual(result["state"], "invalid")
        self.assertIn("approval_owner", result["errors"])

    def test_closed_tracker_with_unintegrated_merge_required_candidate_is_invalid(self):
        result = integration_lifecycle.evaluate(record(tracker_state="closed"))
        self.assertEqual(result["state"], "invalid")
        self.assertIn("closed_tracker_without_integration", result["errors"])

    def test_cli_evaluates_the_mentorship_fixture_as_integration_pending(self):
        result = subprocess.run(
            [sys.executable, ADAPTER_PATH, "--cohort", FIXTURE_PATH],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["state"], "integration_pending")
        self.assertEqual(
            payload["required_next_action"],
            "Create one combined integration pull request and independently audit its exact head SHA.",
        )

    def test_mentorship_sibling_candidates_require_combined_integration_and_audit(self):
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        result = integration_lifecycle.evaluate_cohort(fixture)
        self.assertEqual(result["state"], "integration_pending")
        self.assertEqual(result["required_next_action"], "Create one combined integration pull request and independently audit its exact head SHA.")
        self.assertTrue(result["overlapping_paths"])
        self.assertEqual(result["candidates"], [FOUNDATION, PERMISSIONS])


if __name__ == "__main__":
    unittest.main()
