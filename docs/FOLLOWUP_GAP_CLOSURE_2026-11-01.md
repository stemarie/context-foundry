# Follow-up audit-gap closure — 2026-11-01

The three findings against Context Foundry `37697f9` are corrected. AI.Contract remains unchanged at `d7748418a23e6ae8747bb0bed0730fc6c06f1fbf`. This follow-up uses disposable local fixtures and read-only remote queries during verification. No deployment, persistent profile or scheduler was installed.

## Confirmed causes and fixes

| Finding | Demonstrated cause and correction | Proof |
| --- | --- | --- |
| Late failure shortened reset deadline | Two admitted requests could finish with a rate reset followed by a connection failure. `server_until` survived, but automatic admission used the shortened `until`. Outcomes now preserve the longest existing cooldown/server deadline. | Two admitted requests, reset at 4600, late failure at 1001: automatic and operator probes reject at 1062 and 4599; recovery at 4600 succeeds. |
| Dead controller left transport alive | Probe ownership recorded only the controller PID. Actual command children could outlive it. Remote commands now persist a non-secret transport intent and acknowledge their new process group before exec. Recovery checks group absence, including surviving descendants. | Actual `Gate.run` and command wrapper with a harmless local sleeping transport: kill controller, reject successor probe while child lives, stop child, then recover. A separate exited-leader/live-descendant fixture remains blocked. |
| Native consumer omitted semantic version | Workflow responses contain native revision/digest but no ordinary `contract_version`; the adapter never read it. It now reads the existing ordinary GET API before authority/launch/actions and accepts only Alpha 1.0. The checked version is supplied with the native executable body. | Supported/missing/unknown response tests; unknown version refuses launch before an intent or process exists. Actual scoped Worker/QA clients read Alpha 1.0 from a disposable real service while preserving the different native body. |

The original three regressions ran before implementation: **two failures and one error**. All pass after correction. The complete host suite now passes **30 tests**. Additional controls cover unknown transport starts and legacy probe records: neither can manufacture proof of quiescence. A known failed OS spawn may remove only its own unacknowledged intent. Process-group or permission uncertainty stays blocked rather than signalling an unrelated process. A missing executable releases the probe without claiming connection health. Timeout handling stops a still-owned group and requires confirmed quiescence; it does not interpret an exited leader as safe to signal.

Only process/transport identities and health metadata were added to Context Foundry's private journal. No bearer/provider credential, command payload or remote response is retained there. The journal remains transport reconciliation, not a queue or authoritative contract store. Recovering a connection does not repeat an uncertain write; its operation identity still requires authoritative reconciliation.

## Executed evidence and limits

- The 30-test suite includes actual process loss, surviving transport/descendant exclusion, recovery after stop, prior startup isolation, durable submit retry, paginated QA feedback, content continuation, sandbox denial and uncertain-write controls.
- `scripts/followup_acceptance.py` uses the unchanged service binary with a separate local root, fresh role-scoped credentials and a real local fixture commit. Worker and assigned QA authority reads succeed. Native history is exported before cleanup. This is a real-service transport/authority proof, **not** another model execution, independent QA verdict, Docker replacement or native Done claim.
- A real GitHub head read exercised the tracked command path, returned the expected `37697f9` baseline and left zero outstanding transport records. Delivery uses this same shared journal/alias, expected-head checking, non-force push and remote SHA verification under AGENTS.md.
- The [safe proof artifact](evidence/followup-gap-closure-2026-11-01.json) contains runtime hashes, fail-first/final results, actual service history and cleanup evidence. Test commands and process fixtures are reproducible from `tests/test_followup_regressions.py`.

The earlier [six-gap and actual-image correction/recovery proof](HERMES_GAP_CLOSURE_2026-11-01.md), [real-agent acceptance](HERMES_ACCEPTANCE_2026-11-01.md) and AI.Contract ordinary/serial Docker/Hermes proofs retain their original scope and historical source identities. They were not rerun or relabelled as executions of this follow-up source. The earlier unknown heartbeat trigger remains unknown.

All owned fixture processes and temporary service/SQLite/credential/candidate state were removed. AI.Contract continues to own projects, contracts, revisions, assignments, evidence and lifecycle. Context Foundry owns processes, workspaces, verification/Git and shared external connection health. Additional backends, unrestricted builds, unattended operation, AI Kernel admission and production remain separate scope.
