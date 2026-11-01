# Local real-agent acceptance — 2026-11-01

Passed for the bounded, operator-invoked macOS backend. This was an actual installed-Hermes Worker/QA run with real repository delivery, not a substitution of the service mock receipts. No production deployment, persistent role profile, recurring scheduler or active Hermes configuration change was made.

## Scope and versions

- Approved repository: `stemarie/context-foundry`, direct non-force delivery to `main` under AGENTS.md. AI.Contract source was unchanged.
- AI.Contract source/binary: `d7748418a23e6ae8747bb0bed0730fc6c06f1fbf`.
- Installed Hermes source: `bf0203a794a07aac3ff764972ab9087baa4e4f4e`.
- Parallel-run bootstrap: `e1164bc98c819656bae06f54084cf4bdb3d10885`. Final source/documentation run bootstrap: `2268491c204a5ebdc969c82803bcf6992d63a5e8`. Per-phase and final runtime file hashes are in the evidence artifact.
- Actual provider/model: existing `openai-codex` / `codex_responses` route, `gpt-5.6-terra`. Credential values were passed privately, excluded from contracts, journals and public evidence.
- Backend: separate installed `AIAgent` processes, native homes, branches and worktrees; role-bound HTTP clients; macOS kernel sandbox for fixed local checks. Native MCP and all four skill discovery were separately exercised from installed Hermes.
- Architect/Coordinator actions were bounded operator invocations of the documented roles. Worker and independent QA implementation/review turns used actual Hermes model calls. No native `delegate_task` backend or unattended daemon is claimed.

Human scope covered runtime prerequisites and acceptance/operator documentation. The initial runtime bootstrap was written directly by the operator under explicit user authorization, then included in independent candidate QA. It did not pretend to execute its own missing bootstrap.

## Actual outcomes

