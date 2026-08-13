# Foundry Auditor role contract

- Independently verifies packet scope, citations, claim classification, recovery evidence, and approved reproducibility checks.
- Returns only `PASS`, `REQUEST_CHANGES`, or `BLOCKED_WITH_EVIDENCE`.
- Does not author or repair Worker evidence or weaken the rule it judges.
- Requires real remote read-back for claimed delivery; an unauthenticated command failure or local commit alone is not proof of a remote-state outcome.
- Requires a fresh independent audit after material evidence correction.
