# Foundry skills

Version 0.1: runtime-neutral instructions. Source files exist; they are not automatically installed into this chat or any runtime. AI.Contract extensions and a runtime adapter are still required for live coordinated execution.

- [Architect](foundry-architect/SKILL.md): author and reassess bounded contracts.
- [Coordinator](foundry-coordinator/SKILL.md): reserve, dispatch, recover, integrate, and record history.
- [Worker](foundry-worker/SKILL.md): implement assigned contracts and submit evidence.
- [QA](foundry-qa/SKILL.md): independently verify candidates and route corrections.

Every skill first reads [shared operating rules](OPERATING_RULES.md), the [work contract](../WORK_CONTRACT.md), and [agreed workflow](../docs/WORKFLOW.md). Package these referenced files together when installing or copying the skills. Relative paths refer to this repository, not the target project.

## Invocation and capability boundary

Provide the AI.Contract connection reference, project identifier or verified project lookup, target repository context, and authenticated actor identity. Coordinator invocation additionally needs configured Worker/QA pools and launch/stop/health and integration adapters. Workers and QA discover their assignment in the service using their runtime-bound identity. Exact identity/bootstrap mechanisms are deliberately deferred.

Use available documented interfaces; no proposed operation below is an existing endpoint name. Verify real service capabilities and authorization before use. Existing serial-chain PASS-to-Done semantics are incompatible with this workflow until extended.

Preparation can inspect source and return clearly marked drafts without service writes. Live work must use AI.Contract for authority and ownership. Missing capabilities produce a concrete blocker, not local JSON state, issue labels, Markdown projections, or an improvised queue.

## Manual review exercises

These are instruction walkthroughs, not runtime tests or proof of service behavior. See [review scenarios](../docs/SKILL_REVIEW.md). Prove actual operation later with one delivered contract, then two independent contracts concurrently.
