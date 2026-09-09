# Brainiac reliability-learning activation

`python3 scripts/brainiac_learning.py` is a deterministic state machine, not a runtime service. It evaluates one newly available durable structured incident event at a time, normalizes its fingerprint, records its decision in an operator-selected SQLite database outside this checkout, and emits a durable Astra-invocation record only for a high-severity event or the second same fingerprint within the preceding 30 days. A repeated event ID is a no-op. No LLM, gateway, hook, scheduler, cron job, service, monitor, card, GitHub action, or source mutation is started by this command.

The weekly command records one synthesis request for a changed evidence revision and explicit ISO week. Repeating that revision/window is a no-op. It does not poll.

## Operator-controlled procedure

Only after an independent Candidate Auditor PASS for the candidate may an authorized operator separately install or activate an event hook or weekly scheduler. The operator must select a state path outside the source checkout and provide only structured non-secret incident evidence. Example dry local evaluation:

    python3 scripts/brainiac_learning.py --state /var/lib/context-foundry/brainiac.sqlite incident --input /secure/evidence/incident.json
    python3 scripts/brainiac_learning.py --state /var/lib/context-foundry/brainiac.sqlite synthesis --evidence-revision <revision> --window 2026-W01 --observed-at 2026-01-05T00:00:00Z

The installed integration, if separately authorized, may invoke Astra only when `astra_invoked` or `synthesis_required` is true. It must write no credentials, tokens, sessions, logs, caches, generated state, or source checkout into repository-controlled paths. Brainiac's output is a proposal for Architect consideration, never authorization for a change.

## Profile synchronization

`profiles/foundry-brainiac/` is canonical declarative profile material. `python3 scripts/sync_foundry_profiles.py --apply` copies only managed non-secret profile assets; it does not activate Brainiac or create/start a gateway, event hook, scheduler, cron entry, service, monitor, or dispatcher.
