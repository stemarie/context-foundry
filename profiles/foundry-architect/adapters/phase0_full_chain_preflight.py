#!/usr/bin/env python3
"""Read-only, task-bound readiness preflight for a Phase 0 Architect packet."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

PROFILE = "foundry-architect"
TASK_ID = re.compile(r"t_[0-9a-f]{8}\Z")
SHA = re.compile(r"[0-9a-f]{40}\Z")
AICONTRACT_START = "<!-- FOUNDRY_ARCHITECT_AICONTRACT_AUTHORIZATION_V1\n"
ISSUE_START = "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n"
PREFLIGHT_START = "<!-- FOUNDRY_PHASE0_FULL_CHAIN_PREFLIGHT_V1\n"
BLOCK_END = "-->"
REQUIRED_DOCUMENT_IDS = ("1C8tLVdqncOkTbaIkfXfrn7U8lzr-XeZQyM7SikqO7M8", "1B5hQiaKm6KCZLv0kDe4FQS_18ZReePDq8_yMusA0L98")


class PreflightError(RuntimeError):
    pass


def block(body: Any, start: str, label: str) -> dict[str, Any]:
    if not isinstance(body, str) or body.count(start) != 1 or body.count(BLOCK_END) < 3:
        raise PreflightError(f"{label} authorization block is missing or ambiguous")
    raw = body.split(start, 1)[1].split(BLOCK_END, 1)[0]
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as error:
        raise PreflightError(f"{label} authorization block is invalid JSON") from error
    if not isinstance(value, dict):
        raise PreflightError(f"{label} authorization block is invalid")
    return value


def exact(value: dict[str, Any], keys: set[str], label: str) -> dict[str, Any]:
    if set(value) != keys:
        raise PreflightError(f"{label} authorization has unsupported or missing fields")
    return value


def preflight(card: dict[str, Any], git: Callable[..., str]) -> dict[str, Any]:
    if card.get("assignee") != PROFILE or not str(card.get("title", "")).startswith("Architect:"):
        raise PreflightError("card is not an assigned Architect card")
    if card.get("status") != "running":
        raise PreflightError("card is not in the initial running lifecycle")
    task_id = card.get("id")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise PreflightError("card task ID is invalid")
    body = card.get("body")
    contract = exact(block(body, AICONTRACT_START, "AI.Contract"), {"repository", "api_target", "issue_title", "issue_body"}, "AI.Contract")
    if contract["repository"] != "stemarie/AI.Contract" or contract["api_target"] != "https://api.github.com/repos/stemarie/AI.Contract":
        raise PreflightError("AI.Contract authorization is not canonically bound")
    tracker = exact(block(body, ISSUE_START, "tracker Issue"), {"repository", "origin", "api_target", "branch", "issue_title", "issue_body"}, "tracker Issue")
    packet = exact(block(body, PREFLIGHT_START, "preflight"), {"repository", "origin", "branch", "frozen_base", "document_ids"}, "preflight")
    if tracker["repository"] != packet["repository"] or tracker["origin"] != packet["origin"] or tracker["branch"] != packet["branch"]:
        raise PreflightError("tracker and preflight bindings disagree")
    if packet["repository"] != "stemarie/mentorship-platform" or packet["origin"] != "https://github.com/stemarie/mentorship-platform.git" or packet["branch"] != "main":
        raise PreflightError("preflight target is outside the authorized mentorship-platform binding")
    if not isinstance(packet["frozen_base"], str) or not SHA.fullmatch(packet["frozen_base"]):
        raise PreflightError("preflight frozen base is invalid")
    if packet["document_ids"] != list(REQUIRED_DOCUMENT_IDS):
        raise PreflightError("preflight document binding is invalid")
    workspace = card.get("workspace_path")
    if not isinstance(workspace, str) or not workspace:
        raise PreflightError("card has no target workspace")
    if git(workspace, "remote", "get-url", "origin") != packet["origin"]:
        raise PreflightError("workspace origin differs from the authorized target")
    remote = git(workspace, "ls-remote", "origin", "refs/heads/main").split()
    if len(remote) != 2 or remote[1] != "refs/heads/main" or remote[0] != packet["frozen_base"]:
        raise PreflightError("remote main differs from the frozen base")
    for name in ("task_bound_aicontract.py", "task_bound_issue.py"):
        if not (Path(__file__).resolve().parent / name).is_file():
            raise PreflightError(f"required adapter is absent: {name}")
    return {"operation": "phase0-full-chain-preflight", "task_id": task_id, "target": {"repository": packet["repository"], "origin": packet["origin"], "branch": packet["branch"], "frozen_base": packet["frozen_base"]}, "packet_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(), "verdict": "PASS"}


def git_output(workspace: str, *args: str) -> str:
    run = subprocess.run(["git", "-C", workspace, *args], capture_output=True, text=True, check=False, timeout=30)
    if run.returncode:
        raise PreflightError("could not read target Git state")
    return run.stdout.strip()


def live_card(task_id: str) -> dict[str, Any]:
    run = subprocess.run(["hermes", "kanban", "--board", "context-foundry", "show", task_id, "--json"], capture_output=True, text=True, check=False, timeout=30)
    try:
        value = json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise PreflightError("could not read Architect card") from error
    if run.returncode or not isinstance(value, dict) or not isinstance(value.get("task"), dict):
        raise PreflightError("could not read Architect card")
    return value["task"]


def main() -> int:
    task_id = os.environ.get("HERMES_KANBAN_TASK")
    if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
        raise PreflightError("adapter requires its assigned HERMES_KANBAN_TASK")
    print(json.dumps(preflight(live_card(task_id), git_output), sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PreflightError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
