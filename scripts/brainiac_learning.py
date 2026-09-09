#!/usr/bin/env python3
"""Deterministic, event-driven Brainiac reliability-learning state machine.

Evaluator commands never start a hook, scheduler, gateway, or model.  The
separately operator-controlled bridge commands may invoke the isolated
read-only Brainiac profile only for qualifying durable structured evidence.
Runtime state must live outside this source checkout.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
WINDOW_DAYS = 30
HIGH_SEVERITY = "high"
SEVERITIES = {"low", "normal", "high"}
PERSISTED_INCIDENT_FIELDS = (
    "event_id",
    "occurred_at",
    "severity",
    "source",
    "category",
    "summary",
    "evidence_revision",
)
SENSITIVE_FIELD_NAMES = {"credential", "credentials", "token", "tokens", "session", "sessions", "log", "logs", "cache", "caches"}
EVIDENCE_SCHEMA = "foundry-watchdog-evidence-v1"
EVENT_EXPORT_FIELDS = {"schema", "incident"}
WEEKLY_EXPORT_FIELDS = {"schema", "evidence_revision", "synthesis_window", "observed_at"}
PROPOSAL_FIELDS = {"proposal", "invariant", "regression_test", "metric"}
BRAINIAC_COMMAND = (
    "hermes", "-p", "foundry-brainiac", "chat", "--oneshot",
    "--provider", "openai-codex", "--model", "gpt-6-astra", "--toolsets", "bot_room",
)


class BrainiacInputError(ValueError):
    """An incident or runtime-state boundary is invalid."""


def parse_timestamp(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BrainiacInputError("occurred_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise BrainiacInputError("occurred_at must include a timezone")
    return parsed.astimezone(dt.timezone.utc)


def normalize_fingerprint(incident: dict[str, Any]) -> str:
    """Make a stable fingerprint from structured classification and summary."""
    parts = [str(incident.get(name, "")) for name in ("source", "category", "summary")]
    raw = " ".join(parts).lower()
    raw = re.sub(r"\b[0-9a-f]{8,}\b", "<id>", raw)
    raw = re.sub(r"\b\d+\b", "<n>", raw)
    normalized = re.sub(r"[^a-z0-9<>]+", " ", raw).strip()
    if not normalized:
        raise BrainiacInputError("source, category, and summary cannot all be empty")
    return normalized


def reject_sensitive_fields(value: Any, path: str = "incident") -> None:
    """Reject prohibited state categories before they can reach durable state."""
    if isinstance(value, dict):
        for key, nested_value in value.items():
            normalized_key = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(key)).lower()
            key_parts = set(re.split(r"[^a-z0-9]+", normalized_key))
            if SENSITIVE_FIELD_NAMES & key_parts:
                raise BrainiacInputError(f"sensitive incident field is prohibited: {path}.{key}")
            reject_sensitive_fields(nested_value, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            reject_sensitive_fields(nested_value, f"{path}[{index}]")


def validate_incident(incident: dict[str, Any]) -> tuple[str, dt.datetime, str]:
    unsupported = set(incident) - set(PERSISTED_INCIDENT_FIELDS)
    if unsupported:
        raise BrainiacInputError(f"unsupported incident fields: {', '.join(sorted(unsupported))}")
    for field in ("event_id", "occurred_at", "severity"):
        if not isinstance(incident.get(field), str) or not incident[field].strip():
            raise BrainiacInputError(f"{field} is required")
    severity = incident["severity"].lower()
    if severity not in SEVERITIES:
        raise BrainiacInputError("severity must be low, normal, or high")
    return incident["event_id"], parse_timestamp(incident["occurred_at"]), severity


def require_external_state(state_path: Path) -> Path:
    resolved = state_path.expanduser().resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError:
        return resolved
    raise BrainiacInputError("runtime state must be outside the source checkout")


def connect(state_path: Path) -> sqlite3.Connection:
    state_path = require_external_state(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(state_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS incidents (
            event_id TEXT PRIMARY KEY,
            occurred_at TEXT NOT NULL,
            severity TEXT NOT NULL,
            fingerprint TEXT NOT NULL,
            evidence_revision TEXT NOT NULL,
            payload_json TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS incidents_fingerprint_time
            ON incidents(fingerprint, occurred_at);
        CREATE TABLE IF NOT EXISTS astra_invocations (
            invocation_key TEXT PRIMARY KEY,
            event_id TEXT NOT NULL UNIQUE,
            fingerprint TEXT NOT NULL,
            reason TEXT NOT NULL,
            evidence_revision TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS syntheses (
            synthesis_key TEXT PRIMARY KEY,
            evidence_revision TEXT NOT NULL,
            synthesis_window TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(evidence_revision, synthesis_window)
        );
        CREATE TABLE IF NOT EXISTS brainiac_executions (
            invocation_key TEXT PRIMARY KEY,
            kind TEXT NOT NULL,
            outcome TEXT NOT NULL CHECK(outcome IN ('running', 'completed', 'failed')),
            receipt_json TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS architect_outbox (
            invocation_key TEXT PRIMARY KEY,
            route TEXT NOT NULL,
            proposal_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        """
    )
    return connection


