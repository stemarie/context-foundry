---
name: foundry-runtime-architect
description: Replenish an approved AI.Contract milestone for the Codex runner.
---

# foundry-runtime-architect

Read the approved milestone, current jobs, and the available queue capacity. Invoke [foundry-architect](../foundry-architect/SKILL.md) to publish the bounded batch and its dependencies and conflicts. Return the persisted Ready revision identities or the reason no work was published.

For a planning request, first read the verified Markdown file at `spec_snapshot_path`. Use the supplied source revision and section locator when deciding requirements. Keep contract scope within the approved milestone. On each `workflow_define`, supply `planning_request_id`, `specification_id`, and the applicable `spec_section`. Cite the pinned source revision and relevant section in the contract body. Make each new revision Ready and read it back. Finish with `workflow_planning_report` using the assigned request ID and evidence of the published contracts or why no new work is needed. If the verified source is unavailable or cannot be read, report the blocker to the runner.
