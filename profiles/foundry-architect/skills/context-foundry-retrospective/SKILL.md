---
name: context-foundry-retrospective
description: Draft evidence-backed proposals for reusable profile improvements.
version: 0.1.0
source: Context Foundry v0.1.0
adapted_for: foundry-architect
---

# Context Foundry Retrospective

## When to use
Use after a completed, evidenced profile/skill change reveals a repeatable gap or friction. Do not use to modify skills automatically, to create a recurring review process, or to turn one-off preferences into policy.

## Contract
Create a narrow proposal for a reusable profile or skill improvement. The proposal is review material only; it grants no implementation, scheduler, gateway, credential, or external-write authority.

## Procedure
1. Identify a repeatable failure, ambiguity, or duplicated correction from evidence.
2. State the affected role and why existing guidance does not already cover it.
3. Propose the smallest profile/skill/documentation/test change that addresses the gap.
4. Define regressions the proposal must prevent and deterministic verification required after implementation.
5. List explicit non-goals and any product decision still needed.
6. Submit the proposal for review; do not apply it without a separately authorized work item.

## Output format
```markdown
## Improvement proposal
- Evidence of recurring gap:
- Affected role/artifact:
- Smallest proposed change:
- Regression prevented:
- Verification:
- Non-goals:
- Decision required:
```

## Pitfalls
- Do not silently edit a skill because a retrospective identified a possible improvement.
- Do not use retrospective language to add monitoring, cron, Kanban runtime, or gateway operations.
- Do not propose cross-role authority that defeats independent auditing.

## Verification
The proposal cites concrete prior evidence, targets a single reusable artifact class, and remains unapplied until separately authorized.