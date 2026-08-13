packet_id: CF-P1-role-model
question: How should AI.Contract's current Coordinator/Worker model be extended into Architect/Worker/Auditor, based on the approved pilot corpus?
source_ids: []
allowed_operations: [read, search, extract, test]
forbidden_operations: [write_external_system, edit_global_skill, execute_untrusted_code]
budget:
  max_turns: 25
  max_wall_time_minutes: 30
  max_retries: 1
output:
  evidence_json: evidence/CF-P1-role-model.json
  evidence_markdown: evidence/CF-P1-role-model.md
quality_gate: python3 scripts/validate_evidence.py evidence/CF-P1-role-model.json --packet packets/CF-P1-role-model.md
handoff: Kanban comment with artifact paths, confidence, limitations, and concise conclusion.
