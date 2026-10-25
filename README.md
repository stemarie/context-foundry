# Context Foundry

Runtime-neutral skills for a parallel development assembly line, with AI.Contract as the authoritative project, contract, queue, and execution-evidence service.

Start with the [four skills](skills/README.md), [work contract](WORK_CONTRACT.md), [agreed workflow](docs/WORKFLOW.md), and [AI.Contract extension proposal](docs/AI_CONTRACT_CHANGES.md).

Architect prepares bounded contracts within human-defined scope. Coordinator reserves eligible work and assigns defined Worker and QA pools. Workers implement in isolated worktrees; QA independently verifies. Coordinator integrates and verifies delivery. GitHub issues record final history.

The skill source files are version 0.1. They are not automatically installed or running. Required AI.Contract extensions, runtime adapters, shared circuit breaker, and end-to-end execution are not implemented here. Missing service capabilities are explicit blockers.

The earlier implementation is preserved on [archive/pre-reset-2026-10-25](https://github.com/stemarie/context-foundry/tree/archive/pre-reset-2026-10-25).
