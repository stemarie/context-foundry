# CF-P1 Control-Plane Work Contract

**GitHub Issue:** [#2](https://github.com/stemarie/context-foundry/issues/2)
**Owner:** `foundry-architect`
**Repository:** `stemarie/context-foundry` (`main`)
**Kanban board:** `context-foundry`

## Objective

Activate the temporary Context Foundry Phase 1 control plane while preserving the required human corpus-approval gate.

## In scope

- Role-local Architect, Worker, and Auditor profiles and their minimal Foundry skills.
- Dedicated `context-foundry` Kanban board.
- Completion-triggered continuation plus a quiet hourly recovery fallback.
- A root corpus-selection card assigned to the Architect.
- An open GitHub Issue containing the Worker’s future role-model evidence contract.
- An operational receipt identifying the board, root card, recovery job, hook, and safety constraints.

## Safety contract

- Do not dispatch the Worker evidence packet before Karell approves the exact selected corpus.
- No Phase 2+ monitors, health jobs, retrospectives, public actions, or unrelated external effects.
- Maintain one active repository writer.
- Use only GitHub Issues and the dedicated Kanban board as durable work-control records.

## Acceptance criteria

1. The board and three profiles exist and are configured with their respective role contracts.
2. Exactly one initial Architect corpus-selection card exists and has a deterministic idempotency key.
3. A `kanban_task_completed` observer invokes the safe continuation tick.
4. An enabled once-hourly no-agent fallback invokes the same tick and is silent on healthy no-op runs.
5. The GitHub Worker contract Issue remains open until independently audited evidence is delivered.
6. The verified control-plane receipt and all repository changes are pushed to `main`, with this Issue closed by the delivery commit.
