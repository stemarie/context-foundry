# Connection recovery and receipt acceptance — 2026-11-02

Contract `943c7fb6-ba43-4125-90fa-7cad65032dc8` delivered the repair at `1c84f62b3d04eba9d3a6082b1fcff584f8238e3d` (historical issue [#46](https://github.com/stemarie/context-foundry/issues/46)). The full 52-test host suite passed before and after its push. BEE1 proof passed EOF, direct and group SIGTERM, tunnel disconnect, and suspended owned-master EOF cleanup; the independent installed-code retest retained numeric ID `7002` and string ID `string-request-id`, and stopped the suspended master before removing its control directory. No BEE1 deployment or restart occurred.

A disposable local AI.Contract listener with unmodified installed Hermes Worker/QA previously proved descriptors persist through submit and verdict. That acceptance-only fixture was cancelled after confirmed role stops and deleted; it was neither Done nor a BEE1 delivery.

This BEE1 Worker/QA run records the same `checks.command` descriptor in live-service receipts: the selected argv, resolved cwd, `macos sandbox-exec` backend, and a deterministic identity over exactly those fields. This adapter-generated evidence is distinct from model prose and legacy receipts. It proves the fixed restricted check only, not host discovery; legacy evidence was clarified append-only, never backfilled.

Separate QA reviews the exact document candidate and records its own verdict. Before delivery, the Coordinator reads both live receipts, compares each descriptor to its selected launch command, and recomputes each identity; role workspaces may differ. QA acceptance is not Done. Boundaries remain a read-only global connection, service-wide role scopes with runtime binding, bounded operator invocation, no unattended controller, and no deployment.
