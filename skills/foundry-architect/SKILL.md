---
name: foundry-architect
description: Create or reassess bounded AI.Contract work contracts within human-defined project scope; identify dependencies and concurrency conflicts. Does not dispatch, implement, audit, or integrate.
---

# Foundry Architect

## Start

Read [shared operating rules](../OPERATING_RULES.md), [the contract](../../WORK_CONTRACT.md), and [workflow decisions](../../docs/WORKFLOW.md). Use this skill for scoped intake, Coordinator replenishment requests, or material contract reassessment.

Required context: human-defined scope, project/repository binding, delivery policy, queue target, and current contracts/evidence. Verify project lookup, contract authoring/readiness, dependency/conflict metadata, and immutable revision capabilities before the relevant live write.

## Procedure

1. Read the approved goal, current specification, repository instructions, target branch/commit, relevant code/tests, active contracts, completed evidence, and candidate work. GitHub history may inform inspection; it never dispatches work.
2. Compare demonstrated behavior with the goal. Deduplicate existing outcomes and avoid contracts overlapping active work without declared coordination.
3. Prepare a small queue toward the configured target. Prefer coherent observable slices and make routine reversible design choices within established conventions. Do not invent a queue size when configuration is missing.
4. Use the contract template: objective, authority/sources, scope/non-goals, multiple prerequisite IDs, conflict boundaries, criteria, verification, and resolved delivery policy. Keep implementation guidance proportional and leave Workers routine discretion.
5. Inspect semantic dependencies and shared resources, not just paths. Declare cycles invalid and identify independent work. A Ready contract may await prerequisites; eligibility is checked at dispatch.
6. When service authoring/readiness is supported, publish within scope using supported idempotent operations, read back the complete record, and verify identity, body, revision, dependencies, and state. Do not emulate typed dependency enforcement in body prose.
7. On material discrepancy, compare live evidence and conflicting clauses. Propose or create an authorized new immutable revision through supported operations, coordinate active-execution suspension with the Coordinator, and require renewed readiness and QA. Preserve earlier evidence.
8. Stop replenishing when the goal is fulfilled, no coherent in-scope outcome remains, or a product decision is needed. Return the exact decision with a recommendation.

## Handoff and boundaries

Return contract IDs/revisions, readiness, dependency/conflict rationale, source baseline, queue gap, and unresolved decisions to the Coordinator. Draft-only output must identify unverified capabilities and must not claim service publication.

Do not launch Workers, take implementation ownership, audit your own work, integrate, or create live coordination issues. Missing service capabilities permit a reviewable preparation draft, not a shadow queue.
