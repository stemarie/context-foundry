# Context Foundry audit-gap closure — 2026-11-01

All six confirmed audit defects are corrected. The additional local proofs passed with the actual installed Hermes runtime and the unchanged AI.Contract Docker service image. No deployment, persistent profile or scheduler was installed. AI.Contract remains at `d7748418a23e6ae8747bb0bed0730fc6c06f1fbf` without source changes.

Follow-up audit corrections and proof: [reset concurrency, transport quiescence and semantic version](FOLLOWUP_GAP_CLOSURE_2026-11-01.md). The six original reproductions remain historical evidence; the follow-up covers the later findings.

## Confirmed fixes

| Audit finding | Correction | Verification |
| --- | --- | --- |
| Candidate code imported before isolation | Native Python starts with `-I -B`; only explicit trusted Hermes/adapter roots are inserted before imports. Candidate cwd, user-site and PYTHONPATH cannot select the runtime. | Candidate `run_agent.py`, `json.py`, site customizations and a shadow adapter package cannot execute in the startup regression. Actual installed Hermes also initialized successfully with harmless shadow modules in its disposable workspace. |
| Submit retry attempted an empty second commit | An access-controlled transport journal prepares commit intent before committing and retains the immutable SHA, exact evidence and idempotency request before submission. Current service authority and verified workspace are rechecked. A successor can retry the original request without another commit; unknown local commit outcomes stay blocked. | Real local Git plus an unavailable-service regression: one candidate commit, identical request on retry, successful resubmission after reconstructing Tools. Existing native QA state is reconciled rather than resubmitted. |
| Old history page concealed current QA | Assignment follows native history continuation and returns the latest review for the current revision/attempt separately from its recent-event tail. An actor-bound history tool provides explicit continuation. | Regression with 150 events and a later stale-attempt verdict; actual correction proof exported over 150 canonical events and used same-attempt feedback after the first page. |
| Silent file/diff truncation | Read/diff return total characters, truncation, next_offset and a content version. Further pages reconstruct the whole result; mismatched versions reject mixed snapshots. | Full reconstruction of a file/diff beyond 64,000 characters and rejection of changed-version continuation. Models are instructed to follow continuation for a complete review. |
| Half-open probe stranded by local rejection | Every post-admission exit relinquishes its own still-held probe, reopening without falsely claiming network health. Dead-process ownership can be reconciled through the same shared state; live/unobservable owners cannot be stolen. | Local-rejection and cached-result race regressions, actual dead-owner successor recovery, live-owner exclusion, and the two-project shared-gate fixture. |
| Error substrings/reset timing misclassified | Response status/header metadata drives classification. A 404 request ID containing 401 stays a resource error; 403 permission denial stays local. Retry-After and rate-reset deadlines are honored, including debug output ending in a repeated CLI status. | Header/status regressions, combined timing hints and early automatic/operator probe rejection. |

The six new regression cases were unsatisfied against the audited source (four failures and two errors) before correction. The final host suite passes **22 tests**. Independent native QA ran **18 restricted checks** on the final candidate. Restricted checks use `-B` so interpreter cache writes do not change the candidate snapshot.

The journal's new submissions table is an outbox for a specific attempted service request. It stores no bearer/provider credential, assigns no work, chooses no stage, and never overrides AI.Contract. Current assignments, revisions, candidates and lifecycle remain service-owned.

## Actual local proof

The existing `scripts/real_agent_acceptance.py` adds a `correction` scenario and a disposable Docker fixture. It performs real model calls and authorized main delivery; it is not a mock execution receipt. `--docker-image` pins the inspected image ID, uses a unique labelled Linux-native volume, runs service/token containers as `65532:65532` and exposes only an ephemeral loopback port.

A real Worker first submitted an explicitly authorized draft guide. The service container was removed and replaced by a different container from the identical image using the same volume and listener. The candidate, attempt, authenticated credentials and earlier history survived. HTTP and MCP both read back the persisted native state/history. The live Worker fenced actions during the outage, then revalidated its actual ownership and renewed its lease before resuming on the same PID/attempt.

After replacement, a new nonsecret verification marker was recorded in native evidence. Independent QA inspected the exact draft, ran the marker check and requested changes. The same Worker read current feedback beyond the first history page, changed the guide and submitted a new candidate on the same attempt. A fresh QA invocation independently checked and accepted that candidate. The Coordinator verified expected-head non-force delivery, remote SHA equality and postchecks before native Done and historical publication. Earlier draft candidates were not delivered as accepted results.

The first completed correction/replacement run delivered [`4e60911`](https://github.com/stemarie/context-foundry/commit/4e60911a53e0e0e1e6978642f16182f501a9b385), native contract `67728c04-7ee2-444d-92d5-57697bb3aa22`, closed [history #37](https://github.com/stemarie/context-foundry/issues/37). The final run adds explicit HTTP/MCP readback and delivered [`95bfff0`](https://github.com/stemarie/context-foundry/commit/95bfff07e2a2ae12f5517da213e30f436e15f258), contract `134459c2-e725-42b1-bc02-4d03428940a9`, closed [history #38](https://github.com/stemarie/context-foundry/issues/38). Project `68cd46bf-5b0f-40b6-a06a-1402116678f2`, milestone `531f8aa0-f8d7-4640-aca6-e9d45dfee942` and attempt `c3c85737-0d1e-4d36-a8ce-396dacc60acb` remained service-owned; Worker PID 33383 stayed the same. All 172 canonical events, candidate/container/image identities and publication references are retained in the [safe evidence](evidence/hermes-gap-closure-2026-11-01.json).

Actual service image: `sha256:7eaeb5cb9aa8daf87fac8a27af61bf65b71a88c72ba17dfe3be1d78304876dfa`, built from unchanged AI.Contract source with the existing non-root Dockerfile. Installed Hermes source: `bf0203a794a07aac3ff764972ab9087baa4e4f4e`; existing prepared provider/model route retained. Operator Architect/Coordinator actions and actual model Worker/QA actions remain explicitly distinct.

The new image-replacement proof supplements the earlier ordinary/serial Docker and Hermes-client proofs; their scopes and history remain unchanged. The earlier [real-agent acceptance](HERMES_ACCEPTANCE_2026-11-01.md) remains historical evidence, with this report superseding its identified implementation gaps.

## Outage diagnosis and recovery

During the controlled six-second local outage, actual Worker diagnostics reported `ServiceUnavailable` with `connection_refused`, then recorded `authority_recovered` after successful current-binding validation and heartbeat. Unit tests also verify timeout/reset classification and exclusion of raw exception details. No expired lease is renewed by inference: stale, expired or revoked authority remains fenced and requires stopped-execution recovery.

The initiating cause of the older unclassified heartbeat fence cannot be recovered from its retained record. It remains explicitly unknown. This work closes the current diagnostic/controlled-recovery coverage gap and does not relabel that historical event as diagnosed or passing.

## Cleanup and remaining boundaries

Canonical native history is paginated to completion and exported before fixture database/volume deletion. Evidence excludes private provider logs and credentials. Owned native executions, worktrees, homes, service containers and volumes are removed. The task-only Docker engine/cache are removed separately; existing default/review engines and active configuration are preserved.

The accepted backend remains bounded local macOS execution with restricted checks and the approved repository target. Additional platforms, unrestricted builds, unattended operation, native delegation and production/public deployment require separate scope and proof. AI Kernel admission remains a separate decision. No queue, process supervision, Git execution or connection breaker was added to AI.Contract.
