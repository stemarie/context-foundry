#!/usr/bin/env python3
"""Read-only, task-bound Phase-0 full-chain binding preflight.

The only authenticated remote operations in this module are four fixed GitHub
GETs and one fixed ``git ls-remote``.  It deliberately has no write path.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

BOARD = "context-foundry"
PROFILE = "foundry-architect"
TASK_ID = re.compile(r"t_[0-9a-f]{8}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
OPERATION = "phase0-full-chain-binding-preflight"
PARENT_ID = "t_8df82916"
PACKET_SHA256 = "9b45b3c14cc0624b106c266cd78c06b8264966b2a675bc4c97a7522f6ae19c28"
CANONICAL_REPOSITORY = "stemarie/AI.Contract"
CANONICAL_API = "https://api.github.com/repos/stemarie/AI.Contract"
CANONICAL_ISSUE_URL = "https://github.com/stemarie/AI.Contract/issues/50"
CANONICAL_ISSUE_API = CANONICAL_API + "/issues/50"
CANONICAL_BODY_SHA256 = "2034905f7ca37ea0d88094c35dadb3eadfd7228b6d6e42c0512a0cddf20e10e0"
CANONICAL_MARKER = "<!-- FOUNDRY-ARCHITECT-TASK-BOUND-ISSUE-ADAPTER-V1:t_5085d58e -->"
PHASE0_MARKER = "FOUNDRY_CAREER_OS_PHASE0_DECISION_RECORDS_V1"
TARGET_REPOSITORY = "stemarie/mentorship-platform"
TARGET_API = "https://api.github.com/repos/stemarie/mentorship-platform"
TRACKER_URL = "https://github.com/stemarie/mentorship-platform/issues/9"
TRACKER_API = TARGET_API + "/issues/9"
TRACKER_TITLE = "Career OS Phase 0 decision records — ADR set, database migration strategy, and test strategy"
TRACKER_BODY_SHA256 = "d7b377da1637f9f6052bd1788e693e551b565bd1cb1749ed398508bcc9e9417b"
TRACKER_MARKER = "<!-- FOUNDRY_CAREER_OS_PHASE0_DECISION_RECORDS_TRACKER:t_5085d58e -->"
ORIGIN = "https://github.com/stemarie/mentorship-platform.git"
REF = "refs/heads/main"
FROZEN_BASE = "5bd0dfe42d1cdce1614330fd5892204f22d9cfcb"
ENDPOINTS = frozenset((CANONICAL_API, CANONICAL_ISSUE_API, TARGET_API, TRACKER_API))
FAILURE_CODES = frozenset((
    "invalid-invocation", "task-binding", "card-envelope", "card-shape",
    "credential-helper", "http-method", "endpoint-binding", "http-transport",
    "api-response", "canonical-repository", "canonical-contract",
    "tracker-repository", "tracker", "git-binding", "git-transport",
    "git-response", "receipt-shape", "secret-safety",
))
TASK_KEYS = frozenset((
    "id", "title", "body", "assignee", "status", "priority", "tenant",
    "workspace_kind", "workspace_path", "branch_name", "project_id", "created_by",
    "created_at", "started_at", "completed_at", "result", "skills", "max_retries",
    "model_override", "provider_override", "session_id", "workflow_template_id",
    "current_step_key", "completion_contract", "last_failure_error",
))
ENVELOPE_KEYS = frozenset(("task", "latest_summary", "parents", "children", "comments", "events", "runs"))
EVENT_KEYS = frozenset(("kind", "payload", "created_at", "run_id"))
RUN_KEYS = frozenset((
    "id", "profile", "step_key", "status", "outcome", "summary", "error",
    "metadata", "worker_pid", "started_at", "ended_at",
))


class PreflightError(RuntimeError):
    def __init__(self, code: str):
        if code not in FAILURE_CODES:
            code = "secret-safety"
        self.code = code
        super().__init__(code)


def require(condition: bool, code: str) -> None:
    if not condition:
        raise PreflightError(code)


def exact_keys(value: Any, keys: frozenset[str], code: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == set(keys), code)
    return value


def validate_invocation(argv: list[str], environ: Mapping[str, str]) -> str:
    require(argv == ["preflight"], "invalid-invocation")
    task_id = environ.get("HERMES_KANBAN_TASK")
    require(isinstance(task_id, str) and TASK_ID.fullmatch(task_id) is not None, "task-binding")
    return task_id


def read_envelope(task_id: str) -> dict[str, Any]:
    try:
        run = subprocess.run(
            ["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"],
            capture_output=True, text=True, check=False, timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise PreflightError("card-envelope") from error
    if run.returncode != 0:
        raise PreflightError("card-envelope")
    try:
        value = json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise PreflightError("card-envelope") from error
    require(isinstance(value, dict), "card-envelope")
    return value


def validate_envelope(envelope: Any, task_id: str) -> dict[str, Any]:
    envelope = exact_keys(envelope, ENVELOPE_KEYS, "card-envelope")
    require(envelope["parents"] == [PARENT_ID] and envelope["children"] == [], "card-shape")
    require(envelope["latest_summary"] is None, "card-shape")
    require(envelope["comments"] == [], "card-shape")
    card = exact_keys(envelope["task"], TASK_KEYS, "card-shape")
    require(card["id"] == task_id and TASK_ID.fullmatch(task_id) is not None, "task-binding")
    require(card["assignee"] == PROFILE, "card-shape")
    require(card["title"] == f"Architect: execute transported draft handoff {PARENT_ID}", "card-shape")
    require(card["status"] == "running" and card["created_by"] == "foundry-watchdog", "card-shape")
    body = card["body"]
    require(isinstance(body, str), "card-shape")
    require(body.startswith("FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution\n\n"), "card-shape")
    require(hashlib.sha256(body.encode("utf-8")).hexdigest() == PACKET_SHA256, "card-shape")
    validate_execution_provenance(envelope["events"], envelope["runs"])
    return card


def validate_execution_provenance(events: Any, runs: Any) -> None:
    """Accept only the initial Architect execution lifecycle before any review."""
    require(isinstance(events, list) and isinstance(runs, list), "card-envelope")
    require(len(runs) == 1, "card-shape")
    run = exact_keys(runs[0], RUN_KEYS, "card-shape")
    run_id = run["id"]
    require(
        isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0
        and run["profile"] == PROFILE and run["step_key"] is None
        and run["status"] == "running" and run["outcome"] is None
        and run["summary"] is None and run["error"] is None and run["metadata"] is None
        and isinstance(run["worker_pid"], int) and not isinstance(run["worker_pid"], bool)
        and run["worker_pid"] > 0 and isinstance(run["started_at"], int)
        and run["ended_at"] is None,
        "card-shape",
    )
    require(len(events) >= 3, "card-shape")
    created = exact_keys(events[0], EVENT_KEYS, "card-envelope")
    expected_created = {
        "assignee": PROFILE, "status": "ready", "parents": [PARENT_ID],
        "creator_task_id": None, "tenant": None, "workspace_kind": "scratch",
        "workspace_path": None, "branch_name": None, "project_id": None,
        "skills": None, "goal_mode": None, "model_override": None,
        "provider_override": None,
    }
    require(
        created["kind"] == "created" and created["run_id"] is None
        and isinstance(created["created_at"], int) and created["payload"] == expected_created,
        "card-shape",
    )
    claim = exact_keys(events[1], EVENT_KEYS, "card-envelope")
    require(
        claim["kind"] == "claimed" and claim["run_id"] == run_id
        and isinstance(claim["created_at"], int) and isinstance(claim["payload"], dict)
        and set(claim["payload"]) == {"lock", "expires", "run_id"}
        and isinstance(claim["payload"]["lock"], str) and claim["payload"]["lock"].startswith("overmind:")
        and isinstance(claim["payload"]["expires"], int) and claim["payload"]["run_id"] == run_id,
        "card-shape",
    )
    spawned = exact_keys(events[2], EVENT_KEYS, "card-envelope")
    require(
        spawned["kind"] == "spawned" and spawned["run_id"] == run_id
        and isinstance(spawned["created_at"], int) and isinstance(spawned["payload"], dict)
        and set(spawned["payload"]) == {"pid"} and spawned["payload"]["pid"] == run["worker_pid"],
        "card-shape",
    )
    for event in events[3:]:
        event = exact_keys(event, EVENT_KEYS, "card-envelope")
        require(
            event["kind"] == "heartbeat" and event["payload"] is None
            and event["run_id"] == run_id and isinstance(event["created_at"], int),
            "card-shape",
        )


def load_token() -> str:
    """Use the Architect profile's established local-token loading pattern."""
    env_file = Path.home() / ".hermes" / "profiles" / PROFILE / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise PreflightError("credential-helper") from error
    for line in lines:
        if line.startswith("GITHUB_TOKEN="):
            secret = line.split("=", 1)[1].strip().strip('"').strip("'")
            if secret:
                return secret
    raise PreflightError("credential-helper")


