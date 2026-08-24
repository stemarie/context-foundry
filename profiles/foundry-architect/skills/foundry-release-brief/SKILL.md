---
name: foundry-release-brief
description: Define a bounded target-repository release handoff.
version: 0.1.0
source: Context Foundry
adapted_for: foundry-architect
---

# Foundry Release Brief

## When to use
Use for an explicitly authorized GitHub release in a declared target repository. Do not use to publish, tag, commit, comment, link delivery evidence, or close issues.

## Contract
- Define one immutable candidate SHA, tag/title, release scope, notes, validation gates, and explicit non-goals.
- Bind the packet to three matching identifiers: target repository slug, checkout `origin` remote, and GitHub REST API target.
- Create exactly one initial tracking issue only after the target binding passes.
- Hand release execution to Worker and independent checks to Auditor.

## Procedure
1. Read the target repository state and authenticated remote inventory; record facts, not assumptions.
2. State the candidate SHA, proposed version/tag, release type, notes, assets policy, and required validations.
3. Specify `python3 /home/karell/context-foundry/scripts/foundry_authenticated_git.py` as the approved non-secret authentication helper reference for Worker and Auditor; never copy a credential into the packet. The helper supports only authenticated `fetch`, `ls-remote`, and non-force explicit-branch `push` against a `stemarie` GitHub origin.
4. Create the initial issue only after the three-way repository binding matches.
5. Produce a Worker packet and pre/post-publication Auditor packet. Architect performs no further GitHub write.

## Verification
The brief contains matching repository identifiers, one issue URL, a frozen SHA, clear external-write gates, and role-owned handoffs.

## Anti-patterns
- Creating an issue in the Architect profile repository instead of the declared target repository.
- Inferring GitHub access is unavailable from `gh` absence or an unauthenticated Git invocation.
- Committing, commenting, linking, closing, tagging, or publishing as Architect.
- Treating a plan as permission to bypass Auditor approval.
