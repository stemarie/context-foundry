# Context Foundry Phase 1 Operations Receipt

## Active resources

- Repository: `https://github.com/stemarie/context-foundry` (`main`)
- Hermes Kanban board: `context-foundry`
- Root corpus-selection card: `t_f856515d` (assigned to `foundry-architect`)
- Control-plane contract: GitHub Issue [#2](https://github.com/stemarie/context-foundry/issues/2)
- Future Worker evidence contract: GitHub Issue [#3](https://github.com/stemarie/context-foundry/issues/3)
- Completion observer: `kanban_task_completed` → `/home/karell/.hermes/scripts/context_foundry_phase1_tick.py`
- Recovery fallback: cron job `7259ab347ac8`, `every 1h`, no-agent, silent on healthy no-op

## Current state

- Phase 1 is active.
- `state/phase-1.json` records `corpus_approval: covered_by_authorized_work_order`.
- The Architect mapped the hash-pinned corpus; the work order authorizes its bounded, read-only use.
- Worker evidence work may be created and dispatched; no separate corpus approval is required.

## Role boundaries

- `foundry-architect`: map, gate, route, and synthesize; cannot do Worker/Auditor work.
- `foundry-worker`: execute a bounded approved packet and produce cited evidence.
- `foundry-auditor`: independently audit; it cannot author/repair then approve Worker evidence.
- All roles use the private Foundry repository and dedicated board. One active repository writer is permitted.

## Delivery contracts

- Foundation delivery: GitHub Issue [#1](https://github.com/stemarie/context-foundry/issues/1), closed by commit `22325e156df594d9eff05fcc3e680f1f8d1cf105` after source tests, inventory/extraction smoke checks, and remote SHA verification.
- Control-plane delivery: Issue #2 is closed only by this receipt's verified setup commit.
- Worker evidence delivery: Issue #3 remains open until a Worker evidence commit follows an independent Auditor `PASS`, then closes via `Closes #3`.

## Verification commands

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/*.py
/home/karell/.local/bin/hermes hooks doctor
/home/karell/.local/bin/hermes kanban --board context-foundry show t_f856515d --json
```

## Explicit non-goals

Phase 2+ monitors, health jobs, retrospectives, recursive expansion, and unapproved public/external effects are not enabled.
