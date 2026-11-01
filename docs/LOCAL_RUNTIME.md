# Bounded local Hermes adapter

`foundry_runtime` is an operator-invoked Python library for this host's installed
Hermes and macOS sandbox backend. It installs no scheduler or active profile.
AI.Contract remains the sole authority for projects, immutable revisions,
assignments, leases, candidates, QA and integration evidence.

The operator supplies a separate disposable native home, scratch directory,
workspace, role credential and immutable binding to `Launcher.ensure(config,
model_runtime)`. Provider credentials arrive through private stdin, never the
launch journal or model tool arguments. `inspect(key)` returns running, stopped
or unknown. Repeated `ensure` reconciles the existing identity. An unknown
execution blocks recovery; `stop` must prove the owned process group stopped.

Each actual AIAgent exposes only `foundry_action`: assignment/read/diff/check,
Worker write/submit, or QA verdict. Every operation revalidates current service
ownership. Checks use operator-selected argv under the macOS sandbox, denying
network, process forks, foreign data reads and foreign writes. This intentionally
supports a restricted check suite; arbitrary build systems need a separately
verified backend. There is no unsandboxed fallback.

Workers retain their lease through QA. QA uses a separate exact-candidate
snapshot and credential. Acceptance retires the Worker; it does not mark Done.
Only the operator Coordinator obtains native integration ownership, reconciles
target drift, delivers and verifies the remote target, then completes the job.
Changed candidates require renewed QA.

All operator GitHub paths use `remote.GitHub` and one shared `core.Gate` journal
and stable connection alias across projects. Qualifying failures pause remote
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
prerequisites. It does not claim real-agent acceptance. See the acceptance report
for executed scenarios, actual revisions, delivery identities and remaining limits.
