# Bounded local Hermes adapter

`foundry_runtime` is an operator-invoked Python library for this host's installed
Hermes and macOS sandbox backend. It installs no scheduler or active profile.
AI.Contract remains the sole authority for projects, immutable revisions,
assignments, leases, candidates, QA and integration evidence.

The operator supplies a separate disposable native home, scratch directory,
workspace, role credential and immutable binding to `Launcher.ensure(config,
model_runtime)`. Native startup uses isolated Python (`-I -B`) with explicit trusted import roots; candidate modules cannot bootstrap the agent. Use a prepared Hermes virtualenv. The child sets the supported `HERMES_DISABLE_LAZY_INSTALLS=1` mode, so isolated homes do not provision dependency copies. Missing dependencies fail closed. Provider credentials arrive through private stdin, never the
launch journal or model tool arguments. `inspect(key)` returns running, stopped
or unknown. Repeated `ensure` reconciles the existing identity. An unknown
execution blocks recovery; `stop` must prove the owned process group stopped.

Each actual AIAgent exposes only `foundry_action`: assignment/read/diff/check,
Worker write/submit, or QA verdict. Every operation revalidates current service
ownership. Checks use operator-selected argv under the macOS sandbox, denying
network, process forks, foreign data reads, foreign writes and Git metadata writes. This intentionally
supports a restricted check suite; arbitrary build systems need a separately
verified backend. There is no unsandboxed fallback.

Workers retain their lease through QA. QA uses a separate exact-candidate
snapshot and credential. Acceptance retires the Worker; it does not mark Done.
Only the operator Coordinator obtains native integration ownership, reconciles
target drift, delivers and verifies the remote target, then completes the job.
Changed candidates require renewed QA.

The verified delivery allowlist is `stemarie/context-foundry`; other targets require explicit operator authorization and configuration. All operator GitHub paths use `remote.GitHub` and one shared `core.Gate` journal
and stable connection alias across projects. One shared journal path is mandatory across Coordinators; independent journals cannot coordinate the same connection. `GitHub.integration()` holds a target lock through ownership, push, postchecks and native Done. Qualifying failures pause remote
operations with a single half-open probe; ordinary resource errors remain local.
Uncertain writes require authoritative reconciliation. Git pushes check both the
preflight head and the head advertised to the pre-push hook, use no force option,
and require a fast-forward. Historical issues are published only after outcome.
No remote GitHub credential or generic transport is exposed to agents.

Run local controls with:

