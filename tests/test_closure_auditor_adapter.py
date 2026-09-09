import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-auditor/adapters/closure_auditor.py"
SCHEMA_PATH = ROOT / "profiles/foundry-auditor/schemas/closure_auditor_packet.schema.json"
spec = importlib.util.spec_from_file_location("closure_auditor", ADAPTER_PATH)
assert spec and spec.loader
closure_auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure_auditor)

SHA = closure_auditor.FIXTURE_CANDIDATE_SHA
CANDIDATE_ID = closure_auditor.FIXTURE_CANDIDATE_AUDITOR
DELIVERY_ID = "t_d3110001"
CLOSURE_ID = "t_c1050001"
SCOPE = {"repository": closure_auditor.REPOSITORY, "origin": closure_auditor.ORIGIN, "api_target": closure_auditor.API_TARGET, "issue": closure_auditor.ISSUE, "branch": closure_auditor.BRANCH, "candidate_sha": SHA, "receipt_marker": closure_auditor.RECEIPT_MARKER}


def card_body(delivery_id=DELIVERY_ID):
    return "\n".join((
        f"Canonical external contract: {closure_auditor.CONTRACT_URL}",
        f"Contract ID/revision: Issue #{closure_auditor.ISSUE} / {closure_auditor.ISSUE_MARKER}",
        "Role: Closure Auditor",
        "Dependency: completed direct Delivery parent",
        f"Receipt pointer: Delivery `{delivery_id}`",
    ))


