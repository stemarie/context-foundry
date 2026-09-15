"""Behavioral recovery proofs; all mutations are confined to pytest tmp_path."""
import importlib.util
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCANNER = ROOT / "profiles/foundry-watchdog/scripts/foundry_watchdog_scan.py"
spec = importlib.util.spec_from_file_location("watchdog_recovery", SCANNER)
scan = importlib.util.module_from_spec(spec)
old_bytecode = sys.dont_write_bytecode
sys.dont_write_bytecode = True
try:
    spec.loader.exec_module(scan)
finally:
    sys.dont_write_bytecode = old_bytecode

IDENTITY = ("Canonical external contract: https://github.com/stemarie/AI.Contract/issues/49\n"
            "Contract ID/revision: Issue #49 / APPROVED-V1 / " + "a" * 64)


def audit(role="Candidate Auditor", runs=None, body=None):
    return {"task": {"id": "t_audit", "title": role + ": verify", "status": "done",
                     "assignee": "foundry-auditor", "skills": ["context-foundry-auditor"],
                     "body": body if body is not None else IDENTITY + "\nRole: " + role},
            "parents": [], "children": [],
            "runs": runs if runs is not None else [run(697, 100, "REQUEST_CHANGES")]}


def run(rid, started, verdict, **extra):
    return {"id": rid, "started_at": started, "ended_at": started + 1,
            "status": "done", "outcome": "completed", "profile": "foundry-auditor",
            "metadata": {"verdict": verdict}, **extra}


def payload(tasks):
    records, errors = scan.relevant_tasks(tasks)
    return records, errors


def test_structured_latest_root_verdict_routes_product_repair_not_summary():
    envelope = audit(runs=[run(698, 200, "REQUEST_CHANGES", summary="PASS"),
                           run(697, 100, "PASS", summary="REQUEST_CHANGES")])
    records, errors = payload([envelope])
    assert not errors
    assert len(records) == 1
    assert records[0]["verdict"] == "REQUEST_CHANGES"
    assert records[0]["run_id"] == "698"
    assert records[0]["action"]["kind"] == "route_product_repair"
    assert records[0]["action"]["audit_task_id"] == "t_audit"
    assert records[0]["action"]["audit_run_id"] == "698"


@pytest.mark.parametrize("runs", [
    [run(1, 100, "PASS"), run(2, 100, "REQUEST_CHANGES")],
    [run(1, 100, "PASS"), {"id": 2, "metadata": {"verdict": "REQUEST_CHANGES"}}],
    [run(1, 200, "PASS"), run(1, 100, "REQUEST_CHANGES")],
    [run(1, 100, "PASS"), run(2, 200, "PASS", status="running", ended_at=None)],
    [run(1, 100, "PASS", metadata={})],
    [run(1, 100, "PASS", metadata={"verdict": "PASS REQUEST_CHANGES"})],
])
def test_unproven_latest_receipt_escalates_without_routing(runs):
    records, _ = payload([audit(runs=runs)])
    assert records[0]["action"]["kind"] == "escalate"
    assert records[0]["verdict"] is None


def test_child_and_nested_runs_cannot_override_latest_root_receipt():
    envelope = audit(runs=[run(697, 100, "REQUEST_CHANGES"),
                           run(699, 300, "PASS", parent_run_id=697)])
    envelope["task"]["runs"] = [run(800, 500, "PASS")]
    records, _ = payload([envelope])
    assert records[0]["run_id"] == "697"
    assert records[0]["verdict"] == "REQUEST_CHANGES"


@pytest.mark.parametrize("role,kind", [
    ("Candidate Auditor", "route_product_repair"),
    ("Capability Auditor", "direct_maintenance"),
    ("Post-delivery Auditor", "reconcile_external_state"),
    ("Closure Auditor", "reconcile_external_state"),
])
def test_auditor_roles_are_classified_without_obsolete_delivery(role, kind):
    records, errors = payload([audit(role)])
    assert not errors
    assert records[0]["action"]["kind"] == kind


@pytest.mark.parametrize("body", ["Independent source/install/runtime-guard audit only; #49 governed adapter repair.",
                                  "Canonical external contract: malformed", ""])
