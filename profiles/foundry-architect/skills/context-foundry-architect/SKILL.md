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
2. Before creating or promoting any Worker or Auditor delivery card, perform and record a **per-role readiness preflight** against the exact assigned profile and execution surface. Verify:
   - every explicitly required skill and every lifecycle-injected skill (including `sdlc-review` for a first-class Kanban review lane) resolves from that profile's installed skill index;
   - the effective toolsets expose the required native tools;
   - each required local command, container image, compiler, formatter, linter, or test runner exists at the required version and can execute a harmless version/help probe;
   - the declared workspace is reachable and usable by that role; and
   - each required private source/service has a profile-local, non-secret authenticated read probe. Do not treat another profile's checkout, credential, or successful request as evidence for this role.
3. If a readiness check fails, do not dispatch the delivery card. Create or request one bounded prerequisite-enablement task owned by the profile/service operator that can fix it, with a non-secret verification receipt and a dependency link. Keep the Worker/Auditor card gated until that receipt is terminal. Never copy credentials into a packet or profile kit.
4. Map material requirements to one role-local artifact each; avoid duplicate or runtime-oriented skills.
5. Route a bounded implementation to Worker and define the independent Auditor checks only after both role readiness records are current and passing.
6. Synthesize only evidence and audit outcomes that exist; distinguish delivered source artifacts from future possibilities.
7. Escalate only for a missing authority, material product decision, irreversible action, or reproducible source-of-truth conflict.

## Verification
A completed Architect change has explicit role ownership, deterministic checks, an independent audit path, and no implied activation of runtime automation. Before any delivery dispatch, its packet must also contain current, role-specific readiness evidence for skills, toolsets, commands/toolchains, workspace access, and profile-local source authentication; unmet prerequisites must be terminal dependency cards, not first-run discoveries.

## Anti-patterns
- Turning Foundry into a control plane or generic automation system.
- Editing Worker evidence or auditing the Architect’s own work.
- Treating an inactive recovery policy as permission to schedule recovery work.
- Copying credentials, sessions, logs, host paths, or service settings into the profile kit.
- Dispatching because a different profile, local checkout, or earlier worker run had the needed capability.
- Letting a missing skill, toolchain, container capability, or authenticated source path consume a Worker or Auditor delivery retry.
