---
name: foundry-runtime-operate
description: Operate or reconcile the continuous Codex Foundry runner.
---

# foundry-runtime-operate

Invoke [foundry-coordinator](../foundry-coordinator/SKILL.md) to check project authority, role bindings, runtime health, and unresolved attempts. Use the runner for event-driven execution. Reconcile persisted state and process ownership before retrying an uncertain action.

Use `context-foundry-codex-runner --config <private-config>` for the authorized continuous run. Confirm the process and AI.Contract state before reporting it as active.