def invocation_key(event_id: str, evidence_revision: str) -> str:
    material = f"brainiac-astra-v1:{event_id}:{evidence_revision}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def process_incident(state_path: Path, incident: dict[str, Any]) -> dict[str, Any]:
    """Persist an event and create at most one durable Astra invocation record."""
    reject_sensitive_fields(incident)
    event_id, occurred_at, severity = validate_incident(incident)
    evidence_revision = incident.get("evidence_revision")
    if not isinstance(evidence_revision, str) or not evidence_revision.strip():
        raise BrainiacInputError("evidence_revision is required")
    for field in ("source", "category", "summary"):
        if not isinstance(incident.get(field), str):
            raise BrainiacInputError(f"{field} must be a string")
    persisted_incident = {field: incident[field] for field in PERSISTED_INCIDENT_FIELDS}
    fingerprint = normalize_fingerprint(persisted_incident)
    with connect(state_path) as db:
        duplicate = db.execute("SELECT 1 FROM incidents WHERE event_id = ?", (event_id,)).fetchone()
        if duplicate:
            return {"event_id": event_id, "fingerprint": fingerprint, "decision": "duplicate_noop", "astra_invoked": False}
        cutoff = (occurred_at - dt.timedelta(days=WINDOW_DAYS)).isoformat()
        prior_count = db.execute(
            "SELECT COUNT(*) FROM incidents WHERE fingerprint = ? AND occurred_at >= ? AND occurred_at < ?",
            (fingerprint, cutoff, occurred_at.isoformat()),
        ).fetchone()[0]
        db.execute(
            "INSERT INTO incidents VALUES (?, ?, ?, ?, ?, ?)",
            (event_id, occurred_at.isoformat(), severity, fingerprint, evidence_revision, json.dumps(persisted_incident, sort_keys=True)),
        )
        reason = "high_severity" if severity == HIGH_SEVERITY else "second_in_30_days" if prior_count >= 1 else None
        if reason is None:
            return {"event_id": event_id, "fingerprint": fingerprint, "prior_matching_incidents": prior_count, "decision": "not_qualified", "astra_invoked": False}
        key = invocation_key(event_id, evidence_revision)
        db.execute(
            "INSERT OR IGNORE INTO astra_invocations VALUES (?, ?, ?, ?, ?, ?)",
            (key, event_id, fingerprint, reason, evidence_revision, occurred_at.isoformat()),
        )
        inserted = db.execute("SELECT changes()").fetchone()[0] == 1
        return {"event_id": event_id, "fingerprint": fingerprint, "prior_matching_incidents": prior_count, "decision": reason if inserted else "duplicate_noop", "invocation_key": key, "astra_invoked": inserted}


