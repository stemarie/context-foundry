# Command admission and integration recovery — 2026-11-01

The two confirmed findings against Context Foundry `2477097` are corrected. AI.Contract remains unchanged at `d7748418a23e6ae8747bb0bed0730fc6c06f1fbf`. All proof resources are disposable local state. No deployment, persistent profile or scheduler was installed.

## Demonstrated causes and corrections

| Finding | Correction | Verification |
| --- | --- | --- |
| A compound callback could start a later command after another caller opened the breaker | Every command validates the invocation's admission against the current shared connection state, generation and probe owner in the same transaction that records transport intent. A trip invalidates prior grants, including after later successful recovery. Already admitted commands remain in-flight evidence; a callback cannot use its old grant for a later command. | The original two-command interleaving failed before correction. It now fences the second command and preserves the unresolved operation identity. A separate recovery test rejects the old grant even after the connection closes again; a fresh operation succeeds. Valid half-open owners can finish legitimate compound operations. |
| Controller death released the target lock while its transport survived | After obtaining the target lock, integration checks every recorded transport group across connection aliases in the shared journal before admitting ownership. A live group, unknown start or unobservable identity remains blocked. Stopped groups are reconciled under that lock. | Kill a real controller inside the integration wrapper while its harmless tracked command survives. Reacquisition rejects both same-alias and different-alias callers. After the owned command stops, integration succeeds and the uncertain remote operation remains unresolved rather than being repeated. |

The two new primary regressions were run first against the audited source: **both failed**. The final host suite passes **36 tests**, including the prior six-gap and three-follow-up controls. The previously manual timeout checks are now automated actual-process proofs with a controlled shorter wait: a running transport is stopped and cleared, while an exited leader's surviving descendant stays fenced until explicit stop. Those tests exposed unclosed private stdout/stderr pipes in the exited-leader timeout branch. A `finally` closes both pipes without clearing the live-group barrier. The final suite also passes with ResourceWarning promoted to an error.

No contract state, assignment, queue, actor capacity or lifecycle authority was added to Context Foundry. The additional generation is connection-health metadata in its local process/transport journal. AI.Contract remains authoritative.

## Final-source installed-Hermes proof

`scripts/native_version_acceptance.py` launches the actual installed Hermes AIAgent through the trusted isolated wrapper with the existing prepared provider/model route. A fresh disposable service project supplies separate scoped Worker and QA credentials. Each invocation uses a separate home, scratch directory, branch and worktree. No remote Git capability is exposed.

The native executable body differs from the original ordinary body and contains a unique marker. The real Worker reads its current assignment, writes only a disposable fixture containing the checked semantic version and native marker, runs the restricted check and submits an actual local candidate. A separate QA invocation inspects that exact candidate and independently checks it before recording Accepted. Both processes retire and are confirmed stopped. Coordinator cancellation then terminates the disposable service job; it is never integrated, marked Done or published as delivered work.

The final [safe evidence](evidence/command-admission-proofs-2026-11-01.json) retains runtime SHA-256 fingerprints, real model/tool events, exact native revision/attempt/candidate bindings, complete paginated service history, fixture output and cleanup. A first smoke passed before the timeout pipe correction; it retains its own earlier fingerprints and is not substituted for the repeated final-source run.

Final run: native contract `c15485f7-f4a6-4be5-8e55-9896e42f2e26`, attempt `bb056778-1ebd-4cbe-a879-965bb6322064`, local fixture candidate `1284b9bb7f7040628875d78b579a1e416d1cd572`. Its 41 canonical events include independent QA acceptance followed by stopped-confirmed cancellation. Both model invocations ran on the archived final runtime fingerprints; all owned resources were removed.

This closes the current-version model/prompt verification gap left by the [three-fix follow-up](FOLLOWUP_GAP_CLOSURE_2026-11-01.md). That follow-up's real-service version proof remains separate. The older [six-gap/Docker correction proof](HERMES_GAP_CLOSURE_2026-11-01.md) and [real-agent delivery acceptance](HERMES_ACCEPTANCE_2026-11-01.md) keep their original scope and source identities. No new Docker replacement or production claim is made; the older unknown heartbeat trigger remains unknown.

## Reproduction and delivery

Run the 36 host controls with `PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -W error::ResourceWarning -m unittest discover -s tests -v`. The native runner requires explicit AI.Contract checkout/binary, installed Hermes source/interpreter and a private report destination. It makes real model calls and local fixture commits, but performs no remote repository mutation.

Repository delivery follows AGENTS.md: shared transport gate and target lock, expected-head/non-force direct-main update, remote SHA equality, postchecks and historical issue only after outcome. Specification §11B receives immutable links to the three-fix follow-up and this proof; older service/Docker/real-agent evidence retains its stated bounds.

Owned native processes, homes, worktrees, branches, service database and local credentials are removed after full history export. Safe reports remain. Uncertain remote writes continue to require authoritative reconciliation. Additional backends, unrestricted builds, unattended operation, AI Kernel admission and production remain separate scope.