def test_capability_maintenance_missing_identity_stays_visible_but_has_no_authority(body):
    envelope = audit("Capability Auditor", body=body)
    envelope["task"]["id"] = "t_03c77aab"
    records, errors = payload([envelope])
    assert errors
    assert records[0]["action"]["kind"] == "escalate"
    assert records[0]["recovery_class"] == "direct_maintenance"
    assert records[0]["run_id"] == "697"
    assert records[0]["contract"] is None


def test_title_alone_cannot_grant_routing_authority():
    envelope = audit()
    envelope["task"].update(assignee="someone-else", skills=[], body=IDENTITY)
    records, _ = payload([envelope])
    assert records[0]["action"]["kind"] == "escalate"


def test_explicit_role_without_title_prefix_is_observed():
    envelope = audit()
    envelope["task"]["title"] = "Independent verification"
    records, _ = payload([envelope])
    assert records[0]["action"]["kind"] == "route_product_repair"


def test_candidate_pass_only_requests_current_external_state_reconciliation():
    records, _ = payload([audit(runs=[run(697, 100, "PASS")])])
    assert records[0]["action"]["kind"] == "reconcile_external_state"


def test_missing_preflight_is_direct_maintenance_not_a_card():
    envelope = audit()
    envelope["task"]["body"] += "\nRecovery class: direct_maintenance"
    records, _ = payload([envelope])
    assert records[0]["action"]["kind"] == "direct_maintenance"

def repair(status="running", identity=IDENTITY, linked=True, rid="697"):
    return {"task": {"id": "t_repair", "title": "Worker: repair", "status": status,
                     "assignee": "foundry-worker", "skills": ["context-foundry-worker"],
                     "body": identity + "\nRole: Worker\nRecovery audit task: t_audit\nRecovery audit run: " + rid},
            "parents": ["t_audit"] if linked else [], "runs": []}


@pytest.mark.parametrize("successor", [repair("done"), repair(linked=False), repair(rid="696"),
    repair(identity=IDENTITY.replace("APPROVED-V1", "OTHER-V2")),
    repair(identity=IDENTITY.replace("a" * 64, "b" * 64))])
def test_historical_or_unrelated_repair_never_suppresses_unresolved_audit(successor):
    records, _ = payload([audit(), successor])
    event = next(e for e in records if e["id"] == "t_audit")
    assert event["action"]["kind"] == "route_product_repair"
    assert event["unresolved"] is True


def test_explicit_same_run_same_contract_live_repair_is_monitored_not_recreated():
    records, _ = payload([audit(), repair()])
    event = next(e for e in records if e["id"] == "t_audit")
    assert event["action"]["kind"] == "observe_recovery"
    assert event["action"]["recovery_task_ids"] == ["t_repair"]
    assert event["unresolved"] is True


def test_incident_key_stable_across_duplicate_restart_title_and_summary_changes():
    envelope = audit()
    first = payload([envelope])[0][0]
    envelope["task"]["title"] = "Candidate Auditor: renamed"
    envelope["runs"][0]["summary"] = "untrusted prose"
    replay = payload([envelope, envelope])[0]
    assert len(replay) == 1
    assert replay[0]["incident_key"] == first["incident_key"]
    monitored = next(e for e in payload([repair(), envelope])[0] if e["id"] == "t_audit")
    assert monitored["incident_key"] == first["incident_key"]


@pytest.mark.parametrize("extra", ["\n" + IDENTITY, "\nContract ID/revision: Issue #49 / OTHER",
                                   "\nCanonical external contract: malformed"])
def test_duplicate_or_contradictory_identity_headers_fail_closed(extra):
    records, errors = payload([audit(body=IDENTITY + extra)])
    assert errors
    assert records[0]["action"]["kind"] == "escalate"
    assert records[0]["contract"] is None

