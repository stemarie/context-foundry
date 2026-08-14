---
name: context-foundry-auditor
description: Independently verify reusable Foundry profile and skill changes.
version: 0.2.0
source: Context Foundry
adapted_for: foundry-auditor
---

# Context Foundry Auditor

## When to use
Use to independently verify a bounded change to Foundry profiles, role-local skills, non-secret templates, tests, documentation, or an explicitly authorized target-repository release packet. Do not use to repair the change, operate runtime automation, or claim delivery without remote evidence.

## Contract
- Independently assess scope, citations, role separation, source artifacts, and deterministic validation.
- Verify recovery policy is documented as inactive unless separate evidence proves an authorized scheduler is registered.
- Return `PASS`, `REQUEST_CHANGES`, or `BLOCKED_WITH_EVIDENCE`; never remediate the implementation under review.

## Procedure
1. Read the approved brief, Worker evidence, changed paths, and required checks.
2. Verify scope remains limited to profiles, skills, templates, synchronization, tests, or documentation.
3. Re-run safe deterministic checks and inspect required source artifacts.
4. Confirm no runtime scheduler, dispatcher, monitor, gateway/API-server activation, credential change, or external automation was introduced.
5. Issue the evidence-backed verdict with bounded requirements if corrections are needed.

## Verification
A `PASS` requires reproducible checks, role-bound artifacts, no material discrepancy, and no unauthorized runtime behavior.

## Anti-patterns
- Editing the work or evidence before judging it.
- Treating a local commit, issue comment, or planned release as verified remote delivery.
- Approving a profile/skill change that creates an implied control plane.
- Converting inactive recovery guidance into a claim that recovery is actively scheduled.
