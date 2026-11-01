# Foundry skills

Version 0.4: runtime-neutral instructions. Source files exist; they are not automatically installed into this chat or any runtime. The [native service interface](https://github.com/stemarie/AI.Contract/blob/main/docs/native-workflow.md) is merged and tested; the bounded local macOS adapter and [real-agent acceptance](../docs/HERMES_ACCEPTANCE_2026-11-01.md) are available. Live project configuration and deployment remain separate.

- [Architect](../../foundry-architect/SKILL.md): author and reassess bounded contracts.
- [Coordinator](../../foundry-coordinator/SKILL.md): reserve, dispatch, recover, integrate, and record history.
- [Worker](../../foundry-worker/SKILL.md): implement assigned contracts and submit evidence.
- [QA](../../foundry-qa/SKILL.md): independently verify candidates and route corrections.

Every skill first reads the [AI.Contract interface mapping](AI_CONTRACT_INTERFACE.md), [shared operating rules](OPERATING_RULES.md), the [work contract](../WORK_CONTRACT.md), and [agreed workflow](../docs/WORKFLOW.md). Package these referenced files together when installing or copying the skills. Relative paths refer to this repository, not the target project.

For Hermes installation, actor isolation, runtime implementation, and real-agent proof, follow the [Hermes handoff](../docs/HERMES_HANDOFF.md).

## Invocation and capability boundary

Provide the AI.Contract connection reference, project identifier or verified project lookup, target repository context, and authenticated actor identity. Coordinator invocation additionally needs configured Worker/QA pools and launch/stop/health and integration adapters. Workers and QA discover their assignment in the service using their runtime-bound identity. The verified local identity/bootstrap interface is documented in [LOCAL_RUNTIME.md](../docs/LOCAL_RUNTIME.md).

Use the documented native workflow interface only after checking live capabilities and authorization. Existing serial-chain PASS-to-Done semantics remain incompatible; native workflow enrollment provides a separate state machine.

Preparation can inspect source and return clearly marked drafts without service writes. Live work must use AI.Contract for authority and ownership. Missing capabilities produce a concrete blocker, not local JSON state, issue labels, Markdown projections, or an improvised queue.

## Manual review exercises

These are instruction walkthroughs, not runtime tests or proof of service behavior. See [review scenarios](../docs/SKILL_REVIEW.md). Actual one-contract and concurrent operation are recorded separately in the acceptance report.

## Native execution entry points

The installed `foundry-start` and `foundry-loop` entry points use AI.Contract for
live work. `foundry-create-workorder`, `foundry-implement`, `foundry-audit` and
`foundry-commit` cover bounded native stages; the four role skills provide their
role procedures. GitHub issues record final outcomes only. `foundry-explore`,
`foundry-propose` and the OpenSpec skills retain planning boundaries;
`openspec-foundry` maps requirements/tasks without becoming another queue.

`scripts/package_skills.py` renders portable local/plugin copies with a complete
shared-reference closure. Source role references are preserved semantically and
rewritten only for the installed layout. The four roles and nine entry/adapter
skills are maintained here. Official OpenSpec planning skills remain separate
unchanged dependencies. Reinstall from the owning source rather than editing a
versioned plugin cache.
