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

## Supported bounded coding settings

The operator may set `config.sdk` for either Worker or QA: `max_iterations` 1–48 (default 12), `max_tokens` 256–12000 (default 3000), and `run_budget_seconds` 1–1200 (default 180). Values must be finite integral numbers, never booleans; unknown, malformed, negative, or excessive values fail closed. `invocation_seconds` is still the finite outer 1–1200 second deadline, and each SDK turn is capped to its remaining time. Before every turn and every action the runtime rechecks the assignment authority. Private invocation events retain the selected SDK settings and each actual remaining-time SDK turn cap for later stock-proof assessment. A completed natural-language turn does not invent submit/verdict: the runtime records pending continuation evidence and prompts again while authority and the deadline remain.

A Worker can use public `foundry_action` operation `edit` for an existing checked workspace file: read the complete content, provide that SHA-256 version as `expected_digest`, and provide 1–64 exact `{old,new}` replacements. Every old literal must be nonempty and unique; values are capped at 32 KiB and the resulting file at 512 KiB. Validation occurs before mutation, successful edits clear checks, and stale, ambiguous, missing, traversal, symlink, metadata, and QA edits are rejected. This grants no shell, code, network, or baseline restore access; full write remains compatible.

For this prerequisite delivery the Worker/QA uses the transparent task-only bootstrap supplied by the Coordinator. The larger STOCK runtime coding proof is pending its dependent contract and is not claimed here.

## Native execution and delivery

Inside the human planning horizon, the Architect creates immutable bounded work. The Coordinator reconciles current jobs/pools, reserves natively, launches isolated role processes, and retains the Worker through QA. A Worker acts only on its own assignment. Separate independent QA reviews the exact candidate SHA; QA accepted is not `Done`.

The Coordinator serializes target integration and an expected-head non-force `main` push, verifies the remote and successful postchecks, then records native `Done`. A historical GitHub issue comes **after** the outcome and is linked through `publish_history`. GitHub issues are not a queue; direct ordinary-status updates do not substitute for native workflow. Expiry is not proof of termination: reconcile or stop the prior process before reassignment.

## Shutdown and recovery boundary

During a normal BEE1 read-only bridge invocation, EOF leaves the `with tunnel(...)` scope and closes its owned SSH master. Routine SIGTERM is temporarily converted into orderly stack unwinding while that tunnel is owned, so its `finally` sends the SSH control exit and waits for the client. The previous SIGTERM handler is restored after cleanup. The SSH client remains in the bridge process group rather than creating a detached session, so client-group shutdown cannot intentionally leave its owned tunnel behind.

Control-exit timeout, non-zero exit, and control exceptions still continue to wait for that owned `Popen` child. Bounded termination and then kill escalation apply only to that child. If its exit cannot be proved, cleanup fails closed: its private control directory remains available for reconciliation and the bridge does not claim closure or signal another process/group. SIGKILL and other forced uncatchable termination cannot run Python cleanup and are not verified shutdown.

After a tunnel or upstream service failure, parsed integer and string JSON-RPC request IDs receive the sanitized `private service request unavailable` error with the same ID. Notifications produce no reply; malformed or unparseable input is bounded and cannot be correlated with a later valid request. Before retrying or recovering, the operator must reconcile the owned runtime/attempt identity in AI.Contract and the owned local tunnel/master identity on the operator host; BEE1 is the remote endpoint. Read-only MCP discovery cannot mutate that state.

## Trusted restricted-check evidence

The macOS `sandbox-exec` candidate check records an adapter-generated `checks.command` object alongside pass/fail, exit code, and bounded output. It contains the actual selected argv, resolved cwd, backend (`macos sandbox-exec`), and a SHA-256 identity over precisely those fields. Changing argv, cwd, or backend changes that identity. Worker submissions and QA verdicts persist the actual check object; model summaries are separate narrative and cannot replace the descriptor.

