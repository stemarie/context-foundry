# Hermes acceptance runbook

Use after the [service setup](https://github.com/stemarie/AI.Contract/blob/main/docs/hermes-service-setup.md), [skill installation/handoff](HERMES_HANDOFF.md), and [runtime adapter implementation](HERMES_RUNTIME_ADAPTER.md).

This runbook specifies tests; it is not evidence they have already been run on Hermes. Perform failure injection on a disposable test project/backend with authorized resources.

## Record the test context

Record source/build revisions for both repositories and Hermes, non-secret runtime/backend identity, service origin, actual project/milestone/horizon, configured actor names, queue target, delivery policy, and credential references. Include the exact adapter launch/control interface implemented on this host.

Use a human-approved repository/scope for real delivery. Do not invent a target repository from remembered context. Do not use production failure injection or existing unrelated worktrees as fixtures.

## 1. Service and skill discovery

- Run the two AI.Contract real-server demo clients as a service baseline.
- From the installed Hermes client, discover the deployed native workflow tools and perform authenticated reads.
- Discover all four Foundry skills from the intended checkout and read their shared references. Rule out shadowing versions.
- Demonstrate that the actor names used by the runtime match the registered service pool and credentials.
- Verify prohibited role actions fail; admin scope must not be present in a Worker/QA context.

Evidence: commands, revisions, actual discovered names, safe response categories, and source paths. Service/mock success alone does not pass later stages.

## 2. Runtime primitives

Using actual installed Hermes, prove:

- Repeating a launch request for the same attempt returns/reconciles the same invocation rather than starting another writer.
- Inspect distinguishes running/stopped/unknown and identifies the real owned process/session.
- Stop waits for proven quiescence; a missing handle or expiry does not falsely pass.
- Two child invocations retain separate actor clients and workspace/current-directory state.
- A Worker cannot access another actor's credential or invoke Coordinator/admin tools through inherited capabilities.
- Process loss/restart preserves enough identity to reconcile, or produces an honest blocked state without reassignment.
- Runtime handles and cleanup belong only to adapter-owned fixtures.

Test native delegation and any wrapper actually selected. Do not replace these assertions with tests of a fake launcher and call it Hermes acceptance.

## 3. One real contract end to end

Choose one small observable in-scope outcome in the authorized target. Architect creates its complete milestone contract and native revision, declares dependencies/conflicts, and marks Ready.

Coordinator reserves it, launches the assigned Worker in an isolated worktree, and records the acknowledgement. Worker reads the exact frozen revision, implements, runs relevant checks, and submits an immutable candidate plus actual evidence.

A different QA actor inspects that exact candidate in a separate snapshot, independently exercises the criteria, and records its verdict. If corrections are needed, retain the Worker and use a new candidate/receipt with fresh QA; there is no fixed retry count.

Coordinator obtains integration ownership, verifies target drift and delivery authority, performs direct-main non-force delivery, verifies the remote target and required post-integration checks, then records native Done. Create a historical GitHub issue and record the reference.

Pass only when actual changed behavior is demonstrated, the candidate/target identities are traceable, and native history reflects the correct stages. A local commit, a pushed candidate branch, a QA summary, or the mock client's fake integration receipt is insufficient.

## 4. Two independent contracts in parallel

Architect prepares two independent in-scope contracts with explicit conflict assessment. Configure two Worker actors and a separate QA pool.

Prove the two Worker executions overlap in time using runtime start/finish evidence plus simultaneous active service attempts. Verify distinct actor identities, worktrees, branches, and immutable contract/attempt bindings. Sequential completions alone are not proof of overlap.

QA may review sequentially if the defined pool has one reviewer. Integrations must remain serialized, even though implementation overlapped. Demonstrate both actual outcomes and their Done/history evidence.

## 5. Dependencies, conflicts, and capacity

- An earlier queued contract with unmet prerequisites is skipped for an eligible independent contract.
- Multiple prerequisites all require native integrated-and-verified Done; QA acceptance is insufficient.
- A dependency cycle, self-reference, or foreign-project prerequisite is rejected.
- Declared conflicting work cannot execute together.
- All configured Workers busy means wait, not create more actors or double-assign.
- Routine heartbeat/evidence updates do not reorder eligible FIFO work.

## 6. Recovery and stale authority

- Expire a test lease while its real Worker is still alive. Show no replacement writer is launched until that execution is confirmed stopped.
- Simulate lost launch acknowledgement and Coordinator restart. Reconcile the real invocation before retrying.
- Submit stale revision, attempt, and candidate bindings; show the service and remote-write gate reject them.
- Revise a contract materially only through a new immutable revision, with old evidence preserved and renewed readiness/QA.
- Keep an unknown old execution blocked rather than attesting stopped without proof.
- Retire an accepted Worker invocation before its actor is reused, preserving the candidate for integration.

## 7. QA, drift, and failed integration

- A Worker cannot approve itself; QA must have its own actor/role and actual checks.
- QA acceptance remains separate from Done.
- A target-branch advance is inspected; candidate changes/conflict resolution require fresh QA.
- Failed post-integration checks are recorded without Done or dependency unlock.
- A failed/unknown Git operation is reconciled from authoritative state; no force push or unrelated-work discard is used to obtain success.
- Blocked QA or repeated premise failures return to Architect reassessment with concrete evidence.

## 8. Shared GitHub breaker

Use two disposable projects sharing one test connection alias.

Trigger a qualifying simulated connection/auth/rate/service failure. Show both projects pause remote GitHub operations while local checks can continue. Verify raw CLI/HTTP/SSH paths cannot bypass the gate.

After cooldown, race two coordinators and prove only one probe is admitted. Successful recovery resumes access; failed recovery reopens. Test operator intervention through the same shared state.

An ordinary missing resource or malformed request must remain an operation-local error. Simulate a lost response to a successful issue creation and prove recovery finds it rather than publishing a duplicate. Do not expose credentials in failure output.

## 9. Cleanup and final evidence

Preserve required contract/receipt/audit history. Stop adapter-owned test executions, remove only owned disposable resources, and verify no stale writer can continue. Do not delete canonical project history or unrelated checkouts.

The acceptance report should contain:

| Evidence | Required content |
| --- | --- |
| Scope and versions | Approved target/milestone horizon; service, Foundry, Hermes, adapter revisions |
| Service bindings | Project, contract, revision/digest, attempt, candidate and final target identities |
| Runtime proof | Launch/control handles, actor identity, workspace isolation, overlap and stop evidence |
| Verification | Commands actually run, criterion results, failures/skips and cleanup |
| Delivery | Non-force direct-main commit/read-back and final historical issue reference |
| Limits | Any unimplemented or unproven backend/permission/deployment behavior |

Use workflow_record/Worker/QA/completion/history operations for the appropriate authoritative evidence. Runtime journals support process/transport reconciliation; they do not replace AI.Contract.

Report implementation readiness, installed configuration, and real-agent acceptance separately. If only mock or source tests passed, label the system as awaiting real-agent acceptance.
