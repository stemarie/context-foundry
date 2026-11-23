---
name: foundry-runtime-worker
description: Implement a Codex runner assignment in its attempt worktree.
---

# foundry-runtime-worker

Verify the assigned actor, attempt, frozen revision and worktree. Invoke [foundry-worker](../foundry-worker/SKILL.md) for the implementation or assigned correction. Return the persisted candidate receipt for this attempt.

After verification, use the assigned candidate commit tool for the selected worktree files. Use the returned SHA when submitting evidence through AI.Contract.
