# Bounded coding candidate acceptance — 2026-11-02

## Source and prerequisite

This candidate implements AI.Contract contract `d82dc103-9d99-4c6d-8710-6e642ab3dcc7`,
revision 3 (`54bd0e50b836bc8654ba9fd738b9a1dfc154d41b0f8a3b7d289c478202e32aa2`),
on the Coordinator-recorded prerequisite baseline
`a5335ef2ac53f2bcaed1f36d80c3790a1eab0106`. Its prerequisite contract is
`a46f041c-b7dc-43bc-9b82-4d7407e9ca14`.

## Candidate proof criteria

The stock bounded Worker changes the existing shared-gate, journal and GitHub
operator implementation. It adds an explicit operator-only recovery path for a
started `close:<url>` whose first close is known not to have applied. The path
preserves that identity, appends linked recovery evidence, requires an explicit
attestation, validates issue identity, complete paginated event history and
stable snapshots with valid timestamp tokens, and blocks close/reopen,
concurrent, malformed, incomplete or unverifiable evidence. A durable logical
operation owner covers both the original callback and recovery, preventing two
recoveries or a paused original callback from issuing duplicate closes. Default
`close_history` remains fail-closed.

The recovery uses the existing Gate current admission for every remote command,
requires all connection transport groups to be quiescent before proof and retry,
and rechecks admission and authoritative state before writing. Complete slurped
zero-event pagination (`[[]]`) is distinguished from an absent outer page list
and recovers exactly once. New aliases start with durable transport tracking;
every unconfirmed legacy alias, including a CLOSED `transport_tracking=0` row,
remains fenced until an operator explicitly confirms quiescence with
`Gate.confirm_legacy_quiescence(evidence, confirmed_stopped=True)`, which
preserves breaker metadata and records confirmation evidence. A foreign legacy
half-open alias blocks proof before any GitHub read or retry. It retains normal
cooldown, probe and generation fences. The accompanying disposable regression
coverage simulates a lost first resource response with no application, proves
explicit retry and idempotence, retains the default block, and blocks close/reopen
history and unknown transport tracking. Tests use mocked transport only; they do
not call GitHub or modify an operator journal.

The Worker records actual selected test output in its candidate receipt. A
separate QA actor must inspect the complete candidate diff and relevant code,
then independently run selected pure regressions. Candidate acceptance is not
main delivery, post-integration verification, native `Done`, runtime
installation, GitHub historical publication, or deployment. Those later facts
belong to the Coordinator's final native receipt.

## Limits

The conservative absence proof currently permits only issues with no close or
reopen events. A missing or malformed event page fails closed. Host-only BEE1
bridge/SSH proofs, full-suite execution, expected-head delivery, remote equality,
postchecks, installation, and cleanup are operator/Coordinator actions and are
not asserted by this pre-submission candidate document. No deployment.
