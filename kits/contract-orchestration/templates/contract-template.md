# <WORK_TITLE>

> Canonical editable source template for a work-contract `body_markdown`. Replace only these safe placeholders after reading the current product specification, specific work record, repository policy, and available authority. This template is portable procedure, not an API/schema/runtime feature or authorization.

## Objective

<SMALLEST_OBSERVABLE_OUTCOME>

## Authority

- Product specification: <STABLE_SPECIFICATION_REFERENCE>
- Specific work record: <STABLE_WORK_RECORD_REFERENCE>
- Repository: <REPOSITORY_URL>
- Baseline: <AUTHENTICATED_BRANCH_AND_REVISION>
- Delivery authority: <EXPLICIT_DELIVERY_AUTHORITY_OR_NONE>

## In scope

<BOUNDED_BEHAVIOR_AND_IMPLEMENTATION_SURFACE>

## Required implementation details

<REQUIRED_TECHNICAL_AND_SAFETY_CONSTRAINTS>

## Acceptance criteria

- <OBSERVABLE_PASS_FAIL_CRITERION>

## Verification

```sh
<EXACT_LOCAL_TEST_BUILD_OR_DISPOSABLE_PROBE_COMMAND>
```

<Record real outcomes, required fixture boundaries, and cleanup evidence.>

## Delivery

<EXPLICIT_BRANCH_AND_DELIVERY_RULE; NO_FORCE_UNLESS_SEPARATELY_AUTHORIZED>

<Require local revision, authenticated remote revision, and fetched tracking revision equality when delivery is authorized.>

## Explicit non-goals

<BEHAVIOR_OR_SYSTEM_BOUNDARIES_THAT_MUST_NOT_EXPAND_SILENTLY>

## Safety boundaries

<SECRETS_DESTRUCTIVE_ACTIONS_FIXTURES_NETWORK_PRODUCTION_AND_ROLLBACK_LIMITS>

Treat headings together with this specific contract's current explicit authority, scope, acceptance criteria, verification, non-goals, and safety boundaries. Headings alone must not authorize credentials, deployment, a workflow transition, destructive work, or an otherwise ungranted capability. If reproducible live evidence makes this contract's premise, scope, non-goals, acceptance criteria, or product assumption incompatible with the current product specification, record the required invalidation evidence and follow the target's authorized cancellation process; do not silently broaden or rewrite the contract.

## Idempotency key

<STABLE_DURABLE_DEDUPLICATION_KEY_OR_NOT_APPLICABLE>

`Idempotency key` is mandatory when durable orchestration uses it. Otherwise, state that durable deduplication is not in use rather than inventing a key.

## Authoring-convention change rule

An authorized repository owner/Architect may copy and expand this template, then provide the revision to an authorized Architect agent to propose an authoring-convention or product-capability upgrade. The proposal requires an authorized specification/product decision; it does not silently change existing contracts and does not change any target service API, schema, or runtime unless separately specified.

Authority hierarchy: the current product specification is architectural authority; the specific contract grants bounded work authority; this portable material is interoperable procedure and cannot override either.
