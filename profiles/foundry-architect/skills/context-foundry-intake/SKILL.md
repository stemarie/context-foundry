---
name: context-foundry-intake
description: Turn a bounded objective into a reusable Foundry work brief.
version: 0.1.0
source: Context Foundry v0.1.0
adapted_for: foundry-architect
---

# Context Foundry Intake

## When to use
Use before a new Foundry profile/skill-pack task, a bounded research request, or a reusable operating-pattern revision. Do not use it to create a scheduler, Kanban runtime, monitor, gateway, or service integration.

## Contract
Produce a short, reviewable brief that names the objective, intended reusable artifact, source of truth, role boundaries, non-goals, and verification. The brief is a design input, not an execution engine or a standing task.

## Procedure
1. State the concrete reusable outcome and the users/profiles that need it.
2. Identify authoritative sources and distinguish them from examples or untrusted inputs.
3. Bound the artifact: profile/skill definitions, synchronization, tests, and documentation are in scope; credentials, runtime state, schedules, gateways, and external effects are excluded unless separately authorized.
4. Assign responsibilities: Architect designs and routes; Worker makes bounded changes and evidence; Auditor independently validates and does not remediate.
5. Define observable acceptance criteria and deterministic checks.
6. If a material objective, authority, source, or success criterion is absent, request the smallest decision needed rather than inventing it.

## Output format
```markdown
## Foundry brief
- Objective:
- Reusable artifact:
- Source of truth:
- In scope:
- Non-goals:
- Role boundaries:
- Acceptance criteria:
- Verification:
```

## Pitfalls
- Do not translate a reusable-skill request into a new control plane.
- Do not treat a historical phase document as current authorization.
- Do not embed credentials, host paths, sessions, or runtime state in the brief.
- Do not make the Auditor responsible for implementation.

## Verification
Every brief has a bounded artifact, explicit non-goals, an authoritative source, separate roles, and checks that can prove completion.