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

SHA = "f54e7812e5fb5e06efd2c08eea28e66b1c9b25dc"
WORKER_ID = "t_3fbcbdcd"
OTHER_PARENT_ID = "t_ba5eba11"
CANDIDATE_ID = "t_484e8099"
DELIVERY_ID = "t_d3110001"
CLOSURE_ID = "t_c1050001"
MARKER = "FOUNDRY-WATCHDOG-INITIAL-CONTRACT-V1"


def scope(issue=19, marker=MARKER, sha=SHA):
    return {"repository": closure_auditor.REPOSITORY, "origin": closure_auditor.ORIGIN, "api_target": closure_auditor.API_TARGET, "issue": issue, "branch": closure_auditor.BRANCH, "candidate_sha": sha, "issue_marker": marker, "receipt_marker": closure_auditor.RECEIPT_MARKER}


def card_body(issue=19, marker=MARKER, delivery_id=DELIVERY_ID):
    return "\n".join((
        f"Canonical external contract: https://github.com/stemarie/context-foundry/issues/{issue}",
        f"Contract ID/revision: Issue #{issue} / {marker}",
        "Role: Closure Auditor",
        "Dependency: completed direct Delivery parent",
        f"Receipt pointer: Delivery `{delivery_id}`",
    ))


def cards(issue=19, marker=MARKER, sha=SHA):
    packet_scope = scope(issue, marker, sha)
    worker = {"id": WORKER_ID, "assignee": "foundry-worker", "status": "done", "title": "Worker: Watchdog candidate"}
    other_parent = {"id": OTHER_PARENT_ID, "assignee": "foundry-architect", "status": "done", "title": "Architect: unrelated packet"}
    candidate = {"id": CANDIDATE_ID, "assignee": "foundry-auditor", "status": "done", "title": "Candidate Auditor: Watchdog gate", "parents": [WORKER_ID], "metadata": {"closure_candidate_audit_v1": {"schema_version": "closure_candidate_audit_v1", "verdict": "PASS", **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}}}}
    delivery = {"id": DELIVERY_ID, "status": "done", "title": "Delivery: Watchdog", "parents": [CANDIDATE_ID], "metadata": {"closure_delivery_receipt_v1": {"schema_version": "closure_delivery_receipt_v1", "outcome": "DELIVERED", "delivery_mode": "non-force-direct-main", **{key: packet_scope[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}, "delivered_sha": sha, "candidate_auditor_task_id": CANDIDATE_ID}}}
    closure = {"id": CLOSURE_ID, "assignee": "foundry-auditor", "status": "running", "title": "Closure Auditor: Watchdog", "body": card_body(issue, marker), "parents": [DELIVERY_ID], "workspace_path": "/tmp/example"}
    return {WORKER_ID: {"task": worker}, OTHER_PARENT_ID: {"task": other_parent}, CANDIDATE_ID: {"task": candidate}, DELIVERY_ID: {"task": delivery}}, closure


class Api:
    def __init__(self, packet_scope):
        self.scope, self.closed, self.comments, self.writes = packet_scope, False, [], []

    def __call__(self, method, url, payload):
        if method in {"POST", "PATCH"}:
            self.writes.append(method)
        if url == self.scope["api_target"]:
            return {"full_name": self.scope["repository"], "default_branch": self.scope["branch"]}
        if url.endswith("/git/ref/heads/main"):
            return {"object": {"sha": self.scope["candidate_sha"]}}
        if url.endswith("/comments?per_page=100"):
            if method == "POST": self.comments.append(payload)
            return self.comments
        if url.endswith(f"/issues/{self.scope['issue']}"):
            if method == "PATCH": self.closed = True
            return {"body": f"<!-- {self.scope['issue_marker']} -->", "state": "closed" if self.closed else "open", "closed_at": "now" if self.closed else None}
        raise AssertionError(url)


class ClosureAdapterTests(unittest.TestCase):
    def test_lawful_issue_19_fixture_closes_then_idempotently_reads_back(self):
        lookup, closure = cards()
        api = Api(scope())
        with patch.object(closure_auditor, "validate_workspace"):
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "closed")
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "idempotent-readback")
        self.assertEqual(api.writes, ["POST", "PATCH"])

    def test_scope_is_dynamically_derived_from_card_and_receipts(self):
        dynamic_marker = "FOUNDRY-ALTERNATE-CONTRACT-V1"
        dynamic_sha = "a" * 40
        lookup, closure = cards(issue=42, marker=dynamic_marker, sha=dynamic_sha)
        self.assertEqual(closure_auditor.derive_scope(closure, lookup.__getitem__), scope(42, dynamic_marker, dynamic_sha))

    def test_rejects_card_target_selection_and_contract_reference_mismatches(self):
        for mutate in (
            lambda lookup, closure: closure.update({"body": closure["body"] + "\nPayload: arbitrary"}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace("stemarie/context-foundry", "other/repo")}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace("Issue #19", "Issue #20")}),
            lambda lookup, closure: closure.update({"body": closure["body"].replace(MARKER, "wrong")}),
            lambda lookup, closure: closure.update({"body": card_body(delivery_id="t_d3110002")}),
            lambda lookup, closure: closure.update({"assignee": "foundry-worker"}),
            lambda lookup, closure: closure.update({"title": "Worker: close"}),
        ):
            lookup, closure = cards()
            mutate(lookup, closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

    def test_rejects_every_identity_and_parent_mismatch(self):
        mutations = (
            lambda lookup, closure: closure.update({"id": DELIVERY_ID}),
            lambda lookup, closure: closure.update({"parents": [CANDIDATE_ID]}),
            lambda lookup, closure: lookup[DELIVERY_ID]["task"].update({"parents": [DELIVERY_ID]}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"assignee": "foundry-worker"}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"parents": []}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"parents": [WORKER_ID, WORKER_ID]}),
            lambda lookup, closure: lookup[CANDIDATE_ID]["task"].update({"parents": [WORKER_ID, OTHER_PARENT_ID]}),
            lambda lookup, closure: lookup[WORKER_ID]["task"].update({"status": "running"}),
            lambda lookup, closure: lookup[DELIVERY_ID]["task"]["metadata"]["closure_delivery_receipt_v1"].update({"candidate_auditor_task_id": CLOSURE_ID}),
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

    def test_rejects_workspace_remote_api_marker_and_remote_delivery_bypasses_before_writes(self):
        lookup, closure = cards()
        packet_scope = scope()
        with patch.object(closure_auditor, "git_output", side_effect=[packet_scope["origin"], "b" * 40]):
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.validate_workspace(closure, closure_auditor.derive_scope(closure, lookup.__getitem__))
        for response in (
            lambda method, url, payload: {"full_name": "other/repo", "default_branch": "main"} if url == packet_scope["api_target"] else Api(packet_scope)(method, url, payload),
            lambda method, url, payload: {"object": {"sha": "b" * 40}} if url.endswith("/git/ref/heads/main") else Api(packet_scope)(method, url, payload),
            lambda method, url, payload: {"body": "missing marker", "state": "open", "closed_at": None} if url.endswith("/issues/19") else Api(packet_scope)(method, url, payload),
        ):
            lookup, closure = cards()
            with patch.object(closure_auditor, "validate_workspace"):
                with self.assertRaises(closure_auditor.ClosureError):
                    closure_auditor.execute(closure, lookup.__getitem__, response)

    def test_source_managed_schema_is_dynamic_but_repository_bound_and_valid_json(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        closure_properties = schema["properties"]["closure_card"]["properties"]
        self.assertIn("pattern", closure_properties["canonical_contract_url"])
        self.assertNotIn("const", closure_properties["issue"])
        self.assertEqual(schema["properties"]["delivery_receipt"]["properties"]["repository"]["const"], closure_auditor.REPOSITORY)
        self.assertEqual(schema["properties"]["delivery_receipt"]["properties"]["branch"]["const"], closure_auditor.BRANCH)


if __name__ == "__main__":
    unittest.main()