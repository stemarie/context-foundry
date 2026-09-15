"""Acceptance probes found by live recovery replay, not policy-string tests."""
from test_watchdog_recovery import audit, run, payload, IDENTITY


def test_archived_audit_preserves_history_without_new_recovery_action():
    item = audit()
    item['task']['status'] = 'archived'
    records, errors = payload([item])
    assert len(records) == 1
    assert records[0]['verdict'] == 'REQUEST_CHANGES'
    assert records[0]['disposition'] == 'archived_history'
    assert 'action' not in records[0]
    assert not errors


def test_capability_pass_does_not_request_maintenance():
    records, errors = payload([audit('Capability Auditor', runs=[run(697, 100, 'PASS')])])
    assert not errors
    assert records[0]['verdict'] == 'PASS'
    assert records[0]['disposition'] == 'audit_pass_not_release_authority'
    assert not records[0]['unresolved']
    assert 'action' not in records[0]


def test_lowercase_role_cannot_hide_assigned_auditor_verdict():
    item = audit(body=IDENTITY + '\nRole: independent capability auditor only')
    records, errors = payload([item])
    assert records[0]['verdict'] == 'REQUEST_CHANGES'
    assert records[0]['action']['kind'] == 'escalate'
    assert errors


def test_blocked_exact_recovery_is_not_runnable_and_must_not_duplicate():
    item = audit()
    recovery = {'id': 't_repair', 'title': 'Worker: repair', 'assignee': 'foundry-worker',
                'skills': ['context-foundry-worker'], 'status': 'blocked',
                'parents': ['t_audit'],
                'body': IDENTITY + '\nRole: Worker\nRecovery audit task: t_audit\nRecovery audit run: 697'}
    records, _ = payload([item, recovery])
    action = next(r['action'] for r in records if r['id'] == 't_audit')
    assert action['kind'] == 'escalate'
    assert action['recovery_task_ids'] == ['t_repair']
    assert 'not runnable' in action['reason']


def test_real_show_created_event_skills_are_validated():
    item = audit()
    del item['task']['skills']
    item['events'] = [{'kind': 'created', 'payload': {'skills': ['context-foundry-auditor']}}]
    records, errors = payload([item])
    assert errors
    assert records[0]['action']['kind'] == 'escalate'
    item['task']['skills'] = ['unrelated-skill']
    records, errors = payload([item])
    assert errors
    assert records[0]['action']['kind'] == 'escalate'