def record_weekly_synthesis(state_path: Path, evidence_revision: str, synthesis_window: str, observed_at: str) -> dict[str, Any]:
    """Create one durable synthesis record per changed evidence revision/window."""
    if not evidence_revision.strip() or not synthesis_window.strip():
        raise BrainiacInputError("evidence_revision and synthesis_window are required")
    timestamp = parse_timestamp(observed_at).isoformat()
    key = hashlib.sha256(f"brainiac-synthesis-v1:{evidence_revision}:{synthesis_window}".encode("utf-8")).hexdigest()
    with connect(state_path) as db:
        db.execute("INSERT OR IGNORE INTO syntheses VALUES (?, ?, ?, ?)", (key, evidence_revision, synthesis_window, timestamp))
        inserted = db.execute("SELECT changes()").fetchone()[0] == 1
    return {"synthesis_key": key, "evidence_revision": evidence_revision, "synthesis_window": synthesis_window, "decision": "synthesis_queued" if inserted else "unchanged_noop", "synthesis_required": inserted}


def validate_board_evidence(export: dict[str, Any], expected_fields: set[str]) -> None:
    """Reject non-Foundry, unsupported, or sensitive exports before state access."""
    reject_sensitive_fields(export, "evidence")
    if set(export) - expected_fields:
        raise BrainiacInputError("unsupported board evidence fields")
    if export.get("schema") != EVIDENCE_SCHEMA:
        raise BrainiacInputError("unsupported board evidence schema")


def build_prompt(kind: str, invocation_key_value: str, evidence: dict[str, Any]) -> str:
    """Build the sole non-secret model input from an allowlisted export."""
    return json.dumps({
        "task": "Produce one bounded reliability improvement proposal for Architect consideration.",
        "kind": kind,
        "invocation_key": invocation_key_value,
        "evidence": evidence,
        "required_json_fields": sorted(PROPOSAL_FIELDS),
        "boundary": "Read-only proposal only: no source, GitHub, profile, contract, audit, or task mutation.",
    }, sort_keys=True)


def validate_proposal(output: str) -> dict[str, str]:
    """Keep only a fixed non-secret proposal receipt, never a model transcript."""
    try:
        proposal = json.loads(output)
    except json.JSONDecodeError as exc:
        raise BrainiacInputError("Brainiac output must be a JSON proposal") from exc
    reject_sensitive_fields(proposal, "proposal")
    if not isinstance(proposal, dict) or set(proposal) != PROPOSAL_FIELDS:
        raise BrainiacInputError("Brainiac output must contain only the proposal receipt schema")
    if any(not isinstance(value, str) or not value.strip() for value in proposal.values()):
        raise BrainiacInputError("Brainiac proposal receipt values must be non-empty strings")
    return {field: proposal[field].strip() for field in sorted(PROPOSAL_FIELDS)}


def default_runner(command: tuple[str, ...], prompt: str) -> str:
    completed = subprocess.run([*command, "--query", prompt], check=True, capture_output=True, text=True, timeout=300)
    return completed.stdout


def execute_qualified(
    state_path: Path,
    *,
    kind: str,
    invocation_key_value: str,
    evidence: dict[str, Any],
    observed_at: str,
    runner: Callable[[tuple[str, ...], str], str] = default_runner,
) -> dict[str, Any]:
    """Invoke the isolated profile once and leave a terminal, non-secret receipt."""
    timestamp = parse_timestamp(observed_at).isoformat()
    with connect(state_path) as db:
        existing = db.execute("SELECT outcome FROM brainiac_executions WHERE invocation_key = ?", (invocation_key_value,)).fetchone()
        if existing:
            return {"invocation_key": invocation_key_value, "decision": "execution_duplicate_noop", "model_invoked": False, "outcome": existing[0]}
        db.execute(
            "INSERT INTO brainiac_executions VALUES (?, ?, 'running', NULL, ?, NULL)",
            (invocation_key_value, kind, timestamp),
        )
    try:
        proposal = validate_proposal(runner(BRAINIAC_COMMAND, build_prompt(kind, invocation_key_value, evidence)))
    except (BrainiacInputError, subprocess.SubprocessError, TimeoutError, OSError):
        receipt = {"invocation_key": invocation_key_value, "kind": kind, "outcome": "failed"}
        with connect(state_path) as db:
            db.execute("UPDATE brainiac_executions SET outcome = 'failed', receipt_json = ?, completed_at = ? WHERE invocation_key = ?", (json.dumps(receipt, sort_keys=True), timestamp, invocation_key_value))
        return {**receipt, "model_invoked": True}
    receipt = {"invocation_key": invocation_key_value, "kind": kind, "outcome": "completed", "route": "architect_consideration"}
    with connect(state_path) as db:
        db.execute("INSERT INTO architect_outbox VALUES (?, 'architect_consideration', ?, ?)", (invocation_key_value, json.dumps(proposal, sort_keys=True), timestamp))
        db.execute("UPDATE brainiac_executions SET outcome = 'completed', receipt_json = ?, completed_at = ? WHERE invocation_key = ?", (json.dumps(receipt, sort_keys=True), timestamp, invocation_key_value))
    return {**receipt, "model_invoked": True}


