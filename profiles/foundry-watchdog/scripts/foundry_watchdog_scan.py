#!/usr/bin/env python3
"""Read-only preflight for the Context Foundry Watchdog.

The scanner emits a canonical JSON payload only when board data contains a
relevant, contract-identified lifecycle state.  It never writes board or local
state.  A caller supplies the prior digest file to suppress unchanged output.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BOARD = "context-foundry"
ROLE_RE = re.compile(r"^(Architect|Worker|Candidate Auditor|Delivery|Closure Auditor):")
GITHUB_ISSUE_RE = re.compile(r"^https://github\.com/stemarie/context-foundry/issues/(\d+)$")
CURRENT_CONTRACT_RE = re.compile(r"^Canonical external contract: (https://github\.com/[^\s]+/issues/\d+)$", re.MULTILINE)
CURRENT_REVISION_RE = re.compile(
    r"^Contract ID/revision: Issue #(\d+) / ([^/\n]+?)(?: / ([0-9a-f]{64}))?$", re.MULTILINE
)
LEGACY_CONTRACT_RE = re.compile(r"^External contract: (https://github\.com/[^\s]+/issues/\d+)$", re.MULTILINE)
LEGACY_REVISION_RE = re.compile(
    r"^Contract identity/revision: Issue #(\d+); `([^`]+)`; body SHA-256 `([0-9a-f]{64})`\.$",
    re.MULTILINE,
)
AI_CONTRACT_V2_RE = re.compile(
    r"^AI\.Contract: `([0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})` revision ([1-9][0-9]*)$",
    re.MULTILINE,
)
RELEVANT_STATUSES = {"ready", "running", "blocked", "review", "done"}
DRAFT_HANDOFF_MARKER = "FOUNDRY_DRAFT_HANDOFF_V1"
DRAFT_HANDOFF_KIND = "Handoff kind: contract_execution"


def identity(body: object) -> dict[str, str]:
    text = str(body or "")
    v2 = AI_CONTRACT_V2_RE.search(text)
    if v2:
        contract_id, revision = v2.groups()
        return {
            "protocol": "ai_contract_v2",
            "id": contract_id,
            "revision": revision,
            "url": f"ai-contract://contracts/{contract_id}",
            "issue": contract_id,
            "marker": f"revision-{revision}",
            "sha256": "",
        }
    contract = CURRENT_CONTRACT_RE.search(text) or LEGACY_CONTRACT_RE.search(text)
    revision = CURRENT_REVISION_RE.search(text) or LEGACY_REVISION_RE.search(text)
    if not contract or not revision:
        raise ValueError("missing canonical contract identity")
    issue_url = GITHUB_ISSUE_RE.fullmatch(contract.group(1))
    if not issue_url or issue_url.group(1) != revision.group(1):
        raise ValueError("unrecognized or mismatched canonical contract identity")
    return {
        "url": contract.group(1),
        "issue": revision.group(1),
        "marker": revision.group(2).strip(),
        "sha256": revision.group(3) or "",
    }


def lifecycle_evidence(task: dict[str, Any]) -> dict[str, Any]:
    """Keep compact evidence that makes lifecycle changes observable."""
    evidence: dict[str, Any] = {}
    events = task.get("events")
    if isinstance(events, list):
        evidence["events"] = [
            {key: event[key] for key in ("kind", "created_at", "payload") if key in event}
            for event in events if isinstance(event, dict)
        ]
    runs = task.get("runs")
    if isinstance(runs, list):
        evidence["runs"] = [
            {key: run[key] for key in ("id", "status", "outcome", "summary", "result", "metadata", "ended_at") if key in run}
            for run in runs if isinstance(run, dict)
        ]
    return evidence


def has_live_execution_child(task: dict[str, Any]) -> bool:
    children = task.get("children")
    if not isinstance(children, list):
        return False
    return any(
        isinstance(child, dict)
        and str(child.get("title", "")).startswith("Architect: execute")
        and str(child.get("status", "")) not in {"archived", "cancelled"}
        for child in children
    )


def draft_handoff_record(task: dict[str, Any]) -> dict[str, str] | None:
    """Identify a completed local draft which lacks its execution handoff.

    The scanner may receive list-only task records without children. In that
    conservative case it emits the lead and the Watchdog must re-show the card
    before it creates anything.
    """
    if str(task.get("status", "")) != "done":
        return None
    if not str(task.get("title", "")).startswith("Architect: draft"):
        return None
    body = str(task.get("body") or "")
    if DRAFT_HANDOFF_MARKER not in body or DRAFT_HANDOFF_KIND not in body:
        return None
    if has_live_execution_child(task):
        return None
    events = task.get("events")
    if not isinstance(events, list) or not any(
        isinstance(event, dict) and event.get("kind") == "completed" for event in events
    ):
        return None
    return {"id": str(task.get("id", "")), "kind": "draft_handoff_missing"}


def relevant_tasks(tasks: object) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("Kanban list response must be an array or contain tasks")
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    handoffs: list[dict[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        handoff = draft_handoff_record(task)
        if handoff:
            handoffs.append(handoff)
        if not ROLE_RE.match(str(task.get("title", ""))):
            continue
        body = str(task.get("body") or "")
        scoped = "external contract:" in body.lower() or AI_CONTRACT_V2_RE.search(body) is not None
        if not scoped:
            continue
        try:
            contract = identity(body)
        except ValueError as exc:
            errors.append({"id": str(task.get("id", "")), "error": str(exc)})
            continue
        status = str(task.get("status", ""))
        if status not in RELEVANT_STATUSES:
            continue
        evidence = lifecycle_evidence(task)
        # A historical done card alone is not new work. Its completion evidence
        # is meaningful, however, and changes to it must affect the digest.
        if status == "done" and not evidence:
            continue
        record: dict[str, Any] = {
            "contract": contract,
            "id": str(task.get("id", "")),
            "status": status,
            "title": str(task.get("title", "")),
        }
        if evidence:
            record["lifecycle"] = evidence
        records.append(record)
    return (
        sorted(records, key=lambda item: (item["contract"]["url"], item["id"])),
        sorted(errors, key=lambda item: item["id"]),
        sorted(handoffs, key=lambda item: item["id"]),
    )


def digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_tasks(input_path: Path | None) -> object:
    if input_path:
        return json.loads(input_path.read_text(encoding="utf-8"))
    hermes = os.environ.get("HERMES_BIN", "hermes")
    result = subprocess.run(
        [hermes, "kanban", "--board", BOARD, "list", "--json"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise RuntimeError("kanban list failed")
    return json.loads(result.stdout)


def previous_digest(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="JSON fixture instead of live Kanban")
    parser.add_argument("--previous-digest-file", type=Path)
    args = parser.parse_args()
    records, errors, handoffs = relevant_tasks(load_tasks(args.input))
    if not records and not errors and not handoffs:
        return 0
    payload: dict[str, Any] = {"board": BOARD, "events": [*records, *handoffs], "version": 1}
    if errors:
        payload["scanner_status"] = "non_healthy"
        payload["scanner_errors"] = errors
    payload_digest = digest(payload)
    if payload_digest == previous_digest(args.previous_digest_file):
        return 0
    print(json.dumps({**payload, "digest": payload_digest}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"board": BOARD, "scanner_error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
