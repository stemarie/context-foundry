import hashlib
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "profiles/foundry-architect/adapters/task_bound_contract_issue.py"
spec = importlib.util.spec_from_file_location("contract_issue", PATH)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class ContractIssueV2Tests(unittest.TestCase):
    def setUp(self):
        self.contract_id = "11111111-1111-4111-8111-111111111111"
        scope = {"contract": {"id": self.contract_id, "title": "Phase 0 decision records", "body_markdown": "Bounded contract body."}, "target": {"repository": "stemarie/mentorship-platform", "origin": "https://github.com/stemarie/mentorship-platform.git", "api_target": "https://api.github.com/repos/stemarie/mentorship-platform", "branch": "main", "worktree_path": "/work/mentorship", "base_sha": "a" * 40, "issue_title": "Phase 0 tracker", "issue_body": "Tracking only."}}
        self.card = {"id": "t_deadbeef", "assignee": "foundry-architect", "title": "Architect: execute contract", "workspace_path": "/work/mentorship", "body": "<!-- FOUNDRY_ARCHITECT_CONTRACT_ISSUE_AUTHORIZATION_V2\n" + json.dumps(scope, sort_keys=True) + "\n-->"}
        self.events, self.issues = [], []

    def git(self, workspace, *args):
        self.assertEqual(workspace, "/work/mentorship")
        return {("rev-parse", "--show-toplevel"): "/work/mentorship", ("remote", "get-url", "origin"): "https://github.com/stemarie/mentorship-platform.git", ("status", "--porcelain"): "", ("rev-parse", "HEAD"): "a" * 40, ("ls-remote", "origin", "refs/heads/main"): "a" * 40 + "\trefs/heads/main"}[args]

    def service(self, method, path, payload=None):
        self.events.append(("service", method, path))
        if method == "POST" and path == "/api/v1/chains": return {"chain": [{"id": self.contract_id}]}
        if method == "GET" and path == f"/api/v1/contracts/{self.contract_id}": return {"contract": {"id": self.contract_id, "title": "Phase 0 decision records", "body_markdown": "Bounded contract body.", "status": "In Progress", "version": "Alpha 1.0"}}
        if method == "POST" and path.endswith("/activate"): return {"frozen_revision": {"revision": 1, "digest": adapter.digest_for(self.contract_id, "Phase 0 decision records", "Bounded contract body.")}}
        if method == "GET" and path.endswith("/frozen"): return {"frozen_revision": {"revision": 1, "digest": adapter.digest_for(self.contract_id, "Phase 0 decision records", "Bounded contract body.")}}
        self.fail((method,path,payload))

    def github(self, method, url, payload=None):
        self.events.append(("github", method, url))
        base="https://api.github.com/repos/stemarie/mentorship-platform"
        if method == "GET" and url == base: return {"full_name":"stemarie/mentorship-platform","default_branch":"main"}
        if method == "GET" and url.endswith("issues?state=all&per_page=100"): return self.issues
        if method == "POST":
            issue={"number":1,"title":payload["title"],"body":payload["body"]}; self.issues.append(issue); return issue
        if method == "GET" and url.endswith("/issues/1"): return self.issues[0]
        self.fail((method,url,payload))

    def test_contract_activates_before_single_tracker_write(self):
        result=adapter.execute(self.card,self.service,self.github,self.git)
        self.assertEqual(result["operation"],"contract-activated-and-tracker-created")
        post_issue=next(i for i,e in enumerate(self.events) if e[0]=="github" and e[1]=="POST")
        activate=next(i for i,e in enumerate(self.events) if e[0]=="service" and e[1]=="POST" and e[2].endswith("/activate"))
        self.assertLess(activate,post_issue)

    def test_v1_or_workspace_drift_fails_before_network(self):
        old={**self.card,"body":"<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n{}\n-->"}
        with self.assertRaises(adapter.ContractIssueError): adapter.execute(old,self.service,self.github,self.git)
        with self.assertRaises(adapter.ContractIssueError): adapter.execute({**self.card,"workspace_path":"/wrong"},self.service,self.github,self.git)
        self.assertEqual(self.events,[])

if __name__=='__main__': unittest.main()
