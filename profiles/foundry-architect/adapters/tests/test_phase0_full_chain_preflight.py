"""Deterministic isolation tests for the Phase-0 binding preflight."""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest import mock


ADAPTER = Path(__file__).resolve().parents[1] / "phase0_full_chain_preflight.py"
SPEC = importlib.util.spec_from_file_location("phase0_full_chain_preflight", ADAPTER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TOKEN = "fixture-token-must-never-escape"
TASK = "t_ea213115"
PACKET = "FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution\n\nfixture packet"
CANONICAL_BODY = MODULE.CANONICAL_MARKER + "\n" + MODULE.PHASE0_MARKER
TRACKER_BODY = MODULE.TRACKER_MARKER + "\n" + MODULE.CANONICAL_ISSUE_URL


class Response(io.StringIO):
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False


class Phase0FullChainPreflightTest(unittest.TestCase):
    def setUp(self):
        self.patches = mock.patch.multiple(
            MODULE,
            PACKET_SHA256=hashlib.sha256(PACKET.encode()).hexdigest(),
            CANONICAL_BODY_SHA256=hashlib.sha256(CANONICAL_BODY.encode()).hexdigest(),
            TRACKER_BODY_SHA256=hashlib.sha256(TRACKER_BODY.encode()).hexdigest(),
        )
        self.patches.start()
        self.addCleanup(self.patches.stop)
        self.calls = []
        self.askpass_paths = []

    def envelope(self):
        task = {
            "id": TASK, "title": "Architect: execute transported draft handoff t_8df82916",
            "body": PACKET, "assignee": "foundry-architect", "status": "running",
            "priority": 0, "tenant": None, "workspace_kind": "scratch", "workspace_path": "/safe",
            "branch_name": None, "project_id": None, "created_by": "foundry-watchdog",
            "created_at": 1, "started_at": 2, "completed_at": None, "result": None, "skills": [],
            "max_retries": None, "model_override": None, "provider_override": None, "session_id": None,
            "workflow_template_id": None, "current_step_key": None, "completion_contract": "local-only",
            "last_failure_error": None,
        }
        run_id, pid = 1, 999
        created_payload = {
            "assignee": "foundry-architect", "status": "ready", "parents": ["t_8df82916"],
            "creator_task_id": None, "tenant": None, "workspace_kind": "scratch",
            "workspace_path": None, "branch_name": None, "project_id": None, "skills": None,
            "goal_mode": None, "model_override": None, "provider_override": None,
        }
        events = [
            {"kind": "created", "payload": created_payload, "created_at": 1, "run_id": None},
            {"kind": "claimed", "payload": {"lock": "overmind:1", "expires": 3, "run_id": run_id}, "created_at": 2, "run_id": run_id},
            {"kind": "spawned", "payload": {"pid": pid}, "created_at": 3, "run_id": run_id},
        ]
        runs = [{"id": run_id, "profile": "foundry-architect", "step_key": None, "status": "running", "outcome": None, "summary": None, "error": None, "metadata": None, "worker_pid": pid, "started_at": 2, "ended_at": None}]
        return {"task": task, "latest_summary": None, "parents": ["t_8df82916"], "children": [], "comments": [], "events": events, "runs": runs}

    def data(self):
        return {
            MODULE.CANONICAL_API: {"full_name": MODULE.CANONICAL_REPOSITORY, "default_branch": "main"},
            MODULE.CANONICAL_ISSUE_API: {"number": 50, "html_url": MODULE.CANONICAL_ISSUE_URL, "state": "open", "body": CANONICAL_BODY},
            MODULE.TARGET_API: {"full_name": MODULE.TARGET_REPOSITORY, "private": True, "default_branch": "main", "html_url": "https://github.com/stemarie/mentorship-platform"},
            MODULE.TRACKER_API: {"number": 9, "html_url": MODULE.TRACKER_URL, "title": MODULE.TRACKER_TITLE, "state": "open", "body": TRACKER_BODY},
        }

    def opener(self, request, timeout):
        self.calls.append(request)
        return Response(json.dumps(self.data()[request.full_url]))

    def runner(self, args, **kwargs):
        self.assertEqual(args, ["git", "ls-remote", MODULE.ORIGIN, MODULE.REF])
        self.assertNotIn(TOKEN, " ".join(args))
        self.assertEqual(kwargs["env"]["GIT_TERMINAL_PROMPT"], "0")
        path = Path(kwargs["env"]["GIT_ASKPASS"])
        self.assertEqual(path.stat().st_mode & 0o777, 0o700)
        self.askpass_paths.append(path)
        return subprocess.CompletedProcess(args, 0, MODULE.FROZEN_BASE + "\t" + MODULE.REF + "\n", "")

    def preflight_result(self, envelope=None, opener=None, runner=None):
        return MODULE.preflight(["preflight"], {"HERMES_KANBAN_TASK": TASK}, lambda _: self.envelope() if envelope is None else envelope, lambda: TOKEN, self.opener if opener is None else opener, self.runner if runner is None else runner)

    def test_complete_pass_is_exact_and_secret_free(self):
        result = self.preflight_result()
        rendered = json.dumps(result, sort_keys=True, separators=(",", ":"))
        self.assertEqual(rendered, json.dumps(MODULE.receipt(TASK), sort_keys=True, separators=(",", ":")))
        self.assertNotIn(TOKEN, rendered)
        self.assertEqual({call.get_method() for call in self.calls}, {"GET"})
        self.assertEqual({call.full_url for call in self.calls}, MODULE.ENDPOINTS)
        self.assertEqual(len(self.askpass_paths), 1)
        self.assertFalse(self.askpass_paths[0].exists())
        self.assertEqual(set(result), {"contract", "operation", "operations", "target", "task_id", "tracker", "verdict"})

    def test_invocation_and_identity_fail_before_credential(self):
        for argv, env, code in (([], {}, "invalid-invocation"), (["no"], {"HERMES_KANBAN_TASK": TASK}, "invalid-invocation"), (["preflight", "x"], {"HERMES_KANBAN_TASK": TASK}, "invalid-invocation"), (["preflight"], {"HERMES_KANBAN_TASK": "bad"}, "task-binding")):
            with self.subTest(argv=argv, env=env), self.assertRaisesRegex(MODULE.PreflightError, code):
                MODULE.preflight(argv, env, lambda _: self.fail("board read"), lambda: self.fail("credential"))

    def test_card_validation_rejects_substitution_and_malformed_shapes_before_token(self):
        cases = []
        bad = self.envelope(); bad["task"]["id"] = "t_deadbeef"; cases.append(bad)
        bad = self.envelope(); bad["task"]["assignee"] = "worker"; cases.append(bad)
        bad = self.envelope(); bad["task"]["title"] = "Architect: other"; cases.append(bad)
        bad = self.envelope(); bad["task"]["extra"] = True; cases.append(bad)
        bad = self.envelope(); bad["parents"] = []; cases.append(bad)
        bad = self.envelope(); bad["parents"].append("t_deadbeef"); cases.append(bad)
        bad = self.envelope(); bad["body"] = PACKET + "substituted"; cases.append(bad)
        bad = self.envelope(); bad["extra"] = 1; cases.append(bad)
        bad = self.envelope(); bad["events"][0]["payload"]["assignee"] = "foundry-auditor"; cases.append(bad)
        bad = self.envelope(); bad["events"][0]["payload"]["parents"] = []; cases.append(bad)
        bad = self.envelope(); bad["events"].append({"kind": "review_requested", "payload": {}, "created_at": 4, "run_id": 1}); cases.append(bad)
        bad = self.envelope(); bad["runs"][0]["profile"] = "foundry-auditor"; cases.append(bad)
        bad = self.envelope(); bad["runs"][0]["metadata"] = {"receipt": "substituted"}; cases.append(bad)
        bad = self.envelope(); bad["runs"].append(dict(bad["runs"][0])); cases.append(bad)
        for envelope in cases:
            with self.subTest(envelope=envelope), self.assertRaises(MODULE.PreflightError):
                MODULE.preflight(["preflight"], {"HERMES_KANBAN_TASK": TASK}, lambda _: envelope, lambda: self.fail("token read"))

    def test_transport_permits_only_fixed_get_endpoints(self):
        with self.assertRaisesRegex(MODULE.PreflightError, "http-method"):
            MODULE.get_json("POST", MODULE.CANONICAL_API, TOKEN, self.opener)
        with self.assertRaisesRegex(MODULE.PreflightError, "endpoint-binding"):
            MODULE.get_json("GET", "https://api.github.com/repos/other", TOKEN, self.opener)

    def test_canonical_and_tracker_validation_rejects_every_bound_field_class(self):
        validators = (
            (MODULE.validate_canonical_repository, self.data()[MODULE.CANONICAL_API], ("full_name", "default_branch")),
            (MODULE.validate_canonical_issue, self.data()[MODULE.CANONICAL_ISSUE_API], ("number", "html_url", "state")),
            (MODULE.validate_tracker_repository, self.data()[MODULE.TARGET_API], ("full_name", "private", "default_branch", "html_url")),
            (MODULE.validate_tracker_issue, self.data()[MODULE.TRACKER_API], ("number", "html_url", "title", "state")),
        )
        for validator, value, fields in validators:
            for field in fields:
                bad = dict(value); bad[field] = False
                with self.subTest(validator=validator.__name__, field=field), self.assertRaises(MODULE.PreflightError):
                    validator(bad)
        for validator, value in ((MODULE.validate_canonical_issue, self.data()[MODULE.CANONICAL_ISSUE_API]), (MODULE.validate_tracker_issue, self.data()[MODULE.TRACKER_API])):
            for body in (None, "missing marker", value["body"] + "changed"):
                bad = dict(value); bad["body"] = body
                with self.subTest(validator=validator.__name__, body=body), self.assertRaises(MODULE.PreflightError):
                    validator(bad)

    def test_git_rejects_changed_binding_and_malformed_records(self):
        with self.assertRaisesRegex(MODULE.PreflightError, "git-binding"):
            MODULE.git_ls_remote("https://github.com/other.git", MODULE.REF, TOKEN, self.runner)
        with self.assertRaisesRegex(MODULE.PreflightError, "git-binding"):
            MODULE.git_ls_remote(MODULE.ORIGIN, "refs/heads/other", TOKEN, self.runner)
        for output in ("", MODULE.FROZEN_BASE + "\t" + MODULE.REF + "\nother\t" + MODULE.REF, "not-a-record", "0" * 40 + "\t" + MODULE.REF):
            with self.subTest(output=output), self.assertRaisesRegex(MODULE.PreflightError, "git-response"):
                MODULE.validate_git_output(output)

    def test_cleanup_happens_when_git_fails_after_helper_creation(self):
        def fails(args, **kwargs):
            path = Path(kwargs["env"]["GIT_ASKPASS"]); self.askpass_paths.append(path)
            return subprocess.CompletedProcess(args, 1, "", "")
        with self.assertRaisesRegex(MODULE.PreflightError, "git-transport"):
            self.preflight_result(runner=fails)
        self.assertFalse(self.askpass_paths[0].exists())

    def test_token_bearing_post_helper_failures_are_safe_and_cleanup(self):
        def fails_with_token(args, **kwargs):
            path = Path(kwargs["env"]["GIT_ASKPASS"]); self.askpass_paths.append(path)
            raise OSError(TOKEN + " /unsafe/path raw-output")
        with self.assertRaisesRegex(MODULE.PreflightError, "git-transport") as raised:
            self.preflight_result(runner=fails_with_token)
        self.assertNotIn(TOKEN, str(raised.exception))
        self.assertTrue(all(not path.exists() for path in self.askpass_paths))
        stderr, stdout = io.StringIO(), io.StringIO()
        raw_error = RuntimeError(TOKEN + " /unsafe/path raw-response")
        with mock.patch.object(MODULE, "preflight", side_effect=raw_error), contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
            self.assertEqual(MODULE.main(["preflight"], {"HERMES_KANBAN_TASK": TASK}), 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), json.dumps({"failure_code": "secret-safety", "operation": MODULE.OPERATION, "verdict": "FAIL"}, sort_keys=True, separators=(",", ":")) + "\n")
        self.assertNotIn(TOKEN, stderr.getvalue())

    def test_main_failure_evidence_is_single_safe_line(self):
        stderr, stdout = io.StringIO(), io.StringIO()
        with mock.patch.object(MODULE, "preflight", side_effect=MODULE.PreflightError("canonical-contract")), contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
            self.assertEqual(MODULE.main(["preflight"], {"HERMES_KANBAN_TASK": TASK}), 2)
        self.assertEqual(stdout.getvalue(), "")
        line = stderr.getvalue()
        self.assertEqual(line, json.dumps({"failure_code": "canonical-contract", "operation": MODULE.OPERATION, "verdict": "FAIL"}, sort_keys=True, separators=(",", ":")) + "\n")
        self.assertNotIn(TOKEN, line)

    def test_repeated_pass_is_byte_identical_and_creates_no_workspace_state(self):
        first = json.dumps(self.preflight_result(), sort_keys=True, separators=(",", ":"))
        second = json.dumps(self.preflight_result(), sort_keys=True, separators=(",", ":"))
        self.assertEqual(first, second)
        self.assertTrue(all(not path.exists() for path in self.askpass_paths))


if __name__ == "__main__":
    unittest.main()