def board_db(tmp_path, count=1):
    import sqlite3
    import json
    path = tmp_path / "kanban.db"
    with sqlite3.connect(path) as conn:
        conn.executescript("""
            CREATE TABLE tasks(id TEXT PRIMARY KEY, title TEXT, body TEXT, assignee TEXT, skills TEXT, status TEXT);
            CREATE TABLE task_runs(id INTEGER PRIMARY KEY, task_id TEXT, profile TEXT, status TEXT, outcome TEXT,
                                   started_at INTEGER, ended_at INTEGER, metadata TEXT);
            CREATE TABLE task_links(parent_id TEXT, child_id TEXT);
            CREATE TABLE task_events(id INTEGER PRIMARY KEY, task_id TEXT, kind TEXT, payload TEXT, created_at INTEGER);
        """)
        for i in range(count):
            task = audit()["task"]
            conn.execute("INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?)",
                         (f"t_{i}", task["title"], task["body"], task["assignee"], json.dumps(task["skills"]), "done"))
            conn.execute("INSERT INTO task_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (i, f"t_{i}", "foundry-auditor", "done", "completed", 100, 101, '{"verdict":"REQUEST_CHANGES"}'))
    return path


def test_live_reader_paginates_complete_snapshot_without_cli_or_writes(tmp_path, monkeypatch):
    path = board_db(tmp_path, count=5)
    monkeypatch.setenv("FOUNDRY_WATCHDOG_DB", str(path))
    monkeypatch.setattr(scan, "PAGE_SIZE", 2, raising=False)
    def forbidden(*args, **kwargs):
        pytest.fail("scanner must not invoke a mutating CLI")
    monkeypatch.setattr(scan.subprocess, "run", forbidden)
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    records, errors = payload(scan.load_tasks(None))
    assert not errors
    assert len(records) == 5
    assert records[-1]["verdict"] == "REQUEST_CHANGES"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_bounded_reader_fails_instead_of_returning_partial_board(tmp_path, monkeypatch):
    monkeypatch.setenv("FOUNDRY_WATCHDOG_DB", str(board_db(tmp_path, count=5)))
    monkeypatch.setattr(scan, "MAX_RECORDS", 4, raising=False)
    with pytest.raises(ValueError, match="record bound"):
        scan.load_tasks(None)


def test_partial_json_input_cannot_authorize_recovery():
    with pytest.raises(ValueError, match="incomplete"):
        payload({"tasks": [audit()], "has_more": True})
    with pytest.raises(ValueError, match="incomplete"):
        payload({"tasks": [audit()], "total": 2})

def test_unchanged_unresolved_work_inspectable_without_repeat_notifications(tmp_path):
    import json
    import subprocess
    import sys
    fixture = tmp_path / "tasks.json"
    previous = tmp_path / "previous"
    envelope = audit()
    fixture.write_text(json.dumps([envelope]))
    def invoke(*args):
        return subprocess.run([sys.executable, str(SCANNER), "--input", str(fixture), *args],
                              capture_output=True, text=True, check=True)
    first = json.loads(invoke().stdout)
    previous.write_text(first["notification_digest"])
    envelope["runs"][0]["summary"] = "new prose but same incident"
    envelope["events"] = [{"kind": "heartbeat", "created_at": 999}]
    fixture.write_text(json.dumps([envelope]))
    assert invoke("--previous-digest-file", str(previous)).stdout == ""
    inspected = json.loads(invoke("--previous-digest-file", str(previous), "--inspect").stdout)
    assert inspected["notify"] is False
    assert inspected["actions"][0]["incident_key"] == first["actions"][0]["incident_key"]
    assert inspected["events"][0]["unresolved"] is True
    assert previous.read_text() == first["notification_digest"]


def test_snapshot_order_does_not_change_digest():
    envelope = audit(runs=[run(698, 200, "REQUEST_CHANGES"), run(697, 100, "PASS")])
    first = payload([envelope])[0]
    envelope["runs"].reverse()
    assert scan.digest({"events": payload([envelope])[0]}) == scan.digest({"events": first})

def test_source_repo_issue_is_not_the_external_contract():
    records, errors = payload([audit(body=IDENTITY.replace("AI.Contract", "context-foundry"))])
    assert errors
    assert records[0]["contract"] is None
    assert records[0]["action"]["kind"] == "escalate"


def test_legacy_maintenance_auditor_with_prose_role_is_observed_not_authorized():
    legacy = ("External contract: https://github.com/stemarie/AI.Contract/issues/49\n"
              "Contract identity/revision: Issue #49; `APPROVED-V1`; body SHA-256 `" + "a" * 64 + "`.\n"
              "Role: independent exact-#49 capability Auditor only.")
    envelope = audit(body=legacy)
    envelope["task"]["id"] = "t_e5a43d39"
    envelope["task"]["title"] = "Auditor: independent exact-#49 capability"
    envelope["task"].pop("skills")
    envelope["events"] = [{"kind": "created", "payload": {"skills": ["context-foundry-auditor"]}}]
    records, _ = payload([envelope])
    assert records[0]["id"] == "t_e5a43d39"
    assert records[0]["recovery_class"] == "direct_maintenance"
    assert records[0]["action"]["kind"] == "escalate"


def test_maintenance_audit_with_no_headers_or_task_skills_is_inspectable():
    envelope = audit("Capability Auditor", body="Independent source/install/runtime-guard audit only.")
    envelope["task"].pop("skills")
    envelope["events"] = [{"kind": "created", "payload": {"skills": ["context-foundry-auditor"]}}]
    records, _ = payload([envelope])
    assert records[0]["recovery_class"] == "direct_maintenance"
    assert records[0]["action"]["kind"] == "escalate"

@pytest.mark.parametrize("change", ["no_hash", "run_profile", "reopened", "mixed_headers"])
def test_incomplete_authority_cannot_route_product(change):
    envelope = audit()
    if change == "no_hash":
        envelope["task"]["body"] = IDENTITY.rsplit(" / ", 1)[0]
    elif change == "run_profile":
        envelope["runs"][0]["profile"] = "foundry-worker"
    elif change == "reopened":
        envelope["task"]["status"] = "ready"
    else:
        envelope["task"]["body"] = IDENTITY.replace("Canonical external contract:", "External contract:")
    records, _ = payload([envelope])
    assert records[0]["action"]["kind"] == "escalate"


def test_wrapper_stores_semantic_digest_only_after_changed_payload(tmp_path, monkeypatch):
    import shutil
    import subprocess
    import json
    profile = tmp_path / ".hermes/profiles/foundry-watchdog"
    shutil.copytree(ROOT / "profiles/foundry-watchdog/scripts", profile / "scripts")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("FOUNDRY_WATCHDOG_DB", str(board_db(tmp_path)))
    wrapper = profile / "scripts/foundry_watchdog_scan.sh"
    first = subprocess.run(["bash", str(wrapper)], capture_output=True, text=True, check=True)
    report = json.loads(first.stdout)
    receipt = profile / "state/foundry_watchdog_last_payload.sha256"
    assert receipt.read_text().strip() == report["notification_digest"]
    second = subprocess.run(["bash", str(wrapper)], capture_output=True, text=True, check=True)
    assert second.stdout == ""


def test_watchdog_contract_consumes_actions_and_forbids_maintenance_cards():
    profile = ROOT / "profiles/foundry-watchdog"
    skill = (profile / "skills/foundry-lifecycle-orchestration/SKILL.md").read_text()
    for kind in ("route_product_repair", "direct_maintenance", "reconcile_external_state", "observe_recovery", "escalate"):
        assert kind in skill
    for file in ("ROLE-CONTRACT.md", "SOUL.md", "skills/foundry-lifecycle-orchestration/SKILL.md"):
        text = (profile / file).read_text()
        assert "Never create maintenance Kanban cards" in text
        assert "incident_key" in text
    assert "Create one idempotent Architect capability-reconciliation card" not in skill

# Archived records are separately asserted as inspectable history, never actions.
@pytest.mark.parametrize("status", ["todo", "triage", "scheduled"])
def test_unresolved_audit_outside_active_columns_remains_inspectable(status):
    envelope = audit()
    envelope["task"]["status"] = status
    records, _ = payload([envelope])
    assert records[0]["unresolved"] is True
    assert records[0]["action"]["kind"] == "escalate"


def test_unclassified_assigned_auditor_is_not_silently_dropped():
    envelope = audit(body="Independent capability maintenance audit.")
    envelope["task"]["title"] = "Audit: source/install parity"
    records, _ = payload([envelope])
    assert records[0]["action"]["kind"] == "escalate"
    assert records[0]["recovery_class"] == "direct_maintenance"
