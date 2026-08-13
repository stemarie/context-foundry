# Portable skill: contract authoring and consumption

## Trigger

Use when an authorized repository owner or Architect agent must author, revise, interpret, consume, execute, verify, or invalidate a bounded work-contract body without relying on an agent-specific runtime or global profile skill.

## Prerequisites

1. Read the current product specification, the specific current work record, its latest amendments/comments, and repository policy before authoring or acting. The current product specification is architectural authority; the specific contract grants bounded work authority; portable material is interoperable procedure and cannot override either.
2. Before authoring a delivery contract, inspect the repository identity, branch, checkout state, duplicate work records, and authenticated remote when delivery authority exists. Preserve unrelated checkout work.
3. Before consuming a contract, re-read its `contract_version` and complete current `body_markdown` immediately before acting. Treat a contradiction as a hypothesis and inspect authoritative live sources before diagnosis.
4. Confirm that authority is explicit. Headings do not grant credentials, deployment permission, a workflow transition, destructive work, or any otherwise ungranted capability.

## Authoring procedure

1. Start from [the canonical editable template](../templates/contract-template.md). Keep the nine default headings in order unless an authorized specification/product decision documents a justified expansion or replacement.
2. Replace safe placeholders with one observable objective, stable authority references, bounded scope, required details, observable acceptance criteria, exact verification, explicit delivery rule, non-goals, and safety boundaries. Use no secrets, personal-machine paths, production fixture values, or invented remote authority.
3. Add an `Idempotency key` when durable orchestration uses deduplication. Search open and recent work records for the key and distinctive acceptance criteria before creating another contract.
4. State required disposable fixtures and cleanup evidence. Do not represent a skipped, unrun, or unrelated check as verification.
5. State delivery only when explicitly authorized. A local commit is not delivery; an authorized delivery receipt must include local, authenticated remote, and fetched tracking revision equality.
6. If a reproducible live probe shows a false premise, contradictory scope/non-goal, incompatible acceptance criterion, or an intervening specification/product change, do not silently broaden or amend the contract. Record one idempotent `[contract-invalidated:<fingerprint>]` receipt with sources, probe/outcome, and conflicting clauses; use the target's authorized `not_planned`/cancelled outcome; archive the linked execution card if applicable; then return to a fresh specification/repository audit. Cancellation does not authorize a replacement.

## Consumer procedure

1. Immediately before implementation, verification, delivery, or a state-changing update, re-read the `contract_version` and complete current `body_markdown`, then interpret all headings together with the current explicit authority, scope, acceptance criteria, verification, non-goals, and safety boundaries.
2. Implement only the bounded contract. Preserve unrelated work and serialize a shared checkout behind exactly one active writer.
3. Run every stated verification and disposable probe. Record exact commands, outcomes, changed paths, cleanup, and deferred/non-goal work.
4. Commit, push, deploy, or transition work only when separately and explicitly authorized. After an authorized push, verify local revision equals the authenticated remote branch and fetched tracking branch; re-read the authoritative receipt/work record before terminal completion.
5. Recover ordinary invocation, path, credential-propagation, fixture, checkout, or stale-state failures with the smallest already-authorized reversible action. Escalate only for a product decision, missing authority, irreversible/destructive action, or an externally proven barrier.

## Editable, versioned convention rule

The template and this skill are versioned portable documentation. An authorized repository owner/Architect may copy and expand the template and provide the revision to an authorized Architect agent to propose an authoring-convention or product-capability upgrade. The proposal requires an authorized specification/product decision, must preserve or explicitly document any changed default section, and cannot silently alter existing contracts. Changing this material does not change any target service API, schema, or runtime unless separately specified.

## Pitfalls

- Do not make contract headings into assumed service fields, runtime validators, workflow gates, or a second control plane.
- Do not let `issue-work-contract.md` (generic tracker template) or `implementation-card.md` (execution-card template) compete with the canonical contract-body template.
- Do not infer credentials, repository authentication, deployment permission, task/card state, or authority from a heading or a placeholder.
- Do not use a production, NAS, container, or other live fixture where the contract requires disposable local verification.
- Do not retry or replace an invalidated contract merely because it is incomplete; a fresh authoritative audit is required.

## Verification

1. Run `python3 kits/contract-orchestration/verification/validate.py` and `python3 kits/contract-orchestration/verification/validate.py --self-test` from the target repository root.
2. Confirm the canonical template exists, the template README distinguishes all three templates, the coordinator/worker guidance requires current `contract_version` and full `body_markdown`, and the traceability manifest links this skill/template.
3. Confirm no portable material claims runtime enforcement, introduces agent-profile-specific dependencies, embeds secrets or personal-machine paths, or overrides the product specification or specific contract.
