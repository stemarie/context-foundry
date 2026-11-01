---
name: foundry-explore
description: Explore a system, feature or specification through the installed openspec-explore skill. Use when the user invokes foundry-explore or requests the Foundry exploration entry point; not for implementation or proposal generation.
---

# Foundry Explore

Invoke [openspec-explore](../openspec-explore/SKILL.md) for the user's request.
Read that skill in full and follow its workflow rather than duplicating it here.
Resolve it from the session catalog or sibling directory; if missing, report the
missing dependency and stop.

Pass through the complete user request, project/store selection, existing
conversation context, decisions, scope and authorizations. An explicit
foundry-explore invocation is an explicit request for its OpenSpec exploration
workflow, including its project-setup handling.

Preserve the underlying exploration and write-authorization boundaries. Creating
or editing this wrapper does not invoke exploration. Do not automatically start
foundry-propose, foundry-start or implementation after exploration.