This proves only the operator-selected restricted command, not full discovery or host-suite coverage. Legacy receipts without command metadata remain historical records and are not backfilled. For bootstrap launches made with the pre-fix adapter, the operator appends the public operator-selected command as a clarification rather than rewriting those receipts.

The restricted suite is the operator-fixed pure regression command supplied to the agent. Run host-only process/Git coverage and the full suite separately after QA acceptance:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

## Disposable host connection proof

After QA accepts the exact candidate, the operator runs the host-only proof using private paths outside the checkout:

```sh
python3 scripts/connection_recovery_acceptance.py \
  --config ~/.config/context-foundry/bee1.json \
  --output ~/.local/state/context-foundry/connection-recovery-proof.json
```

The script starts only disposable local bridge/SSH children against BEE1's existing service. It verifies 16-tool read-only discovery, bridge mutation rejection, matching request IDs after closing its own tunnel, suspended-own-master EOF cleanup, ordinary EOF, direct-SIGTERM, and process-group-SIGTERM cleanup, and child reaping. It retains redacted evidence before cleanup and never restarts, mutates, deploys, or otherwise changes BEE1. Do not run this proof from the restricted agent sandbox.

The recorded operator preflight established the BEE1 read-only connection and separate actor identities; it is not final live proof of SIGTERM cleanup. Independent QA reviews the complete exact candidate, including commissioned connection prerequisites, and runs its own check. The operator records the actual BEE1 initialization and owned-master closure after SIGTERM, then runs the full current host suite before and after expected-head `main` delivery. The Coordinator records verified `Done` and history only after delivery. This guide claims no deployment; OpenSpec planning and AI.Contract ownership remain unchanged.

## Pending historical-close recovery

A failed `GitHub.close_history(url)` remains pending when its outcome cannot be
authoritatively reconciled; workers and QA cannot recover it. The operator-only
`recover_close_history_known_not_applied(url, known_not_applied=True,
external_writers_excluded=True, external_writer_evidence='...')` procedure is
available only for an explicit known-not-applied determination and a separate
operator attestation that independent external lifecycle writers are excluded.
The evidence must be a nonempty, at-most-1024-character string describing that
operator-controlled exclusion. The runtime cannot verify this assertion or lock
humans, the GitHub UI, or another GitHub actor; if exclusion cannot be
established, leave history pending. It preserves the original close identity and
journal, appends the asserted conditions and evidence as linked append-only
proof events, and never permits SQL surgery or alternate connections.

Before invoking it, retain the operator's explicit attestation, canonical
repository/URL/number, complete paginated issue-event evidence, and stable OPEN
snapshots with a valid `updatedAt`; CLOSED reconciliation also requires a
valid `closedAt`. Every returned page and event must have the expected
authoritative shape. The shared journal serializes the original callback and
recovery by logical close identity, including an original callback paused before
its first transport. A dead callback owner may be reclaimed only after all
transport groups are quiescent. Any prior close/reopen event, concurrent
snapshot change, missing or malformed page/event, CLOSED ambiguity, live/unknown transport,
or any unconfirmed legacy alias marked `transport_tracking=0` (including CLOSED), stale
admission, cooldown, lost probe, missing acknowledgement, or malformed external
writer evidence blocks the write. A CLOSED legacy alias marked
`transport_tracking=0` remains blocked until an operator has
stopped and independently confirmed all callbacks, transport groups, and probes,
then calls `Gate.confirm_legacy_quiescence(nonempty_evidence,
confirmed_stopped=True)`. The API rejects nonclosed aliases and active or
unknown ownership; it preserves breaker metadata, fences stale admissions by
bumping generation, and appends durable confirmation evidence. Workers and QA
cannot invoke it and operators must not alter the journal directly. The procedure reads through the shared
gate, rechecks immediately before close, then verifies CLOSED. An already CLOSED
issue returns its existing result; an uncertain retry remains pending for normal
authoritative reconciliation. This is historical-record recovery only, not a
native state transition, delivery assertion, or `Done` claim.
