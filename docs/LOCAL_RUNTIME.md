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

The [command-admission/integration proof](COMMAND_ADMISSION_PROOFS_2026-11-01.md)
adds per-command generation checks: opening/recovering the breaker invalidates an
older callback's grant. Each command records its intent only after checking the
current state and probe owner. A new operation must reconcile an uncertain old
outcome; successful connection recovery does not authorize blindly replaying it.
Target integration also waits for all recorded transport groups in the shared
journal, across connection aliases, after acquiring the target lock. Controller
exit releases the OS lock but cannot attest that a prior Git process stopped.
