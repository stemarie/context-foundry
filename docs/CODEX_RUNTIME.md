# Local Codex Foundry runner

The runner connects to AI.Contract on the same host, subscribes to project
workflow events, and starts separate Codex processes for Architect, Worker and QA.
On acknowledgement or reconnect, it reconciles the current workflow before
attempting reservations. The service owns dependency eligibility and attempt
authority. The local journal owns process identity and launch replay detection.

Install Context Foundry and make the runtime and core skills available to Codex.
Run `context-foundry-codex-runner --config /path/to/runner.json`, or
`python3 -m foundry_runtime.codex_runner --config /path/to/runner.json` from a
checkout. The private JSON configuration contains:

| Field | Value |
| --- | --- |
| origin | AI.Contract origin with workflow SSE enabled |
| project_id | Registered project UUID |
| milestone_id | Optional fixed approved milestone UUID for legacy automatic replenishment. Omit it to use MCP planning requests. |
| checkout | Trusted local Git checkout with origin matching the project repository |
| base_ref | Local Worker base ref, default `refs/remotes/origin/main` |
| journal | Absolute path to the shared local runtime SQLite journal |
| codex, skills | Absolute Codex executable and trusted Foundry skill directory |
| coordinator | Object containing a private `credential` JSON path |
| architect | Object containing a private `credential` JSON path and a role-specific `codex_home` |
| workers, reviewers | Arrays of role objects with distinct actor identities and Codex homes |
| delivery | Optional object with explicitly authorized `repository`, shared `connection_alias`, and `checks` as an array of argv arrays |

Each credential file contains `name`, `scopes`, and `token`. Use files with mode
0600. The coordinator, architect, writer and auditor need read, write and their
respective role scope. Register Workers and reviewers and set the project queue
target in AI.Contract. The runner configures the AI.Contract MCP connection for each invocation and
provides its role token through the process environment. The token is excluded
from model shells and kept out of prompts and arguments. The Worker receives an
assignment-bound candidate commit tool for sandboxed Git handoff.
Role homes run under the local operator account. Use a trusted host and
runtime-managed credential access for role sessions.

A Worker uses one detached worktree per attempt, including corrections. QA uses
a separate clean checkout pinned to the submitted candidate SHA, which must
already exist in the local Git object store. A replayed launch resumes
supervision of the recorded invocation. A stopped role process must have
persisted its handoff before the runner advances that assignment. Resolve
uncertain execution through the core Coordinator recovery procedure. For an
expired local assignment, the runner recovers it only after confirming every
journaled process group for the attempt is stopped and rechecking the service
binding. Use the same journal when restarting the runner. A lost subscription
pauses new dispatch until the service acknowledges the next subscription.

With a delivery block, the runner integrates exact QA-accepted candidates
under the shared GitHub gate and the project target lock. Use the same journal
and connection alias across projects sharing GitHub access. The local
integration intent binds the candidate, expected remote main and target commit.
The runner verifies the intended target, runs the configured checks on that
target, records Done and publishes the deduplicated historical issue. The
operator can use the delivery wrapper skill to drive the same core delivery
procedure when resolving a blocked handoff. A failed check, target drift, or
a merge requiring manual conflict resolution stops automated delivery.
Use only authorized check commands and a trusted checkout on this host.

## Start Architect planning from an MCP client

Register the project by configuring the runner once with its project ID, local
checkout, actor credentials and pools. Omit `milestone_id` to let each request
select its own approved milestone. The project queue target determines available
planning capacity. Pending requests wait for capacity and an idle Architect.

1. Call `project_create`, `milestone_create`, then `project_planning_boundary`
   through an authorized MCP client to establish and approve the milestone.
2. Call `workflow_spec_attach` with the project and milestone IDs. For a Git
   document, supply `spec_kind: git`, its repository-relative `spec_path`,
   and the full commit SHA as `spec_revision`. The commit and blob must be
   present in the registered checkout. For a Google Doc or another external
   document, read it with an authenticated client, export the exact approved
   revision as Markdown, and pass `spec_kind: snapshot`, `spec_url`,
   `spec_revision`, and the bytes as `spec_snapshot`. Supply `spec_section` if
   planning should focus on a named section.
3. Call `workflow_planning_request` with `project_id`, `milestone_id`, the
   returned `specification_id`, and a stable `idempotency_key`. The project
   event wakes the runner. It verifies the pinned document before starting
   the Architect and uses the recorded process identity on reconnect.
4. Read `workflow_planning_list` to see Pending, Running, Completed, or Blocked
   and the persisted Architect evidence. Every published executable revision
   carries the planning request, immutable specification ID, and section.

Spec attachment and planning requests require `write` plus `coordinator` or
admin. Planning queries require `read`. Files and snapshots must be nonblank
UTF-8 Markdown, at most 65,536 bytes. The runner uses the locally available Git
object or the saved snapshot. It never fetches a document from a pasted URL.
