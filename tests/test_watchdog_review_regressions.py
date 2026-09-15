"""Independent review regressions: never turn pending/history into recovery."""
import json
import subprocess
import sys
from test_watchdog_recovery import audit, run, payload, IDENTITY, SCANNER


def test_creation_skills_alone_are_not_current_role_authority():
    item = audit()
    del item['task']['skills']
    item['events'] = [{'kind': 'created', 'payload': {'skills': ['context-foundry-auditor']}}]
    records, errors = payload([item])
    assert errors
    assert records[0]['action']['kind'] == 'escalate'


def test_exact_link_with_wrong_recovery_class_requires_disposition_not_duplication():
    recovery = {'id': 't_repair', 'title': 'Worker: repair', 'assignee': 'foundry-worker',
                'skills': ['context-foundry-worker'], 'status': 'running', 'parents': ['t_audit'],
                'body': IDENTITY + '\nRole: Worker\nRecovery audit task: t_audit\nRecovery audit run: 697\nRecovery class: direct_maintenance'}
    records, _ = payload([audit(), recovery])
    action = next(r['action'] for r in records if r['id'] == 't_audit')
    assert action['kind'] == 'escalate'
    assert action['recovery_task_ids'] == ['t_repair']
    assert 'recovery class' in action['reason']


def test_running_audit_is_pending_not_a_failed_recovery():
    item = audit(runs=[run(697, 100, None, status='running', outcome=None, ended_at=None)])
    item['task']['status'] = 'running'
    records, errors = payload([item])
    assert not errors
    assert records[0]['disposition'] == 'audit_pending'
    assert 'action' not in records[0]


def test_notifications_omit_archived_history_and_bulk_lifecycle_payloads(tmp_path):
    live = audit()
    live['runs'][0]['summary'] = 'x' * 100000
    historic = audit()
    historic['task'].update(id='t_old', status='archived')
    path = tmp_path / 'tasks.json'
    path.write_text(json.dumps([live, historic]))
    result = subprocess.run([sys.executable, str(SCANNER), '--input', str(path)], capture_output=True, text=True)
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert [e['id'] for e in data['events']] == ['t_audit']
    assert 'lifecycle' not in data['events'][0]
    assert len(result.stdout) < 5000


def test_malformed_skill_elements_fail_closed_instead_of_crashing():
    item = audit()
    item['task']['skills'] = ['context-foundry-auditor', {'unexpected': 'element'}]
    records, errors = payload([item])
    assert errors
    assert records[0]['action']['kind'] == 'escalate'
