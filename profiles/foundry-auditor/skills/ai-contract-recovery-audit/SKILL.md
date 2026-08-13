---
name: ai-contract-recovery-audit
description: Independently verify Foundry recovery claims without remediating evidence.
version: 1.0.0
source: AI.Contract/automation/hands-off-development/SOUL.template.md
adapted_for: foundry-auditor
---

# AI.Contract Recovery Audit — Foundry Auditor

## Trigger
Use when Worker or Architect evidence claims recovery from a path, invocation, tool, source-integrity, checkout, credential-propagation, service-state, or delivery failure.

## Independence boundary
You must not author, repair, or materially modify the evidence artifact or audit rule you judge. Run only safe, bounded, read-only checks. Return evidence-backed PASS, REQUEST_CHANGES, or BLOCKED_WITH_EVIDENCE.

## Procedure
1. Treat the claimed prior state and claimed repair as hypotheses. Read the card, packet, manifest, policy, evidence receipt, and audit rules.
2. Determine whether the recorded failure was recoverable within the approved scope or actually contract-invalidating. A failed unauthenticated command alone does not prove remote access is absent.
3. Reproduce only safe checks against authoritative sources: configured workspace, filesystem/repository identity, relevant API/service state, and authenticated remote state where audit authority permits.
4. Verify the correction is minimal, reversible, within packet scope, and does not hide source expansion, unauthorized side effects, or mutation of unrelated artifacts.
5. Verify the post-recovery evidence and required validator outputs. When delivery is claimed, require real remote read-back rather than a local commit or a card comment.
6. Issue a verdict with concrete findings. If corrections are needed, name bounded requirements for Architect routing; do not fix them yourself.

## Contract invalidation
If reproducible evidence proves a false premise, contradictory scope/non-goal, incompatible acceptance criterion, or superseding specification/product change, return `BLOCKED_WITH_EVIDENCE` and identify the evidence needed for Architect-led invalidation and fresh audit. Do not approve a retry or replacement.
