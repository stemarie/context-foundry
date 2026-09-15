# Skill template: discrepancy to delivery coordination

## Trigger

Use when a current source, specification, work record, or delivery claim disagrees with another source and a bounded implementation cycle may be needed.

## Procedure

1. Audit current authoritative sources before proposing a fix.
2. Describe the discrepancy as observable facts, not an inferred diagnosis.
3. Search for an equivalent active or recently completed contract using a stable idempotency key.
4. Before selecting successor source work, inspect the authenticated default branch, candidate branches, open pull requests, and relevant trackers. A verified candidate without a valid disposition is an integration problem to reconcile before unrelated work starts.
5. Create or update one bounded contract only when the authority and acceptance criteria are clear. Every source-changing contract selects `candidate_only`, `merge_required`, or `human_approval_required`; default to `merge_required` when delivery authority exists.
6. Serialize shared-checkout work behind one active writer. Require candidate evidence, separate candidate/integration audit gates, an evidence-backed receipt, and authenticated remote read-back for authorized integration.
7. On a contract-invalidating discrepancy, record one evidence fingerprint; cancel the incompatible work record as `not_planned`, archive its execution card, and return to a fresh audit. Do not retry, amend, or create a replacement from the cancellation alone.
8. Keep a periodic or manual audit loop as the continuation fallback; detect verified candidates with no PR, closed trackers absent from the default branch, no continuation owner, and sibling candidates requiring integration reconciliation. Suppress repeated delivery for an unchanged invalidation fingerprint.

## Optional continuation accelerator

A target may add a post-commit card-completion signal only after its normal periodic/manual loop works. The signal must be scoped to an eligible project and receipt, coalesced and idempotent, audited on accept or suppression, and incapable of creating a second scheduler/control plane or concurrent shared-checkout writer. It is an accelerator, never the sole continuation mechanism.

## Stop conditions

Escalate for missing authority, a material product decision, an irreversible action, or a proven external barrier. Do not create a parallel implementation lane to escape a transient failure.
