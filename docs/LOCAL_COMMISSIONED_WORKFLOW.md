# Commissioned local BEE1 workflow

This is the bounded, operator-invoked Context Foundry workflow for commissioned AI.Contract execution on BEE1. It is **not** a deployment, scheduler, daemon, or generic always-running controller. AI.Contract owns contracts, queues, scope, assignments, evidence, QA, integration state, and `Done`. Context Foundry supplies local processes, isolation, the GitHub breaker, and delivery. OpenSpec remains planning authority; it is not an execution queue.

## Private connection and status

Private configuration is `~/.config/context-foundry/bee1.json`. Its credentials directory is mode700 and its files are mode600, owned by the operator. Five separate retained read/architect/coordinator/worker/qa credentials are configured (the read credential is named `reader` in `bee1.json`); there is no active retained admin. Role scopes are **SERVICE-WIDE**, not project-only server ACLs. Local actor/attempt binding adds the project and assignment enforcement.

Current credentials expire 30 days after issue; exact expiry and IDs are in private credential metadata. An authorized operator must renew or revoke them. Never paste bearer values into contracts, logs, commands, or the repository.

Use a trusted absolute import root; do not imply that generic `python -m` works from an arbitrary cwd:

```sh
/usr/bin/python3 -I -B -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/.local/share/context-foundry/runtime')); from foundry_runtime.local_connection import main; main()" --config ~/.config/context-foundry/bee1.json status
```

`os.path.expanduser` converts the trusted runtime location to an absolute path before importing. When configured, status reports the repository, project, planning horizon, queue target, pools, service readiness, and last native job. It does not prove `Done`.

The stdio bridge owns a loopback-only SSH tunnel for its invocation and shuts it down at exit; it is not a daemon. SSH reaches `karell@192.168.1.176` and the already-running private listener `127.0.0.1:18080`. This makes no service change or deployment.

## Read-only MCP discovery

Both Hermes and Codex use the `ai-contract-bee1` connection. It is a read-only MCP view with 16 discovered tools: no Worker, QA, admin, or Coordinator mutation tools are globally exposed. Reopen or reload clients to see a newly added connection. Existing other MCP entries are preserved.

## Runtime and operator route

The managed runtime is `~/.local/share/context-foundry/runtime`. Installed Hermes source is `~/.hermes/hermes-agent`, using its existing Python virtualenv from private config. `HERMES_DISABLE_LAZY_INSTALLS=1`; there is no per-home runtime provisioning. The installed macOS backend requires `sandbox-exec`, with no unsandboxed fallback.

Skills read `bee1.json` privately, use `local_connection.tunnel(config)` and `credential(config, role)` with `Client`, then construct `Journal(config['journal'])` and `Launcher(journal, config['hermes_python'], config['hermes_source'])`. Never print tokens. Every project on this connection shares the same `runtime.sqlite` and GitHub alias `owner-github-context-foundry`.

No finished generic always-running controller exists. The operator constructs bounded configuration from the current assignment, and there is no automatic continuation after invocation exit.

## Native execution and delivery

Inside the human planning horizon, the Architect creates immutable bounded work. The Coordinator reconciles current jobs/pools, reserves natively, launches isolated role processes, and retains the Worker through QA. A Worker acts only on its own assignment. Separate independent QA reviews the exact candidate SHA; QA accepted is not `Done`.

The Coordinator serializes target integration and an expected-head non-force `main` push, verifies the remote and successful postchecks, then records native `Done`. A historical GitHub issue comes **after** the outcome and is linked through `publish_history`. GitHub issues are not a queue; direct ordinary-status updates do not substitute for native workflow. Expiry is not proof of termination: reconcile or stop the prior process before reassignment.

## Shutdown and recovery boundary

During a normal BEE1 read-only bridge invocation, EOF leaves the `with tunnel(...)` scope and closes its owned SSH master. Routine SIGTERM is temporarily converted into orderly stack unwinding while that tunnel is owned, so its `finally` sends the SSH control exit and waits for the client. The previous SIGTERM handler is restored after cleanup. The SSH client remains in the bridge process group rather than creating a detached session, so client-group shutdown cannot intentionally leave its owned tunnel behind.

This protects routine, catchable SIGTERM and normal EOF only. SIGKILL and other forced uncatchable termination cannot run Python cleanup and are not verified shutdown. An uncertain termination also does not prove that the runtime process or SSH tunnel stopped. Before retrying or recovering, the operator must reconcile the owned runtime/attempt identity in AI.Contract and the owned tunnel/master identity on BEE1; only confirmed closure permits a replacement or recovery action. Do not use read-only MCP discovery to mutate that state, and do not create a daemon or deployment as a workaround.

The recorded operator preflight established the BEE1 read-only connection and separate actor identities; it is not final live proof of SIGTERM cleanup. Independent QA reviews the complete exact candidate, including commissioned connection prerequisites, and runs its own check. The operator records the actual BEE1 initialization and owned-master closure after SIGTERM, then runs the full 40-test host suite before and after expected-head `main` delivery. The Coordinator records verified `Done` and history only after delivery. This guide claims no deployment; OpenSpec planning and AI.Contract ownership remain unchanged.