def cards():
    candidate = {"id": CANDIDATE_ID, "assignee": "foundry-auditor", "status": "done", "title": "Candidate Auditor: Watchdog gate", "metadata": {"closure_candidate_audit_v1": {"schema_version": "closure_candidate_audit_v1", "verdict": "PASS", **{key: SCOPE[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}}}}
    delivery = {"id": DELIVERY_ID, "status": "done", "title": "Delivery: Watchdog", "parents": [candidate["id"]], "metadata": {"closure_delivery_receipt_v1": {"schema_version": "closure_delivery_receipt_v1", "outcome": "DELIVERED", "delivery_mode": "non-force-direct-main", **{key: SCOPE[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}, "delivered_sha": SHA, "candidate_auditor_task_id": candidate["id"]}}}
    closure = {"id": CLOSURE_ID, "assignee": "foundry-auditor", "status": "running", "title": "Closure Auditor: Watchdog", "body": card_body(), "parents": [delivery["id"]], "workspace_path": "/tmp/example"}
    return {candidate["id"]: {"task": candidate}, delivery["id"]: {"task": delivery}}, closure


class Api:
    def __init__(self):
        self.closed, self.comments, self.writes = False, [], []

    def __call__(self, method, url, payload):
        if method in {"POST", "PATCH"}:
            self.writes.append(method)
        if url == SCOPE["api_target"]:
            return {"full_name": SCOPE["repository"], "default_branch": "main"}
        if url.endswith("/git/ref/heads/main"):
            return {"object": {"sha": SHA}}
        if url.endswith("/comments?per_page=100"):
            if method == "POST": self.comments.append(payload)
            return self.comments
        if url.endswith("/issues/19"):
            if method == "PATCH": self.closed = True
            return {"body": closure_auditor.ISSUE_MARKER, "state": "closed" if self.closed else "open", "closed_at": "now" if self.closed else None}
        raise AssertionError(url)


class ClosureAdapterTests(unittest.TestCase):
    def test_issue_19_fixture_closes_then_idempotently_reads_back(self):
        lookup, closure = cards()
        api = Api()
        with patch.object(closure_auditor, "validate_workspace"):
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "closed")
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "idempotent-readback")
        self.assertEqual(api.writes, ["POST", "PATCH"])

    def test_card_only_contract_reference_rejects_target_selection_and_bad_receipt_pointer(self):
        for mutate in (
            lambda lookup, closure: closure.update({"body": closure["body"] + "\nPayload: arbitrary"}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace(closure_auditor.CONTRACT_URL, "https://github.com/other/repo/issues/19")}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace("Issue #19", "Issue #20")}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace(closure_auditor.ISSUE_MARKER, "wrong")}),
            lambda lookup, closure: closure.update({"body": card_body("t_d3110002")}),
            lambda lookup, closure: closure.update({"assignee": "foundry-worker"}),
            lambda lookup, closure: closure.update({"title": "Worker: close"}),
        ):
            lookup, closure = cards()
            mutate(lookup, closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

    def test_rejects_identity_parent_and_receipt_mismatches(self):
        mutations = (
            lambda lookup, closure: closure.update({"id": DELIVERY_ID}),
            lambda lookup, closure: closure.update({"parents": [CANDIDATE_ID]}),
            lambda lookup, closure: lookup[DELIVERY_ID]["task"].update({"parents": [DELIVERY_ID]}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"id": "t_cand0001"}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"assignee": "foundry-worker"}),
            lambda lookup, closure: lookup[DELIVERY_ID]["task"]["metadata"]["closure_delivery_receipt_v1"].update({"candidate_auditor_task_id": "t_c1050001"}),
            lambda lookup, closure: lookup[DELIVERY_ID]["task"].update({"status": "running"}),
        )
        for mutate in mutations:
            lookup, closure = cards()
            mutate(lookup, closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

    def test_rejects_every_repository_issue_sha_and_delivery_field_mismatch(self):
        for task_id, receipt_key, fields in (
            (CANDIDATE_ID, "closure_candidate_audit_v1", ("repository", "origin", "api_target", "issue", "branch", "candidate_sha", "schema_version", "verdict")),
            (DELIVERY_ID, "closure_delivery_receipt_v1", ("repository", "origin", "api_target", "issue", "branch", "candidate_sha", "delivered_sha", "candidate_auditor_task_id", "schema_version", "outcome", "delivery_mode")),
        ):
            for field in fields:
                lookup, closure = cards()
                receipt = lookup[task_id]["task"]["metadata"][receipt_key]
                receipt[field] = 99 if field == "issue" else "wrong"
                with self.assertRaises(closure_auditor.ClosureError, msg=f"changed {field}"):
                    closure_auditor.derive_scope(closure, lookup.__getitem__)
                lookup, closure = cards()
                lookup[task_id]["task"]["metadata"][receipt_key].pop(field)
                with self.assertRaises(closure_auditor.ClosureError, msg=f"missing {field}"):
                    closure_auditor.derive_scope(closure, lookup.__getitem__)

    def test_rejects_workspace_remote_api_and_issue_marker_bypasses_before_writes(self):
        lookup, closure = cards()
        with patch.object(closure_auditor, "git_output", side_effect=[SCOPE["origin"], "b" * 40]):
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.validate_workspace(closure, closure_auditor.derive_scope(closure, lookup.__getitem__))
        for response in (
            lambda method, url, payload: {"full_name": "other/repo", "default_branch": "main"} if url == SCOPE["api_target"] else Api()(method, url, payload),
            lambda method, url, payload: {"object": {"sha": "b" * 40}} if url.endswith("/git/ref/heads/main") else Api()(method, url, payload),
            lambda method, url, payload: {"body": "missing marker", "state": "open", "closed_at": None} if url.endswith("/issues/19") else Api()(method, url, payload),
        ):
            lookup, closure = cards()
            with patch.object(closure_auditor, "validate_workspace"):
                with self.assertRaises(closure_auditor.ClosureError):
                    closure_auditor.execute(closure, lookup.__getitem__, response)

    def test_source_managed_schema_declares_only_canonical_fixture_and_is_valid_json(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["closure_card"]["properties"]["canonical_contract_url"]["const"], closure_auditor.CONTRACT_URL)
        self.assertEqual(schema["properties"]["delivery_receipt"]["properties"]["candidate_sha"]["const"], SHA)
        self.assertEqual(schema["properties"]["delivery_receipt"]["properties"]["candidate_auditor_task_id"]["const"], CANDIDATE_ID)


if __name__ == "__main__":
    unittest.main()
