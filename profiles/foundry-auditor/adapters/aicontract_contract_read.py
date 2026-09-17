#!/usr/bin/env python3
"""Task-bound, read-only V2 verification for a Foundry Integration Auditor contract."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import Any

PROFILE = "foundry-auditor"
BOARD = "context-foundry"
ROLE = "Integration Auditor"
TITLE_PREFIX = "Integration Auditor:"
CLIENT = "/home/karell/.hermes/scripts/aicontract_book_client.sh"
TASK_ID_RE = re.compile(r"^t_[0-9a-f]{8}$")
IDENTITY_RE = re.compile(r"^AI\.Contract: ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}) revision ([1-9][0-9]*)$")


class ContractReadError(RuntimeError):
    pass


def _run(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, capture_output=True, text=True, check=False, timeout=30)
    if result.returncode:
        raise ContractReadError("task-bound canonical GET failed")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise ContractReadError("canonical GET returned invalid JSON") from error
    if not isinstance(value, dict):
        raise ContractReadError("canonical GET returned malformed JSON")
    return value


def live_card(task_id: str) -> dict[str, Any]:
    value = _run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"]).get("task")
    if not isinstance(value, dict) or value.get("id") != task_id:
        raise ContractReadError("Integration Auditor card response was malformed")
    if value.get("assignee") != PROFILE or not str(value.get("title", "")).startswith(TITLE_PREFIX):
        raise ContractReadError("assigned card is not a Foundry Integration Auditor card")
    return value


def identity(card: dict[str, Any]) -> tuple[str, int]:
    lines = str(card.get("body", "")).splitlines()
    if len(lines) != 4:
        raise ContractReadError("Integration Auditor card must contain exactly four V2 routing lines")
    match = IDENTITY_RE.fullmatch(lines[0])
    if not match or lines[1] != "Role: Integration Auditor" or not lines[2].startswith("Dependency: ") or not lines[2][12:] or not lines[3].startswith("Receipt pointer: ") or not lines[3][17:]:
        raise ContractReadError("Integration Auditor V2 routing envelope is malformed")
    return match.group(1), int(match.group(2))


def execute(card: dict[str, Any]) -> dict[str, Any]:
    contract_id, revision = identity(card)
    contract = _run([CLIENT, "auditor", "GET", f"/api/v1/contracts/{contract_id}"]).get("contract")
    frozen = _run([CLIENT, "auditor", "GET", f"/api/v1/chain-contracts/{contract_id}/frozen"]).get("frozen_revision")
    if not isinstance(contract, dict) or not isinstance(frozen, dict) or contract.get("id") != contract_id or contract.get("status") != "In Progress" or frozen.get("revision") != revision or not isinstance(frozen.get("digest"), str):
        raise ContractReadError("canonical V2 contract is not the assigned active revision")
    return {"operation": "integration-auditor-task-bound-v2-contract-read", "contract_id": contract_id, "revision": revision, "digest": frozen["digest"], "status": contract["status"]}


def main() -> None:
    task_id = os.environ.get("HERMES_KANBAN_TASK")
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise ContractReadError("adapter requires its assigned canonical HERMES_KANBAN_TASK")
    print(json.dumps(execute(live_card(task_id)), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except ContractReadError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
