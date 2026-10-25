# Foundry work contract

Version: 0.1 — initial convention

This is the shared handoff between Architect, Worker, and Auditor / QA skills. Roles describe responsibilities for an assignment; they do not require persistent agent profiles. Use one GitHub issue per work order and link its implementation and receipts there.

Adapted from the [archived contract template](https://github.com/stemarie/context-foundry/blob/archive/pre-reset-2026-10-25/kits/contract-orchestration/templates/contract-template.md).

## Work order template

### Objective

<One observable outcome and why it matters.>

### Sources and authority

- Target repository: <owner/repository>
- Target branch and inspected baseline SHA: <branch, SHA>
- Requirements and applicable repository instructions: <references and necessary context>
- Allowed delivery actions and approval requirements: <explicit authority>

The baseline records inspected evidence. Preserve intervening work. The order does not override user instructions or repository policy, or grant merge, deployment, credential, or destructive-action permission by itself.

### Scope

<Included behavior, affected components, required constraints, compatibility requirements, and explicit non-goals. Distinguish requirements from implementation suggestions.>

### Dependencies and concurrency

- Prerequisites: <issue links, or none; each must be Done before this order starts>
- Concurrent work: <known related orders and shared interfaces or resources>
- Conflict boundaries: <components or resources requiring coordination, or none known>

The Architect assesses behavioral dependencies as well as overlapping files. Different files alone do not establish independence. Declare strict file boundaries only when needed.

### Acceptance criteria

- [ ] <Independently assessable behavior>
- [ ] <Relevant failure or regression case>

### Verification

<Repository-grounded commands and expected outcomes, plus any runtime or manual checks needed. Mark proposed checks as proposed. Define disposable fixtures and cleanup where relevant. Never count skipped checks as passes.>

### Delivery

<Required implementation artifact, target branch, integration method, authorized integrator, and any approval gate. Follow the target repository's workflow. Define checks required after integration. No force push unless separately authorized.>

## Readiness and ownership

An order is Ready when its outcome, scope, acceptance criteria, verification, delivery rule, and dependencies are clear; prerequisites are Done; and no blocking decision remains. Otherwise it remains Draft or is Blocked with a specific reason.

Before dispatch, check for duplicate or overlapping work. One coordinator assigns one Worker to an order and records the assignment before launching it. A comment alone is not an atomic claim: Workers must not independently race to claim orders. Automated claiming will require a mechanism that guarantees exclusive assignment.

Each Worker uses an isolated branch and worktree. Record the Worker, branch, worktree, and starting SHA in the issue. Never let two agents write the same checkout. Shared external resources also require isolation or explicit serialization.

## Lifecycle

Draft → Ready → Implementing → QA → QA accepted → Integrating → Done

- QA returns actionable corrections to the assigned Worker; the order returns to Implementing.
- Blocked records the concrete unmet dependency, authority, access, or decision and the stage to resume.
- Cancelled records why the order is no longer valid. Do not report it as completed.
- QA accepted means the exact candidate passed its acceptance checks.
- Done means the accepted change is integrated into the target branch and required post-integration checks passed.

These are workflow conventions, not an implemented dispatcher or locking system.

## Worker handoff

Append a receipt containing:

- Order reference and revision used; branch, base SHA, and exact candidate SHA.
- Changed behavior and paths.
- Evidence for each acceptance criterion.
- Checks actually run, results, failures, skipped checks, and limitations.
- Cleanup performed and integration considerations.

Re-read the current order and repository instructions before acting. Recover routine failures within scope. If evidence invalidates the objective or requires a material scope change, return it to the Architect with the conflicting evidence; do not silently rewrite the order.

## Independent QA

An agent other than the implementer reviews the exact candidate against the current order, inspects the diff, and exercises relevant checks. Evaluate demonstrated behavior, not only the Worker's narrative.

Append a receipt with:

- Order revision, candidate SHA, and reviewed scope.
- Acceptance evidence and checks actually run.
- Verdict: Accepted, Changes requested, or Blocked.
- Specific defects and expected corrections, or the exact blocker.

A changed candidate invalidates acceptance of the previous SHA. A material order amendment requires renewed readiness assessment and QA against the amended order. Preserve earlier receipts.

## Integration and completion

Serialize integration into each target branch. Before integration, confirm the candidate and order still match QA acceptance, inspect target-branch drift, and satisfy the delivery rule and approval requirements.

Rebasing, resolving conflicts, or changing the candidate requires QA of the resulting candidate. Combining accepted work also requires the relevant post-integration checks.

Append a completion receipt linking the accepted candidate, integration commit or PR, target branch revision, actual post-integration checks, and remaining limitations. Mark Done only when this evidence demonstrates delivery. Deployment is separate unless explicitly included and authorized.

## Initial limits

This document defines the contract and handoffs only. Agent launching, durable status transitions, exclusive claiming, retry budgets, and scheduling need implementation before unattended parallel execution. Start by demonstrating the full delivery loop, then two independent orders running concurrently.
