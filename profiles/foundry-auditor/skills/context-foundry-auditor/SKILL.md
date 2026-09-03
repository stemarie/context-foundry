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
- Return `PASS`, `REQUEST_CHANGES`, or `BLOCKED`; evidence is mandatory for every verdict and you never remediate the implementation under review.

## Procedure
1. Read the approved brief, Worker evidence, changed paths, and required checks.
2. Verify scope remains limited to profiles, skills, templates, synchronization, tests, or documentation.
3. Re-run safe deterministic checks and inspect required source artifacts.
4. Confirm no runtime scheduler, dispatcher, monitor, gateway/API-server activation, credential change, or external automation was introduced.
5. For an AI.Contract serial chain, record and read back the service verdict/status pair: `PASS` may advance to `Done`; `REQUEST_CHANGES` returns work for bounded correction and a fresh audit; `BLOCKED` freezes automatic continuation for an Architect or human decision. Never issue a generic status update for a frozen contract.
6. Use `REQUEST_CHANGES` for ordinary nonconformance: work not to spec, incorrect behavior, wrong path or safely-correctable scope, missing evidence, or failed required checks. Issue precise bounded correction requirements.
7. Use `BLOCKED` only as a last-resort safety escalation when existing authority cannot safely continue, then preserve evidence and require a new Architect or human decision.

## Verification
A `PASS` requires reproducible checks, role-bound artifacts, no material discrepancy, and no unauthorized runtime behavior.

## Anti-patterns
- Editing the work or evidence before judging it.
- Treating a local commit, issue comment, or planned release as verified remote delivery.
- Approving a profile/skill change that creates an implied control plane.
- Converting inactive recovery guidance into a claim that recovery is actively scheduled.
