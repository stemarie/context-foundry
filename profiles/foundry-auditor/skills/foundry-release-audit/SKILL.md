---
name: foundry-release-audit
description: Independently audit a GitHub release before and after publication.
version: 0.1.0
source: Context Foundry
adapted_for: foundry-auditor
---

# Foundry Release Audit

## When to use
Use to independently audit a Worker release packet for a declared target repository. Do not use to repair, publish, comment, link, or close anything.

## Contract
- Verify target repository slug, checkout remote, and GitHub API target match before accepting evidence.
- Require authenticated remote read-back through `python3 /home/karell/context-foundry/scripts/foundry_authenticated_git.py`, the packet’s non-secret helper reference. It permits only GitHub `fetch`, `ls-remote`, and non-force explicit-branch `push` against a `stemarie` origin.
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
4. Return PASS only when Worker may close the issue.

## Verification
The verdict cites independent command/API output and distinguishes a missing credential adapter from an unavailable service.

## Anti-patterns
- Treating Worker claims, local commits, or unauthenticated 404s as remote proof.
- Repairing an API payload or an incomplete publication.
- Passing a release without a post-publication read-back.
- Allowing issue closure before post-publication PASS.
