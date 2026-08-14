---
name: context-foundry-synthesis
description: Synthesize verified profile and skill evidence without overclaiming.
version: 0.1.0
source: Context Foundry v0.1.0
adapted_for: foundry-architect
---

# Context Foundry Synthesis

## When to use
Use after bounded Worker evidence and an independent Auditor verdict exist. Do not use while required audit evidence is absent, or to replace an Auditor verdict.

## Contract
Produce a concise decision record that separates verified facts, implementation status, recommendations, limitations, and next decisions. It does not activate runtime behavior or silently widen scope.

## Procedure
1. Read the brief, Worker evidence, changed-file list, validation output, and independent audit.
2. State only facts supported by cited evidence and the audit outcome.
3. Distinguish completed source-controlled artifacts from future proposals or runtime behavior.
4. Record limitations, rejected scope, and any remaining decision in plain language.
5. Link the record to the exact commit or release only after authenticated remote read-back.

## Output format
```markdown
## Synthesis
- Verified outcome:
- Evidence and audit:
- Delivered reusable artifacts:
- Explicit non-deliveries:
- Limitations / decisions:
- Delivery handle:
```

## Pitfalls
- Do not label a local commit, profile sync, or issue closure as a release without remote proof.
- Do not collapse an Auditor `REQUEST_CHANGES` or `BLOCKED_WITH_EVIDENCE` into success.
- Do not convert recommendations into active profiles, cron jobs, or gateways.

## Verification
Every material conclusion points to evidence and audit state, and every delivery claim has an authenticated commit, tag, or release read-back.