# Implement <WORK_TITLE>

Work contract: <WORK_RECORD_URL>
Idempotency key: <IDEMPOTENCY_KEY>

1. Re-read the current work record, specification, repository status, and remote baseline before editing.
2. Preserve unrelated checkout changes and use exactly one active writer for this shared checkout.
3. Implement only the accepted scope and run every required verification command.
4. Record changed paths, exact outcomes, disposable-fixture cleanup, and deferred work.
5. Push only with explicit authority. Verify local HEAD equals authenticated `<DEFAULT_BRANCH>` and fetched `origin/<DEFAULT_BRANCH>` before completion.
6. If a reproducible live probe proves this work contract is incompatible with its own premise, accepted scope/non-goals, or current specification, do not keep it blocked or expand scope. Record `[contract-invalidated:<fingerprint>]`, close the linked work record as `not_planned`, archive this execution card, and return control to a fresh audit. Only that audit may select a replacement.
7. Add and re-read the completion receipt before marking terminal.

Do not infer scheduler, credential, remote-write, deployment, or event-hook authority from this card.
