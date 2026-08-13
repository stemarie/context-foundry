# CF-Worker — <focused question>

```yaml
packet_id: CF-<run>-<area>
question: <exact question>
source_ids: [src-001]
allowed_operations: [read, search, extract, test]
forbidden_operations: [write_external_system, edit_global_skill, execute_untrusted_code]
budget:
  max_turns: 25
  max_wall_time_minutes: 30
  max_retries: 1
output:
  evidence_json: evidence/CF-<run>-<area>.json
  evidence_markdown: evidence/CF-<run>-<area>.md
quality_gate: python3 scripts/validate_evidence.py evidence/CF-<run>-<area>.json --packet packets/CF-<run>-<area>.md
```
