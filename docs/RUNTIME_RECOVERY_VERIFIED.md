# Verified runtime recovery and correction

Use this guide for the bounded local Hermes adapter. It describes recovery controls; it is not a deployment or an acceptance record.

## Authority and isolation

**AI.Contract** is the authority for the project, frozen revision and digest, current Worker attempt, candidate, QA verdict and integration evidence. The local runtime journal records launch and transport identities only; it does not create assignments or queue state. Before a write, check, submit, or recovery action, re-read the current assignment and reject a changed revision, attempt, owner, or expired lease.

Each attempt uses its own workspace and branch. The Worker capability permits only its assigned workspace; checks run under the macOS sandbox and deny network access, process forks, Git metadata writes, and reads or writes outside approved roots. The runtime starts Python in isolated mode and keeps trusted runtime imports outside the candidate workspace. Do not substitute an unsandboxed check or a shared writable checkout.

## Recover safely

If a launch identity is `unknown`, do not replace or signal it based on its PID. Recovery is blocked until the operator can establish whether the owned process group stopped. `stop` reports success only after it observes that group stopped. Lease expiry alone is not proof that the previous Worker has stopped.

A service outage fences Worker writes. A successful owning heartbeat first revalidates the assignment and then clears that fence. A stale assignment, revoked access, or expired lease is terminal for that invocation rather than something the Worker may renew by inference.

## Retry and history

A **retry** reuses the original durable submission intent. Submission records the intended parent, summary, workspace, checks, and later the exact candidate request. After an uncertain service response, revalidate current authority and retry that same intent; do not create another commit or change the summary. An existing candidate in QA is reconciled against its SHA instead of submitted again.

Read **history** as append-only evidence, not as a status guess. **Paging** continues until the service returns no continuation: later heartbeats and records can hide the latest QA verdict. Likewise, reconstruct a long file or diff with the returned offset and version. If the version changes between pages, restart at offset zero rather than combining different revisions.

## Shared GitHub breaker

The **breaker** is a single connection-scoped gate stored in one shared runtime journal for all affected projects. Connection, authentication, rate-limit, and service failures open it; ordinary resource errors remain local. While it is open, do not bypass it through another tool or client. Once the cooldown (including a server-provided rate-limit reset) has elapsed, only the coordinated half-open probe may test the connection. A successful probe closes the breaker; an uncertain or failed probe leaves remote work paused.

## Practical correction example

When QA requests a correction, the assigned Worker stays on the same attempt. First read every history page to find the current QA finding and its exact requested evidence. Make only the in-scope guide correction, run the supplied sandboxed check again, and submit the changed immutable candidate with a new concise summary. The submission path verifies that the checked workspace snapshot has not changed, commits once, and binds the service request to that candidate SHA. QA must then review the new exact candidate independently; QA acceptance still does not mark the contract Done.

### Disposable acceptance evidence

`CF-VALIDATED-9438790305684afea8c6e2b8b791b5aa` is disposable acceptance evidence requested by the staged correction fixture. It identifies the corrected guide for the fixture's marker check only; it is not a runtime control, a service record, or evidence of QA acceptance or delivery.
