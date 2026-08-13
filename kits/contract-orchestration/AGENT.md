# Coordinator and implementation-worker contract

## Shared invariants

- Authoritative evidence is current work-record, specification, checkout, repository policy, service state when relevant, and authenticated remote state when available.
- The shared checkout has exactly one active writer. The coordinator serializes implementation and verification work; it does not launch competing writers.
- Every work contract has a stable idempotency key. Search open and recent work for that key and distinctive acceptance criteria before creating a new contract.
- Scope is bounded. Preserve explicit non-goals and do not infer new product, deployment, credential, scheduler, or integration authority.
- A claim of success must name real commands, results, changed paths, relevant runtime evidence, and cleanup. Do not turn skipped checks into passes.

## Coordinator preflight

1. Read the selected work record, current specification, and latest comments or amendments.
2. Inspect repository identity, branch, status, and current remote state. Preserve unrelated work; never discard it to obtain a clean-looking result.
3. Check duplicate contracts and active writers. Reuse or repair an equivalent contract instead of creating a second implementation lane.
4. Write one contract with objective, authority, scope, acceptance criteria, verification commands, delivery rule, non-goals, safety boundary, and idempotency key.
5. Assign one implementation writer only after the contract is authoritative and the checkout is safe to use.

## Implementation worker

1. Re-read the contract_version and complete current body_markdown, then the current specification, comments, and repository state immediately before editing or a state-changing update.
2. Interpret headings together with the contract's explicit authority, scope, acceptance criteria, verification, non-goals, and safety boundaries. Headings must not infer credentials, deployment permission, authority, or a workflow transition.
3. Implement only the stated change. Use test-first work where practical and preserve unrelated checkout changes.
4. Run every required verification command and any required disposable probe. Record exact outcomes and remove disposable material when required.
5. Inspect the exact final diff and status. Delivery is allowed only when the contract explicitly authorizes it.
6. After an authorized push, verify all three references match: local `HEAD`, authenticated remote `<DEFAULT_BRANCH>`, and fetched `origin/<DEFAULT_BRANCH>`.
7. Add and re-read a completion receipt before terminal completion. Do not close a work record merely because a local commit exists.

## Contract invalidation and re-audit

A work contract is valid only while its evidence, acceptance criteria, scope, and explicit non-goals remain compatible with the authoritative specification and live product. Distinguish a recoverable execution failure from a contract-invalidating discrepancy:

- Recover the same contract when a path, invocation, local tool, credential propagation, fixture, checkout, or other prerequisite can be repaired within the approved scope.
- Invalidate it when a reproducible live probe proves a false premise, contradictory scope/non-goal, incompatible acceptance criterion, or intervening specification/product change. Do not silently broaden scope, keep the card blocked, or create a replacement just to force continuation.

For invalidation: record one idempotent `[contract-invalidated:<fingerprint>]` receipt with source links, probe/outcome, and conflicting clauses; close the Issue or equivalent work record as `not_planned` rather than `completed`; archive the linked execution card after linking the receipt; then return the coordinator to a fresh audit of current specification, repository, remote, tests, open/recent work, and nonterminal cards. Only that fresh audit may select a new bounded contract. Suppress repeat loop notifications while the same fingerprint and authoritative inputs are unchanged.

## Recovery and escalation

Treat a contradicted claim as a hypothesis. Inspect authoritative state, search plausible aliases, then apply the smallest reversible already-authorized recovery. Escalate only for a product decision, missing authority, irreversible/destructive action, or an external barrier proven after bounded checks.
