#!/usr/bin/env python3
"""Create one exact Architect execution child from a completed local draft.

This is a board-only, idempotent recovery primitive. It validates the attached
Architect-authored packet before it creates a child; it never calls GitHub,
reads credentials, or performs any external-contract operation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

BOARD = "context-foundry"
DRAFT_MARKER = "FOUNDRY_DRAFT_HANDOFF_V1"
HANDOFF_KIND = "Handoff kind: contract_execution"
AUTH_OPEN = "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n"
AUTH_CLOSE = "\n-->"
AUTH_KEYS = {"repository", "origin", "api_target", "branch", "issue_title", "issue_body"}


class HandoffError(RuntimeError):
    pass


def run(command: list[str]) -> dict[str, Any]:
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        raise HandoffError(completed.stderr.strip() or "Hermes Kanban command failed")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise HandoffError("Hermes Kanban returned malformed JSON") from exc


def show(task_id: str) -> dict[str, Any]:
    return run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"])


def is_execution_child(child: object) -> bool:
    return (
        isinstance(child, dict)
        and str(child.get("title", "")).startswith("Architect: execute")
        and str(child.get("status", "")) not in {"archived", "cancelled"}
    )


def has_live_execution_child(children: object) -> bool:
    if not isinstance(children, list):
        return False
    for child in children:
        if is_execution_child(child):
            return True
        if isinstance(child, str):
            candidate = show(child).get("task")
            if is_execution_child(candidate):
                return True
    return False


def authorized_packet(packet: str) -> str:
    local_header = f"{DRAFT_MARKER}\n{HANDOFF_KIND}\n"
    local_requirements = (
        "## Bounded source change",
        "profiles/foundry-architect/adapters/",
        "Do not modify any target-repository checkout, the AI.Contract or target tracker, cards, credentials",
        "## Deterministic test contract",
        "## Explicit non-goals",
    )
    if packet.startswith(local_header) and all(required in packet for required in local_requirements):
        return packet
    validate_packet(packet)
    return packet


def attached_packet(draft: dict[str, Any]) -> str:
    task = draft.get("task")
    if not isinstance(task, dict):
        raise HandoffError("missing draft task")
    task_id = str(task.get("id", ""))
    artifacts: list[str] = []
    for event in draft.get("events", []):
        if not isinstance(event, dict) or event.get("kind") != "completed":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict) and isinstance(payload.get("artifacts"), list):
            artifacts.extend(str(item) for item in payload["artifacts"])
    packets = [Path(path) for path in artifacts if path.endswith("-contract-packet.md")]
    if len(packets) != 1:
        raise HandoffError("draft must have exactly one contract-packet artifact")
    packet = packets[0]
    expected_directory = Path.home() / ".hermes/kanban/boards" / BOARD / "attachments" / task_id
    try:
        packet.resolve().relative_to(expected_directory.resolve())
    except ValueError as exc:
        raise HandoffError("draft packet is outside the board attachment directory") from exc
    try:
        return packet.read_text(encoding="utf-8")
    except OSError as exc:
        raise HandoffError("draft packet cannot be read") from exc


def validate_packet(packet: str) -> None:
    if packet.count(AUTH_OPEN) != 1 or packet.count(AUTH_CLOSE) != 1:
        raise HandoffError("draft packet has no unique strict authorization block")
    encoded = packet.split(AUTH_OPEN, 1)[1].split(AUTH_CLOSE, 1)[0]
    try:
        authorization = json.loads(encoded)
    except json.JSONDecodeError as exc:
        raise HandoffError("draft authorization is not valid JSON") from exc
    if not isinstance(authorization, dict) or set(authorization) != AUTH_KEYS:
        raise HandoffError("draft authorization has an invalid key set")
    if not all(isinstance(authorization[key], str) and authorization[key] for key in AUTH_KEYS):
        raise HandoffError("draft authorization has an empty or non-string field")


def workspace_for_packet(packet: str) -> str:
    """Map a target-authorized packet to its deterministic target worktree base."""
    encoded = packet.split(AUTH_OPEN, 1)[1].split(AUTH_CLOSE, 1)[0]
    authorization = json.loads(encoded)
    repository = authorization["repository"]
    origin = authorization["origin"]
    if not isinstance(repository, str) or not isinstance(origin, str) or repository.count("/") != 1:
        raise HandoffError("draft authorization has no target repository binding")
    owner, name = repository.split("/", 1)
    if not owner.replace("-", "").replace("_", "").isalnum() or not name.replace("-", "").replace("_", "").replace(".", "").isalnum():
        raise HandoffError("draft authorization repository is invalid")
    if origin != f"https://github.com/{repository}.git":
        raise HandoffError("draft authorization origin does not match repository")
    return "worktree:" + str(Path.home() / ".hermes/work/targets" / f"{owner}__{name}")


def finalize(draft_id: str, allow_legacy: bool = False) -> dict[str, str]:
    draft = show(draft_id)
    task = draft.get("task")
    if not isinstance(task, dict):
        raise HandoffError("missing draft task")
    if task.get("status") != "done" or not str(task.get("title", "")).startswith("Architect: draft"):
        raise HandoffError("task is not a completed Architect draft")
    body = str(task.get("body") or "")
    if (DRAFT_MARKER not in body or HANDOFF_KIND not in body) and not allow_legacy:
        raise HandoffError("task is not an opted-in draft handoff")
    if has_live_execution_child(draft.get("children")):
        return {"status": "already_routed", "draft_id": draft_id}

    packet = attached_packet(draft)
    authorized_packet(packet)
    workspace = "scratch" if packet.startswith(f"{DRAFT_MARKER}\n{HANDOFF_KIND}\n") else workspace_for_packet(packet)
    digest = hashlib.sha256(packet.encode("utf-8")).hexdigest()
    created = run([
        "hermes", "kanban", "--board", BOARD, "create",
        "Architect: execute transported draft handoff " + draft_id,
        "--body", packet,
        "--assignee", "foundry-architect",
        "--parent", draft_id,
        "--workspace", workspace,
        "--created-by", "foundry-watchdog",
        "--completion-contract", "local-only",
        "--idempotency-key", f"foundry-draft-handoff:{draft_id}:{digest}",
        "--json",
    ])
    execution_id = str(created.get("id", ""))
    if not execution_id:
        raise HandoffError("created handoff has no task ID")
    execution = show(execution_id)
    execution_task = execution.get("task")
    parents = execution.get("parents")
    parent_ids = {
        str(parent.get("id", "")) if isinstance(parent, dict) else str(parent)
        for parent in parents
    } if isinstance(parents, list) else set()
    if not isinstance(execution_task, dict) or execution_task.get("body") != packet or draft_id not in parent_ids:
        raise HandoffError("execution card read-back did not preserve the exact packet and parent")
    return {"status": "created", "draft_id": draft_id, "execution_id": execution_id, "packet_sha256": digest}


def finalize_scan_payload(payload: object) -> list[dict[str, str]]:
    if not isinstance(payload, dict) or payload.get("board") != BOARD:
        raise HandoffError("scan payload is not for the Context Foundry board")
    events = payload.get("events")
    if not isinstance(events, list):
        raise HandoffError("scan payload has no events array")
    results: list[dict[str, str]] = []
    for event in events:
        if isinstance(event, dict) and event.get("kind") == "draft_handoff_missing":
            draft_id = str(event.get("id", ""))
            if not draft_id:
                raise HandoffError("draft handoff event has no task ID")
            results.append(finalize(draft_id))
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("draft_id", nargs="?")
    target.add_argument("--scan-payload", action="store_true", help="consume a Watchdog scanner payload from stdin")
    parser.add_argument("--allow-legacy", action="store_true", help="one-time operator recovery for a pre-marker draft")
    args = parser.parse_args(argv)
    try:
        if args.scan_payload:
            print(json.dumps(finalize_scan_payload(json.load(sys.stdin)), sort_keys=True))
        else:
            print(json.dumps(finalize(args.draft_id, allow_legacy=args.allow_legacy), sort_keys=True))
        return 0
    except HandoffError as exc:
        print(json.dumps({"status": "error", "draft_id": args.draft_id, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
