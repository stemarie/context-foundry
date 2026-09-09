#!/usr/bin/env python3
"""Close only the canonical Issue dynamically derived from a governed card."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

PROFILE = "foundry-auditor"
BOARD = "context-foundry"
RECEIPT_MARKER = "FOUNDRY_CLOSURE_RECEIPT_V1"
REPOSITORY = "stemarie/context-foundry"
ORIGIN = "https://github.com/stemarie/context-foundry.git"
API_TARGET = "https://api.github.com/repos/stemarie/context-foundry"
BRANCH = "main"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
TASK_ID = re.compile(r"^t_[0-9a-f]{8}$")
CONTRACT_URL = re.compile(r"^https://github\.com/stemarie/context-foundry/issues/([1-9][0-9]*)$")
CONTRACT_MARKER = re.compile(r"^FOUNDRY-[A-Z0-9-]+-CONTRACT-V1$")


class ClosureError(RuntimeError):
    pass


def exact_dict(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != keys:
        raise ClosureError(f"{label} has unsupported or missing fields")
    return value


def contract_reference(closure: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if closure.get("assignee") != PROFILE or not str(closure.get("title", "")).startswith("Closure Auditor:"):
        raise ClosureError("assigned task is not a foundry-auditor Closure Auditor card")
    body = closure.get("body")
    if not isinstance(body, str):
        raise ClosureError("Closure Auditor card body is invalid")
    lines = body.splitlines()
    if len(lines) != 5:
        raise ClosureError("Closure Auditor card must contain only the canonical reference fields")
    url_match = re.fullmatch(r"Canonical external contract: (https://github\.com/stemarie/context-foundry/issues/[1-9][0-9]*)", lines[0])
    revision_match = re.fullmatch(r"Contract ID/revision: Issue #([1-9][0-9]*) / (FOUNDRY-[A-Z0-9-]+-CONTRACT-V1)", lines[1])
    if not url_match or not revision_match or lines[2:4] != ["Role: Closure Auditor", "Dependency: completed direct Delivery parent"]:
        raise ClosureError("Closure Auditor card does not exactly reference one canonical contract")
    issue_match = CONTRACT_URL.fullmatch(url_match.group(1))
    if not issue_match or int(issue_match.group(1)) != int(revision_match.group(1)) or not CONTRACT_MARKER.fullmatch(revision_match.group(2)):
        raise ClosureError("Closure Auditor contract reference is malformed or inconsistent")
    receipt_match = re.fullmatch(r"Receipt pointer: Delivery `(t_[0-9a-f]{8})`", lines[4])
    if not receipt_match:
        raise ClosureError("Closure Auditor card has no exact Delivery receipt pointer")
    return receipt_match.group(1), {"repository": REPOSITORY, "origin": ORIGIN, "api_target": API_TARGET, "issue": int(issue_match.group(1)), "branch": BRANCH, "issue_marker": revision_match.group(2), "receipt_marker": RECEIPT_MARKER}


def completed_parent(card: dict[str, Any], lookup: Callable[[str], dict[str, Any]], prefix: str) -> tuple[str, dict[str, Any]]:
    parents = card.get("parents")
    if not isinstance(parents, list) or len(parents) != 1 or not isinstance(parents[0], str) or not TASK_ID.fullmatch(parents[0]):
        raise ClosureError(f"{prefix} card requires exactly one valid parent")
    task_id = parents[0]
    task = lookup(task_id).get("task")
    if not isinstance(task, dict) or task.get("id") != task_id or task.get("status") != "done" or not str(task.get("title", "")).startswith(prefix + ":"):
        raise ClosureError(f"direct parent is not a completed {prefix} card")
    return task_id, task


def candidate_has_completed_worker_parent(candidate: dict[str, Any], lookup: Callable[[str], dict[str, Any]]) -> str:
    parents = candidate.get("parents")
    if not isinstance(parents, list) or len(parents) != len(set(parents)):
        raise ClosureError("Candidate Auditor has invalid or duplicate parents")
    workers = []
    for task_id in parents:
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise ClosureError("Candidate Auditor has an invalid parent identity")
        task = lookup(task_id).get("task")
        if isinstance(task, dict) and task.get("id") == task_id and task.get("status") == "done" and task.get("assignee") == "foundry-worker" and str(task.get("title", "")).startswith("Worker:"):
            workers.append(task_id)
    if len(workers) != 1:
        raise ClosureError("Candidate Auditor requires exactly one completed Worker parent")
    return workers[0]


def bound_fields(receipt: dict[str, Any], scope: dict[str, Any], fields: tuple[str, ...], label: str) -> None:
    for field in fields:
        if receipt.get(field) != scope[field]:
            raise ClosureError(f"{label} does not exactly bind {field}")


def candidate_receipt(candidate: dict[str, Any], scope: dict[str, Any]) -> str:
    if candidate.get("assignee") != PROFILE:
        raise ClosureError("Candidate Auditor is not independently assigned to foundry-auditor")
    metadata = exact_dict(candidate.get("metadata"), {"closure_candidate_audit_v1"}, "Candidate Auditor metadata")
    receipt = exact_dict(metadata["closure_candidate_audit_v1"], {"schema_version", "verdict", "repository", "origin", "api_target", "issue", "branch", "candidate_sha"}, "Candidate Auditor receipt")
    if receipt["schema_version"] != "closure_candidate_audit_v1" or receipt["verdict"] != "PASS":
        raise ClosureError("Candidate Auditor receipt is not a PASS")
    bound_fields(receipt, scope, ("repository", "origin", "api_target", "issue", "branch"), "Candidate Auditor receipt")
    candidate_sha = receipt.get("candidate_sha")
    if not isinstance(candidate_sha, str) or not HEX40.fullmatch(candidate_sha):
        raise ClosureError("Candidate Auditor receipt has an invalid candidate SHA")
    return candidate_sha


def delivery_receipt(delivery: dict[str, Any], candidate_id: str, scope: dict[str, Any]) -> None:
    metadata = exact_dict(delivery.get("metadata"), {"closure_delivery_receipt_v1"}, "Delivery metadata")
    receipt = exact_dict(metadata["closure_delivery_receipt_v1"], {"schema_version", "outcome", "delivery_mode", "repository", "origin", "api_target", "issue", "branch", "candidate_sha", "delivered_sha", "candidate_auditor_task_id"}, "Delivery receipt")
    if receipt["schema_version"] != "closure_delivery_receipt_v1" or receipt["outcome"] != "DELIVERED" or receipt["delivery_mode"] != "non-force-direct-main":
        raise ClosureError("Delivery receipt has invalid delivery state")
    bound_fields(receipt, scope, ("repository", "origin", "api_target", "issue", "branch", "candidate_sha"), "Delivery receipt")
    if receipt["delivered_sha"] != scope["candidate_sha"] or receipt["candidate_auditor_task_id"] != candidate_id:
        raise ClosureError("Delivery receipt does not bind delivered SHA and Candidate Auditor parent")


def derive_scope(closure: dict[str, Any], lookup: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
    receipt_delivery_id, scope = contract_reference(closure)
    delivery_id, delivery = completed_parent(closure, lookup, "Delivery")
    if receipt_delivery_id != delivery_id:
        raise ClosureError("Closure Auditor receipt pointer is not its direct Delivery parent")
    candidate_id, candidate = completed_parent(delivery, lookup, "Candidate Auditor")
    worker_id = candidate_has_completed_worker_parent(candidate, lookup)
    if len({closure.get("id"), delivery_id, candidate_id, worker_id}) != 4:
        raise ClosureError("Worker, Candidate Auditor, Delivery, and Closure Auditor must be distinct")
    scope["candidate_sha"] = candidate_receipt(candidate, scope)
    delivery_receipt(delivery, candidate_id, scope)
    return scope


def git_output(workspace: str, *args: str) -> str:
    run = subprocess.run(["git", "-C", workspace, *args], capture_output=True, text=True, check=False, timeout=30)
    if run.returncode:
        raise ClosureError("could not read Closure Auditor workspace Git state")
    return run.stdout.strip()


def validate_workspace(closure: dict[str, Any], scope: dict[str, Any]) -> None:
    workspace = closure.get("workspace_path")
    if not isinstance(workspace, str) or not workspace:
        raise ClosureError("Closure Auditor card has no workspace path")
    if git_output(workspace, "remote", "get-url", "origin") != scope["origin"]:
        raise ClosureError("Closure Auditor workspace origin differs from governed delivery")
    remote_branch = git_output(workspace, "ls-remote", "origin", f"refs/heads/{scope['branch']}").split()
    if not remote_branch or remote_branch[0] != scope["candidate_sha"]:
        raise ClosureError("Closure Auditor workspace remote branch differs from delivered candidate SHA")


def token() -> str:
    env_file = Path.home() / ".hermes" / "profiles" / PROFILE / ".env"
    try:
        lines = env_file.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise ClosureError("Auditor credential helper configuration is unreadable") from error
    for line in lines:
        if line.startswith("GITHUB_TOKEN="):
            value = line.split("=", 1)[1].strip().strip('"').strip("'")
            if value:
                return value
    raise ClosureError("Auditor credential helper configuration lacks a token")


def api(method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
    request = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode("utf-8"), method=method, headers={"Authorization": "Bearer " + token(), "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise ClosureError(f"GitHub {method} {url} returned HTTP {error.code}") from error


def receipt_count(comments: list[dict[str, Any]], marker: str) -> int:
    return sum(marker in str(comment.get("body", "")) for comment in comments)


def execute(closure: dict[str, Any], lookup: Callable[[str], dict[str, Any]], request: Callable[[str, str, dict[str, Any] | None], Any] = api) -> dict[str, Any]:
    scope = derive_scope(closure, lookup)
    validate_workspace(closure, scope)
    base, branch, issue_number, sha, marker = scope["api_target"], scope["branch"], scope["issue"], scope["candidate_sha"], scope["receipt_marker"]
    repo = request("GET", base, None)
    if repo.get("full_name") != scope["repository"] or repo.get("default_branch") != branch:
        raise ClosureError("GitHub API repository does not resolve to governed delivery")
    ref = request("GET", f"{base}/git/ref/heads/{branch}", None)
    if ref.get("object", {}).get("sha") != sha:
        raise ClosureError("GitHub API branch does not resolve to delivered candidate SHA")
    issue_url = f"{base}/issues/{issue_number}"
    issue = request("GET", issue_url, None)
    if f"<!-- {scope['issue_marker']} -->" not in str(issue.get("body", "")):
        raise ClosureError("canonical Issue lacks the required marker")
    comments_url = issue_url + "/comments?per_page=100"
    comments = request("GET", comments_url, None)
    if not isinstance(comments, list):
        raise ClosureError("Issue comments response is malformed")
    existing = receipt_count(comments, marker)
    if existing > 1:
        raise ClosureError("multiple closure receipts exist")
    if issue.get("state") == "closed":
        if existing != 1 or not issue.get("closed_at"):
            raise ClosureError("closed Issue lacks exactly one closure receipt")
        return {"operation": "idempotent-readback", "repository": scope["repository"], "issue": issue_number, "candidate_sha": sha}
    if issue.get("state") != "open" or existing:
        raise ClosureError("open Issue has an invalid pre-existing closure receipt or state")
    request("POST", comments_url, {"body": f"<!-- {marker} -->\nFoundry Closure Auditor PASS\n\n- Closure card: `{closure['id']}`\n- Delivered `{branch}` SHA: `{sha}`\n- Required Issue marker verified: `{scope['issue_marker']}`"})
    readback_comments = request("GET", comments_url, None)
    if not isinstance(readback_comments, list) or receipt_count(readback_comments, marker) != 1:
        raise ClosureError("closure receipt read-back was not exactly one")
    request("PATCH", issue_url, {"state": "closed", "state_reason": "completed"})
    final_issue = request("GET", issue_url, None)
    final_comments = request("GET", comments_url, None)
    if final_issue.get("state") != "closed" or not final_issue.get("closed_at") or not isinstance(final_comments, list) or receipt_count(final_comments, marker) != 1:
        raise ClosureError("Issue close read-back failed")
    return {"operation": "closed", "repository": scope["repository"], "issue": issue_number, "candidate_sha": sha}


def live_card(task_id: str) -> dict[str, Any]:
    run = subprocess.run(["hermes", "kanban", "--board", BOARD, "show", task_id, "--json"], capture_output=True, text=True, check=False, timeout=30)
    if run.returncode:
        raise ClosureError("could not read Closure Auditor Kanban card")
    try:
        data = json.loads(run.stdout)
    except json.JSONDecodeError as error:
        raise ClosureError("Closure Auditor Kanban response was invalid") from error
    if not isinstance(data, dict) or not isinstance(data.get("task"), dict):
        raise ClosureError("Closure Auditor Kanban response was malformed")
    return data


def main() -> None:
    task_id = os.environ.get("HERMES_KANBAN_TASK")
    if not task_id or not TASK_ID.fullmatch(task_id):
        raise ClosureError("adapter requires its assigned canonical HERMES_KANBAN_TASK")
    closure = live_card(task_id)["task"]
    closure["id"] = task_id
    print(json.dumps(execute(closure, live_card), sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except ClosureError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)