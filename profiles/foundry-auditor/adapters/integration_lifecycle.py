#!/usr/bin/env python3
"""Validate an explicit repository-change integration disposition.

This is deterministic policy evidence, not a GitHub client. Callers collect
remote branch, pull-request, and check evidence separately, then pass the
normalized record to this module. The module never writes a repository,
tracker, or profile.
"""
from __future__ import annotations

from typing import Any

CANDIDATE_AUDIT_DISCLAIMER = (
    "PASS certifies the exact candidate SHA and scoped evidence only; it does "
    "not certify PR integration, deployment, or milestone completion."
)
DISPOSITIONS = {"candidate_only", "merge_required", "human_approval_required"}
TRACKER_STATES = {"open", "closed", "reopened", "superseded"}


def _present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _errors_for_common_fields(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in (
        "repository",
        "default_branch",
        "base_sha",
        "candidate_sha",
        "candidate_branch",
        "candidate_audit_verdict",
        "candidate_audit_sha",
        "candidate_audit_disclaimer",
        "disposition_owner",
        "next_decision",
    ):
        if not _present(record.get(field)):
            errors.append(field)
    if record.get("candidate_audit_verdict") != "PASS":
        errors.append("candidate_audit_verdict")
    if record.get("candidate_audit_sha") != record.get("candidate_sha"):
        errors.append("candidate_audit_sha")
    if record.get("candidate_audit_disclaimer") != CANDIDATE_AUDIT_DISCLAIMER:
        errors.append("candidate_audit_disclaimer")
    return errors


def _result(state: str, *, closable: bool, milestone_complete: bool, errors: list[str] | None = None, missing: list[str] | None = None) -> dict[str, Any]:
    return {
        "state": state,
        "closable": closable,
        "milestone_complete": milestone_complete,
        "errors": sorted(set(errors or [])),
        "missing": sorted(set(missing or [])),
    }


def _post_merge_checks_pass(checks: Any, revision: Any) -> bool:
    """Accept only non-empty PASS checks bound to the read-back revision."""
    if not isinstance(checks, list) or not checks or not _present(revision):
        return False
    return all(
        isinstance(check, dict)
        and _present(check.get("command"))
        and check.get("outcome") == "PASS"
        and check.get("revision") == revision
        for check in checks
    )


def evaluate(record: dict[str, Any]) -> dict[str, Any]:
    """Classify a source-changing tranche without inferring missing authority."""
    if not isinstance(record, dict) or record.get("source_change") is not True:
        return _result("invalid", closable=False, milestone_complete=False, errors=["source_change"])

    disposition = record.get("disposition")
    errors = _errors_for_common_fields(record)
    if disposition not in DISPOSITIONS:
        errors.append("disposition")
    tracker_state = record.get("tracker_state")
    if tracker_state not in TRACKER_STATES:
        errors.append("tracker_state")

    if disposition == "candidate_only":
        for field in ("candidate_only_reason", "disposition_owner", "next_decision"):
            if not _present(record.get(field)):
                errors.append(field)
        if tracker_state == "closed" and errors:
            errors.append("closed_tracker_with_invalid_candidate_hold")
        if errors:
            return _result("invalid", closable=False, milestone_complete=False, errors=errors)
        return _result("candidate_verified", closable=True, milestone_complete=False)

    if disposition == "human_approval_required":
        for field in ("pull_request_url", "pull_request_head_sha", "approval_request", "approval_owner"):
            if not _present(record.get(field)):
                errors.append(field)
        if record.get("pull_request_head_sha") != record.get("candidate_sha"):
            errors.append("pull_request_head_sha")
        if record.get("pull_request_merged") is True:
            errors.append("approval_required_already_merged")
        if tracker_state == "closed":
            errors.append("closed_tracker_before_approval")
        if errors:
            return _result("invalid", closable=False, milestone_complete=False, errors=errors)
        return _result("approval_pending", closable=False, milestone_complete=False)

    # merge_required is the default source-changing endpoint.
    missing: list[str] = []
    if not _present(record.get("pull_request_url")):
        missing.append("pull_request_url")
    if record.get("pull_request_head_sha") != record.get("candidate_sha"):
        missing.append("pull_request_head_sha")
    if record.get("pull_request_merged") is not True:
        missing.append("pull_request_merged")
    if not _present(record.get("merged_sha")):
        missing.append("merged_sha")
    # `default_branch_contains_merged` permits squash/rebase merges: a merged
    # tree need not contain the original candidate SHA as an ancestor.
    if record.get("default_branch_contains_merged") is not True:
        missing.append("default_branch_readback")
    if not _post_merge_checks_pass(record.get("post_merge_checks"), record.get("default_branch_head_sha")):
        missing.append("post_merge_checks")

    if tracker_state == "closed" and missing:
        errors.append("closed_tracker_without_integration")
    if tracker_state == "reopened":
        errors.append("reopened_tracker_requires_reconciliation")
    if errors:
        return _result("invalid", closable=False, milestone_complete=False, errors=errors, missing=missing)
    if missing:
        return _result("integration_pending", closable=False, milestone_complete=False, missing=missing)
    return _result("integrated_on_main", closable=True, milestone_complete=True)


def evaluate_cohort(cohort: dict[str, Any]) -> dict[str, Any]:
    """Detect sibling audited candidates that require one combined PR audit."""
    if not isinstance(cohort, dict) or not isinstance(cohort.get("candidates"), list):
        return {"state": "invalid", "errors": ["candidates"]}
    candidates = cohort["candidates"]
    if len(candidates) < 2:
        return {"state": "invalid", "errors": ["sibling_candidates"]}
    base_sha = cohort.get("default_branch_sha")
    candidate_shas: list[str] = []
    paths: dict[str, int] = {}
    for candidate in candidates:
        if not isinstance(candidate, dict) or candidate.get("base_sha") != base_sha:
            return {"state": "invalid", "errors": ["shared_base_sha"]}
        candidate_shas.append(str(candidate.get("candidate_sha", "")))
        for path in candidate.get("changed_paths", []):
            paths[str(path)] = paths.get(str(path), 0) + 1
    overlapping = sorted(path for path, count in paths.items() if count > 1)
    if cohort.get("open_pull_request") is not None:
        return {"state": "invalid", "errors": ["unexpected_open_pull_request"]}
    if any(candidate.get("candidate_reachable_from_default") is True for candidate in candidates if isinstance(candidate, dict)):
        return {"state": "invalid", "errors": ["candidate_already_integrated"]}
    return {
        "state": "integration_pending",
        "candidates": sorted(candidate_shas),
        "overlapping_paths": overlapping,
        "required_next_action": "Create one combined integration pull request and independently audit its exact head SHA.",
    }


def main() -> int:
    """Evaluate a JSON lifecycle record or sibling-candidate cohort read-only."""
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--record", type=Path, help="normalized single-tranche JSON record")
    source.add_argument("--cohort", type=Path, help="normalized sibling-candidate cohort JSON")
    args = parser.parse_args()
    path = args.record or args.cohort
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        parser.error(f"could not read JSON input: {error}")
    print(json.dumps(evaluate(payload) if args.record else evaluate_cohort(payload), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
