# Codex reconnect and expiry acceptance

The Coordinator keeps lease maintenance separate from dispatch. An
unacknowledged or disconnected project subscription cannot trigger a new
reservation through a local wake-up. A targeted test enables the acknowledgement
only after verifying the local wake-up did not dispatch.

Recovery reads the current attempt before stopping any process, requires a
journal entry for the assigned Worker, and confirms all recorded process
groups have stopped. It rechecks the current attempt and expiry before the
native recover mutation. Targeted tests verify unknown or missing ownership
blocks recovery and a renewed lease prevents recovery.

The disposable acceptance used a real AI.Contract service, real process
groups and a bare Git remote, with scripted Codex role and history adapters.
Both original Worker leases expired while the runner was stopped. The new
runner adopted the two journaled processes, confirmed them stopped, and
persisted recovery before replacement attempts completed. The test also
verified a same-attempt correction, dependency ordering, all three delivered
files and final history linkage. No external repository was used.

The Python suite ran 141 tests with one skip. Diff checks passed.
