# Foundry skills

Version 0.2: runtime-neutral instructions. Source files exist; they are not automatically installed into this chat or any runtime. The [native service interface](https://github.com/stemarie/AI.Contract/blob/main/docs/native-workflow.md) is merged and tested; deployment and a runtime adapter are still required for live coordinated execution.

- [Architect](foundry-architect/SKILL.md): author and reassess bounded contracts.
- [Coordinator](foundry-coordinator/SKILL.md): reserve, dispatch, recover, integrate, and record history.
- [Worker](foundry-worker/SKILL.md): implement assigned contracts and submit evidence.
- [QA](foundry-qa/SKILL.md): independently verify candidates and route corrections.

Every skill first reads the [AI.Contract interface mapping](AI_CONTRACT_INTERFACE.md), [shared operating rules](OPERATING_RULES.md), the [work contract](../WORK_CONTRACT.md), and [agreed workflow](../docs/WORKFLOW.md). Package these referenced files together when installing or copying the skills. Relative paths refer to this repository, not the target project.

## Invocation and capability boundary

Provide the AI.Contract connection reference, project identifier or verified project lookup, target repository context, and authenticated actor identity. Coordinator invocation additionally needs configured Worker/QA pools and launch/stop/health and integration adapters. Workers and QA discover their assignment in the service using their runtime-bound identity. Exact identity/bootstrap mechanisms are deliberately deferred.

Use the documented native workflow interface only after checking live capabilities and authorization. Existing serial-chain PASS-to-Done semantics remain incompatible; native workflow enrollment provides a separate state machine.

Preparation can inspect source and return clearly marked drafts without service writes. Live work must use AI.Contract for authority and ownership. Missing capabilities produce a concrete blocker, not local JSON state, issue labels, Markdown projections, or an improvised queue.

## Manual review exercises

These are instruction walkthroughs, not runtime tests or proof of service behavior. See [review scenarios](../docs/SKILL_REVIEW.md). Prove actual operation later with one delivered contract, then two independent contracts concurrently.
