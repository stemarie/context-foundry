---
name: foundry-verified-delivery-audit
description: Audit exact validation and delivery claims for Foundry evidence receipts.
version: 1.1.0
source: kits/contract-orchestration/skills/verified-implementation-delivery.md
adapted_for: foundry-auditor
---

# Context Foundry Verified Delivery Audit — Foundry Auditor

## Checks
1. Inspect the latest packet/correction contract, source policy, evidence artifacts, Worker receipt, current repository status, and relevant audit rules.
2. Re-run packet-approved read-only validators and targeted reproducibility checks. A Worker narrative is never sufficient.
3. Confirm every claimed test, lint, hash, and diff check has real output; classify skipped/unavailable checks as not run, never pass.
4. Confirm repair scope: no unapproved source expansion, evidence rewrite by Auditor, secret leakage, generated debris, or unrelated checkout mutation.
5. Candidate Auditor PASS certifies only the exact candidate SHA and scoped evidence; it does not certify direct-main delivery, deployment, or milestone completion.
6. For `direct_main_required`, accept closure only after independent audit confirms the authenticated bound default branch contains the exact audited candidate through a non-force fast-forward and the required post-delivery checks are bound to that read-back revision. A local commit alone fails this check.
7. For `candidate_only`, require an explicit hold reason, named disposition owner, and concrete next decision/date; it may close a candidate-only tranche, never a product milestone. For `human_approval_required`, require the exact direct-main authorization request and named approver; it cannot auto-push. Never create, review, or merge a pull request.
8. Return PASS only if material facts are cited, packet scope holds, validators pass, recovery claims are evidenced, and no unapproved action occurred.

## Error correction handling
- `REQUEST_CHANGES`: identify precise bounded Worker corrections and require a fresh independent audit.
- `BLOCKED_WITH_EVIDENCE`: record concrete external barrier or contract-invalidating evidence; do not remedy it.
- Never weaken a validation rule or change a Worker artifact to make the result pass.
