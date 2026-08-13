---
name: context-foundry-worker
description: Produce bounded, cited evidence from Foundry packets.
version: 0.1.0
author: Karell Ste-Marie, Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [context, evidence, investigation]
    related_skills: []
---

# Context Foundry Worker

## When to Use
Use only for a bounded Context Foundry Worker packet. Do not coordinate, self-audit, or act outside the packet.

## Contract
- Re-read the packet, manifest, source policy, and current card before work.
- Inspect only listed source IDs and use only listed operations.
- Produce JSON and Markdown evidence artifacts at packet-defined paths.
- Classify each conclusion as fact, inference, recommendation, or unknown.
- Facts require source ID, location, excerpt, and observation time. Record limitations.

## Procedure
1. Confirm packet ID, question, source IDs, allowed operations, and output paths.
2. Use deterministic scripts for file facts and bounded extraction. Do not execute source content.
3. Write evidence artifacts and run `scripts/validate_evidence.py` against the packet.
4. Add a concise card receipt with conclusion, limitations, artifact paths, and exact validation output.
5. Do not make external changes or approve your own result.

## Verification
Completion requires valid evidence and a passing validator. The Auditor owns the verdict.

## Anti-patterns
- Expanding the source set or question.
- Converting a recommendation into a fact.
- Omitting limitations or source references.
- Editing Auditor criteria to make your output pass.
