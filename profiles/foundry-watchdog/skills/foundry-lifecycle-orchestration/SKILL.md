---
name: foundry-lifecycle-orchestration
description: Use when the Watchdog scanner emits a changed Foundry lifecycle payload. Apply only deterministic board routing rules.
version: 1.0.0
source: Context Foundry
adapted_for: foundry-watchdog
---

# Foundry Lifecycle Orchestration

## Entry gate

Use only after `scripts/foundry_watchdog_scan.sh` emits a changed relevant payload for `context-foundry`. Re-read every cited card before mutation. An empty scanner result permits no LLM work or board action.

## Contract

A Foundry cohort is identified by the exact current pair:

- `Canonical external contract: <URL>`
- `Contract ID/revision: Issue #<number> / <marker> / <body SHA-256>`

V2 AI.Contract cohorts are identified by the exact pair:

- `AI.Contract: <UUID> revision <n>`
- the card's required `Role`, `Dependency`, and `Receipt pointer` lines.

The canonical five-line Closure Auditor form may omit the body SHA-256 after
the marker. The scanner also accepts the legacy compatibility pair
`External contract: <URL>` and `Contract identity/revision: <marker and
SHA-256>`; no other field or title-only association is permitted.

Never join cards by title alone. Never invent a contract URL, marker, candidate SHA, audit verdict, or successor.

## Allowed transitions

| Live fact | One permitted Watchdog action |
|---|---|
| A completed opted-in `FOUNDRY_DRAFT_HANDOFF_V1` Architect draft has no live `Architect: execute` child | Re-show the draft; run the exact handoff finalizer only when its sole attached packet validates, then read back the one byte-identical execution child. |
| Candidate Auditor has explicit `REQUEST_CHANGES`, with no equivalent live Architect repair-selection card | Create one idempotent fixed-template Architect repair-selection card citing the verdict/card/contract. |
| Candidate Auditor has explicit `PASS`, with no equivalent live Architect delivery-reconciliation card | Create one idempotent fixed-template Architect delivery-reconciliation card citing the verdict/candidate/contract. |
| A role card lacks a passing task-bound capability preflight | Create one idempotent Architect capability-reconciliation card citing the card, role, preflight failure, and contract reference; do not redispatch it. |
| A V2 cohort has reached a terminal milestone, has no ready or running successor, and its required next role is blocked or absent | Create one idempotent fixed-template Architect soft-nudge/reconciliation card. Re-read every cohort card and record a concise board nudge receipt citing the stable AI.Contract ID/revision, blocked/terminal card IDs, and no-ready/running observation. Append the matching allowlisted durable incident with `scripts/foundry_incident_log.py record-nudge`; the wrapper bridges the stored row to Brainiac. |
| A card is marked superseded and its named replacement is live and read back | Archive the stale card and re-read it. |

## Forbidden actions

Do not write source, run git, inspect or mutate GitHub, read credentials, comment on/edit/close an Issue, create a product contract, create Delivery or Closure cards, alter profile or cron configuration, start services, or issue an audit verdict.

## Verification

Every action requires an idempotency key, exact card reference, concise receipt comment, and re-read of affected cards. Stop and escalate rather than routing if more than one successor is equally valid or no transition in the table applies.

## Soft-nudge boundary

A soft-nudge is a board-only recovery signal, not a new contract or a user approval request. Its narrowly authorized incident append is the sole external persistence: use an occurrence key made from the exact contract/revision, triggering terminal card, and reconciliation card; include only IDs, role, action, and receipt revision. Never create a second nudge while its exact Architect reconciliation card is ready or running; log the original nudge receipt instead. The Architect decides the repair/delivery routing after live read-back.
