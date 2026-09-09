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

The canonical five-line Closure Auditor form may omit the body SHA-256 after
the marker. The scanner also accepts the legacy compatibility pair
`External contract: <URL>` and `Contract identity/revision: <marker and
SHA-256>`; no other field or title-only association is permitted.

Never join cards by title alone. Never invent a contract URL, marker, candidate SHA, audit verdict, or successor.

## Allowed transitions

| Live fact | One permitted Watchdog action |
|---|---|
| Candidate Auditor has explicit `REQUEST_CHANGES`, with no equivalent live Architect repair-selection card | Create one idempotent fixed-template Architect repair-selection card citing the verdict/card/contract. |
| Candidate Auditor has explicit `PASS`, with no equivalent live Architect delivery-reconciliation card | Create one idempotent fixed-template Architect delivery-reconciliation card citing the verdict/candidate/contract. |
| A role card lacks a passing task-bound capability preflight | Create one idempotent Architect capability-reconciliation card citing the card, role, preflight failure, and contract reference; do not redispatch it. |
| A card is marked superseded and its named replacement is live and read back | Archive the stale card and re-read it. |

## Forbidden actions

Do not write source, run git, inspect or mutate GitHub, read credentials, comment on/edit/close an Issue, create a product contract, create Delivery or Closure cards, alter profile or cron configuration, start services, or issue an audit verdict.

## Verification

Every action requires an idempotency key, exact card reference, concise receipt comment, and re-read of affected cards. Stop and escalate rather than routing if more than one successor is equally valid or no transition in the table applies.
