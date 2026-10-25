# Agreed Foundry workflow

Status: design decisions agreed with the project owner; implementation pending.

## Ownership and boundaries

A human defines project goal and scope. Within it the Architect can create ready contracts without a separate approval for every routine order. It stops when scope is fulfilled or a product decision is needed.

Each AI.Contract project binds one target repository and has its own queue. AI.Contract owns contracts, queue state, execution claims, revisions, and evidence. Foundry owns runtime-neutral skills and coordination behavior. GitHub hosts source and final historical issues; it is not the work queue or authority for execution state.

Runtime selection is deferred. Do not restore the archived Hermes profiles, Kanban control plane, or a competing contract store.

## Four skills

| Skill | Responsibility |
| --- | --- |
| Architect | Inspect current evidence, prepare bounded contracts, declare dependencies/conflict boundaries, reassess material changes. |
| Coordinator | Replenish the queue through the Architect, reserve work, assign pools, track execution, recover failures, and integrate. |
| Worker | Implement within scope in isolation and submit candidate evidence; return material decisions to the Architect. |
| Auditor / QA | Independently inspect candidates, verify every criterion, run relevant checks, and return acceptance, corrections, or blockers. |

The Architect maintains a small configurable ready-queue target. Replenishment is requested automatically by the Coordinator and never expands human-defined scope.

## Selection and capacity

- FIFO among eligible ready contracts; prerequisites must be integrated and verified (Done).
- Multiple prerequisites per contract; reject cycles.
- The Architect declares conflicts; the Coordinator prevents concurrent conflicting execution.
- A project coordinator dispatches against its defined Worker pool and waits when all Workers are busy.
- Reservation is atomic in AI.Contract and precedes Worker launch. Workers discover assigned contracts there.
- Workers retain assignments through QA/corrections until acceptance or reassignment.
- Each execution uses an isolated worktree and branch. Integration is serialized per target branch.
- QA has a separate pool assigned by the Coordinator. Initial reviews use FIFO; retain the correction reviewer when available.
- No fixed correction retry limit. QA decides when Architect reassessment is needed.

FIFO must skip currently ineligible contracts, rather than stall independent work behind an unmet dependency or conflict.

## Identity, recovery, and revisions

Reservations and evidence need distinct execution-attempt identities even if agents share a GitHub account. Exact actor bootstrap and runtime transport are deferred; no particular account arrangement is selected.

On expired execution ownership, the Coordinator confirms termination or stops the old execution before reassignment. Reject stale submissions and prevent stale integration. Expiry alone cannot guarantee the old process stopped.

Material changes create a new immutable contract revision and require reassessment before resuming. Preserve previous revisions, attempts, receipts, and verdicts. QA acceptance binds a revision and candidate, not just a contract ID.

## Delivery

Projects define delivery defaults; contracts may record explicit authorized exceptions. Resolve and record the effective policy for an executable revision so later project edits do not silently change its authority.

QA accepted is separate from Done. The Coordinator integrates under the repository policy, runs post-integration checks, and records delivery evidence. Done requires both integration and successful verification. Dependencies unlock only then.

Create a historical GitHub issue after delivery or cancellation. Link the contract and delivered commits/evidence. GitHub publication is an outstanding record obligation when unavailable; it must not erase actual delivery evidence or bypass the circuit breaker.

## GitHub circuit breaker

The breaker covers all projects sharing the affected GitHub connection.

- Connection, authentication, rate-limit, or service failures trigger the breaker. Ordinary operation-specific errors stay local.
- While open, halt access through that connection. Local implementation and QA continue where possible; GitHub-dependent steps wait.
- After cooldown, allow one controlled probe. Resume only if successful; otherwise reopen.
- A human may intervene to restore access. Coordinate intervention with the same shared breaker state.
- Preserve pending operation identity and reconcile uncertain outcomes before retrying writes, including historical issue creation.

Cooldown durations, failure thresholds, probe selection, and authentication-specific recovery policy remain implementation details. Circuit state must be shared across affected coordinators; isolated per-agent breakers cannot enforce this agreement.

## Deferred decisions

Runtime and launch/stop/health adapter; worker and QA identity/bootstrap; API/schema details; fairness for correction reviews; exact conflict-key vocabulary and reservation lifetime; breaker storage owner and timing; compatibility/migration of existing AI.Contract chains.

These do not change the agreed workflow. Specify them in bounded implementation work before claiming unattended operation.

## Delivery progression

1. Define AI.Contract extensions and verify existing compatibility requirements.
2. Implement the required service foundations in bounded increments.
3. Implement the four skills against the real service interface.
4. Demonstrate one order from scope to integrated, verified delivery and historical issue.
5. Demonstrate two independent orders concurrently, plus conflict exclusion, failure recovery, and serialized integration.