def get_json(method: str, endpoint: str, secret: str, opener: Callable[..., Any] = urllib.request.urlopen) -> Any:
    require(method == "GET", "http-method")
    require(endpoint in ENDPOINTS, "endpoint-binding")
    request = urllib.request.Request(
        endpoint, method="GET",
        headers={
            "Authorization": "Bearer " + secret,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with opener(request, timeout=30) as response:
            return json.load(response)
    except (OSError, ValueError, urllib.error.HTTPError, urllib.error.URLError) as error:
        raise PreflightError("http-transport") from error


def body_hash(body: Any, code: str) -> str:
    require(isinstance(body, str), code)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def validate_canonical_repository(value: Any) -> None:
    require(isinstance(value, dict), "api-response")
    require(value.get("full_name") == CANONICAL_REPOSITORY and value.get("default_branch") == "main", "canonical-repository")


def validate_canonical_issue(value: Any) -> None:
    require(isinstance(value, dict), "api-response")
    require(value.get("number") == 50 and value.get("html_url") == CANONICAL_ISSUE_URL and value.get("state") == "open", "canonical-contract")
    body = value.get("body")
    require(isinstance(body, str) and CANONICAL_MARKER in body and PHASE0_MARKER in body, "canonical-contract")
    require(body_hash(body, "canonical-contract") == CANONICAL_BODY_SHA256, "canonical-contract")


def validate_tracker_repository(value: Any) -> None:
    require(isinstance(value, dict), "api-response")
    require(value.get("full_name") == TARGET_REPOSITORY and value.get("private") is True and value.get("default_branch") == "main" and value.get("html_url") == "https://github.com/stemarie/mentorship-platform", "tracker-repository")


def validate_tracker_issue(value: Any) -> None:
    require(isinstance(value, dict), "api-response")
    require(value.get("number") == 9 and value.get("html_url") == TRACKER_URL and value.get("title") == TRACKER_TITLE and value.get("state") == "open", "tracker")
    body = value.get("body")
    require(isinstance(body, str) and TRACKER_MARKER in body and CANONICAL_ISSUE_URL in body, "tracker")
    require(body_hash(body, "tracker") == TRACKER_BODY_SHA256, "tracker")


def git_ls_remote(origin: str, ref: str, secret: str, runner: Callable[..., Any] = subprocess.run) -> str:
    require(origin == ORIGIN and ref == REF, "git-binding")
    try:
        with tempfile.TemporaryDirectory(prefix="phase0-preflight-") as directory:
            askpass = Path(directory) / "askpass"
            askpass.write_text(
                "#!/bin/sh\ncase \"${1:-}\" in\n*Username*|*username*) printf '%s\\n' x-access-token ;;\n*Password*|*password*) printf '%s\\n' \"${PHASE0_GIT_TOKEN:?}\" ;;\n*) exit 1 ;;\nesac\n",
                encoding="utf-8",
            )
            askpass.chmod(0o700)
            environment = os.environ.copy()
            environment.update({"GIT_ASKPASS": str(askpass), "GIT_TERMINAL_PROMPT": "0", "PHASE0_GIT_TOKEN": secret})
            result = runner(["git", "ls-remote", ORIGIN, REF], capture_output=True, text=True, check=False, timeout=30, env=environment)
    except (OSError, subprocess.SubprocessError) as error:
        raise PreflightError("git-transport") from error
    require(getattr(result, "returncode", 1) == 0 and isinstance(getattr(result, "stdout", None), str), "git-transport")
    return result.stdout


def validate_git_output(output: str) -> None:
    lines = output.splitlines()
    require(len(lines) == 1, "git-response")
    fields = lines[0].split("\t")
    require(len(fields) == 2 and SHA.fullmatch(fields[0]) is not None and fields == [FROZEN_BASE, REF], "git-response")


def receipt(task_id: str) -> dict[str, Any]:
    result = {
        "contract": {"body_sha256": CANONICAL_BODY_SHA256, "issue": 50, "state": "open", "url": CANONICAL_ISSUE_URL},
        "operation": OPERATION,
        "operations": ["GET", "git-ls-remote"],
        "target": {"api_target": TARGET_API, "branch": "main", "frozen_base": FROZEN_BASE, "origin": ORIGIN, "repository": TARGET_REPOSITORY},
        "task_id": task_id,
        "tracker": {"body_sha256": TRACKER_BODY_SHA256, "issue": 9, "state": "open", "url": TRACKER_URL},
        "verdict": "PASS",
    }
    require(set(result) == {"contract", "operation", "operations", "target", "task_id", "tracker", "verdict"}, "receipt-shape")
    require(set(result["contract"]) == {"body_sha256", "issue", "state", "url"} and set(result["target"]) == {"api_target", "branch", "frozen_base", "origin", "repository"} and set(result["tracker"]) == {"body_sha256", "issue", "state", "url"}, "receipt-shape")
    return result


def preflight(argv: list[str], environ: Mapping[str, str], board_reader: Callable[[str], dict[str, Any]] = read_envelope, token_loader: Callable[[], str] = load_token, opener: Callable[..., Any] = urllib.request.urlopen, git_runner: Callable[..., Any] = subprocess.run) -> dict[str, Any]:
    task_id = validate_invocation(argv, environ)
    validate_envelope(board_reader(task_id), task_id)
    secret = token_loader()
    try:
        validate_canonical_repository(get_json("GET", CANONICAL_API, secret, opener))
        validate_canonical_issue(get_json("GET", CANONICAL_ISSUE_API, secret, opener))
        validate_tracker_repository(get_json("GET", TARGET_API, secret, opener))
        validate_tracker_issue(get_json("GET", TRACKER_API, secret, opener))
        validate_git_output(git_ls_remote(ORIGIN, REF, secret, git_runner))
        result = receipt(task_id)
        require(secret not in json.dumps(result, sort_keys=True), "secret-safety")
        return result
    finally:
        secret = ""


def fail(code: str) -> int:
    safe_code = code if code in FAILURE_CODES else "secret-safety"
    print(json.dumps({"failure_code": safe_code, "operation": OPERATION, "verdict": "FAIL"}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
    return 2


def main(argv: list[str] | None = None, environ: Mapping[str, str] | None = None) -> int:
    try:
        result = preflight(list(sys.argv[1:] if argv is None else argv), os.environ if environ is None else environ)
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except PreflightError as error:
        return fail(error.code)
    except Exception:
        return fail("secret-safety")


if __name__ == "__main__":
    raise SystemExit(main())
