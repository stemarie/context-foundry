# Context Foundry Contract-Orchestration Kit

## Purpose and scope

This is Context Foundry-owned, portable protocol-and-template material for a repository owner and an authorized agent. It standardizes a repeatable, source-grounded development loop without assuming a particular agent, scheduler, task board, credential store, host, or remote service.

It is documentation and local validation material. It does not install a scheduler, continuation hook, listener, credential, remote integration, or control plane.

## Lifecycle

1. **Source and specification audit.** Read the current work record, authoritative specification, repository policy, current checkout, and authenticated remote when authority exists. Resolve contradictions from those sources rather than from remembered context.
2. **One bounded work contract.** Deduplicate comparable open work before creating one observable contract with scope, acceptance criteria, non-goals, safety boundaries, verification, and delivery authority.
3. **Serialized implementation.** Assign exactly one active writer for a shared checkout. The coordinator records an idempotency key and does not create competing implementation work.
4. **Real verification.** Run the contract's required checks and any real disposable runtime probe. Record commands, outcomes, changed paths, and cleanup evidence. A skipped check is not a passing check.
5. **Authenticated remote delivery and receipt.** Every source-changing contract declares one integration disposition: `candidate_only`, `direct_main_required`, or `human_approval_required`. The default is `direct_main_required`. Candidate PASS and a pushed branch are not delivery. For direct-main work, non-force fast-forward the exact audited candidate to the bound default branch, independently audit that read-back, and run required post-delivery checks before closure. Pull requests are forbidden.
6. **Contract invalidation or fresh continuation.** If live evidence proves the work order false, contradictory, out of scope, or superseded, record one fingerprinted receipt, cancel it as `not_planned`, archive its execution card, and return to the source/specification audit. Do not keep retrying it, silently expand its scope, or presume a replacement. Otherwise re-read current state after verified completion and use the periodic/manual audit loop as the reliable continuation fallback.

## State vocabulary

`candidate produced → candidate verified → integration pending → integrated on main → milestone closed`

- **Candidate produced**: scoped source changes and the named candidate SHA/branch exist. This says nothing about audit, direct-main integration, deployment, or milestone closure.
- **Candidate verified**: an independent audit passed for the exact candidate SHA. Candidate PASS does not certify direct-main integration, deployment, or milestone completion.
- **Integration pending**: a `direct_main_required` candidate lacks independently audited default-branch evidence, non-force direct delivery, or required post-delivery evidence.
- **Integrated on main**: the exact audited candidate was non-force fast-forwarded to the authenticated bound default branch and independently verified. This is distinct from deployment.
- **Milestone closed**: the contract's selected endpoint and all required receipts are satisfied. A candidate-only tranche may close only as an explicit owned hold; it never proves a product milestone complete.
- **Held for approval**: direct main delivery awaits the exact named approval and approver required by `human_approval_required`; it does not auto-push.
- **Superseded**: a successor or decision explicitly replaces the work with preserved evidence and a named owner.
- **Deployed**: an explicitly authorized release reached its intended runtime and was probed there. A pushed commit is not deployment.
- **Blocked**: a concrete decision, missing authority, irreversible action, or externally proven access barrier prevents the next authorized step. It is not a generic review queue or a synonym for unfinished work.
- **Invalidated**: reproducible evidence proves a work contract's premise, scope/non-goals, acceptance criteria, or product assumptions are no longer compatible. Cancel the work record as `not_planned`, archive its execution card, preserve the receipt, and return to a fresh audit; do not call it completed or leave it blocked.

## Integration disposition

A source-changing contract names its bound repository/default branch, authenticated base SHA, candidate SHA/branch, disposition owner, and concrete next decision. `candidate_only` also records its hold reason and decision/date; `human_approval_required` names the exact approval and approver. Before any successor selection, inspect the authenticated remote `main`, candidate branches, open PRs, and relevant trackers. A verified candidate with no valid disposition is an integration problem to reconcile, not permission to start unrelated work.

## Portable artifacts

- [Coordinator and worker contract](AGENT.md)
- [Agent-neutral recovery template](SOUL.template.md)
- [Coordination skill](skills/discrepancy-to-delivery.md)
- [Implementation skill](skills/verified-implementation-delivery.md)
- [Card orchestration skill](skills/card-orchestration.md)
- [Canonical contract body template](templates/contract-template.md)
- [Contract-authoring skill](skills/contract-authoring.md)
- [Generic templates](templates/README.md)
- [Adapter guidance](adapters/README.md)
- [Traceability manifest](manifest.md)
- [Local validator](verification/README.md)

## Portable adoption

Use this Foundry-owned kit directly or copy it into a target repository when a local copy is needed. Replace placeholders only after checking the target's current authoritative sources, and run the documented validator before enabling a workflow. A target may use a board, issue tracker, direct files, a periodic job, or a manual review cadence. These are adaptation choices, not assumed capabilities.

The product specification remains architectural authority; a specific contract supplies bounded work authority; this kit is portable procedure and cannot override either. The canonical editable source for a contract body is `templates/contract-template.md`; `templates/issue-work-contract.md` is the generic tracker template and `templates/implementation-card.md` is the separate execution-card template.
