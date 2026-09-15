#!/usr/bin/env python3
"""Read-only preflight for the Context Foundry Watchdog.

The scanner emits deterministic recovery actions and observation-only evidence,
including malformed maintenance packets. It never writes board, source or local
state. A caller supplies the prior notification digest to suppress unchanged
notifications; --inspect keeps unresolved work visible without notifying.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

BOARD = "context-foundry"
PAGE_SIZE = 256
MAX_RECORDS = 100000
ROLE_RE = re.compile(r"^(Architect|Worker|Candidate Auditor|Capability Auditor|Post-delivery Auditor|Delivery|Closure Auditor):")
GITHUB_ISSUE_RE = re.compile(r"^https://github\.com/stemarie/AI\.Contract/issues/(\d+)$")
CURRENT_CONTRACT_RE = re.compile(r"^Canonical external contract: (https://github\.com/[^\s]+/issues/\d+)$", re.MULTILINE)
CURRENT_REVISION_RE = re.compile(
    r"^Contract ID/revision: Issue #(\d+) / ([^/\n]+?)(?: / ([0-9a-f]{64}))?$", re.MULTILINE
)
LEGACY_CONTRACT_RE = re.compile(r"^External contract: (https://github\.com/[^\s]+/issues/\d+)$", re.MULTILINE)
LEGACY_REVISION_RE = re.compile(
    r"^Contract identity/revision: Issue #(\d+); `([^`]+)`; body SHA-256 `([0-9a-f]{64})`\.$",
    re.MULTILINE,
)
RELEVANT_STATUSES = {"todo", "triage", "scheduled", "ready", "running", "blocked", "review", "done", "archived"}


def identity(body: object) -> dict[str, str]:
    text = str(body or "")
    contracts = re.findall(r"^(?:Canonical external contract|External contract):.*$", text, re.MULTILINE)
    revisions = re.findall(r"^(?:Contract ID/revision|Contract identity/revision):.*$", text, re.MULTILINE)
    if len(contracts) != 1 or len(revisions) != 1:
        raise ValueError("missing or duplicate canonical contract identity")
    contract = CURRENT_CONTRACT_RE.search(text)
    revision = CURRENT_REVISION_RE.search(text) if contract else LEGACY_REVISION_RE.search(text)
    contract = contract or LEGACY_CONTRACT_RE.search(text)
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
    for key in evidence:
        evidence[key].sort(key=lambda row: json.dumps(row, sort_keys=True, separators=(",", ":")))
    return evidence


def latest_receipt(runs: object) -> tuple[str | None, str | None, str | None]:
    """Only a uniquely latest completed root run can attest a verdict."""
    if not isinstance(runs, list) or not runs or any(not isinstance(r, dict) for r in runs):
        return None, None, "missing or malformed root runs"
    roots = [r for r in runs if r.get("parent_run_id") is None]
    ids = [str(r.get("id", "")) for r in roots]
    if not roots or any(not i or i == "None" for i in ids) or len(set(ids)) != len(ids):
        return None, None, "missing or duplicate root run identity"
    if len(roots) > 1:
        if any(type(r.get("started_at")) not in (int, float) for r in roots):
            return None, None, "ambiguous root run ordering"
        newest = max(r["started_at"] for r in roots)
        roots = [r for r in roots if r["started_at"] == newest]
    if len(roots) != 1:
        return None, None, "ambiguous root run ordering"
    latest = roots[0]
    rid = str(latest["id"])
    if latest.get("status") not in {"done", "completed"} or latest.get("outcome") not in (None, "completed"):
        return rid, None, "latest root run is not completed"
    if latest.get("profile") != "foundry-auditor":
        return rid, None, "root run is not owned by foundry-auditor"
    metadata = latest.get("metadata")
    verdict = metadata.get("verdict") if isinstance(metadata, dict) else None
    if verdict not in ("PASS", "REQUEST_CHANGES", "BLOCKED_WITH_EVIDENCE"):
        return rid, None, "missing or invalid structured verdict"
    return rid, verdict, None


def normalize(task: dict[str, Any]) -> dict[str, Any]:
    if isinstance(task.get("task"), dict):
        # The show envelope's root arrays are authoritative, never nested task.runs.
        return {**task["task"], **{k: task.get(k, []) for k in ("runs", "events", "parents", "children")}}
    return task


def role_identity(task: dict[str, Any]) -> tuple[str, bool]:
    title = ROLE_RE.match(str(task.get("title", "")))
    fields = re.findall(r"^Role: (.+)$", str(task.get("body") or ""), re.MULTILINE)
    role = fields[0] if fields else (title.group(1) if title else "")
    if not role and task.get("assignee") == "foundry-auditor":
        role = "Unclassified Auditor"
    known = ROLE_RE.fullmatch(role + ":") is not None
    owner = "auditor" if "Auditor" in role else ("architect" if role == "Architect" else "worker")
    created = [event for event in task.get("events", [])
               if isinstance(event, dict) and event.get("kind") == "created"]
    event_skills = (created[0].get("payload", {}).get("skills")
                    if len(created) == 1 and isinstance(created[0].get("payload"), dict) else None)
    # Creation-time skills cannot substitute for current authoritative task skills.
    skills = task.get("skills")
    skills_consistent = (len(created) <= 1 and isinstance(skills, list)
                         and all(isinstance(skill, str) for skill in skills)
                         and (event_skills is None or event_skills == skills))
    trusted = (known and skills_consistent and len(fields) <= 1 and (not title or title.group(1) == role)
               and task.get("assignee") == "foundry-" + owner
               and "context-foundry-" + owner in (skills or []))
    return role, trusted


def relevant_tasks(tasks: object) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if isinstance(tasks, dict):
        if tasks.get("has_more") or tasks.get("next_cursor") or tasks.get("next_page"):
            raise ValueError("incomplete task snapshot")
        if "total" in tasks and tasks["total"] != len(tasks.get("tasks", [])):
            raise ValueError("incomplete task snapshot: total mismatch")
        tasks = [tasks] if "task" in tasks else tasks.get("tasks", [])
    if not isinstance(tasks, list):
        raise ValueError("Kanban list response must be an array or contain tasks")
    unique = {}
    for raw in tasks:
        if not isinstance(raw, dict):
            raise ValueError("malformed task record")
        task = normalize(raw)
        tid = task.get("id")
        if not isinstance(tid, str) or not tid:
            raise ValueError("missing task identity")
        if tid in unique and task != unique[tid]:
            raise ValueError("conflicting duplicate task identity: " + tid)
        unique[tid] = task
    tasks = list(unique.values())
    records: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for raw in tasks:
        if not isinstance(raw, dict):
            raise ValueError("malformed task record")
        task = normalize(raw)
        role, trusted = role_identity(task)
        if not role:
            continue
        body = str(task.get("body") or "")
        # Title is only an observation hint, never authority. Assigned Foundry
        # auditors remain visible even when their maintenance packet lacks headers.
        if "external contract:" not in body.lower() and not (trusted or task.get("assignee") == "foundry-auditor"):
            continue
        problem = None
        try:
            contract = identity(body)
        except ValueError as exc:
            contract, problem = None, str(exc)
        status = str(task.get("status", ""))
        if status not in RELEVANT_STATUSES:
            continue
        evidence = lifecycle_evidence(task)
        is_audit = "auditor" in role.lower() or task.get("assignee") == "foundry-auditor"
        if status == "done" and not evidence and not is_audit:
            continue
        recovery_class = "product_repair"
        classes = re.findall(r"^Recovery class: (.+)$", body, re.MULTILINE)
        if classes:
            if len(classes) != 1 or classes[0] not in {"product_repair", "direct_maintenance", "reconcile_external_state"}:
                problem = problem or "invalid recovery class"
            else:
                recovery_class = classes[0]
        if role == "Capability Auditor" or (not trusted and "capability" in (role + " " + body).lower()):
            recovery_class = "direct_maintenance"
        elif role in {"Post-delivery Auditor", "Closure Auditor"} and not classes:
            recovery_class = "reconcile_external_state"
        record: dict[str, Any] = {
            "contract": contract, "id": str(task.get("id", "")), "status": status,
            "title": str(task.get("title", "")), "role": role,
            "recovery_class": recovery_class,
        }
        if evidence:
            record["lifecycle"] = evidence
        if is_audit:
            record["run_id"], record["verdict"], receipt_error = latest_receipt(task.get("runs"))
            role_problem = None if trusted else "unverified or conflicting role identity"
            pending = (status in {"todo", "ready", "running", "scheduled", "review"}
                       and (not task.get("runs") or receipt_error == "latest root run is not completed"))
            if pending and not problem and not role_problem:
                record["disposition"] = "audit_pending"
                records.append(record)
                continue
            problem = problem or role_problem or receipt_error
            if status != "done":
                problem = problem or "audit task is not completed"
            if contract and not contract["sha256"] and role != "Closure Auditor":
                problem = problem or "missing contract body hash"
            kind = ("escalate" if problem or record["verdict"] == "BLOCKED_WITH_EVIDENCE" else
                    "direct_maintenance" if recovery_class == "direct_maintenance" else
                    "reconcile_external_state" if record["verdict"] == "PASS" or recovery_class == "reconcile_external_state" else
                    "route_product_repair")
            record["action"] = {"kind": kind, "audit_task_id": record["id"], "reason": problem,
                                "audit_run_id": record["run_id"], "contract": contract}
        elif problem:
            record["action"] = {"kind": "escalate", "reason": problem, "audit_task_id": record["id"],
                                "audit_run_id": None, "contract": contract}
        if status == "archived":
            # Preserve evidence without resurrecting archived work as new tasks.
            record.pop("action", None)
            record["disposition"] = "archived_history"
            if problem:
                record["observation_warning"] = problem
            records.append(record)
            continue
        if is_audit and not problem and record.get("verdict") == "PASS" and role == "Capability Auditor":
            record.pop("action", None)
            record["disposition"] = "audit_pass_not_release_authority"
            record["unresolved"] = False
        if problem:
            errors.append({"id": record["id"], "error": problem})
        if "action" in record:
            record["unresolved"] = True
            record["incident_key"] = "foundry-recovery-v2:" + digest({
                "board": BOARD, "task": record["id"], "run": record.get("run_id"),
                "contract": contract, "role": role, "recovery_class": recovery_class,
            })
            record["action"]["incident_key"] = record["incident_key"]
            if record["action"]["kind"] == "route_product_repair":
                matches = linked_recoveries(record, tasks)
                if matches:
                    record["action"]["kind"] = "observe_recovery" if len(matches) == 1 else "escalate"
                    record["action"]["recovery_task_ids"] = matches
                    if len(matches) > 1:
                        record["action"]["reason"] = "multiple live linked recoveries"
                    elif re.findall(r"^Recovery class: (.+)$", str(unique[matches[0]].get("body") or ""), re.MULTILINE) not in ([], [record["recovery_class"]]):
                        record["action"]["kind"] = "escalate"
                        record["action"]["reason"] = "linked recovery class conflicts or is malformed; resolve without duplication"
                    elif unique[matches[0]].get("status") not in {"ready", "running", "review"}:
                        record["action"]["kind"] = "escalate"
                        record["action"]["reason"] = "linked recovery is not runnable; resolve its disposition, do not duplicate"
        records.append(record)
    return (sorted(records, key=lambda item: ((item["contract"] or {}).get("url", ""), item["id"])),
            sorted(errors, key=lambda item: item["id"]))


def linked_recoveries(event: dict[str, Any], tasks: list[dict[str, Any]]) -> list[str]:
    matches = []
    # A missing Closure hash is observable but cannot equate two product cohorts.
    if not event["contract"] or not event["contract"]["sha256"]:
        return matches
    for task in tasks:
        role, trusted = role_identity(task)
        if not trusted or role not in {"Architect", "Worker"} or task.get("status") not in {"todo", "ready", "running", "blocked", "review", "triage", "scheduled"}:
            continue
        try:
            if identity(task.get("body")) != event["contract"]:
                continue
        except ValueError:
            continue
        body = str(task.get("body") or "")
        audit_ids = re.findall(r"^Recovery audit task: (.+)$", body, re.MULTILINE)
        run_ids = re.findall(r"^Recovery audit run: (.+)$", body, re.MULTILINE)
        if (audit_ids == [event["id"]] and run_ids == [event["run_id"]]
                and event["id"] in task.get("parents", [])):
            matches.append(task["id"])
    return sorted(matches)


def digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_table(conn: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    # Names are fixed by load_tasks; no caller-controlled SQL. Count and pages
    # share one read transaction, so dispatch cannot create partial snapshots.
    count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if count > MAX_RECORDS:
        raise ValueError(f"record bound exceeded: {table} ({count} > {MAX_RECORDS})")
    cursor = conn.execute(f"SELECT * FROM {table} ORDER BY rowid")
    rows = []
    while page := cursor.fetchmany(PAGE_SIZE):
        rows.extend(dict(row) for row in page)
    if len(rows) != count:
        raise ValueError("incomplete board snapshot")
    return rows


def load_tasks(input_path: Path | None) -> object:
    if input_path:
        return json.loads(input_path.read_text(encoding="utf-8"))
    # Installed CLI list has no pagination, and calls recompute_ready (a write).
    # Even show/runs use a migrating connection. Never invoke them from a scanner.
    path = Path(os.environ.get("FOUNDRY_WATCHDOG_DB", str(
        Path.home() / ".hermes/kanban/boards" / BOARD / "kanban.db")))
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=5)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        tasks = read_table(conn, "tasks")
        runs = read_table(conn, "task_runs")
        links = read_table(conn, "task_links")
        events = read_table(conn, "task_events")
    finally:
        conn.close()
    by_id = {}
    for task in tasks:
        if isinstance(task.get("skills"), str):
            task["skills"] = json.loads(task["skills"])
        by_id[task["id"]] = {"task": task, "runs": [], "events": [], "parents": [], "children": []}
    for rows, key, json_key in ((runs, "runs", "metadata"), (events, "events", "payload")):
        for row in rows:
            if row["task_id"] not in by_id:
                raise ValueError("orphan board evidence")
            if isinstance(row.get(json_key), str):
                row[json_key] = json.loads(row[json_key])
            by_id[row["task_id"]][key].append(row)
    for link in links:
        parent, child = link["parent_id"], link["child_id"]
        if parent not in by_id or child not in by_id:
            raise ValueError("orphan board link")
        by_id[parent]["children"].append(child)
        by_id[child]["parents"].append(parent)
    return list(by_id.values())


def previous_digest(path: Path | None) -> str:
    if not path or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8").strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, help="JSON fixture instead of live Kanban")
    parser.add_argument("--previous-digest-file", type=Path)
    parser.add_argument("--inspect", action="store_true", help="Include unchanged unresolved actions; do not notify")
    args = parser.parse_args()
    records, errors = relevant_tasks(load_tasks(args.input))
    if not records and not errors:
        return 0
    active_records = [record for record in records if record["status"] != "archived"]
    if not active_records and not args.inspect:
        return 0
    # Full historical receipts are available only on explicit inspection.
    emitted = records if args.inspect else [
        {key: value for key, value in record.items() if key != "lifecycle"}
        for record in active_records]
    payload: dict[str, Any] = {"board": BOARD, "events": emitted, "version": 2,
                               "actions": [record["action"] for record in records if "action" in record]}
    if errors:
        payload["scanner_status"] = "non_healthy"
        payload["scanner_errors"] = errors
    payload_digest = digest(payload)
    # Human titles, summaries, and heartbeat timestamps are not new incidents.
    notification_digest = digest({"board": BOARD, "version": 2, "events": [
        {key: value for key, value in record.items() if key not in {"title", "lifecycle"}}
        for record in active_records], "scanner_errors": errors})
    changed = previous_digest(args.previous_digest_file) not in {payload_digest, notification_digest}
    if not changed and not args.inspect:
        return 0
    print(json.dumps({**payload, "digest": payload_digest, "notification_digest": notification_digest,
                      "notify": changed and not args.inspect}, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"board": BOARD, "scanner_error": str(exc)}, sort_keys=True), file=sys.stderr)
        raise SystemExit(2)
