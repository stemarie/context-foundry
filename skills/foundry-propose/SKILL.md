---
name: foundry-propose
description: Create an OpenSpec proposal and its schema-defined planning artifacts through the installed openspec-propose skill. Use when the user invokes foundry-propose or requests the Foundry proposal entry point; not for implementation or execution.
---

# Foundry Propose

Invoke [openspec-propose](../openspec-propose/SKILL.md) for the user's request.
Read that skill in full and follow its workflow rather than duplicating it here.
Resolve it from the session catalog or sibling directory; if missing, report the
missing dependency and stop.

Pass through the complete user request, change name or description, project/store
selection, existing conversation context, decisions, scope and authorizations.
An explicit foundry-propose invocation is an explicit request for its OpenSpec
proposal workflow, including its project-setup handling.

Preserve the underlying planning boundary and schema-defined artifact workflow.
Creating or editing this wrapper does not create a proposal. After presenting the
planning artifacts, stop; do not automatically start foundry-start or implementation.
When the user later requests Foundry execution, use foundry-start as its entry point.

Within this Foundry wrapper, the final execution handoff is `foundry-start`.
Use that handoff instead of the underlying skill's standalone apply suggestion.
Do not invoke either executor automatically. The official OpenSpec apply workflow
remains available when separately requested outside a Foundry cycle.
