# Skill template: Kanban or card orchestration

## Trigger

Use when a work-record system is available and a bounded change benefits from durable assignment, dependencies, and receipts.

## Operating rules

1. The card is a control record, not proof that a remote change or deployment happened.
2. Deduplicate by idempotency key and acceptance criteria before creating cards.
3. Use explicit parent dependencies for real prerequisites; do not encode dependencies only in prose.
4. Assign one writer for a shared checkout. Parallel research/review is allowed only when it cannot write that checkout.
5. A card terminal receipt includes changed paths, commands/outcomes, cleanup, delivery evidence, and deferred work.

## Continuation adaptation

Use a periodic audit or manual dispatch as the base continuation mechanism. If the target exposes a completion event, an optional receipt-gated trigger may request the existing loop after completion. It must be project-scoped, coalesced, idempotent, auditable, and unable to create another scheduler/control plane or simultaneous writer.

## Contract invalidation

A card is not a retry bucket for a contract that has become false. When a reproducible live probe proves the linked work order’s premise, scope/non-goals, acceptance criteria, or product assumptions conflict, record one `[contract-invalidated:<fingerprint>]` receipt; close the work record as `not_planned`, archive the execution card, and return to a fresh discrepancy audit. Do not leave it blocked, silently expand scope, or create a replacement before that audit selects one. Suppress repeat notifications while the same fingerprint is unchanged.

## Recovery

A card is blocked only for a concrete external decision, authority gap, or proven external barrier. Recover ordinary tool, path, or stale-state failures with the smallest authorized action and record the evidence.
