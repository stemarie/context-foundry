#!/usr/bin/env python3
"""Deterministic, event-driven Brainiac reliability-learning state machine.

This module never starts a hook, scheduler, gateway, or model.  A separately
operator-controlled integration may call its functions when new durable,
structured incident evidence arrives.  Runtime state must live outside this
source checkout.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WINDOW_DAYS = 30
HIGH_SEVERITY = "high"
SEVERITIES = {"low", "normal", "high"}


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


def validate_incident(incident: dict[str, Any]) -> tuple[str, dt.datetime, str]:
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
        """
    )
    return connection


def invocation_key(event_id: str, evidence_revision: str) -> str:
    material = f"brainiac-astra-v1:{event_id}:{evidence_revision}".encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def process_incident(state_path: Path, incident: dict[str, Any]) -> dict[str, Any]:
    """Persist an event and create at most one durable Astra invocation record."""
    event_id, occurred_at, severity = validate_incident(incident)
    evidence_revision = incident.get("evidence_revision")
    if not isinstance(evidence_revision, str) or not evidence_revision.strip():
        raise BrainiacInputError("evidence_revision is required")
    fingerprint = normalize_fingerprint(incident)
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
            (event_id, occurred_at.isoformat(), severity, fingerprint, evidence_revision, json.dumps(incident, sort_keys=True)),
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", required=True, type=Path)
    command = parser.add_subparsers(dest="command", required=True)
    incident = command.add_parser("incident")
    incident.add_argument("--input", required=True, type=Path)
    synthesis = command.add_parser("synthesis")
    synthesis.add_argument("--evidence-revision", required=True)
    synthesis.add_argument("--window", required=True)
    synthesis.add_argument("--observed-at", required=True)
    args = parser.parse_args()
    try:
        if args.command == "incident":
            result = process_incident(args.state, json.loads(args.input.read_text(encoding="utf-8")))
        else:
            result = record_weekly_synthesis(args.state, args.evidence_revision, args.window, args.observed_at)
    except (BrainiacInputError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
