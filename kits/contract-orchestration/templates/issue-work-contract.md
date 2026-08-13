# <WORK_TITLE>

## Objective

<OBSERVABLE_OUTCOME>

## Authority

- Repository: <REPOSITORY_URL>
- Default branch: <DEFAULT_BRANCH>
- Baseline revision: <BASELINE_SHA>
- Specification: <SPECIFICATION_REFERENCE>

## In scope

<BOUNDED_CHANGE>

## Acceptance criteria

- <OBSERVABLE_ACCEPTANCE_CRITERION>

## Verification

```sh
<VERIFICATION_COMMAND>
```

Use only disposable fixtures. Record cleanup evidence.

## Delivery

<DELIVERY_AUTHORITY>. No force push. Final delivery confirms local HEAD equals authenticated `<DEFAULT_BRANCH>` and fetched `origin/<DEFAULT_BRANCH>`.

## Contract invalidation

If a reproducible live acceptance probe proves that this work order has a false premise, contradictory acceptance/non-goals, scope incompatible with required behavior, or has been superseded by an intervening specification/product change, do not silently broaden it or report completion. Add one `[contract-invalidated:<fingerprint>]` evidence receipt, close this work record as `not_planned`, archive its execution card, and return control to a fresh current-spec/repository audit. Only that audit may select a new work contract.

## Explicit non-goals

<NON_GOAL>

## Safety boundaries

<SAFETY_BOUNDARY>

## Idempotency key

<IDEMPOTENCY_KEY>
