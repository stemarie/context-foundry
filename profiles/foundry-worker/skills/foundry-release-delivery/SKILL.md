---
name: foundry-release-delivery
description: Deliver an audited GitHub release from a frozen candidate.
version: 0.1.0
source: Context Foundry
adapted_for: foundry-worker
---

# Foundry Release Delivery

## When to use
Use after Architect supplies a bounded target-repository release packet. Do not use without a frozen candidate, approved authentication-helper reference, and Auditor-defined gates.

## Contract
- Worker owns approved source commits, issue evidence/linking/closure, tag/release publication, and remote read-back.
- Before every external write, require target repository slug = checkout remote = GitHub API target.
- Use only the packet’s non-secret authentication helper; never print, copy, or change credentials.
- Publish only after pre-publication Auditor PASS; close the issue only after post-publication Auditor PASS.

## Procedure
1. Run authenticated preflight: candidate branch/SHA, tag/release absence, and clean checkout.
2. Make only approved source changes. If a commit is required, link it to the issue and return the new SHA for fresh audit.
3. Run required validation gates and submit evidence to Auditor.
4. After pre-publication PASS, create the annotated tag and read it back before creating the release.
5. Create the approved release, read back its metadata/body/assets, and add Worker evidence to the issue.
6. If an external step partially succeeds, verify prior writes and repair only the failed step idempotently.
7. After post-publication PASS, add final evidence and close the issue as completed.

## Verification
Evidence contains exact SHA, command outcomes, tag object/target, release URL/fields/assets, issue URLs/comments, and authenticated read-back.

## Anti-patterns
- Publishing before pre-publication audit or closing before post-publication audit.
- Retagging, overwriting a release, or retrying without inspecting partial state.
- Calling missing `gh` or bare HTTPS Git proof that authenticated access is unavailable.
- Publishing images/assets or changing source outside packet scope.
