import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-auditor/adapters/closure_auditor.py"
SCHEMA_PATH = ROOT / "profiles/foundry-auditor/schemas/closure_auditor_packet.schema.json"
LIVE_ENVELOPE_FIXTURE = ROOT / "tests/closure_auditor_live_envelope_fixture.json"
spec = importlib.util.spec_from_file_location("closure_auditor", ADAPTER_PATH)
assert spec and spec.loader
closure_auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure_auditor)

CANDIDATE_SHA = "f54e7812e5fb5e06efd2c08eea28e66b1c9b25dc"
INTEGRATION_HEAD_SHA = "a" * 40
MERGE_SHA = "b" * 40
READBACK_SHA = "c" * 40
CURRENT_MAIN_SHA = "d" * 40
WORKER_ID = "t_3fbcbdcd"
OTHER_PARENT_ID = "t_ba5eba11"
CANDIDATE_ID = "t_484e8099"
INTEGRATION_AUDITOR_ID = "t_a11d0001"
DELIVERY_ID = "t_d3110001"
CLOSURE_ID = "t_c1050001"
MARKER = "FOUNDRY-WATCHDOG-INITIAL-CONTRACT-V1"
PR_NUMBER = 77


def scope(issue=19, marker=MARKER, sha=CANDIDATE_SHA):
    return {
        "repository": closure_auditor.REPOSITORY,
        "origin": closure_auditor.ORIGIN,
        "api_target": closure_auditor.API_TARGET,
        "issue": issue,
        "branch": closure_auditor.BRANCH,
        "candidate_sha": sha,
        "issue_marker": marker,
        "receipt_marker": closure_auditor.RECEIPT_MARKER,
    }


def card_body(issue=19, marker=MARKER, delivery_id=DELIVERY_ID):
    return "\n".join((
        f"Canonical external contract: https://github.com/stemarie/context-foundry/issues/{issue}",
        f"Contract ID/revision: Issue #{issue} / {marker}",
        "Role: Closure Auditor",
        "Dependency: completed direct Delivery parent",
        f"Receipt pointer: Delivery `{delivery_id}`",
    ))


def captured_live_envelope():
    return json.loads(LIVE_ENVELOPE_FIXTURE.read_text(encoding="utf-8"))["envelope"]


def envelope(task, *, parents, metadata=None):
    result = captured_live_envelope()
    task = dict(task)
    task.pop("parents", None)
    task.pop("metadata", None)
    result["task"] = task
    result["parents"] = parents
    result["runs"][0]["metadata"] = metadata
    return result


def candidate_metadata(packet_scope):
    return {"closure_candidate_audit_v1": {
        "schema_version": "closure_candidate_audit_v1",
        "verdict": "PASS",
        **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")},
    }}


def integration_audit_metadata(packet_scope):
    return {"closure_integration_audit_v1": {
        "schema_version": "closure_integration_audit_v1",
        "verdict": "PASS",
        **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")},
        "integration_pr_number": PR_NUMBER,
        "integration_head_sha": INTEGRATION_HEAD_SHA,
    }}


def delivery_metadata(packet_scope, *, disposition="merge_required", checks=None):
    return {"closure_integration_receipt_v1": {
        "schema_version": "closure_integration_receipt_v1",
        "outcome": "DELIVERED",
        "disposition": disposition,
        "closure_scope": "product_milestone",
        **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")},
        "candidate_auditor_task_id": CANDIDATE_ID,
        "integration_pr_number": PR_NUMBER,
        "integration_head_sha": INTEGRATION_HEAD_SHA,
        "integration_auditor_task_id": INTEGRATION_AUDITOR_ID,
        "merged_sha": MERGE_SHA,
        "default_branch_readback_sha": READBACK_SHA,
        "post_merge_checks": checks if checks is not None else [{
            "command": "python3 -m unittest discover -s tests -v",
            "outcome": "PASS",
            "revision": READBACK_SHA,
        }],
    }}


