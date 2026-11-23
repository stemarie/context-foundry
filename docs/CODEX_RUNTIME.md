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
| project_id, milestone_id | Approved project and milestone UUIDs |
| checkout | Trusted local Git checkout with origin matching the project repository |
| base_ref | Local Worker base ref, default `refs/remotes/origin/main` |
| journal | Absolute path to the shared local runtime SQLite journal |
| codex, skills | Absolute Codex executable and trusted Foundry skill directory |
| coordinator | Object containing a private `credential` JSON path |
| architect | Object containing a private `credential` JSON path and a role-specific `codex_home` |
| workers, reviewers | Arrays of role objects with distinct actor identities and Codex homes |

Each credential file contains `name`, `scopes`, and `token`. Use files with mode
0600. The coordinator, architect, writer and auditor need read, write and their
respective role scope. Register Workers and reviewers and set the project queue
target in AI.Contract. Configure a role-scoped AI.Contract connection in each
Codex home. The runner keeps the service token out of the invocation prompt.
Role homes run under the local operator account. Use a trusted host and
runtime-managed credential access for role sessions.

A Worker uses one detached worktree per attempt, including corrections. QA uses
a separate clean checkout pinned to the submitted candidate SHA, which must
already exist in the local Git object store. A replayed launch resumes
supervision of the recorded invocation. A stopped role process must have
persisted its handoff before the runner advances that assignment. Resolve
uncertain execution and expired attempts through the core Coordinator recovery
procedure. Use the same journal when restarting the runner.

This stage covers Architect, Worker and QA dispatch. Automated integration,
history publication and live multi-role Codex acceptance are tracked as follow-up
work for the full §5D harness.
