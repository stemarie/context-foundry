# Adapter guidance

## Hermes Kanban and cron mapping

Map one work contract to one Issue or equivalent source record and one durable Kanban card when a target uses Hermes. The card controls assignment and receipt capture; the repository and authenticated remote remain the code-delivery sources of truth. Keep one writer in a shared checkout. A periodic cron audit can inspect eligible completed receipts and request the existing dispatcher loop.

A completion-triggered request is optional, not present by default. Adopt it only if the target can prove it is scoped, receipt-gated, coalesced/idempotent, audited, and unable to introduce a second scheduler/control plane or concurrent writer. If no event surface exists, retain periodic or manual continuation.

See [generic adaptation](generic.md).
