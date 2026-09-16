#!/usr/bin/env python3
"""Exact-task, authenticated GET-only evidence reader for Career OS #9."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping

BOARD = "context-foundry"
PROFILE = "foundry-auditor"
TASK_ID = "t_ea213115"
PARENT_ID = "t_8df82916"
TITLE = "Architect: execute transported draft handoff t_8df82916"
PACKET_BODY = "FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution\n\nfixture packet"
PACKET_SHA256 = "9b45b3c14cc0624b106c266cd78c06b8264966b2a675bc4c97a7522f6ae19c28"
CONTRACT_URL = "https://github.com/stemarie/AI.Contract/issues/50"
TRACKER_URL = "https://github.com/stemarie/mentorship-platform/issues/9"
CONTRACT_ENDPOINT = "https://api.github.com/repos/stemarie/AI.Contract/issues/50"
TRACKER_ENDPOINT = "https://api.github.com/repos/stemarie/mentorship-platform/issues/9"
CANONICAL_MARKER = "<!-- FOUNDRY-ARCHITECT-TASK-BOUND-ISSUE-ADAPTER-V1:t_5085d58e -->"
PHASE_MARKER = "FOUNDRY_CAREER_OS_PHASE0_DECISION_RECORDS_V1"
TRACKER_MARKER = "<!-- FOUNDRY_CAREER_OS_PHASE0_DECISION_RECORDS_TRACKER:t_5085d58e -->"
TRACKER_TITLE = "Career OS Phase 0 decision records — ADR set, database migration strategy, and test strategy"
CONTRACT_SHA256 = "2034905f7ca37ea0d88094c35dadb3eadfd7228b6d6e42c0512a0cddf20e10e0"
TRACKER_SHA256 = "d7b377da1637f9f6052bd1788e693e551b565bd1cb1749ed398508bcc9e9417b"
ENDPOINTS = frozenset((CONTRACT_ENDPOINT, TRACKER_ENDPOINT))


class ReadError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ReadError(code)


def token() -> str:
    try:
        lines = (Path.home() / ".hermes/profiles" / PROFILE / ".env").read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ReadError("credential-helper") from error
    for line in lines:
        if line.startswith("GITHUB_TOKEN="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise ReadError("credential-helper")


def live_envelope(task_id: str) -> dict[str, Any]:
    import subprocess
    completed = subprocess.run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"], capture_output=True, text=True, check=False, timeout=30)
    try:
        value = json.loads(completed.stdout) if completed.returncode == 0 else None
    except json.JSONDecodeError:
        value = None
    require(isinstance(value, dict), "card-envelope")
    return value


def validate(environ: Mapping[str, str], envelope: Any) -> None:
    require(environ.get("HERMES_KANBAN_TASK") == TASK_ID, "task-binding")
    require(isinstance(envelope, dict) and isinstance(envelope.get("task"), dict) and envelope.get("parents") == [PARENT_ID], "card-envelope")
    card = envelope["task"]
    require(card.get("id") == TASK_ID and card.get("assignee") == PROFILE and card.get("title") == TITLE, "card-shape")
    body = card.get("body")
    require(isinstance(body, str) and body.startswith("FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution\n"), "card-shape")
    require(hashlib.sha256(body.encode("utf-8")).hexdigest() == PACKET_SHA256, "card-shape")


def get(endpoint: str, access_token: str, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    require(endpoint in ENDPOINTS, "endpoint-binding")
    request = urllib.request.Request(endpoint, method="GET", headers={"Authorization": "Bearer " + access_token, "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with opener(request, timeout=30) as response:
            value = json.load(response)
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, ValueError) as error:
        raise ReadError("http-transport") from error
    require(isinstance(value, dict), "api-response")
    return value


def read(environ: Mapping[str, str], reader: Callable[[str], dict[str, Any]] = live_envelope, credential: Callable[[], str] = token, opener: Callable[..., Any] = urllib.request.urlopen) -> dict[str, Any]:
    validate(environ, reader(TASK_ID))
    access_token = credential()
    try:
        contract = get(CONTRACT_ENDPOINT, access_token, opener)
        tracker = get(TRACKER_ENDPOINT, access_token, opener)
    finally:
        access_token = ""
    contract_body, tracker_body = contract.get("body"), tracker.get("body")
    require(contract.get("number") == 50 and contract.get("html_url") == CONTRACT_URL and contract.get("state") == "open" and isinstance(contract_body, str) and CANONICAL_MARKER in contract_body and PHASE_MARKER in contract_body and hashlib.sha256(contract_body.encode()).hexdigest() == CONTRACT_SHA256, "canonical-contract")
    require(tracker.get("number") == 9 and tracker.get("html_url") == TRACKER_URL and tracker.get("title") == TRACKER_TITLE and tracker.get("state") == "open" and isinstance(tracker_body, str) and TRACKER_MARKER in tracker_body and CONTRACT_URL in tracker_body and hashlib.sha256(tracker_body.encode()).hexdigest() == TRACKER_SHA256, "tracker")
    return {"operation": "task-bound-phase0-audit-read", "operations": ["GET"], "task_id": TASK_ID, "contract": {"issue": 50, "url": CONTRACT_URL, "body_sha256": CONTRACT_SHA256}, "tracker": {"issue": 9, "url": TRACKER_URL, "body_sha256": TRACKER_SHA256}, "verdict": "PASS"}


def main() -> int:
    try:
        print(json.dumps(read(os.environ), sort_keys=True, separators=(",", ":")))
        return 0
    except ReadError as error:
        print(json.dumps({"failure_code": str(error), "operation": "task-bound-phase0-audit-read", "verdict": "FAIL"}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2
    except Exception:
        print(json.dumps({"failure_code": "secret-safety", "operation": "task-bound-phase0-audit-read", "verdict": "FAIL"}, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
