# Runtime recovery guide

This is an operator guide for the bounded local Hermes adapter. AI.Contract remains
authority for the assignment, immutable revision, lease, candidate, QA, integration
evidence, and Done state. Local journal state is not a substitute for a service
transition.

## Before recovery

Keep the operator-provided disposable Hermes home, scratch directory, isolated
workspace, role credential, and immutable `Launcher.ensure(config, model_runtime)`
binding intact. Provider credentials are supplied over private stdin; do not copy
them into the launch journal, model arguments, or diagnostics. Repeating `ensure`
for the same binding returns its durable launch identity rather than creating a
replacement.

Check the service assignment and lease before an operation. The runtime rejects a
stale revision/digest, attempt, expired lease, changed Worker ownership, or changed
QA candidate. A Worker remains assigned through QA and corrections.

## Unknown execution

Use `Launcher.inspect(key)` (or the underlying journal) to determine the recorded
state:

- `running` means the recorded PID, start identity, and launch nonce still match.
- `stopped` means the owned process group was confirmed absent.
- `unknown` is deliberate: launch intent without acknowledgement, a missing leader,
  PID reuse, or an identity mismatch does not establish that it is safe to recover.

**Recovery example:** if `Launcher.inspect(key)` returns `unknown`, do not call
`ensure` to launch a replacement and do not signal a process based only on its PID.
`Journal.stop` and `Launcher.stop` reject unknown identity. Reconcile the execution
with the operator and current AI.Contract assignment first; this prevents an
uncertain launch from becoming two concurrent writers. Once the owned identity is
known to be running, stopping targets only its process group and requires confirmed
quiescence before reporting success.

## Lease and independent QA

Each exposed Worker or QA operation revalidates current AI.Contract authority. If
service authority is unavailable, the runtime fences writes; it does not infer a
local transition. Recover authority through the operator/service path before trying
again.

QA is independent: it uses a separate actor credential and must review the exact
candidate snapshot. QA runs its own check and cannot accept when the candidate SHA
or workspace changes. Any changed candidate needs fresh QA. QA acceptance retires
the Worker; it is not Done. Only the Coordinator has integration authority to
reconcile target drift, make the expected-head non-force fast-forward delivery, run
postchecks, and record completion.

## Shared GitHub breaker

All operator GitHub work uses one journal-backed `core.Gate` and stable connection
alias across projects. Connection, authentication, rate-limit, and service failures
open the breaker. While open, remote operations pause. After cooldown, `Gate.acquire`
allows one half-open probe; a successful probe closes the breaker, while a qualifying
failure reopens it. Resource-specific failures are not breaker failures.

Do not bypass an open breaker through another CLI or transport. An uncertain remote
write must be reconciled by its authoritative read before retrying. The adapter's
Git push checks the expected remote head before push and in its pre-push hook, uses
no force option, and requires a fast-forward; historical issues are published only
after delivery or cancellation.

## Local verification

From the isolated checkout, run the supported local control suite:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

The check backend is intentionally restricted: on macOS it requires verified
`sandbox-exec` and denies network access, process forks, foreign reads, and foreign
writes. There is no unsandboxed fallback. `scripts/acceptance_preflight.py` checks
native service and skill prerequisites only; it does not establish real-agent
acceptance, remote delivery, or Done.
