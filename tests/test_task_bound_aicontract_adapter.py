import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-architect/adapters/task_bound_aicontract.py"
spec = importlib.util.spec_from_file_location("task_bound_aicontract", ADAPTER_PATH)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class TaskBoundAIContractTests(unittest.TestCase):
    def setUp(self):
        self.card = {
            "id": "t_deadbeef",
            "assignee": "foundry-architect",
            "title": "Architect: execute Phase 0 contract packet",
            "body": "<!-- FOUNDRY_ARCHITECT_AICONTRACT_AUTHORIZATION_V1\n"
            + json.dumps({
                "repository": "stemarie/AI.Contract",
                "api_target": "https://api.github.com/repos/stemarie/AI.Contract",
                "issue_title": "Contract: bounded Phase 0 foundation",
                "issue_body": "A bounded, immutable Phase 0 contract.",
            }, sort_keys=True)
            + "\n-->",
        }
        self.issues = []
        self.calls = []

    def request(self, method, url, payload=None):
        self.calls.append((method, url, payload))
        base = "https://api.github.com/repos/stemarie/AI.Contract"
        if method == "GET" and url == base:
            return {"full_name": "stemarie/AI.Contract", "default_branch": "main"}
        if method == "GET" and url == base + "/issues?state=all&per_page=100":
            return self.issues
        if method == "POST" and url == base + "/issues":
            issue = {"number": len(self.issues) + 1, "title": payload["title"], "body": payload["body"], "state": "open"}
            self.issues.append(issue)
            return issue
        if method == "GET" and url == base + "/issues/1":
            return self.issues[0]
        self.fail(f"unexpected request: {method} {url}")

    def test_creates_exact_one_contract_and_reads_it_back(self):
        result = adapter.execute(self.card, self.request)
        self.assertEqual(result, {"operation": "created-and-read-back", "repository": "stemarie/AI.Contract", "issue": 1})
        self.assertEqual([call[0] for call in self.calls], ["GET", "GET", "POST", "GET"])
        self.assertIn(adapter.marker_for("t_deadbeef"), self.issues[0]["body"])

    def test_reread_is_idempotent(self):
        adapter.execute(self.card, self.request)
        self.calls.clear()
        result = adapter.execute(self.card, self.request)
        self.assertEqual(result["operation"], "idempotent-readback")
        self.assertNotIn("POST", [call[0] for call in self.calls])

    def test_rejects_non_architect_wrong_repo_and_duplicate_marker(self):
        with self.assertRaisesRegex(adapter.AIContractAdapterError, "not a foundry-architect"):
            adapter.execute({**self.card, "assignee": "foundry-worker"}, self.request)
        bad = self.card["body"].replace("stemarie/AI.Contract", "stemarie/not-contract", 1)
        with self.assertRaisesRegex(adapter.AIContractAdapterError, "must bind stemarie/AI.Contract"):
            adapter.execute({**self.card, "body": bad}, self.request)
        marker = adapter.marker_for("t_deadbeef")
        self.issues = [{"number": 1, "title": "x", "body": marker, "state": "open"}, {"number": 2, "title": "x", "body": marker, "state": "open"}]
        with self.assertRaisesRegex(adapter.AIContractAdapterError, "multiple contract Issues"):
            adapter.execute(self.card, self.request)

    def test_receipt_never_exposes_contract_body(self):
        self.card["body"] = self.card["body"].replace("immutable Phase 0 contract", "secret-contract-content")
        self.assertNotIn("secret-contract-content", json.dumps(adapter.execute(self.card, self.request)))


if __name__ == "__main__":
    unittest.main()
