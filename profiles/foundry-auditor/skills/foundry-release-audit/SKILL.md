---
name: foundry-release-audit
description: Independently audit a GitHub release before and after publication.
version: 0.3.0
source: Context Foundry
adapted_for: foundry-auditor
---

# Foundry Release Audit

## When to use
Use to independently audit a Worker release packet for a declared target repository. Do not use to repair, publish, comment, link, or close anything.

## Contract
- Verify target repository slug, checkout remote, and GitHub API target match before accepting evidence.
- Require authenticated remote read-back through the packet’s non-secret helper reference.
- Return `PASS`, `REQUEST_CHANGES`, or `BLOCKED_WITH_EVIDENCE` only.
- Perform distinct pre-publication and post-publication audits.

## Pre-publication audit
1. Verify clean candidate checkout, immutable SHA, remote branch equality, and absent proposed tag/release.
2. Re-run mandatory validation gates and review scope, notes, type, assets policy, and external-write plan.
3. Return PASS only when Worker may create the tag/release.

## Post-publication audit
1. Verify annotated tag object resolves to the audited SHA.
2. Verify release title/tag, draft/prerelease/latest status, body, and assets match the packet.
3. Verify issue evidence, unchanged source state, and no unauthorized external side effect.
4. Return PASS only when the separately assigned Closure Auditor may use its card-derived closure adapter; Worker leaves the Issue open.

## Verification
The verdict cites independent command/API output and distinguishes a missing credential adapter from an unavailable service.

## Anti-patterns
- Treating Worker claims, local commits, or unauthenticated 404s as remote proof.
- Repairing an API payload or an incomplete publication.
- Passing a release without a post-publication read-back.
- Allowing issue closure before post-publication PASS.

## Direct Foundry maintenance boundary

- Do not create Kanban maintenance cards for Foundry profiles, skills, adapters, tests, templates, or process repairs. Karell-authorized maintenance is performed directly in source, independently reviewed, verified against installed behavior, and tracked in a linked GitHub issue when requested.
- AI.Contract remains the sole contract plane for governed product work. A maintenance issue, an old PASS, and a completed Kanban run do not grant current authorization to deliver or close a product tranche.
- Treat structured root-run verdicts as evidence; `done` is not `PASS`. Product REQUEST_CHANGES requires one explicitly linked, current, authorized correction path and fresh independent audit. Maintenance failures require direct maintenance, not a replacement card chain.
- If the target branch has advanced or the old packet is stale, reconcile authenticated current state before selecting an action. Do not redispatch stale Delivery/Closure instructions or close a tracker merely because a merge exists.
- Before dispatch, preflight the actual authorized role envelopes, lineage, and receipt shape through every required installed adapter. Invalid identity, scope, lineage, or receipt must fail before credential acquisition or network/write actions. A green policy-string test is not runtime proof.
- Record one named owner, evidence link, and concrete next decision for unresolved work. Preserve holds and audit evidence. Archive only confirmed superseded chains; do not mark unfinished work complete to reduce blocked counts.
