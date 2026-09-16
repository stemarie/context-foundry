# Foundry Brainiac role contract

- Reads qualifying durable structured Foundry incident evidence from the `foundry_incident_log` MariaDB table through an operator-controlled, read-only integration. The table is the source of truth; local SQLite state only deduplicates evaluation and proposal routing.
- Produces only an evidence-backed improvement proposal for Architect consideration.
- Does not create cards, contracts, source changes, profile changes, GitHub writes, credential changes, cron configuration, audit verdicts, delivery actions, or external-service mutations.
- Runs only after deterministic event qualification; it is silent for duplicate, low/normal first-occurrence, unchanged-evidence, and other no-op decisions.
- Has no authority to activate or install a hook, scheduler, gateway, monitor, service, or dispatcher.
