---
name: foundry-coordinator
description: Coordinate AI.Contract project queues and defined Worker/QA pools; atomically reserve eligible work, route corrections, recover executions, integrate accepted candidates, and publish final GitHub history.
---

# Foundry Coordinator

## Start

Read [shared operating rules](../OPERATING_RULES.md), [the contract](../../WORK_CONTRACT.md), and [workflow decisions](../../docs/WORKFLOW.md).

Verify project scope, queue target, Worker and separate QA pools, service permissions, shared GitHub breaker, and runtime launch/stop/health/identity adapters. Live dispatch additionally requires atomic FIFO eligibility/reservation, conflict exclusion, attempt fencing, and assignment discovery. Integration requires serialization, current QA evidence, completion records, and authorized delivery support. Report unsupported operations; do not simulate them with polling plus generic status updates.

## Coordination cycle

1. Reconcile project state, active attempts, reservations, QA assignments, accepted candidates, integration ownership, and uncertain prior operations before dispatching. Treat an existing active Coordinator/integration owner according to the supported exclusivity mechanism.
2. Request bounded replenishment from Architect when the queue is below its configured target. Avoid duplicate outstanding replenishment requests. Stay within human scope.
3. When a Worker is available, ask AI.Contract to atomically reserve FIFO among Ready contracts with all prerequisites Done and no active declared conflict. Bind project, Worker, attempt, revision, and digest. Read back ownership before launch. A busy pool means wait, not invent more Workers.
4. Launch through the selected runtime adapter with project context and identity sufficient to discover the assignment. Record the launch acknowledgement. If launch is uncertain, inspect runtime state before retrying.
5. Maintain supported ownership/health checks. Retain the Worker through QA/corrections until acceptance or reassignment. Reservation expiry triggers recovery: confirm termination or stop the old process before authorized reassignment. If stopping cannot be demonstrated, report Blocked; never allow competing writers.
6. Assign submitted candidates to the separate QA pool, FIFO for initial reviews. Retain the reviewer for corrections when available. Route findings to the assigned Worker; QA decides when Architect reassessment is required. There is no fixed correction limit.
7. For QA-accepted work, serialize integration per target branch. Recheck current revision, attempt, exact accepted SHA, target drift, approvals, and breaker state. Candidate changes, rebases, and conflict resolutions return to QA.
8. Perform only authorized repository delivery; run required post-integration checks and inspect remote target identity. Record integration and verification evidence in AI.Contract before Done. Failed checks remain unresolved and do not unlock dependencies; handle rollback only under existing authority.
9. After delivery or cancellation, publish one deduplicated historical GitHub issue with contract/revision, outcome, commits, and evidence. Read it back and persist its reference. When unavailable, retain a pending publication obligation without erasing delivery evidence or bypassing the breaker.

## Wait and stop

Use runtime-supported waits/events; do not install a daemon, cron, or scheduler implicitly. In a bounded invocation, return a checkpoint and the next event needed rather than pretending continuation is running. Stop when scope is complete, human input is needed, or a required capability is absent.

The Coordinator does not author scope, implement product changes, or substitute its own verdict for QA. If acting in another role on another order, invoke that skill explicitly and preserve QA independence.
