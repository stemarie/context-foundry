---
name: foundry-audit
description: Review an assigned AI.Contract candidate through independent native QA, or perform an explicitly read-only repository, skill or historical-outcome audit. Audit-only requests never authorize fixes, native assignments, verdict writes or publication.
---

# Foundry Audit

Apply [request routing](../foundry-shared/skills/ROUTING.md) first. For "audit only" or "change nothing," take the read-only path below without requiring native execution setup. For an assigned native acceptance review, retain its exact binding and independent QA role.

For native acceptance, read [QA](../foundry-qa/SKILL.md), the [native interface](../foundry-shared/skills/AI_CONTRACT_INTERFACE.md) and [operating rules](../foundry-shared/skills/OPERATING_RULES.md). Require Coordinator-assigned independent QA identity and the exact current revision/digest/attempt/candidate. Use an isolated exact-candidate snapshot; Worker self-review is forbidden.

Read the semantic contract version and full authoritative native body/policy. Inspect relevant source, complete diff, current-attempt review history and actual evidence; follow history and versioned read/diff continuation. Independently run the required checks. Reuse earlier evidence only when its actual source/configuration and scope match; structural validation or checked boxes are not behavioral proof.

Record `Accepted`, `Changes requested` or `Blocked` through `workflow_verdict` only with current binding and justified evidence. Accepted requires successful independent exact-candidate checks and remains distinct from Done. Corrections preserve the Worker/attempt and require a changed candidate plus renewed review. Material premise/scope problems return to Architect; no arbitrary retry count substitutes for that decision.

For an explicitly read-only system or historical issue audit, inspect source/specification/tests/delivery records and return findings without assigning yourself QA or writing a verdict. An issue is historical context, not the contract authority. Do not implement, publish or deploy from an audit-only request.

For discretionary findings, apply the operating rules' autonomous work selection. Explain the realistic trigger, concrete consequence, evidence/uncertainty, exposure and proportionate fix/verification cost; order actionable findings by practical impact. Start with primary workflows and known friction, and pursue further investigation when evidence warrants it. A contrived failure alone does not justify a work order. Rare severe failures may still warrant action; distinguish justified risk from unsupported speculation.

During authorized execution, send material in-scope findings through the normal role handoffs without a routine user prioritization gate. Leave low-value observations alone. For a read-only audit, return the assessment without starting those handoffs. When no worthwhile discretionary finding remains, say so; do not manufacture findings or a follow-up backlog. This never weakens mandatory exact-candidate acceptance criteria or checks.

Report confirmed causes separately from hypotheses and verification limits. Include criterion results, source/candidate identity, actual stage and the evidence needed for the next authorized action.
