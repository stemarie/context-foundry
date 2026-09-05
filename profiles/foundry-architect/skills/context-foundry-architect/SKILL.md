---
name: context-foundry-architect
description: Design bounded reusable Foundry profiles and skills.
version: 0.2.0
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
3. Route a bounded implementation to Worker and define the independent Auditor checks.
4. Synthesize only evidence and audit outcomes that exist; distinguish delivered source artifacts from future possibilities.
5. Escalate only for a missing authority, material product decision, irreversible action, or reproducible source-of-truth conflict.

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
