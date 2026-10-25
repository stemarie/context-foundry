# Hermes runtime adapter specification

Status: implementation contract, not an existing adapter. The native AI.Contract operations already exist; the runtime bridge and GitHub breaker described here still need to be built and tested against the installed Hermes version.

Use [the handoff](HERMES_HANDOFF.md) for setup and [acceptance](HERMES_ACCEPTANCE.md) for observable completion criteria.

## Responsibility split

| Component | Owns |
| --- | --- |
| AI.Contract | Project/milestone scope, revisions, queue order, dependencies/conflicts, assignments, attempts, receipts, QA/integration stages |
| Hermes adapter in Context Foundry | Launch identity/handles, tool/credential scoping, isolated workspaces, health/stop evidence, idempotent launch/recovery |
| GitHub transport gate in Context Foundry | Shared connection health, allowed remote Git/GitHub operations, uncertain-write reconciliation |
| Skills | Architect reasoning, Coordinator decisions, Worker implementation, independent QA and real verification |

A local runtime journal is allowed for process handles and transport health. It must not become a second queue, contract database, or source of assignment truth.

## Required adapter operations

These are proposed interface responsibilities, not callable Hermes commands:

| Responsibility | Inputs | Required result |
| --- | --- | --- |
| Inspect capabilities | Installed runtime/build and current configuration | Verified launch, inspect, stop, identity, credential/tool isolation, and backend behavior |
| Ensure one launch | Project, contract, revision/digest, attempt ID, actor, skill, workspace and credential references | Existing or newly acknowledged handle for that same attempt, never an extra invocation on replay |
| Inspect execution | Durable attempt/handle binding | Running, stopped, or unknown; runtime/process identity and evidence |
| Stop and wait | Exact owned execution binding | Confirmed termination/quiescence evidence, or a concrete unknown/barrier |
| Report progress/lease | Current service binding under that Worker's identity | Actual heartbeat/record result; no silent ownership renewal after expiry |
| Retire invocation | Accepted/cancelled/stopped attempt | No old writer remains able to act, while candidate/evidence is preserved |
| Gate GitHub operation | Connection alias, actor/attempt, authorized operation | Allowed through shared breaker and ownership policy, or paused/denied |
| Resume bounded coordination | Project and current service state | Reconciled checkpoint and next event/action, not a fictional running daemon |

Select API names and files using repository conventions. Keep the implementation narrow enough to understand and exercise locally.

## Launch identity and duplicate prevention

The stable launch identity includes service origin/instance, project ID, contract ID, immutable revision/digest, execution attempt ID, and actor. Do not key only by issue, branch, model name, PID, or repository path.

Persist launch intent before starting an execution. Repeated launch requests must find the existing invocation or reconcile an uncertain start. If the runtime returns a handle late or the parent crashes before saving it, identify the child through the same attempt binding before retrying.

Native delegation may be used if it provides the required behavior. Inspect the live tool schema. Upstream delegate_task exposes spawn/list/steer/stop, but its prompt role label is not authentication, and a session-scoped handle is not proof of cross-restart control. If persistence/control is unavailable, return unknown and keep recovery blocked, or implement the smallest supervised isolated-process path. Never infer stopped from a missing list entry or from elapsed time alone.

Test lost launch responses and parent restarts explicitly. An idempotent reservation response can be an old snapshot: read current ownership before every launch. Do not promise exactly-once operating-system execution based only on a database receipt.

## Per-invocation actor and capability isolation

Every Worker/QA invocation has a service credential whose token name matches its configured actor. Coordinator scope cannot be inherited by a Worker; Writer scope cannot serve as QA. Admin credentials stay in operator setup.

Do not mutate process-global MCP headers, environment, current directory, or HERMES_HOME to switch identities while children run concurrently. Use verified per-invocation contexts, scoped clients/credential broker, or isolated child processes. A role instruction in a prompt is insufficient.

The trusted adapter may resolve an allowed credential reference, but the child may access only its own role-bound client. Do not put all role tokens in a model-visible environment or expose all privileged MCP connections through the parent tool registry. If Hermes inherits parent tools, filter or replace those capabilities before giving the child work.

Validate that a child cannot select another actor's token/reference, call Coordinator/admin operations, impersonate QA, or use a generic network/terminal path to bypass the transport gate. Record tests against the actual chosen backend. Reusing one GitHub login does not remove the need for distinct AI.Contract actor identities.

## Workspace and source delivery

Create a separate worktree and candidate branch for each Worker attempt, based on the inspected target revision. Give QA a separate exact-candidate snapshot. Terminal/task isolation alone is not worktree isolation.

Record non-secret workspace path, branch, base SHA, runtime identity, and attempt binding through supported service evidence operations. Worker heartbeat evidence can record workspace/progress; Coordinator workflow_record can record launch acknowledgement and health observations.

The Worker may make routine changes within its frozen contract and run relevant checks. A submitted candidate identifies an immutable commit, not a moving branch. Candidate pushes, if authorized, go through the GitHub gate. Stale attempts lose remote-write capability.

