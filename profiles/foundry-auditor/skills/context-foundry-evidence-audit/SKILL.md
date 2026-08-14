---
name: context-foundry-evidence-audit
description: Independently audit bounded profile and skill evidence.
version: 0.1.0
source: Context Foundry v0.1.0
adapted_for: foundry-auditor
---

# Context Foundry Evidence Audit

## When to use
Use after a Worker supplies bounded evidence for a profile/skill change. Do not use to edit the implementation, to create missing evidence, or to approve runtime automation.

## Contract
Independently verify scope, citations, changed artifacts, and reported command outcomes. Return `PASS`, `REQUEST_CHANGES`, or `BLOCKED_WITH_EVIDENCE` with concrete findings; never remediate the work under review.

## Procedure
1. Read the brief, source map, Worker evidence, changed-file list, and required checks.
2. Verify every material claim against its cited source or reproducible repository state.
3. Confirm changed files stay within profile/skill, synchronization, documentation, and test scope.
4. Re-run safe deterministic checks independently where audit authority permits.
5. Check that no credentials, runtime state, schedules, gateway activation, or external behavior was introduced.
6. Return a verdict and bounded requirements for any correction; do not change files yourself.

## Output format
```markdown
## Independent evidence audit
- Verdict: PASS | REQUEST_CHANGES | BLOCKED_WITH_EVIDENCE
- Scope findings:
- Citation findings:
- Reproducibility checks:
- Delivery evidence:
- Required corrections / blocker:
```

## Pitfalls
- A Worker test log is evidence to verify, not proof by itself.
- Do not replace a missing citation with an inference.
- Do not repair an implementation and then audit it as independent work.
- Do not approve a profile/skill change that secretly adds orchestration runtime behavior.

## Verification
A `PASS` requires evidence-backed scope compliance, reproducible required checks, and no unresolved material discrepancy.