```
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

The separate `scripts/acceptance_preflight.py` verifies service/native skill
prerequisites. It does not claim real-agent acceptance. The `real_agent_acceptance.py` scenarios use actual model calls and authorized main delivery; `breaker_acceptance.py` uses actual disposable service projects with simulated remote failures. See the [acceptance report](HERMES_ACCEPTANCE_2026-11-01.md)
for executed scenarios, actual revisions, delivery identities and remaining limits.


Read/diff pages expose `next_offset`, `total_characters`, `truncated` and `version`.
Continue with the returned offset/version until next_offset is null. History uses
`after`/`next_after`; assignment resolves all pages and separately exposes the
current-attempt `latest_review`. Historical reviews never transfer acceptance.

Submission prepares a durable local outbox intent before committing. Retrying a
verified unchanged workspace uses its original SHA/evidence/idempotency request;
`pending_submission` exposes its original summary. The outbox is transport
reconciliation only. AI.Contract remains authoritative for whether it accepted it.

Connection probes are released on every callback exit. Recovery can reclaim a
proven dead process owner, never a live/unobservable one. Operator intervention
respects known server reset deadlines. Transport diagnostics use safe categories;
transient service outages fence actions until actual current authority and the
owning heartbeat are revalidated. See the [gap-closure proof](HERMES_GAP_CLOSURE_2026-11-01.md).

The [three-gap follow-up](FOLLOWUP_GAP_CLOSURE_2026-11-01.md) strengthens that
recovery boundary. A late failure cannot shorten an existing server deadline.
Remote commands entered through the gate persist a transport intent, then an
isolated trampoline acknowledges a new process group before executing Git/GitHub.
A dead controller is recoverable only after every recorded transport group is
absent. An absent leader does not prove its descendants stopped. Unknown starts,
permission uncertainty and legacy probes without transport tracking stay blocked
for explicit reconciliation. No credential, command arguments or output is added
to the journal. Uncertain remote outcomes still require authoritative readback.

Before native authority, launch or each actor action, the adapter reads the
ordinary record's immutable semantic `contract_version` through the existing GET
API. Only `Alpha 1.0` is supported; missing/unknown versions fail closed. The
model receives the checked version alongside the current native executable body;
the ordinary body never substitutes for the native revision. No service schema,
endpoint or assignment authority changes.

## Bounded model configuration, continuation, and focused editing

The public launch `config` may include an optional `sdk` object for both Worker and QA: `max_iterations` (integer 1–48, default 12), `max_tokens` (integer 256–12000, default 3000), and `run_budget_seconds` (integer 1–1200, default 180). Unknown keys, booleans, non-integral numbers, non-finite values, and values outside those ranges are rejected. `invocation_seconds` remains an independent finite 1–1200 second outer deadline; each model turn is capped to its remaining time. The adapter revalidates native authority before every turn and tool action. It records the selected SDK settings and each actual remaining-time turn cap in the private invocation event evidence. A model's natural-language completion without submission or verdict is recorded as a pending required transition and is re-prompted within that deadline; provider and authority failures are not converted into transitions.

Workers also have an `edit` operation for bounded literal changes to an existing regular workspace file. First `read` the complete current file and retain its returned SHA-256 `version`; then supply it as `expected_digest` with 1–64 `{old, new}` string replacements. Each `old` must be nonempty and occur exactly once; each old/new value is at most 32 KiB and the result at most 512 KiB. All replacements are validated before the write, stale/ambiguous/missing values fail without mutation, and a successful edit clears prior check evidence. The same checked-path, current Implementing authority, worker role, lock, traversal/symlink/metadata restrictions apply. QA cannot edit. This is literal file editing only: it has no shell, code execution, network, or baseline-source restore path; full `write` remains available under its existing limits.

This delivery uses the coordinator's transparent task-only bootstrap for the prerequisite Worker/QA execution. It is not the larger stock-runtime coding proof; that proof remains pending the dependent contract.

The [command-admission/integration proof](COMMAND_ADMISSION_PROOFS_2026-11-01.md)
adds per-command generation checks: opening/recovering the breaker invalidates an
older callback's grant. Each command records its intent only after checking the
current state and probe owner. A new operation must reconcile an uncertain old
outcome; successful connection recovery does not authorize blindly replaying it.
Target integration also waits for all recorded transport groups in the shared
journal, across connection aliases, after acquiring the target lock. Controller
exit releases the OS lock but cannot attest that a prior Git process stopped.

## Operator-only historical close recovery

`remote.GitHub.close_history(url)` remains conservative: a started close whose
outcome reads OPEN remains uncertain and refuses another write. The operator may
use `GitHub.recover_close_history_known_not_applied(url,
known_not_applied=True)` only after explicitly determining that the original
close is known not applied. This API is not exposed through `foundry_action` to
Worker or QA and operators must not edit the SQLite journal directly.

The procedure preserves `close:<url>` and its original intent. It records an
append-only recovery attempt linked to that identity in the shared journal and
holds a durable per-logical-operation callback owner across both the original
`Gate.run` callback and recovery. This blocks a recovery while an original
callback is paused before its first transport, and blocks concurrent recoveries;
a dead owner is reclaimable only after all transport groups are quiescent. It
validates the authorized repository, canonical issue URL and nonzero canonical
issue number, reads a stable OPEN issue snapshot with a valid `updatedAt`,
and reads complete paginated GitHub issue-event history. Every page and event
must have the expected authoritative shape; closed snapshots require a valid
`closedAt`. It rejects any close/reopen evidence, malformed or incomplete
pagination, identity mismatch, or a changed snapshot. Thus an OPEN read alone
never proves absence. A CLOSED result is reconciled without a second close.

All proof reads, the retry, and final reconciliation run through the existing
shared `Gate` current admission. Before proof and again before retry, every
recorded transport group and every alias across connection aliases must be
quiescent and tracked; live, unknown, unobservable, or any unconfirmed legacy
`transport_tracking=0` alias (including CLOSED) blocks recovery. A CLOSED
legacy alias with `transport_tracking=0` is not silently trusted: only an
operator, after stopping and independently confirming all old callbacks,
transports, and probes, may call
`Gate.confirm_legacy_quiescence(evidence, confirmed_stopped=True)`. It requires
nonempty evidence, rejects active/unknown ownership, preserves breaker state and
deadlines, bumps generation to fence stale admissions, and appends durable
confirmation evidence. It is not exposed to Worker/QA and never permits journal
SQL edits. A stale
admission generation, newly opened gate, cooldown, or another probe owner blocks
the next command. The retry performs a fresh state read immediately before the
close and verifies CLOSED afterward. A lost second response remains a started,
reconcilable operation; it is never blindly retried. Retain the explicit operator
attestation and command/check evidence with the pending historical-publication
record. This does not claim delivery, native `Done`, or post-integration checks.
