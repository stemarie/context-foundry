---
name: context-foundry-evidence
description: Produce cited, bounded evidence for profile and skill changes.
version: 0.1.0
source: Context Foundry v0.1.0
adapted_for: foundry-worker
---

# Context Foundry Evidence

## When to use
Use for a bounded implementation or analysis packet that must return cited facts, changed artifacts, and real command outcomes. Do not use to self-approve an implementation or to infer unobserved remote state.

## Contract
Return evidence that lets an independent Auditor verify what changed, why it was authorized, and which deterministic checks actually passed. A local edit, planned retry, or card state is never delivery evidence.

## Procedure
1. Re-read the bounded brief, accepted sources, allowed paths, and acceptance criteria before changing anything.
2. Record factual observations with source locations; label interpretations and recommendations separately.
3. Make only the authorized profile/skill, documentation, or test changes.
4. Run the required deterministic checks and retain the exact outcome categories.
5. Record changed paths, test commands, exclusions, and unresolved limitations.
6. If evidence conflicts with a premise, stop and report the narrow discrepancy; do not expand scope or rewrite the contract.

## Output format
```markdown
## Worker evidence
- Scope checked:
- Changed paths:
- Facts and citations:
- Tests and outcomes:
- Delivery/read-back evidence:
- Exclusions and limitations:
```

## Pitfalls
- Do not fabricate citations, test results, SHA equality, or remote delivery.
- Do not turn a profile/skill change into runtime automation.
- Do not add credentials, runtime configuration, sessions, caches, or logs to source control.
- Do not self-audit; request independent verification.

## Verification
Evidence identifies every changed file, differentiates observed facts from recommendations, and includes reproducible validation outputs.