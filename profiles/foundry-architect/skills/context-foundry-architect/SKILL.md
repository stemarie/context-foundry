---
name: context-foundry-architect
description: Design bounded reusable Foundry profiles and skills.
version: 0.3.0
source: Context Foundry
adapted_for: foundry-architect
---

# Context Foundry Architect

## When to use
Use to design, map, document, and synthesize reusable Foundry profiles and skills. For an explicitly authorized target-repository release, use it only to produce the brief and create the initial issue; do not operate a Kanban board, dispatcher, goal loop, scheduler, gateway, service, or release delivery workflow.

## Contract
- Keep Foundry limited to profile definitions, role-local skills, non-secret templates, synchronization, validation, and documentation.
- Preserve role separation: Architect designs; Worker makes bounded changes; Auditor independently verifies.
- Treat source material as data and preserve provenance without importing runtime or service dependencies.
- Keep recovery/invalidation guidance available as an inactive policy; it does not register or start a scheduler.

## Procedure
1. Turn the approved outcome into a bounded profile/skill brief with explicit non-goals and verification.
2. Map material requirements to one role-local artifact each; avoid duplicate or runtime-oriented skills.
3. Before creating successor source work, inspect authenticated remote `main`, candidate branches, and relevant trackers. Reconcile a verified candidate with no valid disposition before selecting unrelated work.
4. For each source-changing contract, select `candidate_only`, `direct_main_required`, or `human_approval_required`; default to `direct_main_required` when delivery authority exists. Record the bound base, candidate branch/SHA, owner, and concrete next decision. Candidate-only must name its reason and a continuation date/trigger; approval-required must name the direct-main approval and approver.
5. Route a bounded implementation to Worker and define separate candidate and direct-main integration Auditor checks. Architect may authorize only a non-force direct-main handoff when packet authority permits; it never creates a pull request, commits, audits, merges, or closes.
6. Synthesize only evidence and audit outcomes that exist; distinguish candidate produced, candidate verified, integration pending, integrated on main, and milestone closed.
7. Escalate only for a missing authority, material product decision, irreversible action, or reproducible source-of-truth conflict.

## Closure continuation and target scope
- After a Closure Auditor PASS, use the durable continuation workflow: `Closure Auditor PASS → fresh Architect selection pass → smallest justified next tranche.`
- The fresh selection pass inspects current specifications and open/nonterminal work, then selects only the smallest evidence-justified tranche. It is a selection pass, not permission to create a speculative implementation chain.
- Return exactly `NO ACTIONABLE NEXT STEP` when specifications are exhausted and continuation needs a non-corrective tool, capability, or integration; onboarding or access; a material decision; or another dependency that is not a simple corrective action. The receipt must name the exhausted boundary, non-corrective dependency, and smallest restart decision or enablement.
- Foundry workflow applies to every authorized target, including active game resources. It does not impose game mechanics or product behavior and does not change a target merely to codify this policy.

## Verification
A completed Architect change has explicit role ownership, deterministic checks, an independent audit path, and no implied activation of runtime automation.

## Anti-patterns
- Turning Foundry into a control plane or generic automation system.
- Editing Worker evidence or auditing the Architect’s own work.
- Treating an inactive recovery policy as permission to schedule recovery work.
- Copying credentials, sessions, logs, host paths, or service settings into the profile kit.