| Run | Native contract | Delivered commit | Historical record |
| --- | --- | --- | --- |
| First complete contract | `f90b4d53-3d53-4c4c-a37b-7f79bc2e01c4` | [`380c053`](https://github.com/stemarie/context-foundry/commit/380c053e0293b7eeb58da837d433df6518efff30) | Included in final task history; initial fixture archived before publication |
| Parallel recovery guide | `5a287dd2-ad08-402a-b29b-ea2e76ced3eb` | [`20afe9b`](https://github.com/stemarie/context-foundry/commit/20afe9b6e50b9c26e84092dc48ac6453c02b7f55) | [Closed #33](https://github.com/stemarie/context-foundry/issues/33) |
| Parallel isolation guide, renewed after drift | `6cbf5f3a-0300-4d4a-8306-9ece804096d6` | [`8e15773`](https://github.com/stemarie/context-foundry/commit/8e15773b48a8802e208b18dded6f1af4595b5fae) | [Closed #34](https://github.com/stemarie/context-foundry/issues/34) |
| Final runtime/quickstart verification | `57e123fc-c558-434c-8813-2c251dfb8f88` | [`2fdca76`](https://github.com/stemarie/context-foundry/commit/2fdca761dd7a7f255d2641c564405c456d26e985) | [Closed #35](https://github.com/stemarie/context-foundry/issues/35) |

The final parallel project was `54459d07-b24e-4f43-bae5-7e00a799a5e0`, milestone `9cac8821-0429-4e79-8ddd-dde905a69abd`, planning horizon 1, queue target 2. Actors were `acceptance-worker-one`, `acceptance-worker-two`, and independent `acceptance-qa`, each with its own scoped client. The service assigned separate immutable attempts and the actual model intervals overlapped for **27.924 seconds**. Runtime event timestamps, handles, candidate/target identities and all exported service events are in the [safe history artifact](evidence/hermes-acceptance-2026-11-01.json).

Both original candidates received independent QA. Integrating one prevented a simultaneous second native integration. After the first target advance, the second accepted execution was confirmed stopped, recovered through the native service, reserved with a new attempt on current main, implemented again, and independently reviewed again. Its prior accepted candidate and evidence remain in history. No candidate was rebased or silently substituted under old QA.

Each final delivery used an expected-head check, a pre-push check of Git's advertised target head, a fast-forward push without force, remote SHA read-back and actual post-integration checks before native Done. A deliberate failing postcheck exited 1: its evidence was recorded, completion with `checks_passed=false` was rejected, and the job remained Integrating until the required checks actually passed.

## Verification matrix

| Requirement | Executed evidence and classification |
| --- | --- |
| Service baseline and persisted workflow | AI.Contract real-server mock and workflow clients over HTTP/MCP, including restart. Their synthetic Worker/Git attestations remain labelled mock; prior Docker/service-image and Hermes-client proofs remain valid and separate. |
| Native client and skills | Installed Hermes discovered required workflow tools, authenticated role reads and all four unshadowed skills/shared references. Prohibited Coordinator calls were rejected for Worker/QA credentials. |
| Real launch/replay/restart | Actual installed AIAgent processes; repeated launch reconciled the same identity. In the final recovery proof the original launcher was a separate process that exited; a successor with no original Popen handle reconciled the surviving Worker without spawning a replacement. Inspect/stop used PID, start identity, nonce and process-group quiescence. |
| Isolation | Distinct actors, clients, homes, worktrees and branches. Native advertised and dispatch registries exposed only the role-bound `foundry_action`. No terminal, delegation, raw remote transport or Coordinator/admin tool was exposed. |
| Kernel check restrictions | Actual successful local check plus explicit PermissionError for network, fork, another actor's fixture secret and Git metadata writes. A separate two-project proof denied a raw socket connection to a known live service. |
| Independent QA/corrections | Actual QA read exact-candidate diffs and relevant source, independently ran checks and wrote native verdicts. An early scope mismatch produced a real Changes requested verdict. QA acceptance remained distinct from Done. |
| Capacity and eligibility | Actual two-Worker busy-pool wait. Existing authoritative Go workflow tests passed for eligible FIFO, multiple prerequisites, conflicts, dependency rejection, concurrent reservations, revisions and controlled recovery. These service tests are not described as model execution. |
| Expiry and stale authority | Actual initialized Hermes Worker alive at its start barrier; lease expired, actor stayed busy, old writes were fenced. Recovery without stop proof was rejected. Actual stop preceded recovery/new attempt. Old bindings stayed fenced. |
| Immutable revision | Recovery fixture created a new digest/revision, preserved the old history and required renewed Draft → Ready before a new reservation. Final real QA separately rejected stale revision, attempt and candidate bindings; Worker self-QA was forbidden. |
| Target drift and completion | Actual fresh attempt/QA after main advanced; serialized integration; failed postcheck kept unresolved; remote read-back and successful checks before Done. |
| Shared GitHub breaker | Two actual disposable AI.Contract projects on separate service fixtures used one shared journal/connection alias. Simulated rate/connection failures paused both, local Git continued, competing probes admitted exactly one, a failed probe reopened and operator recovery used the same state. Resource errors stayed local. No live outage was induced. |
| Uncertain writes | Simulated successful issue creation with lost response reconciled once; explicit lost Git push response regression reconciled the authoritative SHA without another push. Real historical issue #32 was recovered after a search/read-back delay, without duplication. |
| History and cleanup | Safe canonical service event/revision/candidate exports retained; adapter-owned processes stopped, native homes/databases and owned worktrees removed. A capacity failure's interrupted history was recovered through the service API before deleting its fixture. |

The [two-project breaker evidence](evidence/breaker-acceptance-2026-11-01.json) explicitly distinguishes actual local projects/gate/kernel enforcement from simulated GitHub failures and clock advancement. The local regression suite passes **12 tests**, including report-capacity preservation and unknown-push reconciliation. Parallel candidate QA ran the then-current **9 pure tests**; final source/quickstart QA independently ran **11 pure tests**. The host suite additionally exercised the actual sandbox. The final native history records launch handle/PID, branch, workspace and base; the Worker receipt records its actual branch and candidate.

## Confirmed causes fixed

1. Hermes rejects `plugins.enabled: false`; isolated configuration now uses its supported empty-list schema. Native profile-scoped inherited tools are removed as well as global registrations, with a fail-closed registry assertion.
2. Hermes bootstrap may re-exec and replace the module path. The native import now precedes private stdin consumption/acknowledgement and restores the adapter path after bootstrap.
3. A model iteration limit after successful native submission previously retired the Worker. The runtime now reconciles the recorded transition and retains the Worker/heartbeat through QA and corrections within its bounded invocation.
4. Python 3.9 rejects some variable RFC3339Nano fractional lengths. Service timestamps are normalized, with one-through-nine-digit regression cases.
5. Service submission can precede the model's final return. The overlap proof waits for actual model completion events before calculating its intervals.
6. Immediate issue search can miss a successful creation. A returned URL is verified directly; uncertain responses use durable operation identity and authoritative reconciliation before any repeat.
7. Per-home automatic dependency provisioning filled disk during a later QA run. The adapter now uses the supported no-lazy-install mode with the prepared virtualenv. Actual concurrent fixtures used about 3 MB rather than about 2 GB. Reporting is atomic; failures stop the service and retain unresolved private canonical state instead of deleting history or falsely claiming cleanup.
8. Fixed checks could modify the workspace's Git metadata. The actual escape was reproduced on a harmless fixture, denied by the kernel profile, and retested with explicit permission-denial assertions.
9. The newly added lost-push test used a global temporary hook directory outside the restricted check capability. Its PermissionError was reproduced directly. Hook/issue temporary files now use the owned journal directory. All 11 scoped checks and the original real Worker/QA delivery flow then passed.

One additional trial logged a heartbeat authority fence before detailed service-code diagnostics were added; its initiating trigger is unestablished. It produced no candidate or delivery and is not counted as a pass. That trial and the subsequent confirmed scoped-test failure remain in the exported history. The final successful flow is recorded separately; no root cause for the earlier unclassified fence is claimed.

## Reproduction and boundaries

Run `python3 -m unittest discover -s tests -v` with bytecode disabled and `TMPDIR=/private/tmp`. The parameterized runners are `scripts/acceptance_preflight.py`, `scripts/real_agent_acceptance.py` (`single`, `parallel`, `recovery`) and `scripts/breaker_acceptance.py`. Supply explicit checkout, compiled service, prepared Hermes interpreter/source and report paths. Single/parallel scenarios perform real authorized `main` delivery; they are not dry runs.

The verified adapter is restricted to this host/backend and approved delivery target. Arbitrary builds requiring child processes/network, other operating systems, native delegation, unattended scheduling, live production outage recovery and production deployment require separate authorization/setup and backend verification. An abandoned half-open probe or unknown execution stays blocked for operator reconciliation; there is no automatic unsafe reset.

AI.Contract continues to own service/schema/API/storage, projects, revisions, assignments and execution evidence. Context Foundry owns role skills, runtime processes, isolated workspaces, integration orchestration and connection health. Its journal holds process/transport reconciliation only; it is not another work queue. Ordinary contracts, serial chains, existing Docker/Hermes client proofs and their semantics were preserved.
