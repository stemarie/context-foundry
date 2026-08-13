---
name: ai-contract-verified-delivery-audit
description: Audit exact validation and delivery claims for Foundry evidence receipts.
version: 1.0.0
source: AI.Contract/automation/hands-off-development/skills/verified-implementation-delivery.md
adapted_for: foundry-auditor
---

# AI.Contract Verified Delivery Audit — Foundry Auditor

## Checks
1. Inspect the latest packet/correction contract, source policy, evidence artifacts, Worker receipt, current repository status, and relevant audit rules.
2. Re-run packet-approved read-only validators and targeted reproducibility checks. A Worker narrative is never sufficient.
3. Confirm every claimed test, lint, hash, and diff check has real output; classify skipped/unavailable checks as not run, never pass.
4. Confirm repair scope: no unapproved source expansion, evidence rewrite by Auditor, secret leakage, generated debris, or unrelated checkout mutation.
5. For a delivery claim, require equality among local revision, authenticated remote branch, and fetched tracking branch. A local commit alone fails this check.
6. Return PASS only if material facts are cited, packet scope holds, validators pass, recovery claims are evidenced, and no unapproved action occurred.

## Error correction handling
- `REQUEST_CHANGES`: identify precise bounded Worker corrections and require a fresh independent audit.
- `BLOCKED_WITH_EVIDENCE`: record concrete external barrier or contract-invalidating evidence; do not remedy it.
- Never weaken a validation rule or change a Worker artifact to make the result pass.
