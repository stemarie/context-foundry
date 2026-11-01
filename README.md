# Context Foundry

Runtime-neutral skills for a parallel development assembly line, with AI.Contract as the authoritative project, contract, queue, and execution-evidence service.

For Hermes setup, the bounded local runtime and executed acceptance evidence, start with the [Hermes handoff](docs/HERMES_HANDOFF.md), [adapter specification](docs/HERMES_RUNTIME_ADAPTER.md), and [acceptance runbook](docs/HERMES_ACCEPTANCE.md).

Start with the [four skills](skills/README.md), [work contract](WORK_CONTRACT.md), [agreed workflow](docs/WORKFLOW.md), and [AI.Contract extension proposal](docs/AI_CONTRACT_CHANGES.md).

Architect prepares bounded contracts within human-defined scope. Coordinator reserves eligible work and assigns defined Worker and QA pools. Workers implement in isolated worktrees; QA independently verifies. Coordinator integrates and verifies delivery. GitHub issues record final history.

The skill source pack is version 0.3. Native AI.Contract workflow support and the
bounded local Hermes adapter/shared GitHub gate are implemented and tested.
[Real-agent acceptance](docs/HERMES_ACCEPTANCE_2026-11-01.md) passed with independent
QA, concurrent Workers, restart/expiry recovery and actual direct-main delivery.
The verified backend is an operator-invoked macOS process wrapper with restricted
checks. No persistent profiles, scheduler, active configuration change or
production deployment was installed. Other backends require their own proof.

The earlier implementation is preserved on [archive/pre-reset-2026-10-25](https://github.com/stemarie/context-foundry/tree/archive/pre-reset-2026-10-25).
