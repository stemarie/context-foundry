# Context Foundry

Runtime-neutral skills for a parallel development assembly line, with AI.Contract as the authoritative project, contract, queue, and execution-evidence service.

For Hermes setup and the remaining runtime implementation, start with the [Hermes handoff](docs/HERMES_HANDOFF.md), [adapter specification](docs/HERMES_RUNTIME_ADAPTER.md), and [acceptance runbook](docs/HERMES_ACCEPTANCE.md).

Start with the [four skills](skills/README.md), [work contract](WORK_CONTRACT.md), [agreed workflow](docs/WORKFLOW.md), and [AI.Contract extension proposal](docs/AI_CONTRACT_CHANGES.md).

Architect prepares bounded contracts within human-defined scope. Coordinator reserves eligible work and assigns defined Worker and QA pools. Workers implement in isolated worktrees; QA independently verifies. Coordinator integrates and verifies delivery. GitHub issues record final history.

The skill source pack is version 0.2. Native AI.Contract workflow support is merged and tested. The skills are not automatically installed or running; Hermes runtime adapters, the shared GitHub breaker, deployment, and real-agent acceptance remain to be implemented or demonstrated. The handoff documents the complete next implementation/setup sequence without claiming those pieces already exist.

The earlier implementation is preserved on [archive/pre-reset-2026-10-25](https://github.com/stemarie/context-foundry/tree/archive/pre-reset-2026-10-25).
