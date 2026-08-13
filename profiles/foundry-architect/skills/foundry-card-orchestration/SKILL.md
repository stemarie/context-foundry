---
name: foundry-card-orchestration
description: Operate Foundry cards as serialized control records with recovery receipts.
version: 1.0.0
source: kits/contract-orchestration/skills/card-orchestration.md
adapted_for: foundry-architect
---

# Context Foundry Card Orchestration — Foundry Architect

## Operating rules
- A card controls assignment and receipts; it is never proof that a source, remote, or external state changed.
- Deduplicate by stable idempotency key and acceptance criteria before creating a card.
- Express real prerequisites with explicit parent dependencies, not prose alone.
- Maintain exactly one active writer for a shared checkout. Research/audit may run in parallel only when it cannot write the shared checkout.
- A terminal receipt names changed paths, commands/outcomes, cleanup, delivery/read-back evidence, and deferred work.

## Recovery
A card is blocked only for a concrete external decision, authority gap, or proven external barrier. Recover ordinary path, tool, invocation, stale-state, or credential-propagation failures using the smallest already-authorized reversible repair and record evidence.

A contract-invalidating discrepancy is not a block or retry condition. Record one `[contract-invalidated:<fingerprint>]` receipt, close the linked work record as `not_planned`, archive the execution card, and return to a fresh discrepancy audit. Suppress repeat notifications while the fingerprint and authoritative inputs are unchanged.

## Continuation
Use the board dispatcher/manual audit as the base continuation mechanism. Any completion signal is an accelerator only: project-scoped, receipt-gated, idempotent, coalesced, auditable, and incapable of spawning concurrent writers or a second control plane.
