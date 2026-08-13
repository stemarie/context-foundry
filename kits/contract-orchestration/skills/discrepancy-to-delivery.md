# Skill template: discrepancy to delivery coordination

## Trigger

Use when a current source, specification, work record, or delivery claim disagrees with another source and a bounded implementation cycle may be needed.

## Procedure

1. Audit current authoritative sources before proposing a fix.
2. Describe the discrepancy as observable facts, not an inferred diagnosis.
3. Search for an equivalent active or recently completed contract using a stable idempotency key.
4. Create or update one bounded contract only when the authority and acceptance criteria are clear.
5. Serialize shared-checkout work behind one active writer.
6. Require an evidence-backed receipt and remote-SHA equality for authorized delivery.
7. On a contract-invalidating discrepancy, record one evidence fingerprint; cancel the incompatible work record as `not_planned`, archive its execution card, and return to a fresh audit. Do not retry, amend, or create a replacement from the cancellation alone.
8. Keep a periodic or manual audit loop as the continuation fallback; suppress repeated delivery for an unchanged invalidation fingerprint.

## Optional continuation accelerator

A target may add a post-commit card-completion signal only after its normal periodic/manual loop works. The signal must be scoped to an eligible project and receipt, coalesced and idempotent, audited on accept or suppression, and incapable of creating a second scheduler/control plane or concurrent shared-checkout writer. It is an accelerator, never the sole continuation mechanism.

## Stop conditions

Escalate for missing authority, a material product decision, an irreversible action, or a proven external barrier. Do not create a parallel implementation lane to escape a transient failure.
