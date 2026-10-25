# AI.Contract extension proposal

Status: requirements and implementation sequence proposed from the agreed Foundry workflow. No AI.Contract code or deployment is changed by this document.

## Inspected baseline

Repository: [stemarie/AI.Contract](https://github.com/stemarie/AI.Contract)
Inspected main commit: `1d2a548c51f2482293d2857b8633abf917cbfbcc`.

Sources at that baseline:
- [README](https://github.com/stemarie/AI.Contract/blob/1d2a548c51f2482293d2857b8633abf917cbfbcc/README.md): SQLite authority, projections, CRUD/API/MCP, serial chains, frozen revisions, expiring Writer claims, receipts/verdicts, and chain lifecycle.
- [Chain domain](https://github.com/stemarie/AI.Contract/blob/1d2a548c51f2482293d2857b8633abf917cbfbcc/internal/domain/chain.go): chain roles, revision/digest bindings, claim release, artifact bindings, and append-only evidence.
- [Ownership boundary](https://github.com/stemarie/AI.Contract/blob/1d2a548c51f2482293d2857b8633abf917cbfbcc/docs/ownership-boundary.md): standalone service; Foundry owns skills/orchestration.

This is a source/document review, not a running-service capability test. Inspect application/store behavior, tests, migrations, and current deployed version before implementation.

## Current capabilities and gaps

| Existing capability | Required extension |
| --- | --- |
| Contract CRUD and status listing | Projects bound to one repository, project queues, human scope references, delivery defaults. |
| Pre-created serial chains | Multiple prerequisite contracts, cycle rejection, eligibility after integrated completion. |
| Expiring Writer claims | Coordinator atomic FIFO reservation, attempt identities, pool assignment references, conflict exclusion, controlled reassignment. |
| Frozen executable revision | New immutable revisions for material changes, reassessment and evidence retention across revisions. |
| Writer receipts and Auditor verdicts | Explicit QA acceptance versus integration/completion evidence, repeat correction attempts. |
| Chain PASS sets Done | PASS means QA accepted; Done requires Coordinator-recorded integration and successful post-integration verification. |

Do not equate the existing constant contract-format version (Alpha 1.0) with an executable revision. Define compatibility for both concepts.

## Required service behavior

### Projects and contracts

Persist one repository binding and queue per project, approved scope references, a configurable queue target, and versioned delivery defaults. Contract exceptions are explicit. Executable revisions retain their resolved delivery policy. Keep secrets out of records and projections.

Support contracts authored ahead of execution. Separate readiness from current dispatch eligibility. Define stable FIFO ordering and tie-breaking; do not reorder contracts accidentally during ordinary updates.

### Dependencies and conflict exclusion

Support multiple project-scoped prerequisites and reject cycles, self-dependencies, and invalid references. Specify cross-project dependency policy before enabling it; the agreed design does not require it.

Eligibility requires all prerequisites Done and no active declared conflict. Enforce reservation and conflict checks transactionally so concurrent requests cannot double-assign or bypass conflicts. Conflict boundaries include semantic/shared-resource conflicts, not only changed paths.

### Assignment and attempts

Expose an atomic Coordinator operation selecting and reserving the oldest eligible contract for an available configured Worker. Persist owner, attempt identity, revision/digest, and lease data. Make retries idempotent.

A reservation timeout enters recovery; it does not immediately permit a second Writer. Require Coordinator acknowledgement that the prior execution stopped before reassignment. Fence stale receipt, verdict, transition, and integration requests by attempt/revision where applicable. The service can reject stale records; Foundry/runtime adapters must stop or isolate real processes and control remote writes.

Track QA assignments and candidate submissions. Initial QA selection is FIFO; correction reviews prefer their existing reviewer when available. Leave runtime agent launching outside the service.

### Evidence and lifecycle

Implement the agreed stages: Draft, Ready, Implementing, QA, QA accepted, Integrating, Done, plus Blocked and Cancelled with reason and resume context.

Worker evidence names candidate SHA, attempt, checks and outcomes. QA independently binds a verdict to the exact revision/candidate and evidence. Preserve correction attempts without a fixed retry limit; QA can request Architect reassessment.

Material amendment creates a new immutable revision. Invalidate eligibility and old acceptance for resumed execution without deleting historical evidence. Handle active executions explicitly before amendment takes effect.

Only authorized Coordinator completion with integration identity and successful required verification can produce Done and unlock successors. Define role permissions for Coordinator separately from current architect/writer/auditor scopes; role declarations alone are not authorization.

### Historical publication

Store final delivery/cancellation and associated GitHub history publication reference/state. Publication failure preserves delivery evidence and a pending obligation. Use stable deduplication identity and reconcile uncertain publication before retries. GitHub issues cannot drive queue eligibility or ownership.

## Foundry integration responsibilities

Foundry skills/coordinator consume the API/MCP interfaces, launch and stop agents through a future runtime adapter, manage isolated worktrees, perform real QA and integration, and publish historical issues.

A GitHub connection-scoped circuit breaker must be shared across project coordinators, halt GitHub access on qualifying failures, allow local work, and reopen access only through controlled recovery. Its persistence/enforcement owner needs an explicit implementation choice; do not assume AI.Contract already proxies GitHub or add a second execution runtime to it.

## Suggested bounded implementation sequence

1. Projects, repository/scope binding, delivery defaults, and contract association.
2. Dependency graph and readiness/eligibility rules with cycle validation.
3. Coordinator reservations, conflict exclusion, attempts, and recovery fencing.
4. Immutable revision evolution, QA assignment/evidence, integration receipts, and Done semantics.
5. Historical publication tracking and Foundry API/MCP consumption.

Each increment needs its own executable contract once the service is available. This document is a proposal, not a set of dispatched contracts.

Before changing existing chain semantics, choose and document migration/compatibility behavior. Do not silently reinterpret old PASS/Done records as proof of integration.

## Required acceptance scenarios for implementation

- Two concurrent reservations cannot assign one contract or one exclusive resource twice.
- FIFO skips dependency-blocked and conflicting work and selects an eligible independent contract.
- Multiple prerequisites unlock only after verified integration; cycles are rejected.
- A busy Worker pool causes waiting; a Worker stays assigned through QA corrections.
- QA is independent, reviews exact candidates, and changing a candidate requires renewed acceptance.
- Reassessment preserves old evidence and prevents stale revision/attempt submissions.
- Expiry does not enable reassignment before old-execution resolution.
- QA PASS alone cannot mark Done; failed integration checks cannot unlock dependants.
- Replayed mutations and uncertain history publication do not duplicate results.
- Existing persistence/projection guarantees, authorization boundaries, and supported legacy behavior remain valid.

Use repository-grounded tests plus disposable end-to-end API/MCP and runtime evidence where relevant. Commands and exact schema changes must be established during implementation inspection.