def cards(*, issue=19, marker=MARKER, sha=CANDIDATE_SHA, legacy=False, disposition="merge_required", checks=None):
    packet_scope = scope(issue, marker, sha)
    worker = envelope({"id": WORKER_ID, "assignee": "foundry-worker", "status": "done", "title": "Worker: candidate"}, parents=[])
    other = envelope({"id": OTHER_PARENT_ID, "assignee": "foundry-architect", "status": "done", "title": "Architect: unrelated"}, parents=[])
    candidate = envelope({"id": CANDIDATE_ID, "assignee": "foundry-auditor", "status": "done", "title": "Candidate Auditor: candidate"}, parents=[WORKER_ID], metadata=candidate_metadata(packet_scope))
    if legacy:
        delivery = envelope({"id": DELIVERY_ID, "status": "done", "title": "Delivery: legacy"}, parents=[CANDIDATE_ID], metadata={"closure_delivery_receipt_v1": {
            "schema_version": "closure_delivery_receipt_v1", "outcome": "DELIVERED", "delivery_mode": "non-force-direct-main",
            **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")},
            "delivered_sha": sha, "candidate_auditor_task_id": CANDIDATE_ID,
        }})
        lookup = {WORKER_ID: worker, OTHER_PARENT_ID: other, CANDIDATE_ID: candidate, DELIVERY_ID: delivery}
    else:
        integration_auditor = envelope({"id": INTEGRATION_AUDITOR_ID, "assignee": "foundry-auditor", "status": "done", "title": "Integration Auditor: candidate"}, parents=[CANDIDATE_ID], metadata=integration_audit_metadata(packet_scope))
        delivery = envelope({"id": DELIVERY_ID, "status": "done", "title": "Delivery: integration"}, parents=[INTEGRATION_AUDITOR_ID], metadata=delivery_metadata(packet_scope, disposition=disposition, checks=checks))
        lookup = {WORKER_ID: worker, OTHER_PARENT_ID: other, CANDIDATE_ID: candidate, INTEGRATION_AUDITOR_ID: integration_auditor, DELIVERY_ID: delivery}
    closure = {"id": CLOSURE_ID, "assignee": "foundry-auditor", "status": "running", "title": "Closure Auditor: integration", "body": card_body(issue, marker), "parents": [DELIVERY_ID], "workspace_path": "/tmp/example"}
    return lookup, closure


class Api:
    def __init__(self, packet_scope, *, merged=True, pr_head=INTEGRATION_HEAD_SHA, pr_base="main", pr_repo=None, merge_sha=MERGE_SHA, compare_status="ahead"):
        self.scope = packet_scope
        self.merged = merged
        self.pr_head = pr_head
        self.pr_base = pr_base
        self.pr_repo = pr_repo or packet_scope["repository"]
        self.merge_sha = merge_sha
        self.compare_status = compare_status
        self.closed = False
        self.comments = []
        self.writes = []

    def __call__(self, method, url, payload):
        if method in {"POST", "PATCH"}:
            self.writes.append(method)
        if url == self.scope["api_target"]:
            return {"full_name": self.scope["repository"], "default_branch": self.scope["branch"]}
        if url.endswith(f"/pulls/{PR_NUMBER}"):
            return {"number": PR_NUMBER, "merged": self.merged, "merge_commit_sha": self.merge_sha, "base": {"ref": self.pr_base, "repo": {"full_name": self.pr_repo}}, "head": {"sha": self.pr_head}}
        if url.endswith("/git/ref/heads/main"):
            return {"object": {"sha": CURRENT_MAIN_SHA}}
        if "/compare/" in url:
            return {"status": self.compare_status}
        if url.endswith("/comments?per_page=100"):
            if method == "POST":
                self.comments.append(payload)
            return self.comments
        if url.endswith(f"/issues/{self.scope['issue']}"):
            if method == "PATCH":
                self.closed = True
            return {"body": f"<!-- {self.scope['issue_marker']} -->", "state": "closed" if self.closed else "open", "closed_at": "now" if self.closed else None}
        raise AssertionError(url)


