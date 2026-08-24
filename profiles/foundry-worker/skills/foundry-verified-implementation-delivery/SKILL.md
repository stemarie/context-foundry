---
name: foundry-verified-implementation-delivery
description: Execute bounded Foundry corrections with real checks and delivery proof.
version: 1.0.0
source: kits/contract-orchestration/skills/verified-implementation-delivery.md
adapted_for: foundry-worker
---

# Context Foundry Verified Delivery — Foundry Worker

## Trigger
Use only for a bounded Worker packet or Architect-routed correction with named scope, output paths, acceptance criteria, and verification gates.

## Procedure
1. Re-read the current packet/correction card, manifest, source policy, prior evidence, comments, and repository state immediately before changing anything.
2. Confirm the failure is recoverable inside scope. Treat a failed command as evidence about that invocation, not proof a path, credential, service, or capability is absent.
3. Inspect authoritative state in order: card/packet, configured workspace, filesystem/repository, relevant service/API, then authenticated remote when delivery matters. Search plausible aliases before saying missing.
4. Apply the smallest reversible, authorized correction. Preserve unrelated changes; never expand source set, question, operations, or side effects.
5. Regenerate only the packet-defined evidence/receipt outputs. Run every required validator, focused test, lint/diff check, and cleanup check. Record actual commands and outcomes.
6. Inspect the exact final diff for secrets, generated debris, accidental path exposure, or scope expansion.
7. Commit/push only when authorized. For every authenticated GitHub read or branch delivery, invoke `python3 /home/karell/context-foundry/scripts/foundry_authenticated_git.py` with only its permitted `fetch`, `ls-remote`, or non-force explicit-branch `push` form. Never use bare HTTPS Git or copy/export a credential. For delivery, verify local `HEAD`, authenticated remote branch, and fetched tracking branch agree. A local commit is not delivery proof.
8. Write and re-read the Kanban receipt with changed paths, repair evidence, validation output, limitations, delivery evidence, and unresolved facts. Do not self-audit or declare the Auditor verdict.

## Contract invalidation
If a reproducible probe proves the packet/work order has a false premise, contradictory scope/non-goals, incompatible acceptance rule, or has been superseded, do not retry unchanged work or silently broaden scope. Record the exact evidence and stop for Architect routing; only the Architect can invalidate/archive/re-audit the contract.

## Recovery fallback
If immediate continuation is unavailable, leave a durable receipt with the exact state observed. Do not fabricate a successful remote state or repeatedly redispatch an unchanged invalidation.
