---
name: foundry-loop
description: Run one authorized AI.Contract-backed cycle from bounded contract authorship through Worker implementation, independent QA, verified integration and final historical publication.
---

# Foundry Loop

Run exactly one native work cycle. Read [operating rules](../OPERATING_RULES.md) and [native interface](../AI_CONTRACT_INTERFACE.md). Resolve the service/project, approved repository/milestone horizon, configured Worker/QA pools and runtime/remote adapters before live execution. Missing service capabilities produce a concrete blocker, never a GitHub issue or local file queue.

1. Use [foundry-create-workorder](../foundry-create-workorder/SKILL.md) and [Architect](../foundry-architect/SKILL.md) to reuse or author the next bounded native revision and verify its Ready state.
2. Use [Coordinator](../foundry-coordinator/SKILL.md) to atomically reserve eligible work for a free configured Worker, re-read current ownership, ensure one actor-bound launch and record acknowledgement. Busy capacity means wait.
3. Use [foundry-implement](../foundry-implement/SKILL.md) for that assignment. Preserve revision/attempt identity and heartbeat through QA. Expiry is not stop evidence; confirm process termination before recovery/reassignment.
4. Assign separate QA and use [foundry-audit](../foundry-audit/SKILL.md). Route reproducible corrections to the same Worker and renew acceptance for changed candidates. Material changes require Architect reassessment/new immutable revision. No fixed correction retry count replaces QA judgment.
5. On current exact-candidate acceptance, use [foundry-commit](../foundry-commit/SKILL.md) for serialized authorized delivery, remote verification, postchecks, native Done and final historical publication. Stop after this cycle.

Carry the same goal, bindings, exclusions and acceptance through all stages. Follow the user's repair/stop policy; resolve authorized routine errors within the stage, and stop on unresolved authority, failed required acceptance or missing dependency. Do not start a successor from an incomplete cycle.

For OpenSpec-backed work include [openspec-foundry](../openspec-foundry/SKILL.md) for requirement/task mapping. It owns planning/tracking, not reservations, attempts or a second execution loop. Planning alone starts no live work. An explicit cycle request authorizes the bounded sequence only within supplied repository/service permissions; it does not grant credentials, new scope or deployment.

Return project/contract/revision/attempt, actual stage, verification, target and historical references. Distinguish local, accepted, delivered and native Done.
