---
name: foundry-release-brief
description: Define a bounded target-repository release handoff.
version: 0.3.0
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
3. Specify an approved non-secret authentication helper reference for Worker and Auditor; never copy a credential into the packet.
4. Create the initial issue only after the three-way repository binding matches.
5. Produce a Worker packet and pre/post-publication Auditor packet. Architect performs no further GitHub write.

## Verification
The brief contains matching repository identifiers, one issue URL, a frozen SHA, clear external-write gates, and role-owned handoffs.

## Anti-patterns
- Creating an issue in the Architect profile repository instead of the declared target repository.
- Inferring GitHub access is unavailable from `gh` absence or an unauthenticated Git invocation.
- Committing, commenting, linking, closing, tagging, or publishing as Architect.
- Treating a plan as permission to bypass Auditor approval.

## Direct Foundry maintenance boundary

- Do not create Kanban maintenance cards for Foundry profiles, skills, adapters, tests, templates, or process repairs. Karell-authorized maintenance is performed directly in source, independently reviewed, verified against installed behavior, and tracked in a linked GitHub issue when requested.
- AI.Contract remains the sole contract plane for governed product work. A maintenance issue, an old PASS, and a completed Kanban run do not grant current authorization to deliver or close a product tranche.
- Treat structured root-run verdicts as evidence; `done` is not `PASS`. Product REQUEST_CHANGES requires one explicitly linked, current, authorized correction path and fresh independent audit. Maintenance failures require direct maintenance, not a replacement card chain.
- If the target branch has advanced or the old packet is stale, reconcile authenticated current state before selecting an action. Do not redispatch stale Delivery/Closure instructions or close a tracker merely because a merge exists.
- Before dispatch, preflight the actual authorized role envelopes, lineage, and receipt shape through every required installed adapter. Invalid identity, scope, lineage, or receipt must fail before credential acquisition or network/write actions. A green policy-string test is not runtime proof.
- Record one named owner, evidence link, and concrete next decision for unresolved work. Preserve holds and audit evidence. Archive only confirmed superseded chains; do not mark unfinished work complete to reduce blocked counts.
