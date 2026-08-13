# Context Foundry Contract-Orchestration Kit

## Purpose and scope

This is Context Foundry-owned, portable protocol-and-template material for a repository owner and an authorized agent. It standardizes a repeatable, source-grounded development loop without assuming a particular agent, scheduler, task board, credential store, host, or remote service.

It is documentation and local validation material. It does not install a scheduler, continuation hook, listener, credential, remote integration, or control plane.

## Lifecycle

1. **Source and specification audit.** Read the current work record, authoritative specification, repository policy, current checkout, and authenticated remote when authority exists. Resolve contradictions from those sources rather than from remembered context.
2. **One bounded work contract.** Deduplicate comparable open work before creating one observable contract with scope, acceptance criteria, non-goals, safety boundaries, verification, and delivery authority.
3. **Serialized implementation.** Assign exactly one active writer for a shared checkout. The coordinator records an idempotency key and does not create competing implementation work.
4. **Real verification.** Run the contract's required checks and any real disposable runtime probe. Record commands, outcomes, changed paths, and cleanup evidence. A skipped check is not a passing check.
5. **Authenticated remote delivery and receipt.** Only an agent explicitly authorized and authenticated for delivery may commit or push. Confirm local HEAD, the authenticated remote branch, and fetched tracking branch agree before terminal completion. Add a receipt to the authoritative work record.
6. **Contract invalidation or fresh continuation.** If live evidence proves the work order false, contradictory, out of scope, or superseded, record one fingerprinted receipt, cancel it as `not_planned`, archive its execution card, and return to the source/specification audit. Do not keep retrying it, silently expand its scope, or presume a replacement. Otherwise re-read current state after verified completion and use the periodic/manual audit loop as the reliable continuation fallback.

## State vocabulary

- **Implemented**: scoped source changes exist locally. This says nothing about tests, remote delivery, deployment, or acceptance.
- **Verified**: the stated checks actually passed against the stated revision and fixture. A skipped, unrun, or unrelated check is not verification.
- **Deployed**: an explicitly authorized release reached its intended runtime and was probed there. A pushed commit is not deployment.
- **Blocked**: a concrete decision, missing authority, irreversible action, or externally proven access barrier prevents the next authorized step. It is not a generic review queue or a synonym for unfinished work.
- **Invalidated**: reproducible evidence proves a work contract's premise, scope/non-goals, acceptance criteria, or product assumptions are no longer compatible. Cancel the work record as `not_planned`, archive its execution card, preserve the receipt, and return to a fresh audit; do not call it completed or leave it blocked.

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
