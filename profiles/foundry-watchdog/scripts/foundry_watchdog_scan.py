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
RELEVANT_STATUSES = {"ready", "running", "blocked", "review", "done"}


def identity(body: object) -> dict[str, str]:
    text = str(body or "")
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


def relevant_tasks(tasks: object) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if isinstance(tasks, dict):
        tasks = tasks.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("Kanban list response must be an array or contain tasks")
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for task in tasks:
        if not isinstance(task, dict) or not ROLE_RE.match(str(task.get("title", ""))):
            continue
        body = str(task.get("body") or "")
        scoped = "external contract:" in body.lower()
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
    records, errors = relevant_tasks(load_tasks(args.input))
    if not records and not errors:
        return 0
    payload: dict[str, Any] = {"board": BOARD, "events": records, "version": 1}
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