The Coordinator serializes integration, obtains workflow_integrate for the accepted candidate, inspects target drift, and performs direct-main non-force delivery under AGENTS.md. No PRs. If rebasing, conflict resolution, or new code changes the candidate, require fresh execution/QA before delivery. Preserve unrelated intervening work.

Only record workflow_complete after actual remote revision verification and successful post-integration checks, with the real target SHA/reference and evidence. Failed checks are recorded with workflow_record while the job remains unresolved. The service does not run those checks or validate an artifact merely from checks_passed=true.

Do not remove an active worktree or discard unrelated edits. Retain required candidate/evidence until the terminal handoff and then clean only adapter-owned disposable resources.

## Lifetime, leases, and recovery

A healthy Worker keeps its lease current while implementing and awaiting QA/corrections. The service accepts renewals only from its current actor/attempt before expiry. A successful progress summary is not a heartbeat.

On a lost/expired lease, stop new writes from that invocation and notify the Coordinator. Confirm or stop the old execution before workflow_recover with stopped_confirmed=true and evidence. Then re-read the service and reserve a fresh attempt. Never auto-requeue solely on expiry.

On Coordinator restart, reconcile service state, persisted launch intents/handles, process identity, workspaces, and uncertain remote operations. PID reuse must not identify a new process as the old execution. Treat unprovable identity or termination as unknown; do not kill unrelated processes or falsely attest a stop.

Workers remain reserved through corrections. Acceptance releases service Worker capacity, but the adapter must still retire or prove the old invocation quiescent before reusing that actor for new work. Keep the accepted candidate accessible for integration. QA actor capacity and corrections follow the service's current assignment.

If AI.Contract becomes unavailable, do not invent assignment transitions or accepted evidence locally. Preserve reportable evidence, stop actions that need current authority, and reconcile using idempotency keys when connectivity returns.

## Shared GitHub circuit breaker

This is required transport behavior, not another work lifecycle. Key state by the actual shared GitHub connection/credential alias across all projects using it.

| State | Allowed behavior |
| --- | --- |
| Closed | Authorized operations proceed; qualifying failure opens the breaker |
| Open | All GitHub access through that connection pauses; local work may continue where possible |
| Half-open | One coordinated probe after cooldown or operator intervention; success closes, failure reopens |

Connection, authentication, rate-limit, and GitHub service failures qualify. Ordinary resource/request errors remain local. Distinguish an operation-specific permission denial from an invalid connection; do not open a global breaker for every 403/404.

Honor Retry-After/reset timing where present. Choose and document bounded transient-failure cooldown/backoff defaults (a reasonable starting proposal is 30 seconds up to five minutes). Human credential repair/reset must use the same shared state and controlled probe. These are implementation settings to verify, not a claim that current code already enforces them.

Use atomic shared state so two coordinators cannot both own the half-open probe. Store only safe aliases, times, outcome categories, and probe ownership; never token values or raw sensitive responses. Persist across restarts.

All remote Git/GitHub paths must go through the gate: MCP/API calls, gh, curl-like clients, and Git HTTP/SSH transport. Unrestricted child shell/network capabilities would defeat the breaker; enforce the selected backend's tool/network policy or a trusted broker/wrapper. Local Git diff/test operations remain possible while open.

A push/merge/issue request can succeed remotely and lose its response. Preserve the operation identity. Once access is restored, read remote state before retrying, and deduplicate final historical issue creation. Do not mark a successful repository delivery undone just because historical publication is pending.

Test connection-sharing and bypass attempts on disposable fixtures. Do not revoke production credentials or disrupt real shared networking to manufacture a test.

## Coordinator cycle

1. Inspect the actual project, human milestone horizon, queue target, pools, native jobs/history, and runtime health.
2. Ask Architect for in-scope replenishment when needed; coalesce outstanding replenishment requests.
3. Reserve eligible FIFO work for a free, healthy configured Worker. A busy pool means wait.
4. Ensure one actor-bound launch and record acknowledgement. Monitor ownership/lifetime.
5. Assign independent QA, bind exact candidate, and route corrections to the assigned Worker.
6. Reassess material scope/revision changes through Architect; preserve old attempts/evidence.
7. Integrate accepted work one target at a time; verify delivery and mark native Done.
8. Publish final history only after delivery/cancellation and record its reference.
9. Return a checkpoint when a bounded invocation ends; stop at the approved milestone or a genuine external decision.

Do not create a recurring scheduler merely to make a one-shot session look autonomous. Add long-running operation only when requested, using the same service/adapter responsibilities.

## Implementation deliverable

Provide tested adapter source in Context Foundry, configuration examples containing references rather than secrets, installed-runtime capability evidence, and the [acceptance report](HERMES_ACCEPTANCE.md). Keep source tests, mock transport tests, real Hermes process tests, and actual repository delivery evidence distinct. Document any backend capability that remains blocked rather than downgrading the contract silently.
