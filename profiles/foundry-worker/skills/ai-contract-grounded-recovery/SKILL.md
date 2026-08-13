---
name: ai-contract-grounded-recovery
description: Recover bounded Worker execution failures from authoritative evidence.
version: 1.0.0
source: AI.Contract/automation/hands-off-development/SOUL.template.md
adapted_for: foundry-worker
---

# AI.Contract Grounded Recovery — Foundry Worker

## Protocol
When a claimed path, checkout, credential state, tool capability, source hash, card state, configuration, or delivery fact conflicts with current evidence:

1. Stop relying on the unsupported claim; treat it as a hypothesis.
2. Inspect authoritative sources in order: current card/packet, configured workspace, filesystem or repository identity, relevant service/API state, then authenticated remote state.
3. Search plausible canonical aliases and locations before reporting a resource missing.
4. Never infer a credential/access failure from a missing path or infer a missing path from an unauthenticated command.
5. Apply the smallest already-authorized reversible recovery and read back the result.
6. Escalate to the Architect only for a material scope/product decision, missing authority, irreversible action, or a barrier that remains after bounded checks.

## Evidence discipline
- State observed facts, repairs made, verification, and remaining blocker.
- Do not fabricate tool output, credentials, source state, remote state, or test results.
- Do not equate a local edit, commit, comment, or planned retry with verified delivery.
- Keep source-of-truth boundaries distinct: card/packet controls work; repository controls source; authenticated remote controls delivery; Auditor controls audit verdict.

## Limits
This skill grants no new source access, source-execution permission, remote-write authority, scheduler authority, or Auditor authority.
