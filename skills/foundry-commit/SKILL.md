---
name: foundry-commit
description: Integrate an AI.Contract QA-accepted candidate under current repository authority, verify delivery and record native completion plus final historical GitHub evidence. Does not grant deployment authority.
---

# Foundry Commit

Read [Coordinator](../foundry-coordinator/SKILL.md), the [native interface](../AI_CONTRACT_INTERFACE.md), [operating rules](../OPERATING_RULES.md) and target AGENTS.md. Require current authorized delivery, an exact QA-accepted candidate and actual checks. Missing native bindings or delivery support are blockers, not permission to substitute an issue queue.

Before integration, retire/confirm the old Worker and reconcile runtime identity, target drift and uncertain remote operations. Obtain native integration ownership for the accepted candidate. Hold the external target lock through delivery, postchecks and native completion. The shared GitHub gate must check every command's current admission/generation/probe owner and prevent target reacquisition while any recorded prior transport group is alive or unknown. Local work can continue while remote access is paused.

Follow the repository's actual delivery policy. AI.Contract and Context Foundry require expected-head, non-force direct-main delivery, with intervening changes inspected and preserved; do not introduce a PR gate. Candidate changes, rebases or conflict resolutions require renewed QA. Never infer production deployment authority from delivery prose.

Verify remote target SHA and required post-integration checks. Only then record `workflow_complete` with matching candidate/SHA, actual target, checks_passed=true and evidence. Failed checks or uncertain writes remain unresolved; do not unlock dependencies or erase successful delivery because publication is pending.

After Done or authorized stopped-confirmed cancellation, create/reconcile one final historical GitHub issue, verify it, close it under repository policy and record its reference using `workflow_publish_history`. Preserve a pending publication obligation during an outage without bypassing the gate. No pre-execution issue is required or created.

Report native bindings/stage, candidate/target SHA, checks, historical reference and any outstanding obligation. This skill does not deploy, force-push, discard unrelated work or create a scheduler.
