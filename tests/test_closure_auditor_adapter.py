import copy
import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-auditor/adapters/closure_auditor.py"
spec = importlib.util.spec_from_file_location("closure_auditor", ADAPTER_PATH)
assert spec and spec.loader
closure_auditor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure_auditor)

SHA = "a" * 40
SCOPE = {"repository": "stemarie/context-foundry", "origin": "https://github.com/stemarie/context-foundry.git", "api_target": "https://api.github.com/repos/stemarie/context-foundry", "issue": 14, "branch": "main", "candidate_sha": SHA, "receipt_marker": "FOUNDRY_CLOSURE_RECEIPT_V1"}


def cards():
    candidate = {"id": "t_cand0001", "status": "done", "title": "Candidate Auditor: gate", "metadata": {"closure_candidate_audit_v1": {"schema_version": "closure_candidate_audit_v1", "verdict": "PASS", **{key: SCOPE[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}}}}
    delivery = {"id": "t_delv0001", "status": "done", "title": "Delivery: deliver", "parents": [candidate["id"]], "metadata": {"closure_delivery_receipt_v1": {"schema_version": "closure_delivery_receipt_v1", "outcome": "DELIVERED", "delivery_mode": "non-force-direct-main", **{key: SCOPE[key] for key in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha")}, "delivered_sha": SHA, "candidate_auditor_task_id": candidate["id"]}}}
    closure = {"id": "t_clos0001", "assignee": "foundry-auditor", "title": "Closure Auditor: close", "body": closure_auditor.AUTH_START + json.dumps(SCOPE) + closure_auditor.AUTH_END, "parents": [delivery["id"]], "workspace_path": "/tmp/example"}
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
        if url.endswith("/issues/14"):
            if method == "PATCH": self.closed = True
            return {"body": closure_auditor.ISSUE_MARKER, "state": "closed" if self.closed else "open", "closed_at": "now" if self.closed else None}
        raise AssertionError(url)


class ClosureAdapterTests(unittest.TestCase):
    def test_only_bound_pass_and_delivery_can_close_then_idempotently_read_back(self):
        lookup, closure = cards()
        api = Api()
        with patch.object(closure_auditor, "validate_workspace"):
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "closed")
            self.assertEqual(closure_auditor.execute(closure, lookup.__getitem__, api)["operation"], "idempotent-readback")
        self.assertEqual(api.writes, ["POST", "PATCH"])

    def test_rejects_prose_extra_fields_wrong_bindings_and_non_pass(self):
        for mutate in (
            lambda lookup, closure: lookup["t_cand0001"]["task"].update({"metadata": {"closure_candidate_audit_v1": "REQUEST_CHANGES but PASS appears"}}),
            lambda lookup, closure: lookup["t_cand0001"]["task"]["metadata"]["closure_candidate_audit_v1"].update({"extra": "x"}),
            lambda lookup, closure: lookup["t_delv0001"]["task"]["metadata"]["closure_delivery_receipt_v1"].update({"candidate_sha": "b" * 40}),
            lambda lookup, closure: lookup["t_delv0001"]["task"]["metadata"]["closure_delivery_receipt_v1"].update({"outcome": "DELIVERED PASS"}),
            lambda lookup, closure: closure.update({"assignee": "foundry-worker"}),
        ):
            lookup, closure = cards()
            mutate(lookup, closure)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

        for field in ("repository", "origin", "api_target", "issue", "branch", "candidate_sha", "receipt_marker"):
            lookup, closure = cards()
            scope = copy.deepcopy(SCOPE)
            scope[field] = 99 if field == "issue" else "wrong"
            closure["body"] = closure_auditor.AUTH_START + json.dumps(scope) + closure_auditor.AUTH_END
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.derive_scope(closure, lookup.__getitem__)

        for task_id, receipt_key, fields in (
            ("t_cand0001", "closure_candidate_audit_v1", ("repository", "origin", "api_target", "issue", "branch", "candidate_sha", "schema_version", "verdict")),
            ("t_delv0001", "closure_delivery_receipt_v1", ("repository", "origin", "api_target", "issue", "branch", "candidate_sha", "delivered_sha", "candidate_auditor_task_id", "schema_version", "outcome", "delivery_mode")),
        ):
            for field in fields:
                lookup, closure = cards()
                receipt = lookup[task_id]["task"]["metadata"][receipt_key]
                receipt[field] = 99 if field == "issue" else "wrong"
                with self.assertRaises(closure_auditor.ClosureError):
                    closure_auditor.derive_scope(closure, lookup.__getitem__)
                lookup, closure = cards()
                lookup[task_id]["task"]["metadata"][receipt_key].pop(field)
                with self.assertRaises(closure_auditor.ClosureError):
                    closure_auditor.derive_scope(closure, lookup.__getitem__)

    def test_rejects_authorization_schema_and_workspace_or_api_mismatch(self):
        lookup, closure = cards()
        bad_scope = copy.deepcopy(SCOPE); bad_scope["issue"] = True
        closure["body"] = closure_auditor.AUTH_START + json.dumps(bad_scope) + closure_auditor.AUTH_END
        with self.assertRaises(closure_auditor.ClosureError):
            closure_auditor.derive_scope(closure, lookup.__getitem__)
        lookup, closure = cards()
        with patch.object(closure_auditor, "git_output", side_effect=[SCOPE["origin"], "b" * 40]):
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.validate_workspace(closure, closure_auditor.derive_scope(closure, lookup.__getitem__))
        with patch.object(closure_auditor, "validate_workspace"):
            def wrong_ref(method, url, payload):
                if url.endswith("/git/ref/heads/main"):
                    return {"object": {"sha": "b" * 40}}
                return Api()(method, url, payload)
            with self.assertRaises(closure_auditor.ClosureError):
                closure_auditor.execute(closure, lookup.__getitem__, wrong_ref)


if __name__ == "__main__":
    unittest.main()
