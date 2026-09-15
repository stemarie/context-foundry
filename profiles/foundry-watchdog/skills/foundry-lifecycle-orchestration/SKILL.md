---
name: foundry-lifecycle-orchestration
description: Use when Watchdog emits a recovery action. Revalidate exact incident evidence and preserve maintenance boundaries.
version: 2.0.0
source: Context Foundry
adapted_for: foundry-watchdog
---

# Foundry Lifecycle Orchestration

## Entry gate

Consume the scanner's version-2 `actions`, not summaries or inferred lifecycle transitions. Re-read every cited card and the complete root `runs` before any permitted routing. Empty or unchanged notification output permits no work or message. `--inspect` exposes unresolved incidents even when notification is suppressed; `notify: false` never authorizes a notification or mutation.

The scanner is read-only. The existing wrapper stores only `notification_digest` as a deduplication receipt, not completion evidence. `incident_key` binds the board, exact audit task/run, role, contract and recovery class. Reuse it after restart; never generate a fresh key merely because a title, summary, heartbeat, or Worker changed. Unresolved incidents remain inspectable until fresh authoritative audit/reconciliation evidence is obtained.

## Contract

The sole external contract repository is `stemarie/AI.Contract`; `stemarie/context-foundry` is source, not contract authority. Observe identity using the exact pair:

- `Canonical external contract: <URL>`
- `Contract ID/revision: Issue #<number> / <marker> / <body SHA-256>`

The canonical five-line Closure Auditor form may omit the body SHA-256 after the marker, but that omission cannot authorize a product-repair cohort join. Compatibility accepts the exact legacy pair `External contract: <URL>` and `Contract identity/revision: Issue #<number>; `<marker>`; body SHA-256 `<hash>`.`. Mixed, duplicate, malformed or mismatched headers fail closed. Never normalize a malformed token or infer identity from an Issue number in prose.

Recognize Candidate, Capability, Post-delivery and Closure Auditor roles. Role/title must agree when both are present; assignee and forced task skills must corroborate the exact role. Current task skills must be present as an exact list of strings; historical creation-event skills cannot supply missing current authority, and conflicting event/task skills fail closed. Titles and noncanonical Role prose are observation hints only. Even corroborated role/skills never grant product-write authority. Missing/noncanonical maintenance identity must stay visible as an escalation, not disappear.

Archived records remain inspectable history without fresh recovery actions; do not resurrect them. A valid Capability Auditor PASS is an observation, not a maintenance incident or release authorization. A linked blocked/queued repair prevents duplication but is not runnable: escalate its disposition rather than calling it active delivery.

Use only the latest uniquely ordered root `runs[].metadata.verdict` from a completed `foundry-auditor` run on a completed audit task. Ignore `latest_summary`, nested `task.runs`, child-run verdicts and narrative PASS claims. A tied latest start time, missing multi-run ordering data, duplicate run identity, running latest attempt, or missing/invalid metadata means escalation, never selecting a favorable historical verdict.

## Allowed actions

| Scanner action | Bounded consumer behavior |
|---|---|
| `route_product_repair` | Only for an explicitly authorized product contract: fresh readback of the same audit task/run and exact URL/Issue/marker/hash, plus no equivalent linked live recovery, permits one fixed-template Architect repair-selection card. Use `incident_key` as idempotency key and add the exact audit card as parent. Re-read the created card and dependency. |
| `observe_recovery` | Read the named live recovery; do not create another card. It is unresolved, not repaired. A completed Worker is not independent verification. |
| `direct_maintenance` | Report to the existing directly authorized maintenance owner/session, with exact audit/run evidence. Do not create or dispatch a card and do not perform source/install/runtime work as Watchdog. |
| `reconcile_external_state` | Request read-only current-state evidence from the authorized repository owner/session. Distinguish an already-advanced main or merged PR from an undelivered frozen candidate. No automatic repair, Delivery, Closure, or obsolete direct push. |
| `escalate` | Preserve evidence and the failure reason; obtain missing identity/ordering/authority from the owner. Do not manufacture a canonical contract or a maintenance route. |

A product-repair packet contains only the validated canonical identity pair, `Role: Architect`, `Recovery audit task: <exact task id>`, `Recovery audit run: <exact run id>`, `Recovery incident: <incident_key>`, and the bounded instruction to select repair within the existing product contract. Set assignee `foundry-architect`, its required skills, the exact parent and idempotency key explicitly. Verify the current contract still authorizes the work before creation. Direct user no-card instructions override this generic product route.

An equivalent live recovery must have a verified Architect/Worker role, the exact same contract URL/Issue/marker/hash, exact `Recovery audit task` and `Recovery audit run` fields, and an actual parent link to that audit. It must be active, not historical done/archived work. Unrelated active cards, matching titles, old repair Workers, different runs/revisions, or guessed graph relationships cannot suppress the incident. Multiple matching recoveries are ambiguous: escalate without creating more.

## Forbidden actions

Never create maintenance Kanban cards. This includes capability reconciliation, failed/missing preflight, adapter, scanner, profile, scheduler, and installation repairs. A passing preflight is a gate, not permission to redispatch or create maintenance work.

Do not write source, run git, inspect or mutate GitHub, read credentials, change an Issue, invent a product contract, create Delivery or Closure cards, alter profiles/cron, start services, dispatch, or issue an audit verdict. PASS is not a Delivery instruction. A frozen candidate never overrides freshly verified product main/PR state.

## Verification

Recompute the proposed action against current read-only evidence immediately before permitted product routing. Re-read affected exact cards and links after any authorized write; record the stable incident key once. Do not treat a seen digest, a completed repair, an old PASS or an old receipt as resolution. If a product route, direct maintenance or external reconciliation lacks authority, leave it unresolved and escalate rather than inventing a substitute route.

## Read-only collection and replay

The installed `kanban list` implementation calls `recompute_ready`, and list/runs help exposes no pagination. Do not invoke those commands from the scanner. Its narrow SQLite `mode=ro`, `query_only` transaction reads the complete board's task/run/link/event tables in 256-row pages, bounded to 100000 rows per table; exceeding a bound or encountering partial input fails closed. It never opens the Hermes migrating/repairing connection. `FOUNDRY_WATCHDOG_DB` selects an explicit read-only board snapshot for tests; the default is `~/.hermes/kanban/boards/context-foundry/kanban.db`. No scheduler architecture or runtime service changes are part of this procedure.

For investigation run the scanner with `--inspect` (and optionally `--input <JSON snapshot>`). Preserve the real root envelope. Notification deduplication is not incident resolution.
