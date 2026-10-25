# Foundry work contract

Version: 0.2 — agreed workflow; service extensions not yet implemented.

Architect, Coordinator, Worker, and Auditor / QA are separate runtime-neutral skills, not persistent profiles. AI.Contract is the authoritative record for projects, contracts, queue state, claims, revisions, and execution evidence. GitHub issues are historical records created only after delivery or cancellation.

See [workflow decisions](docs/WORKFLOW.md) and [AI.Contract change proposal](docs/AI_CONTRACT_CHANGES.md). These describe the target behavior, not current service capabilities.

Adapted from the [archived template](https://github.com/stemarie/context-foundry/blob/archive/pre-reset-2026-10-25/kits/contract-orchestration/templates/contract-template.md).

## Contract template

### Objective

<One observable outcome and why it matters.>

### Sources and authority

- AI.Contract project and contract identifiers: <assigned service identifiers>
- Human-defined project goal and scope: <reference and relevant requirements>
- Target repository: <project repository>
- Target branch and inspected baseline SHA: <branch, SHA>
- Specification and repository instructions: <references and necessary context>
- Executable revision and digest: <service-owned immutable identity when activated>

The baseline records evidence, not permission to overwrite newer work. Contracts cannot override user instructions or repository policy. Human-defined scope authorizes the Architect to create ready contracts within it; stop for decisions outside that scope.

### Scope

<Included behavior, affected components, constraints, compatibility, and non-goals. Separate requirements from suggestions. Workers may make routine implementation choices within scope; material requirement or architecture changes return to the Architect.>

### Dependencies and concurrency

- Prerequisites: <contract IDs, or none; all must be Done before execution>
- Concurrent work and shared interfaces: <related contracts or none known>
- Conflict boundaries: <shared components/resources that must not be used concurrently>

Multiple prerequisites are allowed; dependency cycles must be rejected. Different files do not prove behavioral independence. Strict file boundaries are optional where justified.

### Acceptance criteria

- [ ] <Independently assessable observable behavior>
- [ ] <Relevant negative or regression case>

### Verification

<Repository-grounded commands, expected results, required runtime/manual checks, disposable fixtures, and cleanup. Identify proposed checks. Skipped checks are never passes.>

### Delivery

- Project delivery policy: <policy reference/version>
- Explicit contract exception: <exception and authority, or none>
- Target branch, integration method, and required approvals: <resolved policy>
- Required post-integration checks: <commands or observable checks>

The Coordinator integrates under the resolved policy. A contract does not independently grant deployment, credential, destructive-action, or merge authority. No force push unless separately authorized.

## Readiness and dispatch

The Architect maintains a small queue toward a configurable target within the approved scope. A contract is Ready when its outcome, boundaries, dependencies, acceptance criteria, verification, and delivery policy are defined and no blocking decision remains. Prerequisite completion and conflict availability determine dispatch eligibility separately.

The Coordinator selects FIFO among eligible ready contracts: all prerequisites are Done, no declared conflicts are active, and an assigned Worker is available. It atomically reserves the contract in AI.Contract before launching the Worker. Workers discover their assigned work through AI.Contract; GitHub issues do not assign or unlock work. Runtime bootstrap and actor identity details remain deferred.

Each project has a defined Worker pool. When all Workers are busy the Coordinator waits. The Worker stays assigned through QA and corrections until acceptance or explicit reassignment.

Use an isolated branch and worktree per execution attempt. Record assignment, attempt identity, branch, starting SHA, and non-secret workspace reference in AI.Contract. Never share a writable checkout. Coordinate shared external resources too.

Expired reservations do not automatically release work to a second Writer. The Coordinator confirms the old execution has stopped or stops it before reassignment. Stale attempts cannot submit accepted results or perform authorized integration.

## Lifecycle

Draft → Ready → Implementing → QA → QA accepted → Integrating → Done

- Dependency and conflict checks govern eligibility, not a new source of authority.
- QA corrections return the order to its assigned Worker.
- Blocked identifies an unmet dependency, authority, access, or decision and the stage to resume.
- Cancelled preserves the reason and evidence; it is not completion.
- QA accepted binds the contract revision and exact candidate SHA.
- Done requires integration into the target branch and successful required post-integration checks.

These are proposed Foundry/service semantics. Current AI.Contract serial-chain PASS-to-Done behavior must be changed before using it for this workflow.

## Worker receipt

Append evidence in AI.Contract identifying:

- Contract revision/digest, execution attempt, Worker, branch, base SHA, and candidate SHA.
- Changed behavior and paths; evidence for every acceptance criterion.
- Exact checks actually run, outcomes, failures, skips, and limitations.
- Required cleanup and integration considerations.

Read the current authorized revision and repository instructions before acting. Recover routine failures within scope. Return material discrepancies to the Architect rather than silently broadening the contract.

## Independent QA

A separate QA pool is assigned by the Coordinator. Initial reviews are FIFO by candidate submission. Retain the reviewer for corrections when available; correction priority and fallback timing remain implementation details to specify.

QA inspects the exact candidate and diff, assesses every criterion, and independently runs relevant verification. Append revision, attempt, candidate SHA, checks, acceptance evidence, and an Accepted / Changes requested / Blocked verdict with reproducible findings.

QA decides when reassessment by the Architect is needed; there is no fixed correction-round limit. A changed candidate needs fresh acceptance. Material contract changes create a new immutable revision, preserve prior attempts/evidence, and require reassessment before execution resumes. Prior acceptance does not transfer.

## Integration, completion, and history

The Coordinator serializes integration into each target branch, verifies acceptance still applies, checks target drift and approvals, and performs the required post-integration checks. Rebases, conflict resolutions, or other candidate changes require QA of the resulting candidate.

Record the accepted candidate, integration commit or PR, target revision, verification, and limitations in AI.Contract. Only then mark Done. Deployment is separate unless included and authorized.

After delivery or cancellation create a historical GitHub issue linking the contract identity/revision, outcome, relevant commits, and evidence. Issues never coordinate live work. If publication is unavailable, retain actual delivery/cancellation evidence and the outstanding historical publication; do not duplicate an issue after an uncertain response.

## GitHub outage behavior

Use the shared connection-scoped circuit breaker defined in [WORKFLOW.md](docs/WORKFLOW.md). Pause GitHub-dependent steps while open; local implementation and QA can continue where possible. A paused integration cannot count as Done.

## Limits

This is a contract convention. [Version 0.1 skill instructions](skills/README.md) are available. Dispatching, service extensions, runtime adapters, and unattended execution are not yet implemented. Prove one complete delivery, then two independent contracts concurrently.
