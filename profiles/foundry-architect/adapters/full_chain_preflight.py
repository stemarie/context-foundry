#!/usr/bin/env python3
"""Validate a proposed Foundry chain before it creates external authority.

The validator is deliberately local and read-only.  It checks a JSON manifest
containing non-secret, role-local readiness receipts plus a realistic Hermes
Kanban ``show`` envelope.  A PASS is required before an Architect activates an
AI.Contract record, creates a traceability tracker, or releases successor cards.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

ROLE_RULES = {
    "Architect": {
        "assignee": "foundry-architect",
        "title_prefix": "Architect:",
        "parents": set(),
    },
    "Worker": {
        "assignee": "foundry-worker",
        "title_prefix": "Worker:",
        "parents": {"Architect"},
    },
    "Candidate Auditor": {
        "assignee": "foundry-auditor",
        "title_prefix": "Candidate Auditor:",
        "parents": {"Worker"},
    },
    "Integration Auditor": {
        "assignee": "foundry-auditor",
        "title_prefix": "Integration Auditor:",
        "parents": {"Candidate Auditor"},
    },
    "Delivery": {
        "assignee": "foundry-worker",
        "title_prefix": "Delivery:",
        "parents": {"Candidate Auditor", "Integration Auditor"},
    },
    "Closure Auditor": {
        "assignee": "foundry-auditor",
        "title_prefix": "Closure Auditor:",
        "parents": {"Delivery"},
    },
}

UUID_RE = re.compile(r"^[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}$", re.IGNORECASE)
SHA1_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)
V2_HEADER_RE = re.compile(
    r"^AI\.Contract: `(?P<id>[0-9a-f-]{36})` revision (?P<revision>[1-9][0-9]*)\nRole: (?P<role>[^\n]+)(?=\n|$)"
)


def error(code: str, message: str) -> dict[str, str]:
    return {"code": code, "message": message}


def verdict(errors: list[dict[str, str]]) -> str:
    codes = {item["code"] for item in errors}
    if "SOURCE_UNAVAILABLE" in codes:
        return "SOURCE_UNAVAILABLE"
    if "CAPABILITY_UNAVAILABLE" in codes:
        return "CAPABILITY_UNAVAILABLE"
    if "WORKSPACE_MISMATCH" in codes:
        return "WORKSPACE_MISMATCH"
    return "MALFORMED_PACKET"


def installed_skill(source_root: Path, assignee: str, skill: object) -> bool:
    return isinstance(skill, str) and (source_root / "profiles" / assignee / "skills" / skill / "SKILL.md").is_file()


def validate_envelope(envelope: object) -> list[dict[str, str]]:
    if not isinstance(envelope, dict):
        return [error("MALFORMED_PACKET", "kanban_show_envelope must be an object")]
    errors: list[dict[str, str]] = []
    task = envelope.get("task")
    if not isinstance(task, dict):
        errors.append(error("MALFORMED_PACKET", "kanban_show_envelope.task must be an object"))
    for key in ("parents", "runs"):
        if not isinstance(envelope.get(key), list):
            errors.append(error("MALFORMED_PACKET", f"kanban_show_envelope.{key} must be a list"))
    for run in envelope.get("runs", []):
        if not isinstance(run, dict) or not isinstance(run.get("metadata"), dict):
            errors.append(error("MALFORMED_PACKET", "completion receipt must be in root runs[].metadata"))
            break
    return errors


def validate_manifest(manifest: object, source_root: Path = ROOT) -> dict[str, Any]:
    """Return a deterministic preflight receipt without invoking external systems."""
    if not isinstance(manifest, dict):
        return {
            "verdict": "MALFORMED_PACKET",
            "errors": [error("MALFORMED_PACKET", "manifest must be an object")],
        }

    errors: list[dict[str, str]] = []
    contract = manifest.get("contract")
    if not isinstance(contract, dict) or not UUID_RE.fullmatch(str(contract.get("id", ""))) or not isinstance(contract.get("revision"), int) or contract["revision"] < 1:
        errors.append(error("MALFORMED_PACKET", "contract must contain a UUID id and positive integer revision"))

    sources = manifest.get("required_sources")
    if not isinstance(sources, list) or not sources:
        errors.append(error("SOURCE_UNAVAILABLE", "required_sources must contain one passing role-bound receipt per required source"))
    else:
        for source in sources:
            if not isinstance(source, dict) or not isinstance(source.get("id"), str) or source.get("read_receipt") != "PASS":
                errors.append(error("SOURCE_UNAVAILABLE", "every required source needs an explicit PASS read receipt"))
                break

    target = manifest.get("target")
    if not isinstance(target, dict):
        errors.append(error("WORKSPACE_MISMATCH", "target binding is missing"))
    else:
        repository = target.get("repository")
        expected_origin = f"https://github.com/{repository}.git" if isinstance(repository, str) else None
        if not repository or target.get("origin") != expected_origin or not target.get("api_target") == f"https://api.github.com/repos/{repository}" or target.get("branch") != "main" or target.get("workspace_clean") is not True or not isinstance(target.get("base_sha"), str) or not SHA1_RE.fullmatch(target["base_sha"]):
            errors.append(error("WORKSPACE_MISMATCH", "target must bind repository, origin, API target, clean main workspace, and frozen 40-character base SHA"))

    errors.extend(validate_envelope(manifest.get("kanban_show_envelope")))

    roles = manifest.get("roles")
    if not isinstance(roles, list) or not roles:
        errors.append(error("MALFORMED_PACKET", "roles must be a non-empty list"))
        roles = []
    seen_roles: set[str] = set()
    for card in roles:
        if not isinstance(card, dict):
            errors.append(error("MALFORMED_PACKET", "every role card must be an object"))
            continue
        role = card.get("role")
        rule = ROLE_RULES.get(role)
        if rule is None:
            errors.append(error("MALFORMED_PACKET", f"unrecognized role {role!r}"))
            continue
        if role in seen_roles:
            errors.append(error("MALFORMED_PACKET", f"duplicate proposed role {role}"))
        seen_roles.add(role)
        if card.get("assignee") != rule["assignee"]:
            errors.append(error("MALFORMED_PACKET", f"{role} assignee must be {rule['assignee']}"))
        if not isinstance(card.get("title"), str) or not card["title"].startswith(rule["title_prefix"]):
            errors.append(error("MALFORMED_PACKET", f"{role} title must begin exactly {rule['title_prefix']!r}"))
        parent_roles = card.get("parent_roles")
        if not isinstance(parent_roles, list) or set(parent_roles) != rule["parents"]:
            errors.append(error("MALFORMED_PACKET", f"{role} parent roles must be exactly {sorted(rule['parents'])}"))
        body = card.get("body")
        header = V2_HEADER_RE.match(body) if isinstance(body, str) else None
        if not header or header.group("role") != role:
            errors.append(error("MALFORMED_PACKET", f"{role} body must begin with exact AI.Contract and Role lines"))
        elif isinstance(contract, dict) and (header.group("id") != contract.get("id") or int(header.group("revision")) != contract.get("revision")):
            errors.append(error("MALFORMED_PACKET", f"{role} body contract reference must match manifest contract"))
        skills = card.get("skills")
        if not isinstance(skills, list) or not skills:
            errors.append(error("CAPABILITY_UNAVAILABLE", f"{role} needs at least one installed forced skill"))
        else:
            missing = [skill for skill in skills if not installed_skill(source_root, rule["assignee"], skill)]
            if missing:
                errors.append(error("CAPABILITY_UNAVAILABLE", f"{role} has unavailable forced skills: {', '.join(map(str, missing))}"))
        if card.get("role_read_receipt") != "PASS":
            errors.append(error("CAPABILITY_UNAVAILABLE", f"{role} lacks a passing task-bound read receipt"))

    continuation = manifest.get("continuation")
    if not isinstance(continuation, dict) or set(continuation) != {"on_pass", "on_request_changes", "on_blocked"} or not all(isinstance(value, str) and value for value in continuation.values()) or len(set(continuation.values())) != 3:
        errors.append(error("MALFORMED_PACKET", "continuation must define distinct non-empty on_pass, on_request_changes, and on_blocked routes"))

    if errors:
        return {"verdict": verdict(errors), "errors": errors}
    return {
        "verdict": "PASS",
        "contract": {"id": contract["id"], "revision": contract["revision"]},
        "validated_roles": [card["role"] for card in roles],
        "external_writes": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="non-secret full-chain preflight manifest JSON")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "MALFORMED_PACKET", "errors": [error("MALFORMED_PACKET", str(exc))]}, sort_keys=True))
        return 2
    receipt = validate_manifest(manifest)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
