---
name: foundry-audit
description: Independently verify a current AI.Contract candidate against its executable revision and evidence, using the assigned QA role. Also supports explicitly read-only repository or historical-outcome audits without service mutation.
---

# Foundry Audit

For native acceptance, read [QA](../foundry-qa/SKILL.md), the [native interface](../foundry-shared/skills/AI_CONTRACT_INTERFACE.md) and [operating rules](../foundry-shared/skills/OPERATING_RULES.md). Require Coordinator-assigned independent QA identity and the exact current revision/digest/attempt/candidate. Use an isolated exact-candidate snapshot; Worker self-review is forbidden.

Read the semantic contract version and full authoritative native body/policy. Inspect relevant source, complete diff, current-attempt review history and actual evidence; follow history and versioned read/diff continuation. Independently run the required checks. Reuse earlier evidence only when its actual source/configuration and scope match; structural validation or checked boxes are not behavioral proof.

Record `Accepted`, `Changes requested` or `Blocked` through `workflow_verdict` only with current binding and justified evidence. Accepted requires successful independent exact-candidate checks and remains distinct from Done. Corrections preserve the Worker/attempt and require a changed candidate plus renewed review. Material premise/scope problems return to Architect; no arbitrary retry count substitutes for that decision.

For an explicitly read-only system or historical issue audit, inspect source/specification/tests/delivery records and return findings without assigning yourself QA or writing a verdict. An issue is historical context, not the contract authority. Do not implement, publish or deploy from an audit-only request.

Report confirmed causes separately from hypotheses and verification limits. Include criterion results, source/candidate identity, actual stage and the evidence needed for the next authorized action.
