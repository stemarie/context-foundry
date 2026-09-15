---
name: foundry-release-delivery
description: Deliver an audited GitHub release from a frozen candidate.
version: 0.3.0
source: Context Foundry
adapted_for: foundry-worker
---

# Foundry Release Delivery

## When to use
Use after Architect supplies a bounded target-repository release packet. Do not use without a frozen candidate, approved authentication-helper reference, and Auditor-defined gates.

## Contract
- Worker owns approved source commits, issue evidence/linking, tag/release publication, and remote read-back; it leaves delivery Issues open.
- Before every external write, require target repository slug = checkout remote = GitHub API target.
- Use only the packet’s non-secret authentication helper; never print, copy, or change credentials.
- Publish only after Candidate Auditor PASS and pre-publication Auditor PASS. For merge-required source work, a distinct Integration Auditor must PASS the exact integration PR head; Closure Auditor may close a product-milestone Issue only after non-force merge, authenticated default-branch ancestry/read-back, and post-merge checks bound to that read-back revision.

## Procedure
1. Run authenticated preflight: candidate branch/SHA, tag/release absence, and clean checkout.
2. Make only approved source changes. If a commit is required, link it to the issue and return the new SHA for fresh audit.
3. Run required validation gates and submit evidence to Auditor.
4. After pre-publication PASS, create the annotated tag and read it back before creating the release.
5. Create the approved release, read back its metadata/body/assets, and add Worker evidence to the issue.
6. If an external step partially succeeds, verify prior writes and repair only the failed step idempotently.
7. After post-publication PASS, add final evidence and leave the Issue open for the distinct Closure Auditor step.

## Verification
Evidence contains exact SHA, command outcomes, tag object/target, release URL/fields/assets, issue URLs/comments, and authenticated read-back.

## Anti-patterns
- Publishing before pre-publication audit or closing before post-publication audit.
- Retagging, overwriting a release, or retrying without inspecting partial state.
- Calling missing `gh` or bare HTTPS Git proof that authenticated access is unavailable.
- Publishing images/assets or changing source outside packet scope.

## Direct Foundry maintenance boundary

- Do not create Kanban maintenance cards for Foundry profiles, skills, adapters, tests, templates, or process repairs. Karell-authorized maintenance is performed directly in source, independently reviewed, verified against installed behavior, and tracked in a linked GitHub issue when requested.
- AI.Contract remains the sole contract plane for governed product work. A maintenance issue, an old PASS, and a completed Kanban run do not grant current authorization to deliver or close a product tranche.
- Treat structured root-run verdicts as evidence; `done` is not `PASS`. Product REQUEST_CHANGES requires one explicitly linked, current, authorized correction path and fresh independent audit. Maintenance failures require direct maintenance, not a replacement card chain.
- If the target branch has advanced or the old packet is stale, reconcile authenticated current state before selecting an action. Do not redispatch stale Delivery/Closure instructions or close a tracker merely because a merge exists.
- Before dispatch, preflight the actual authorized role envelopes, lineage, and receipt shape through every required installed adapter. Invalid identity, scope, lineage, or receipt must fail before credential acquisition or network/write actions. A green policy-string test is not runtime proof.
- Record one named owner, evidence link, and concrete next decision for unresolved work. Preserve holds and audit evidence. Archive only confirmed superseded chains; do not mark unfinished work complete to reduce blocked counts.
