---
name: improve-foundry-temp
description: "Use when improving Foundry. Runs manual evidence review."
version: 1.0.0
triggers:
  - "improve the foundry"
  - "improve Foundry"
  - "review Foundry reliability"
mutating: false
---

# Improve Foundry (Temporary Manual Activation)

## Contract

- Replaces the **unbuilt** recurring Brainiac loop with one manual, evidence-first review.
- Establishes live current state before interpreting historic sessions or prior assurances.
- Produces at most one small, falsifiable Foundry improvement packet per invocation.
- Makes no source, profile, scheduler, Kanban, GitHub, credential, or external-service change unless Karell separately authorizes that exact follow-up.
- Treats “no qualifying evidence” as a valid no-change result.

## Scope

Use this only for Context Foundry reliability learning: repeated lifecycle/control-plane failures, incident recovery, evidence integrity, role/authority boundaries, or delivery verification. It is not a general product roadmap, a request to build another control plane, or permission to resume speculative platform work.

This skill is deliberately temporary. It does **not** start Brainiac, create a cron job, enable a gateway, or claim periodic reassessment is live.

## Manual Activation Workflow

1. **Inspect live state first.**
   - Identify the authoritative Context Foundry board, repository, current task/run/receipt state, and active Watchdog/Brainiac runtime state.
   - Distinguish configured, running, used, and verified. Do not treat a stopped profile, a passing cron row, or a historical test as current lifecycle coverage.

2. **Collect only qualifying evidence.** A review qualifies only if there is:
   - a new high-severity incident;
   - a second matching incident fingerprint within 30 days; or
   - a user-requested weekly synthesis that contains new deterministic evidence.
   Evidence must come from live cards/runs/receipts, repository checks, deterministic probes, or authenticated service reads—not model claims or vague recollection.

3. **Classify the failure.**
   - Name a concise incident fingerprint.
   - Separate a one-off invocation/path/credential failure from a systemic defect.
   - Identify the narrow broken invariant and the affected lifecycle boundary.
   - Reject scope drift: do not propose a platform, dashboard, scheduler, or self-hosting foundation as a remedy for an unproven problem.

4. **Produce one bounded learning packet.** Include:
   - Incident fingerprint and severity.
   - Evidence citations: exact resource IDs/paths, observed prior/final state, and deterministic probe/test results.
   - Root-cause hypothesis, explicitly labelled as hypothesis where not proven.
   - One proposed invariant.
   - One replay/regression test that would fail before the correction and pass afterward.
   - Expected safe transition and a metric that demonstrates recurrence fell.
   - Smallest owning role and a strict change boundary.

5. **Stop at the decision gate.**
   - If evidence does not qualify, report `NO_CHANGE — insufficient qualifying evidence` and what evidence would reopen the review.
   - If it qualifies, report the packet and ask for explicit authorization before implementation. Foundry profile/skill/adapter/process maintenance is then performed directly in source with independent review, not through an Architect/Worker/Auditor Kanban maintenance chain. Create a linked GitHub issue and publish only when requested; AI.Contract remains the contract plane for product work.

## Output Format

```text
Foundry improvement review — <date/time>
Live status: <configured / running / used / verified facts>
Verdict: NO_CHANGE | PROPOSE_IMPROVEMENT | BLOCKED_WITH_EVIDENCE

Incident fingerprint: <only if qualified>
Evidence: <IDs, paths, checks, observed results>
Systemic? <yes/no and why>

Proposed invariant: <one sentence>
Regression/replay test: <one sentence>
Success metric: <measurable recurrence/quality signal>
Owner and boundary: <role; smallest permitted scope>

Decision required: <explicit authorization needed, or none>
```

## Anti-Patterns

- Do not call Brainiac operational merely because its profile exists or its instructions are present.
- Do not create a cron, start a gateway, or add a new autonomous loop as a side effect of a manual review.
- Do not convert a single bad command or historical failure into a systemic defect without matching evidence.
- Do not treat passing unit tests or a healthy scheduler row as proof that real cards, receipts, and adapters interoperate.
- Do not create Issue/board/commit/profile changes until Karell explicitly approves the bounded packet.
- Do not revive Phase 3 platform work merely because an improvement packet exists; Phase 3 remains on hold pending evidence of recurring assurance demand.

## Authorized recovery follow-through

- Reconcile authenticated product state and current contract authority before routing recovery; an already merged candidate does not authorize tracker closure or a new implementation tranche.
- Test the whole observed detector-to-decision boundary. A scanner fix, a healthy cron row, or policy-string assertions alone do not prove restored productive delivery.
- Preserve unresolved work as inspectable evidence with one owner and concrete decision; repeated-scan notification suppression must not erase the unresolved incident. Historical completed repair cards are not live successors.
- Use real root task/runs/events envelopes in replay fixtures. Parse structured verdicts and exact audit/run recovery links; missing or ambiguous role, contract, lineage, or remote evidence escalates without granting authority.
- Verify source/install parity and run the installed read-only path before claiming a repair is operational. Keep maintenance success separate from product progress and report any remaining genuine decision gate.

## Verification

Before reporting, verify that every factual claim is backed by a live read or deterministic probe, label hypotheses, and state whether any external state changed. Under normal invocation, the answer must state that no external state changed.
