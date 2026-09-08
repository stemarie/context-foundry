import importlib.util
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
ADAPTER_PATH = ROOT / "profiles/foundry-architect/adapters/task_bound_issue.py"
spec = importlib.util.spec_from_file_location("task_bound_issue", ADAPTER_PATH)
assert spec and spec.loader
issue_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(issue_adapter)


class FakeGitHub:
    def __init__(self, repository="stemarie/example"):
        self.repository = repository
        self.issues = []
        self.requests = []
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.handler())
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def handler(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def reply(self, status, value):
                encoded = json.dumps(value).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

            def do_GET(self):
                fake.requests.append(("GET", self.path, None))
                if self.path == "/repos/stemarie/example":
                    return self.reply(200, {"full_name": fake.repository, "default_branch": "main"})
                if self.path == "/repos/stemarie/example/issues?state=all&per_page=100":
                    return self.reply(200, fake.issues)
                if self.path.startswith("/repos/stemarie/example/issues/"):
                    number = int(self.path.rsplit("/", 1)[1])
                    for issue in fake.issues:
                        if issue["number"] == number:
                            return self.reply(200, issue)
                return self.reply(404, {"message": "not found"})

            def do_POST(self):
                length = int(self.headers["Content-Length"])
                payload = json.loads(self.rfile.read(length))
                fake.requests.append(("POST", self.path, payload))
                if self.path != "/repos/stemarie/example/issues":
                    return self.reply(404, {"message": "not found"})
                issue = {"number": len(fake.issues) + 1, **payload, "state": "open"}
                fake.issues.append(issue)
                return self.reply(201, issue)

        return Handler

    def request(self, method, url, payload=None):
        from urllib.request import Request, urlopen

        path = urlsplit(url)
        target = f"http://127.0.0.1:{self.server.server_port}{path.path}"
        if path.query:
            target += "?" + path.query
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        with urlopen(Request(target, data=data, method=method, headers={"Content-Type": "application/json"}), timeout=3) as response:
            return json.load(response)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)


class TaskBoundIssueTests(unittest.TestCase):
    def setUp(self):
        self.github = FakeGitHub()
        self.kanban_state = {
            "id": "t_deadbeef",
            "assignee": "foundry-architect",
            "title": "Architect: example release packet",
            "workspace_path": "/temporary/example",
            "body": "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n" + json.dumps({
                "repository": "stemarie/example",
                "origin": "https://github.com/stemarie/example.git",
                "api_target": "https://api.github.com/repos/stemarie/example",
                "branch": "main",
                "issue_title": "Track example release",
                "issue_body": "Bounded initial tracking issue; architect-secret-must-not-print",
            }, sort_keys=True) + "\n-->",
        }

    def tearDown(self):
        self.github.close()

    def git(self, workspace, *args):
        self.assertEqual(workspace, "/temporary/example")
        if args == ("remote", "get-url", "origin"):
            return "https://github.com/stemarie/example.git"
        if args == ("ls-remote", "origin", "refs/heads/main"):
            return "a" * 40 + "\trefs/heads/main"
        self.fail(f"unexpected Git command: {args}")

    def execute(self, card=None):
        return issue_adapter.execute(card or self.kanban_state, self.github.request, self.git)

    def test_creates_one_issue_then_exactly_reads_it_back(self):
        result = self.execute()
        self.assertEqual(result, {"operation": "created-and-read-back", "repository": "stemarie/example", "issue": 1})
        self.assertEqual(len(self.github.issues), 1)
        self.assertIn(issue_adapter.marker_for("t_deadbeef"), self.github.issues[0]["body"])
        self.assertEqual([method for method, _, _ in self.github.requests], ["GET", "GET", "POST", "GET"])

    def test_marker_reread_is_idempotent_and_does_not_post(self):
        self.execute()
        self.github.requests.clear()
        result = self.execute()
        self.assertEqual(result["operation"], "idempotent-readback")
        self.assertEqual(len(self.github.issues), 1)
        self.assertNotIn("POST", [method for method, _, _ in self.github.requests])

    def test_rejects_non_architect_out_of_scope_repo_and_origin_api_mismatch(self):
        non_architect = dict(self.kanban_state, assignee="foundry-worker")
        with self.assertRaisesRegex(issue_adapter.IssueAdapterError, "not a foundry-architect"):
            self.execute(non_architect)
        scope = json.loads(self.kanban_state["body"].split("\n", 1)[1].rsplit("\n-->", 1)[0])
        scope["repository"] = "other-owner/example"
        out_of_scope = dict(self.kanban_state, body="<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n" + json.dumps(scope) + "\n-->")
        with self.assertRaisesRegex(issue_adapter.IssueAdapterError, "outside stemarie"):
            self.execute(out_of_scope)
        scope["repository"] = "stemarie/example"
        scope["api_target"] = "https://api.github.com/repos/stemarie/other"
        mismatch = dict(self.kanban_state, body="<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n" + json.dumps(scope) + "\n-->")
        with self.assertRaisesRegex(issue_adapter.IssueAdapterError, "origin/API target"):
            self.execute(mismatch)
        self.assertEqual(self.github.issues, [])

    def test_refuses_duplicate_marker_matches(self):
        marker = issue_adapter.marker_for("t_deadbeef")
        self.github.issues.extend([
            {"number": 1, "title": "a", "body": marker, "state": "open"},
            {"number": 2, "title": "b", "body": marker, "state": "open"},
        ])
        with self.assertRaisesRegex(issue_adapter.IssueAdapterError, "multiple tracking Issues"):
            self.execute()
        self.assertNotIn("POST", [method for method, _, _ in self.github.requests])

    def test_result_and_failure_never_emit_issue_body_or_credentials(self):
        output = json.dumps(self.execute(), sort_keys=True)
        self.assertNotIn("architect-secret-must-not-print", output)
        self.assertNotIn("GITHUB_TOKEN", output)


if __name__ == "__main__":
    unittest.main()
