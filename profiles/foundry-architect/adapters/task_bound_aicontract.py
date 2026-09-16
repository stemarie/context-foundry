#!/usr/bin/env python3
"""Create or read back one immutable AI.Contract Issue from an Architect card."""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

PROFILE = "foundry-architect"
BOARD = "context-foundry"
REPOSITORY = "stemarie/AI.Contract"
API_TARGET = "https://api.github.com/repos/stemarie/AI.Contract"
AUTH_START = "<!-- FOUNDRY_ARCHITECT_AICONTRACT_AUTHORIZATION_V1\n"
AUTH_END = "-->"
MARKER = "FOUNDRY-ARCHITECT-TASK-BOUND-AICONTRACT-ADAPTER-V1"
TASK_ID = re.compile(r"t_[0-9a-f]{8}\Z")


class AIContractAdapterError(RuntimeError):
    pass


def marker_for(task_id: str) -> str:
    return f"<!-- {MARKER}:{task_id} -->"


def authorization(card: dict[str, Any]) -> dict[str, str]:
    if card.get("assignee") != PROFILE or not str(card.get("title", "")).startswith("Architect:"):
        raise AIContractAdapterError("assigned task is not a foundry-architect Architect card")
    task_id = card.get("id")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise AIContractAdapterError("Architect card has an invalid task ID")
    body = card.get("body")
    if not isinstance(body, str) or body.count(AUTH_START) != 1 or body.count(AUTH_END) != 1:
        raise AIContractAdapterError("Architect card requires exactly one AI.Contract authorization block")
    try:
        value = json.loads(body.split(AUTH_START, 1)[1].split(AUTH_END, 1)[0])
    except json.JSONDecodeError as error:
        raise AIContractAdapterError("AI.Contract authorization block is invalid JSON") from error
    if not isinstance(value, dict) or set(value) != {"repository", "api_target", "issue_title", "issue_body"}:
        raise AIContractAdapterError("AI.Contract authorization has unsupported or missing fields")
    if value["repository"] != REPOSITORY or value["api_target"] != API_TARGET:
        raise AIContractAdapterError("AI.Contract authorization must bind stemarie/AI.Contract exactly")
    if not isinstance(value["issue_title"], str) or not value["issue_title"].strip() or len(value["issue_title"]) > 256:
        raise AIContractAdapterError("AI.Contract title is invalid")
    if not isinstance(value["issue_body"], str) or not value["issue_body"].strip() or len(value["issue_body"]) > 60000:
        raise AIContractAdapterError("AI.Contract body is invalid")
    return value


def expected_body(card: dict[str, Any], scope: dict[str, str]) -> str:
    return f"{marker_for(card['id'])}\n{scope['issue_body']}"


def exact_readback(issue: Any, card: dict[str, Any], scope: dict[str, str]) -> dict[str, Any]:
    if not isinstance(issue, dict) or issue.get("title") != scope["issue_title"] or issue.get("body") != expected_body(card, scope):
        raise AIContractAdapterError("AI.Contract Issue read-back does not exactly bind Architect card")
    number = issue.get("number")
    if isinstance(number, bool) or not isinstance(number, int) or number < 1:
        raise AIContractAdapterError("AI.Contract Issue read-back has invalid number")
    return {"repository": REPOSITORY, "issue": number}


def execute(card: dict[str, Any], request: Callable[[str, str, dict[str, Any] | None], Any]) -> dict[str, Any]:
    scope = authorization(card)
    repo = request("GET", API_TARGET, None)
    if not isinstance(repo, dict) or repo.get("full_name") != REPOSITORY or repo.get("default_branch") != "main":
        raise AIContractAdapterError("AI.Contract repository read-back is invalid")
    issues = request("GET", API_TARGET + "/issues?state=all&per_page=100", None)
    if not isinstance(issues, list) or not all(isinstance(issue, dict) for issue in issues):
        raise AIContractAdapterError("AI.Contract Issues listing is malformed")
    matches = [issue for issue in issues if marker_for(card["id"]) in str(issue.get("body", ""))]
    if len(matches) > 1:
        raise AIContractAdapterError("multiple contract Issues match Architect card marker")
    if matches:
        result = exact_readback(request("GET", API_TARGET + f"/issues/{matches[0].get('number')}", None), card, scope)
        return {"operation": "idempotent-readback", **result}
    created = request("POST", API_TARGET + "/issues", {"title": scope["issue_title"], "body": expected_body(card, scope)})
    result = exact_readback(created, card, scope)
    exact_readback(request("GET", API_TARGET + f"/issues/{result['issue']}", None), card, scope)
    return {"operation": "created-and-read-back", **result}


def token() -> str:
    env_file = Path.home() / ".hermes" / "profiles" / PROFILE / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise AIContractAdapterError("Architect credential helper configuration is unreadable") from error
    for line in lines:
        if line.startswith("GITHUB_TOKEN="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise AIContractAdapterError("Architect credential helper configuration lacks a token")


def api(method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
    if method not in {"GET", "POST"} or not url.startswith(API_TARGET):
        raise AIContractAdapterError("AI.Contract API operation is outside adapter authority")
    request = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode("utf-8"), method=method, headers={"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise AIContractAdapterError(f"GitHub {method} {url} returned HTTP {error.code}") from error


def live_card(task_id: str) -> dict[str, Any]:
    import subprocess
    run = subprocess.run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"], capture_output=True, text=True, check=False, timeout=30)
    try:
        value = json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise AIContractAdapterError("could not read Architect Kanban card") from error
    if run.returncode or not isinstance(value, dict) or not isinstance(value.get("task"), dict) or value["task"].get("id") != task_id:
        raise AIContractAdapterError("could not read Architect Kanban card")
    return value["task"]


def main() -> int:
    task_id = os.environ.get("HERMES_KANBAN_TASK")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise AIContractAdapterError("adapter requires its assigned canonical HERMES_KANBAN_TASK")
    print(json.dumps(execute(live_card(task_id), api), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AIContractAdapterError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
