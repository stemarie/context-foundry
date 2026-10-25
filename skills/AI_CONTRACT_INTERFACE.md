# AI.Contract interface for Foundry skills

Interface source: [AI.Contract PR #53](https://github.com/stemarie/AI.Contract/pull/53), candidate `8d25067867e44acdb2a9b075c74c15ac9dbbda76`. Projects and milestones are merged via PR #51. Native workflow operations are implemented and tested on the PR #53 branch; deployment and runtime connectivity are not established.

This mapping does not grant capabilities. Before live use inspect the connected service's MCP tools and verify the required behavior/permissions. A source implementation, successful mock client, or merged PR is not proof of a running deployment.

## Shared invocation and bindings

Use MCP `workflow_<operation>`, or POST JSON to `/api/v1/workflow/<operation>`. Both return a `workflow` result. Every operation needs `project_id`. Mutations need a stable `idempotency_key`.

The authoritative executable body is `job.revision.body_markdown`, with `job.revision.number` and `job.revision.digest`. Generic contract CRUD/projection data remains the original record; it is not a replacement for this frozen revision.

Mutations of an existing job use `contract_id`, `revision`, and `digest`. Execution operations add `attempt_id`. Candidate-bound operations use `candidate_id`; integration/completion also require exact `candidate_sha`. Read and reuse service-returned bindings. Contract format `Alpha 1.0` and serial-chain digests do not identify a native revision.

Actor identity is the authenticated token name. Worker/QA pool actor names must match their actual credentials. Do not pass actor or role as client-selectable JSON authority. Runtime adapters must bind an agent invocation to that identity and execution attempt.

## Human/operator setup

An authorized admin creates a repository project, appends human-defined milestones, and sets the planning boundary through the project APIs. Scope is milestone-defined; Architect authorship cannot extend the authorized horizon.

Admin `workflow_configure` sets a small explicit `queue_target`. Admin `workflow_agent` registers the defined pool using `agent` and `agent_role` (worker or qa). `workflow_agents` reads the pool/target. This is configuration, not a grant to create more actors when the pool is busy.

Credentials require read for reads, write plus the relevant mutation scope (architect, coordinator, writer, auditor). Keep credential values in runtime-managed secret storage, never contracts or skill files.

## Architect

1. Read current scope, milestones, policy, enrolled jobs, and source evidence.
2. Create a milestone contract using `milestone_contract_create` only within the authorized horizon.
3. `workflow_define` enrolls it in Draft with title, complete body, typed dependency IDs and conflict keys; expected_revision is 0 initially. Later material revisions name the current expected_revision and require stopped execution.
4. `workflow_ready` declares readiness using the returned revision/digest. Read back the exact body, graph, and stage.
5. Do not treat textual dependency headings as native enforcement. Missing or foreign prerequisite jobs and cycles are rejected.

Queue eligibility is separate from Ready. Only native integrated-and-verified Done satisfies prerequisites.

## Coordinator

1. Reconcile `workflow_list`, `workflow_get`, `workflow_agents`, and `workflow_history` before dispatch.
2. `workflow_reserve` atomically selects eligible FIFO work for a free configured Worker. An optional worker selects the runtime actor known to be healthy; the service does not measure machine health.
3. Read back the attempt before launch. Launch must be idempotent by attempt identity; a replayed reservation response is an old snapshot, not a fresh launch instruction.
4. Record launch acknowledgements/checkpoints via `workflow_record` with current bindings and evidence. The service does not launch or monitor processes.
5. `workflow_assign_qa` assigns FIFO submitted candidates to available QA actors, retaining the correction reviewer when free.
6. On expired/stopped work, inspect or stop the runtime process first. `workflow_recover` requires stopped_confirmed=true and evidence; then a later reservation creates a new fenced attempt. Never infer termination from expiry.
7. `workflow_integrate` acquires serialized integration for the accepted candidate. Perform authorized Git delivery outside the service; changed candidates need recovery and fresh QA.
8. `workflow_complete` requires exact candidate binding, target_sha, integration reference, checks_passed=true, and actual verification evidence. Do not submit mock attestations for real delivery.
9. After Done/cancellation create the historical issue and store its reference using `workflow_publish_history`. Use `workflow_record` for failed checks or outstanding-publication evidence; it does not change stage.

Busy capacity or no eligible work returns idle. A new scheduling decision needs a new idempotency key; retrying an uncertain prior decision reuses its key and reconciles current state before acting.

## Worker

Discover work through `workflow_assignments` using the Worker's own read credential. Require one current active assignment and verify the full frozen revision/attempt before writing.

Use an isolated worktree/branch supplied or created under Coordinator authority. Record workspace/base and actual progress evidence using supported heartbeat evidence; `workflow_heartbeat` renews only an unexpired owned lease. Runtime health reporting must continue while awaiting QA.

Submit with `workflow_submit`: exact bindings, candidate_sha, and evidence containing changed paths/behavior, acceptance evidence, checks actually run, cleanup, and limitations. The service returns an immutable candidate_id.

Corrections preserve Worker ownership and append new candidate evidence. Acceptance releases Worker capacity; it does not imply Done. Never use ordinary contract status updates to complete native work.

## Independent QA

Discover review assignment through `workflow_assignments` with the QA identity. Inspect current job, exact candidate, prior findings/history, and the full frozen revision. Review independently in an isolated snapshot and run relevant checks.

`workflow_verdict` binds the revision, attempt and candidate_id, with verdict Accepted / Changes requested / Blocked and evidence. Accepted becomes QA accepted, never Done. Request Architect reassessment through Coordinator when required; no fixed correction limit is imposed.

The service validates identity/state and stores attestations. It does not perform your checks, prove a runtime process stopped, or establish independence merely from a role label.

## Remaining live-operation requirements

Deployment of the matching interface, a reachable connection, actor-bound credentials, project scope/pools, workspace isolation, launch/stop/health adapters, idempotent runtime launching, and a shared GitHub connection breaker are still prerequisites. No Hermes installation or background process is supplied by these files.

The [native workflow guide](https://github.com/stemarie/AI.Contract/blob/8d25067867e44acdb2a9b075c74c15ac9dbbda76/docs/native-workflow.md) documents fields, limits, pagination, and compatibility. Report missing capabilities with concrete evidence; preparation drafts do not become a local substitute for AI.Contract.