class ClosureAdapterTests(unittest.TestCase):
    def execute(self, lookup, closure, api):
        with patch.object(closure_auditor, "validate_workspace"):
            return closure_auditor.execute(closure, lookup.__getitem__, api)

    def reject_without_writes(self, lookup, closure, api):
        with self.assertRaises(closure_auditor.ClosureError):
            self.execute(lookup, closure, api)
        self.assertEqual(api.writes, [])

    def test_retired_pr_adapter_cannot_close_even_with_complete_legacy_evidence(self):
        lookup, closure = cards()
        api = Api(scope())
        self.reject_without_writes(lookup, closure, api)

    def test_scope_is_dynamic_and_captured_runtime_envelope_is_normalized(self):
        lookup, closure = cards(issue=42, marker="FOUNDRY-ALTERNATE-CONTRACT-V1", sha="e" * 40)
        derived = closure_auditor.derive_scope(closure, lookup.__getitem__)
        self.assertEqual(derived["issue"], 42)
        self.assertEqual(derived["candidate_sha"], "e" * 40)
        self.assertEqual(derived["integration_pr_number"], PR_NUMBER)
        captured = captured_live_envelope()
        self.assertIn("parents", captured)
        self.assertIn("metadata", captured["runs"][0])
        self.assertNotIn("parents", captured["task"])
        self.assertNotIn("metadata", captured["task"])

    def test_legacy_candidate_delivery_and_non_merge_dispositions_cannot_close(self):
        lookup, closure = cards(legacy=True)
        self.reject_without_writes(lookup, closure, Api(scope()))
        for disposition in ("candidate_only", "human_approval_required", "unknown"):
            lookup, closure = cards(disposition=disposition)
            self.reject_without_writes(lookup, closure, Api(scope()))

    def test_pr_and_remote_evidence_fail_closed_before_writes(self):
        cases = (
            Api(scope(), merged=False),
            Api(scope(), pr_head="e" * 40),
            Api(scope(), pr_base="other"),
            Api(scope(), pr_repo="other/repo"),
            Api(scope(), merge_sha="e" * 40),
            Api(scope(), compare_status="diverged"),
        )
        for api in cases:
            lookup, closure = cards()
            self.reject_without_writes(lookup, closure, api)

    def test_post_merge_checks_and_chain_binding_fail_closed_before_writes(self):
        for checks in (
            [],
            [{"command": "go test ./...", "outcome": "FAIL", "revision": READBACK_SHA}],
            [{"command": "go test ./...", "outcome": "PASS", "revision": MERGE_SHA}],
        ):
            lookup, closure = cards(checks=checks)
            self.reject_without_writes(lookup, closure, Api(scope()))
        for mutate in (
            lambda lookup, closure: lookup[DELIVERY_ID]["runs"][0]["metadata"]["closure_integration_receipt_v1"].update({"candidate_auditor_task_id": CLOSURE_ID}),
            lambda lookup, closure: lookup[DELIVERY_ID]["runs"][0]["metadata"]["closure_integration_receipt_v1"].update({"integration_auditor_task_id": CLOSURE_ID}),
            lambda lookup, closure: lookup[INTEGRATION_AUDITOR_ID]["runs"][0]["metadata"]["closure_integration_audit_v1"].update({"integration_head_sha": "e" * 40}),
            lambda lookup, closure: lookup[INTEGRATION_AUDITOR_ID]["runs"][0]["metadata"]["closure_integration_audit_v1"].update({"candidate_sha": "e" * 40}),
            lambda lookup, closure: lookup[DELIVERY_ID].update({"parents": [CANDIDATE_ID]}),
        ):
            lookup, closure = cards()
            mutate(lookup, closure)
            self.reject_without_writes(lookup, closure, Api(scope()))

    def test_receipt_field_tampering_fails_closed_before_writes(self):
        mutations = (
            (CANDIDATE_ID, "closure_candidate_audit_v1", "repository", "other/repo"),
            (CANDIDATE_ID, "closure_candidate_audit_v1", "candidate_sha", "e" * 40),
            (INTEGRATION_AUDITOR_ID, "closure_integration_audit_v1", "issue", 99),
            (INTEGRATION_AUDITOR_ID, "closure_integration_audit_v1", "candidate_sha", "e" * 40),
            (DELIVERY_ID, "closure_integration_receipt_v1", "origin", "https://github.com/other/repo.git"),
            (DELIVERY_ID, "closure_integration_receipt_v1", "candidate_sha", "e" * 40),
            (DELIVERY_ID, "closure_integration_receipt_v1", "integration_pr_number", True),
        )
        for task_id, receipt_key, field, value in mutations:
            lookup, closure = cards()
            lookup[task_id]["runs"][0]["metadata"][receipt_key][field] = value
            self.reject_without_writes(lookup, closure, Api(scope()))
        for task_id, receipt_key, field in (
            (CANDIDATE_ID, "closure_candidate_audit_v1", "verdict"),
            (INTEGRATION_AUDITOR_ID, "closure_integration_audit_v1", "candidate_sha"),
            (DELIVERY_ID, "closure_integration_receipt_v1", "merged_sha"),
        ):
            lookup, closure = cards()
            del lookup[task_id]["runs"][0]["metadata"][receipt_key][field]
            self.reject_without_writes(lookup, closure, Api(scope()))

    def test_card_reference_and_workspace_identity_fail_closed(self):
        for mutate in (
            lambda lookup, closure: closure.update({"body": closure["body"] + "\nPayload: arbitrary"}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace("Issue #19", "Issue #20")}),
            lambda lookup, closure: closure.update({"parents": [CANDIDATE_ID]}),
        ):
            lookup, closure = cards()
            mutate(lookup, closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)
        lookup, closure = cards()
        derived = closure_auditor.derive_scope(closure, lookup.__getitem__)
        with patch.object(closure_auditor, "git_output", side_effect=[derived["origin"], "wrong"]):
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.validate_workspace(closure, derived)

    def test_contract_references_and_issue_marker_fail_closed_before_writes(self):
        for mutate in (
            lambda closure: closure.update({"body": closure["body"] + "\nPayload: arbitrary"}),
            lambda closure: closure.update({"body": closure["body"].replace("context-foundry", "other-repo", 1)}),
            lambda closure: closure.update({"body": closure["body"].replace("Issue #19", "Issue #20")}),
            lambda closure: closure.update({"body": card_body(delivery_id="t_d3110002")}),
        ):
            lookup, closure = cards()
            mutate(closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

        lookup, closure = cards()
        api = Api(scope())

        def missing_marker(method, url, payload):
            if url.endswith("/issues/19"):
                return {"body": "missing marker", "state": "open", "closed_at": None}
            return api(method, url, payload)

        with self.assertRaises(closure_auditor.ClosureError):
            self.execute(lookup, closure, missing_marker)
        self.assertEqual(api.writes, [])

    def test_conflicting_or_duplicate_closure_receipts_are_write_free(self):
        lookup, closure = cards()
        api = Api(scope())
        api.comments.append({"body": "<!-- FOUNDRY_CLOSURE_RECEIPT_V1 -->\nwrong"})
        self.reject_without_writes(lookup, closure, api)
        lookup, closure = cards()
        api = Api(scope())
        expected = closure_auditor.receipt_body(CLOSURE_ID, closure_auditor.derive_scope(closure, lookup.__getitem__))
        api.comments.extend(({"body": expected}, {"body": expected}))
        self.reject_without_writes(lookup, closure, api)

    def test_closed_issue_with_one_exact_receipt_is_idempotent_and_write_free(self):
        lookup, closure = cards()
        api = Api(scope())
        expected = closure_auditor.receipt_body(CLOSURE_ID, closure_auditor.derive_scope(closure, lookup.__getitem__))
        api.closed = True
        api.comments.append({"body": expected})
        self.reject_without_writes(lookup, closure, api)

    def test_malformed_completed_evidence_and_remote_identity_are_write_free(self):
        lookup, closure = cards()
        lookup[CANDIDATE_ID]["runs"][0]["metadata"] = None
        with self.assertRaises(closure_auditor.ClosureError):
            closure_auditor.derive_scope(closure, lookup.__getitem__)

        lookup, closure = cards()
        api = Api(scope())

        def wrong_repository(method, url, payload):
            if url == scope()["api_target"]:
                return {"full_name": "other/repo", "default_branch": "main"}
            return api(method, url, payload)

        with self.assertRaises(closure_auditor.ClosureError):
            self.execute(lookup, closure, wrong_repository)
        self.assertEqual(api.writes, [])

    def test_schema_is_strict_and_binds_integration_evidence(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertTrue(schema["additionalProperties"] is False)
        self.assertEqual(set(schema["required"]), {"closure_card", "candidate_auditor_receipt", "integration_auditor_receipt", "integration_receipt"})
        receipt = schema["properties"]["integration_receipt"]
        self.assertTrue(receipt["additionalProperties"] is False)
        self.assertEqual(receipt["properties"]["disposition"]["const"], "merge_required")
        self.assertEqual(receipt["properties"]["repository"]["const"], closure_auditor.REPOSITORY)
        self.assertEqual(receipt["properties"]["branch"]["const"], closure_auditor.BRANCH)


if __name__ == "__main__":
    unittest.main()
