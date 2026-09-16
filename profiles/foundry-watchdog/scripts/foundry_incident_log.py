#!/usr/bin/env python3
"""Append-only MariaDB incident log and Brainiac bridge for Context Foundry.

This helper accepts only a compact, allowlisted incident record. It never stores
credentials, raw task runs, chat transcripts, or source logs. The database table
is the durable incident source of truth; Brainiac's SQLite state only deduplicates
model evaluation and proposal routing.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import pymysql

BOARD = "context-foundry"
SCHEMA = "foundry-incident-log-v1"
ALLOWED_SOURCES = {"watchdog", "foundry-check", "user"}
ALLOWED_SEVERITIES = {"low", "normal", "high"}
ALLOWED_ACTIONS = {"soft_nudge", "unblock", "none"}
SENSITIVE_WORDS = {"credential", "credentials", "token", "tokens", "password", "secret", "session", "sessions", "log", "logs", "cache", "caches"}
DEFAULT_WRITER_ENV = Path("/home/karell/.hermes/profiles/foundry-watchdog/.secrets/foundry_incident_log.env")
DEFAULT_READER_ENV = Path("/home/karell/.hermes/profiles/foundry-brainiac/.secrets/foundry_incident_log.env")
BRAINIAC_STATE = Path("/home/karell/.hermes/profiles/foundry-brainiac/state/brainiac.sqlite")
BRAINIAC_LEARNING = Path("/home/karell/.hermes/profiles/foundry-brainiac/scripts/brainiac_learning.py")


class IncidentLogError(ValueError):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="microseconds")


def parse_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise IncidentLogError(f"credential file is absent: {path}")
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise IncidentLogError("credential file has malformed line")
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    expected = {"FOUNDRY_INCIDENT_DB_HOST", "FOUNDRY_INCIDENT_DB_PORT", "FOUNDRY_INCIDENT_DB_USER", "FOUNDRY_INCIDENT_DB_PASSWORD", "FOUNDRY_INCIDENT_DB_NAME"}
    if set(values) != expected or any(not values[key] for key in expected):
        raise IncidentLogError("credential file has an unsupported schema")
    return values


def connect(env_path: Path):
    values = parse_env(env_path)
    return pymysql.connect(
        host=values["FOUNDRY_INCIDENT_DB_HOST"],
        port=int(values["FOUNDRY_INCIDENT_DB_PORT"]),
        user=values["FOUNDRY_INCIDENT_DB_USER"],
        password=values["FOUNDRY_INCIDENT_DB_PASSWORD"],
        database=values["FOUNDRY_INCIDENT_DB_NAME"],
        charset="utf8mb4",
        autocommit=False,
        connect_timeout=10,
        read_timeout=20,
        write_timeout=20,
        cursorclass=pymysql.cursors.DictCursor,
    )


def reject_sensitive(value: Any, path: str = "incident") -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            parts = set(re.split(r"[^a-z0-9]+", re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(key)).lower()))
            if parts & SENSITIVE_WORDS:
                raise IncidentLogError(f"sensitive field is prohibited: {path}.{key}")
            reject_sensitive(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            reject_sensitive(nested, f"{path}[{index}]")


def clean_text(value: str, field: str, maximum: int) -> str:
    value = value.strip()
    if not value or len(value) > maximum or "\x00" in value:
        raise IncidentLogError(f"{field} is invalid")
    return value


def stable_id(occurrence_key: str) -> str:
    return hashlib.sha256(f"foundry-incident-log-v1:{occurrence_key}".encode("utf-8")).hexdigest()


def build_incident(args: argparse.Namespace) -> dict[str, Any]:
    evidence = json.loads(args.evidence_json)
    if not isinstance(evidence, dict):
        raise IncidentLogError("evidence_json must be an object")
    reject_sensitive(evidence, "evidence")
    source = clean_text(args.source, "source", 32)
    severity = clean_text(args.severity.lower(), "severity", 16)
    action = clean_text(args.action, "action", 32)
    if source not in ALLOWED_SOURCES or severity not in ALLOWED_SEVERITIES or action not in ALLOWED_ACTIONS:
        raise IncidentLogError("source, severity, or action is unsupported")
    occurrence_key = clean_text(args.occurrence_key, "occurrence_key", 512)
    if not re.fullmatch(r"[A-Za-z0-9._:/-]+", occurrence_key):
        raise IncidentLogError("occurrence_key must be a stable identifier")
    occurred_at = args.occurred_at or utc_now()
    try:
        parsed = dt.datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise IncidentLogError("occurred_at must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise IncidentLogError("occurred_at must include timezone")
    occurred_at = parsed.astimezone(dt.timezone.utc).isoformat(timespec="microseconds")
    incident = {
        "incident_id": stable_id(occurrence_key),
        "occurrence_key": occurrence_key,
        "occurred_at": occurred_at,
        "severity": severity,
        "detection_source": source,
        "category": clean_text(args.category, "category", 80),
        "summary": clean_text(args.summary, "summary", 1000),
        "board_id": BOARD,
        "trigger_card_id": clean_text(args.trigger_card_id, "trigger_card_id", 80),
        "contract_id": clean_text(args.contract_id, "contract_id", 128),
        "contract_revision": clean_text(str(args.contract_revision), "contract_revision", 32),
        "affected_role": clean_text(args.affected_role, "affected_role", 80),
        "action_taken": action,
        "replacement_card_id": (clean_text(args.replacement_card_id, "replacement_card_id", 80) if args.replacement_card_id else None),
        "evidence_revision": clean_text(args.evidence_revision, "evidence_revision", 128),
        "evidence_json": json.dumps(evidence, sort_keys=True, separators=(",", ":")),
    }
    return incident


def record(conn, incident: dict[str, Any]) -> dict[str, Any]:
    evidence_sha = hashlib.sha256(incident["evidence_json"].encode("utf-8")).hexdigest()
    with conn.cursor() as cursor:
        cursor.execute(
            """INSERT IGNORE INTO foundry_incident_log
            (incident_id, occurrence_key, occurred_at, severity, detection_source, category, summary,
             board_id, trigger_card_id, contract_id, contract_revision, affected_role, action_taken,
             replacement_card_id, evidence_revision, evidence_json, evidence_sha256, brainiac_state)
            VALUES (%(incident_id)s, %(occurrence_key)s, %(occurred_at)s, %(severity)s, %(detection_source)s,
                    %(category)s, %(summary)s, %(board_id)s, %(trigger_card_id)s, %(contract_id)s,
                    %(contract_revision)s, %(affected_role)s, %(action_taken)s, %(replacement_card_id)s,
                    %(evidence_revision)s, %(evidence_json)s, %(evidence_sha256)s, 'pending')""",
            {**incident, "evidence_sha256": evidence_sha},
        )
        inserted = cursor.rowcount == 1
        cursor.execute("SELECT incident_id, brainiac_state FROM foundry_incident_log WHERE incident_id = %s", (incident["incident_id"],))
        readback = cursor.fetchone()
    conn.commit()
    if not readback or readback["incident_id"] != incident["incident_id"]:
        raise IncidentLogError("incident read-back failed")
    return {"incident_id": incident["incident_id"], "inserted": inserted, "brainiac_state": readback["brainiac_state"]}


def row_to_evidence(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a durable allowlisted incident row to Brainiac's fixed input."""
    return {
        "schema": "foundry-watchdog-evidence-v1",
        "incident": {
            "event_id": row["incident_id"],
            "occurred_at": row["occurred_at"].replace(tzinfo=dt.timezone.utc).isoformat() if isinstance(row["occurred_at"], dt.datetime) else str(row["occurred_at"]),
            "severity": row["severity"],
            "source": row["detection_source"],
            "category": row["category"],
            "summary": row["summary"],
            "evidence_revision": row["evidence_revision"],
        },
    }


