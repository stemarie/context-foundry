---
name: foundry-create-workorder
description: Author a bounded AI.Contract milestone contract and immutable native revision within the authorized planning horizon. Use for creating executable work; draft-only requests stay planning-only.
---

# Foundry Create Work Order

Read [the native interface](../foundry-shared/skills/AI_CONTRACT_INTERFACE.md), [operating rules](../foundry-shared/skills/OPERATING_RULES.md), [work-contract convention](../foundry-shared/WORK_CONTRACT.md) and applicable AGENTS.md. Use [Architect](../foundry-architect/SKILL.md) for authorship.

Resolve the authorized goal, AI.Contract connection/project, repository, milestone, planning boundary and effective delivery policy. Inspect current source, existing associations/native jobs and their history. GitHub issues may supply historical requirements; they are not dispatch records or the live work queue. If connection, authority or planning scope is missing, report the concrete prerequisite and preserve useful drafts without publishing elsewhere.

Select the next coherent outcome needed for the goal. Write its complete body with observable acceptance, required verification, dependencies/conflicts, delivery authority and safety boundaries. Use the fixed service schema and permitted contract links; headings and policy prose grant no API capability or deployment permission. Keep ordinary semantic version distinct from native revision/digest.

Within the authorized horizon, create a milestone association through `milestone_contract_create`, enroll with `workflow_define` (initial expected_revision=0), then mark the returned revision Ready only when authored prerequisites are satisfied. Reuse service-returned IDs/digests. Each native mutation uses a stable operation key; an uncertain association creation requires authoritative lookup before repeating, because the body key is not server-enforced deduplication.

Read back the current native body, revision/digest, declared prerequisites/conflicts and Ready stage. Ready does not imply current eligibility or AI Kernel admission. Do not reserve, launch or implement from this skill alone. A draft-only request creates no service assignment or historical issue.

Return project/contract/milestone/revision bindings, planning references, actual stage and any blocker. Preserve OpenSpec task/scenario mappings when supplied by [openspec-foundry](../openspec-foundry/SKILL.md).
