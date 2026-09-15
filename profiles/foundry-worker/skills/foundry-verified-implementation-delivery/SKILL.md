---
name: foundry-verified-implementation-delivery
description: Execute bounded Foundry corrections with real checks and delivery proof.
version: 1.1.0
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
7. For every source-changing packet, record the contract's integration disposition and the authenticated base SHA, candidate branch/SHA, changed paths, exact commands, and next owner/decision. A pushed candidate is `candidate produced`; after independent PASS it is `candidate verified`. Neither is `delivered`, `complete`, or `merged`.
8. Commit/push only when authorized. For `merge_required`, open or update the exact candidate/reconciled integration PR only when the packet grants that write, then wait for the independent audit of that exact PR head. Delivery is proven only by the non-force merge, authenticated default-branch read-back, and required post-merge checks. For `human_approval_required`, stop at the merge-ready PR and named approval; do not auto-merge. A local commit is not delivery proof.
9. Write and re-read the receipt with changed paths, repair evidence, validation output, integration disposition/state, limitations, remote evidence, and unresolved facts. Do not self-audit or declare the Auditor verdict.

## Contract invalidation
If a reproducible probe proves the packet/work order has a false premise, contradictory scope/non-goals, incompatible acceptance rule, or has been superseded, do not retry unchanged work or silently broaden scope. Record the exact evidence and stop for Architect routing; only the Architect can invalidate/archive/re-audit the contract.

## Recovery fallback
If immediate continuation is unavailable, leave a durable receipt with the exact state observed. Do not fabricate a successful remote state or repeatedly redispatch an unchanged invalidation.