def bridge_pending(reader_env: Path, writer_env: Path, limit: int) -> list[dict[str, Any]]:
    """Claim pending durable incidents, give Brainiac structured evidence, read back receipt."""
    if limit < 1 or limit > 20:
        raise IncidentLogError("limit must be between 1 and 20")
    with connect(reader_env) as reader:
        with reader.cursor() as cursor:
            cursor.execute(
                """SELECT incident_id, occurred_at, severity, detection_source, category, summary, evidence_revision
                   FROM foundry_incident_log WHERE brainiac_state = 'pending'
                   ORDER BY occurred_at ASC LIMIT %s""",
                (limit,),
            )
            rows = cursor.fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        with connect(writer_env) as writer:
            with writer.cursor() as cursor:
                cursor.execute(
                    "UPDATE foundry_incident_log SET brainiac_state = 'processing', brainiac_attempted_at = UTC_TIMESTAMP(6) WHERE incident_id = %s AND brainiac_state = 'pending'",
                    (row["incident_id"],),
                )
                claimed = cursor.rowcount == 1
            writer.commit()
        if not claimed:
            continue
        payload = row_to_evidence(row)
        input_path = Path("/tmp") / f"foundry-brainiac-{row['incident_id']}.json"
        try:
            input_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(BRAINIAC_LEARNING), "--state", str(BRAINIAC_STATE), "bridge-event", "--input", str(input_path)],
                capture_output=True,
                text=True,
                timeout=360,
                check=False,
            )
            if completed.returncode:
                raise IncidentLogError("Brainiac bridge command failed")
            receipt = json.loads(completed.stdout)
            receipt_json = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
            state = "processed"
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, IncidentLogError):
            receipt_json = json.dumps({"outcome": "bridge_failed"}, sort_keys=True)
            state = "failed"
        finally:
            input_path.unlink(missing_ok=True)
        with connect(writer_env) as writer:
            with writer.cursor() as cursor:
                cursor.execute(
                    """UPDATE foundry_incident_log SET brainiac_state = %s, brainiac_processed_at = UTC_TIMESTAMP(6),
                       brainiac_receipt_json = %s, brainiac_receipt_sha256 = %s
                       WHERE incident_id = %s AND brainiac_state = 'processing'""",
                    (state, receipt_json, hashlib.sha256(receipt_json.encode("utf-8")).hexdigest(), row["incident_id"]),
                )
                updated = cursor.rowcount == 1
            writer.commit()
        if not updated:
            raise IncidentLogError("Brainiac receipt read-back failed")
        results.append({"incident_id": row["incident_id"], "state": state})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writer-env", type=Path, default=DEFAULT_WRITER_ENV)
    parser.add_argument("--reader-env", type=Path, default=DEFAULT_READER_ENV)
    commands = parser.add_subparsers(dest="command", required=True)
    record_parser = commands.add_parser("record-nudge")
    record_parser.add_argument("--occurrence-key", required=True)
    record_parser.add_argument("--source", required=True, choices=sorted(ALLOWED_SOURCES))
    record_parser.add_argument("--severity", default="normal", choices=sorted(ALLOWED_SEVERITIES))
    record_parser.add_argument("--category", default="lifecycle_routing")
    record_parser.add_argument("--summary", required=True)
    record_parser.add_argument("--trigger-card-id", required=True)
    record_parser.add_argument("--contract-id", required=True)
    record_parser.add_argument("--contract-revision", required=True)
    record_parser.add_argument("--affected-role", required=True)
    record_parser.add_argument("--action", required=True, choices=sorted(ALLOWED_ACTIONS))
    record_parser.add_argument("--replacement-card-id")
    record_parser.add_argument("--evidence-revision", required=True)
    record_parser.add_argument("--evidence-json", required=True)
    record_parser.add_argument("--occurred-at")
    bridge_parser = commands.add_parser("bridge-pending")
    bridge_parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    try:
        if args.command == "record-nudge":
            incident = build_incident(args)
            with connect(args.writer_env) as db:
                result = record(db, incident)
        else:
            result = {"bridged": bridge_pending(args.reader_env, args.writer_env, args.limit)}
        print(json.dumps(result, sort_keys=True))
        return 0
    except (IncidentLogError, pymysql.MySQLError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
