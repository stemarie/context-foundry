# Skill review scenarios

These are static instruction walkthroughs for version 0.1, not executed agent or service tests.

| Scenario | Expected instruction path |
| --- | --- |
| Service has only legacy serial chains where PASS sets Done | Capability check blocks live workflow; no fake status mapping or premature dependency unlock. |
| Architect lacks project authoring extensions | Can return a clearly marked preparation draft; cannot claim persisted Ready work. |
| Two coordinators see the same ready contract | Require atomic service reservation/exclusion; read-then-update and issue comments are rejected substitutes. |
| Oldest Ready order has incomplete prerequisites or active conflict | Coordinator uses eligible FIFO and skips it; independent work can proceed. |
| All Workers busy | Coordinator waits; no implicit pool expansion. Worker remains assigned through correction. |
| Worker assignment expired | Worker stops writes; Coordinator confirms termination before reassignment. No automatic competing attempt. |
| Candidate or material contract revision changes during QA | Recheck bindings and require fresh assessment; old acceptance is not transferred. |
| Worker asks QA to fix then accept implementation | QA returns defects; implementation remains Worker responsibility. |
| Post-integration verification fails | Coordinator does not mark Done or unlock dependants; records actual result and follows authorized recovery. |
| GitHub connection fails | Shared breaker halts GitHub access; local work can continue; no alternate CLI bypass. |
| Issue creation times out after delivery | Preserve pending history; reconcile remote result before retrying. |
| Runtime cannot launch or stop agents | Coordinator reports missing capability and checkpoint, not a fictional running system. |

Review method: check each row against the four skills, shared rules, and work contract; inspect relative links and skill metadata. Actual confidence in behavior requires a connected service and runtime demonstrations.
