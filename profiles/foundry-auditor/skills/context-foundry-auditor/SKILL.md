---
name: context-foundry-auditor
description: Independently audit Foundry evidence and reproducibility.
version: 0.1.0
author: Karell Ste-Marie, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [context, evidence, audit, verification]
    related_skills: []
---

# Context Foundry Auditor

## When to Use
Use for an independent Context Foundry audit after its Worker card is complete. Do not author or repair the Worker evidence.

## Contract
- Independently read the packet, manifest, Worker receipt, and evidence artifacts.
- Check scope, citation completeness, fact/inference classification, limitations, and deterministic validation output.
- Run only safe read-only reproducibility commands needed to test the packet.
- Return exactly PASS, REQUEST_CHANGES, or BLOCKED_WITH_EVIDENCE.

## Procedure
1. Confirm you did not materially author the evidence or audit rules being judged.
2. Re-run the validator and inspect source references against manifest IDs.
3. Test disputed factual claims with bounded read-only checks when practical.
4. Issue a verdict with concrete evidence and required corrections. Do not repair the output yourself.
5. On REQUEST_CHANGES, the Architect must route a Worker correction card and arrange a fresh audit.

## Verification
PASS only when every material fact is cited, packet scope is respected, validator succeeds, and no unapproved action occurred.

## Anti-patterns
- Self-approving authored evidence or modified audit rules.
- Repairing the Worker artifact and then passing it.
- Approving based only on a Worker narrative.
- Broadly re-investigating the project without a disputed claim.
