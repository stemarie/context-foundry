# Local runtime quickstart

This guide is for an operator using the bounded local Hermes adapter. It covers AI.Contract, unknown execution recovery, independent QA, and no deployment. It is not an unattended runtime, deployment procedure, or proof of delivery.

## What the adapter controls

**AI.Contract** is the authority for projects, immutable contract revisions, assignments, leases, candidates, QA, integration evidence, and completion. The local adapter does not create a competing queue or infer a service transition from local state.

The operator provides a disposable native Hermes home, scratch directory, isolated workspace, role credential, and immutable binding to `Launcher.ensure(config, model_runtime)`. Provider credentials are supplied through private stdin and are not placed in the launch journal or model tool arguments. The agent receives only `foundry_action`; it has no shell, remote Git, or generic network capability.

Worker tools are limited to assignment/read/diff/check/write/submit. QA tools are limited to assignment/read/diff/check/verdict. Each tool operation revalidates the current service authority. Checks run under the verified macOS `sandbox-exec` backend, which denies network access, process forks, foreign data reads, and foreign writes. There is no unsandboxed fallback.

## Start and observe an invocation

Call `Launcher.ensure(config, model_runtime)` after preparing the operator-controlled configuration and verifying the bound assignment. Repeating `ensure` for the same binding reconciles its existing durable identity rather than creating a replacement.

Use `Launcher.inspect(key)` to determine the recorded execution state:

- `running` means the recorded process identity still matches.
- `stopped` means the owned process group is confirmed absent.
- `unknown` is intentionally conservative: launch intent, a missing leader, PID reuse, or an unmatched identity does not prove safety.

### Recovery example: an unknown execution

If `inspect(key)` returns `unknown`, do **not** launch another process or infer that the previous process stopped. `Journal.stop` and `Launcher.stop` reject unknown identity; reconcile the execution with the operator and AI.Contract first. This preserves the source control that prevents a second writer from being created after an uncertain launch or recovery.

## Verify local controls

Run the repository checks from the isolated checkout:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

`scripts/acceptance_preflight.py` separately checks supplied native service and skill prerequisites. It is a disposable preflight only: it does not start an agent and does not assert real-agent acceptance, Git delivery, or Done.

## QA and delivery boundary

Independent QA uses a separate actor credential and an exact-candidate snapshot, and must run its own checks before recording a verdict. A candidate change requires renewed QA. QA acceptance retires the Worker but is **not Done**.

Only the Coordinator obtains integration authority. It reconciles target drift, makes the expected-head non-force fast-forward delivery, runs postchecks, and records completion in AI.Contract. Historical GitHub issues are created only after delivery or cancellation. This quickstart performs **no deployment**.