def process_board_event(
    state_path: Path,
    export: dict[str, Any],
    runner: Callable[[tuple[str, ...], str], str] = default_runner,
) -> dict[str, Any]:
    """Evaluate one explicit Watchdog/Foundry event export before any model call."""
    validate_board_evidence(export, EVENT_EXPORT_FIELDS)
    incident = export.get("incident")
    if not isinstance(incident, dict):
        raise BrainiacInputError("board evidence incident must be an object")
    decision = process_incident(state_path, incident)
    if not decision["astra_invoked"]:
        return {**decision, "model_invoked": False}
    return {**decision, **execute_qualified(state_path, kind="event", invocation_key_value=decision["invocation_key"], evidence={field: incident[field] for field in PERSISTED_INCIDENT_FIELDS}, observed_at=incident["occurred_at"], runner=runner)}


def process_weekly_board_evidence(
    state_path: Path,
    export: dict[str, Any],
    runner: Callable[[tuple[str, ...], str], str] = default_runner,
) -> dict[str, Any]:
    """Evaluate one explicit changed weekly evidence revision before any model call."""
    validate_board_evidence(export, WEEKLY_EXPORT_FIELDS)
    for field in ("evidence_revision", "synthesis_window", "observed_at"):
        if not isinstance(export.get(field), str) or not export[field].strip():
            raise BrainiacInputError(f"board evidence {field} is required")
    decision = record_weekly_synthesis(state_path, export["evidence_revision"], export["synthesis_window"], export["observed_at"])
    if not decision["synthesis_required"]:
        return {**decision, "model_invoked": False}
    evidence = {field: export[field] for field in ("evidence_revision", "synthesis_window")}
    return {**decision, **execute_qualified(state_path, kind="weekly", invocation_key_value=decision["synthesis_key"], evidence=evidence, observed_at=export["observed_at"], runner=runner)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    command = parser.add_subparsers(dest="command", required=True)
    incident = command.add_parser("incident")
    incident.add_argument("--input", required=True, type=Path)
    bridge_event = command.add_parser("bridge-event")
    bridge_event.add_argument("--input", required=True, type=Path)
    synthesis = command.add_parser("synthesis")
    synthesis.add_argument("--evidence-revision", required=True)
    synthesis.add_argument("--window", required=True)
    synthesis.add_argument("--observed-at", required=True)
    bridge_weekly = command.add_parser("bridge-weekly")
    bridge_weekly.add_argument("--input", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.command == "incident":
            result = process_incident(args.state, json.loads(args.input.read_text(encoding="utf-8")))
        elif args.command == "bridge-event":
            result = process_board_event(args.state, json.loads(args.input.read_text(encoding="utf-8")))
        elif args.command == "bridge-weekly":
            result = process_weekly_board_evidence(args.state, json.loads(args.input.read_text(encoding="utf-8")))
        else:
            result = record_weekly_synthesis(args.state, args.evidence_revision, args.window, args.observed_at)
    except (BrainiacInputError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
