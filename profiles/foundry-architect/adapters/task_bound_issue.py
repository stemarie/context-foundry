#!/usr/bin/env python3
"""Create or read back the sole tracking Issue authorized by an Architect card."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable


PROFILE = "foundry-architect"
BOARD = "context-foundry"
AUTH_START = "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n"
AUTH_END = "\n-->"
ISSUE_MARKER = "FOUNDRY-ARCHITECT-TASK-BOUND-ISSUE-ADAPTER-V1"
REPOSITORY = re.compile(r"^stemarie/[A-Za-z0-9][A-Za-z0-9._-]*$")
TASK_ID = re.compile(r"^t_[0-9a-f]{8}$")


class IssueAdapterError(RuntimeError):
    pass


def exact_dict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise IssueAdapterError(f"{label} has unsupported or missing fields")
    return value


def authorization(card: dict[str, Any]) -> dict[str, Any]:
    if card.get("assignee") != PROFILE or not str(card.get("title", "")).startswith("Architect:"):
        raise IssueAdapterError("assigned task is not a foundry-architect Architect card")
    task_id = card.get("id")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise IssueAdapterError("Architect card has an invalid task ID")
    body = card.get("body")
    if not isinstance(body, str) or body.count(AUTH_START) != 1 or body.count(AUTH_END) != 1:
        raise IssueAdapterError("Architect card requires exactly one Issue authorization block")
    try:
        scope = json.loads(body.split(AUTH_START, 1)[1].split(AUTH_END, 1)[0])
    except json.JSONDecodeError as error:
        raise IssueAdapterError("Architect Issue authorization block is invalid JSON") from error
    scope = exact_dict(scope, {"repository", "origin", "api_target", "branch", "issue_title", "issue_body"}, "Architect Issue authorization")
    repository = scope["repository"]
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        raise IssueAdapterError("Architect Issue repository is outside stemarie/<repo>")
    expected_origin = f"https://github.com/{repository}.git"
    expected_api = f"https://api.github.com/repos/{repository}"
    if scope["origin"] != expected_origin or scope["api_target"] != expected_api:
        raise IssueAdapterError("Architect Issue origin/API target does not exactly bind repository")
    if not isinstance(scope["branch"], str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]*", scope["branch"]):
        raise IssueAdapterError("Architect Issue branch is invalid")
    if not isinstance(scope["issue_title"], str) or not scope["issue_title"].strip() or len(scope["issue_title"]) > 256:
        raise IssueAdapterError("Architect Issue title is invalid")
    if not isinstance(scope["issue_body"], str) or len(scope["issue_body"]) > 60000:
        raise IssueAdapterError("Architect Issue body is invalid")
    return scope


def validate_workspace(card: dict[str, Any], scope: dict[str, Any], git: Callable[..., str]) -> None:
    workspace = card.get("workspace_path")
    if not isinstance(workspace, str) or not workspace:
        raise IssueAdapterError("Architect card has no workspace path")
    if git(workspace, "remote", "get-url", "origin") != scope["origin"]:
        raise IssueAdapterError("Architect workspace origin differs from authorization")
    remote_branch = git(workspace, "ls-remote", "origin", f"refs/heads/{scope['branch']}").split()
    if not remote_branch:
        raise IssueAdapterError("Architect workspace authorized branch is absent from remote")


def git_output(workspace: str, *args: str) -> str:
    run = subprocess.run(["git", "-C", workspace, *args], capture_output=True, text=True, check=False, timeout=30)
    if run.returncode:
        raise IssueAdapterError("could not read Architect workspace Git state")
    return run.stdout.strip()


def token() -> str:
    env_file = Path.home() / ".hermes" / "profiles" / PROFILE / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise IssueAdapterError("Architect credential helper configuration is unreadable") from error
    for line in lines:
        if line.startswith("GITHUB_TOKEN="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise IssueAdapterError("Architect credential helper configuration lacks a token")


def api(method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
    request = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode("utf-8"), method=method, headers={"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise IssueAdapterError(f"GitHub {method} {url} returned HTTP {error.code}") from error


def marker_for(task_id: str) -> str:
    return f"<!-- {ISSUE_MARKER}:{task_id} -->"


def expected_body(card: dict[str, Any], scope: dict[str, Any]) -> str:
    return f"{marker_for(card['id'])}\n{scope['issue_body']}"


def matching_issues(issues: Any, marker: str) -> list[dict[str, Any]]:
    if not isinstance(issues, list) or not all(isinstance(issue, dict) for issue in issues):
        raise IssueAdapterError("GitHub Issues listing is malformed")
    if len(issues) >= 100:
        raise IssueAdapterError("GitHub Issues listing reached pagination limit")
    return [issue for issue in issues if marker in str(issue.get("body", ""))]


def exact_readback(issue: Any, card: dict[str, Any], scope: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(issue, dict) or issue.get("title") != scope["issue_title"] or issue.get("body") != expected_body(card, scope):
        raise IssueAdapterError("tracking Issue read-back does not exactly bind Architect card")
    number = issue.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise IssueAdapterError("tracking Issue read-back has invalid number")
    return {"repository": scope["repository"], "issue": number}


def execute(card: dict[str, Any], request: Callable[[str, str, dict[str, Any] | None], Any] = api, git: Callable[..., str] = git_output) -> dict[str, Any]:
    scope = authorization(card)
    validate_workspace(card, scope, git)
    base = scope["api_target"]
    repo = request("GET", base, None)
    if not isinstance(repo, dict) or repo.get("full_name") != scope["repository"] or repo.get("default_branch") != scope["branch"]:
        raise IssueAdapterError("GitHub API repository does not resolve to authorization")
    marker = marker_for(card["id"])
    issues_url = f"{base}/issues?state=all&per_page=100"
    matches = matching_issues(request("GET", issues_url, None), marker)
    if len(matches) > 1:
        raise IssueAdapterError("multiple tracking Issues match Architect card marker")
    if matches:
        result = exact_readback(request("GET", f"{base}/issues/{matches[0].get('number')}", None), card, scope)
        return {"operation": "idempotent-readback", **result}
    created = request("POST", f"{base}/issues", {"title": scope["issue_title"], "body": expected_body(card, scope)})
    result = exact_readback(created, card, scope)
    readback = request("GET", f"{base}/issues/{result['issue']}", None)
    exact_readback(readback, card, scope)
    return {"operation": "created-and-read-back", **result}


def live_card(task_id: str) -> dict[str, Any]:
    run = subprocess.run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"], capture_output=True, text=True, check=False, timeout=30)
    if run.returncode:
        raise IssueAdapterError("could not read Architect Kanban card")
    try:
        data = json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise IssueAdapterError("Architect Kanban response was invalid") from error
    if not isinstance(data, dict) or not isinstance(data.get("task"), dict) or data["task"].get("id") != task_id:
        raise IssueAdapterError("Architect Kanban response was malformed")
    return data


def main() -> None:
    task_id = os.environ.get("HERMES_KANBAN_TASK")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise IssueAdapterError("adapter requires its assigned canonical HERMES_KANBAN_TASK")
    print(json.dumps(execute(live_card(task_id)["task"]), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except IssueAdapterError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
