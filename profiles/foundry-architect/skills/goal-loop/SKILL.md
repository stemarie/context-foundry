---
name: goal-loop
description: "Design and operate persistent or temporary goal loops: desired-state monitors with memory, guardrails, human gates, and repeated checks until achieved, obsolete, blocked, or no longer needed."
version: 1.0.0
author: Overmind + Karell
license: MIT
metadata:
  hermes:
    tags: [goals, automation, cron, kanban, mariadb, dashboard, orchestration]
    related_skills: [task-interview, scheduled-automation-operations, kanban-orchestrator]
    created_by: agent
---

# Goal Loop

Use this skill when Karell asks to create, design, inspect, or operate a **goal-loop**: a persistent or temporary automation that keeps comparing reality against a desired state and takes the next safe step until the goal is achieved, obsolete, blocked, paused, or failed.

A goal-loop is not just a cron job and not just a checker. It is a desired-state operator with:

- a clear goal contract,
- durable state,
- append-only context/history,
- active progress actions,
- safe-action rules,
- human approval boundaries,
- stop/obsolete conditions,
- and a visible dashboard state.

Important: the checker must not merely observe whether the goal is true. When safe and inside the goal contract, it should take the next useful action that moves reality toward the desired state. Example: for a broad goal like “negotiate all incoming brand deals to the best of your ability,” the loop should inspect inbound opportunities, gather context, draft/respond/negotiate within approved guidelines, update the ledger, and stop for Karell only at human gates such as final acceptance, pricing exceptions, legal/financial commitments, or unclear judgment calls.

## Core definitions

| Term | Meaning |
|---|---|
| Prompt | One request. No durable loop implied. |
| Loop | One recurring job with memory. |
| Goal-loop | A loop tied to a desired state and end/stop conditions. |
| Loop of loops | A control pattern where multiple loops notice each other, share state, hand off context, and stop at boundaries. |

Basic runtime shape:

```text
Goal defined
→ Check current state
→ Compare against desired state
→ Decide next move
→ Act or create work if safe
→ Leave a context record
→ Update compact state
→ Schedule next check
→ Repeat until done/blocked/obsolete/paused
```

## Mandatory intake rule

Before creating a new goal-loop, use `task-interview` as the ingest layer unless Karell has already provided a complete goal contract.

This implication is one-way:

```text
goal-loop → use task-interview intake
```

Do **not** infer the reverse:

```text
task-interview → goal-loop
```

`task-interview` remains general-purpose. It only becomes a goal-loop intake when the user explicitly asks for a persistent/recurring goal monitor or uses goal-loop language.

## Intake checklist

The intake must capture enough to create a goal contract:

1. **Goal title** — what should become or remain true?
2. **Goal type** — temporary, permanent, or recurring.
3. **Desired state / success condition** — exact definition of done or healthy.
4. **Current-state sources** — APIs, web pages, files, Kanban, Gmail, ClickUp, Patreon, Skool, database tables, etc.
5. **Cadence / trigger** — schedule, webhook, manual, event-driven, or mixed.
6. **Safe actions** — what Hermes may do without asking.
7. **Human gates** — what requires Karell approval or external login/2FA/credential action.
8. **Blocked condition** — when to stop and ask.
9. **Obsolete condition** — when the goal no longer matters.
10. **Notification policy** — silent unless changed, daily summary, critical-only, etc.
11. **Evidence and record** — what to log every pass.
12. **Related references** — Kanban IDs, URLs, repo, ClickUp task, Google Doc, etc.
13. **Assigned profile** — ask which Hermes profile should own/operate the goal because of specialization, skills, credentials, tone, or local adapters. Suggest the likely best profile when obvious (for example: `brand-deal-ops` for sponsorship negotiation, `scto-producer` for content production, `finance-receivables` for receivables/cashflow, PM/default for cross-system coordination).
14. **Handler** — choose the profile-local behavior module that should handle the goal, e.g. `noop`, `project_flow`, `dashboard_watchdog`, or a domain-specific handler.
15. **Sources** — choose the profile-local source/adapters the handler may use, e.g. local Kanban, issue trackers, task apps, email, HTTP, files, or APIs.

Ask one question at a time. Do not dump a giant form into Telegram.

### Interview clarity

When Karell selects a role model, naming convention, or other design choice, restate the settled choice plainly and move to the next unresolved question. Do not introduce unrelated generic conventions as a “correction.” If a qualification is genuinely needed, say in one short paragraph exactly what changes and what remains unchanged before continuing the interview.

## Broad-goal and sub-goal doctrine

Karell's goal-loops may be broad operating mandates, not only narrow checks. Treat broad goals as adaptive agents with a mandate, memory, boundaries, and escalation rules.

A broad goal usually needs more interview context than a narrow monitor. Use `task-interview` to discover:

- operating objective,
- assigned profile,
- profile-local handler,
- profile-local sources/adapters,
- normal playbook,
- safe autonomous actions,
- forbidden actions,
- approval gates,
- escalation thresholds,
- tone/style/preferences,
- success metrics,
- and examples of good/bad outcomes.

Broad goals can later become sub-goals under a higher-level goal. Design every goal row so it can be parented later:

- keep goal contract self-contained;
- record `related_system` and `related_ref` clearly;
- use context rows for handoffs and spawned sub-goals;
- do not bake in assumptions that prevent a parent “loop of loops” from coordinating it later.

For broad mandates, the loop should run an action cycle:

```text
Observe sources
→ Identify opportunities/problems
→ Decide next safe move
→ Act within guidelines
→ Record evidence/action
→ Ask Karell only at defined gates
→ Continue adapting
```

Do not wait for Karell to manually decompose every sub-action. If the goal contract says negotiation is allowed, negotiate. If it says draft/respond/follow up/research/update records is allowed, do those things. Final acceptance, irreversible commitments, public/financial/legal/destructive actions, or out-of-policy exceptions remain human-gated.

## Kanban work-assignment doctrine

Anything that needs to be done by a profile/handler/operator must be assigned through a Kanban card. The card title must include `Goal-[ID]` using the concrete goal id and should also include a human-friendly task name, for example `Goal-17 Draft rollout notes`, so the work is visibly tied back to the goal-loop without making the board unreadable.

Before creating a new Kanban card, the handler must inspect the board for an existing card with the same `Goal-[ID]` marker and the same purpose. If one exists, do not duplicate it. If it is blocked, stale, or otherwise problematic, try to fix that existing card within the goal's `safe_actions` first; only create a new card when no matching card exists and creating one is explicitly allowed.

This is a throttle. It keeps the system difficult to overwhelm and prevents autonomous card spam.

### Post-delivery verification gates

When a goal-owned implementation or migration card must be followed by operational verification, create a small explicit dependency chain rather than putting a vague “check afterward” note in the root:

1. Create a first `todo` child with the implementation card as its literal parent. Require it to independently inspect delivered artifacts and the live source of truth, then examine the named blocked/dependent card(s).
2. The verifier must choose the truthful status outcome: unblock/requeue the same card only if its remaining work is necessary and concretely recoverable; archive it with an evidence comment if the completed change genuinely supersedes it. Never bulk-unblock unrelated cards or call a stale card complete merely to clear the board.
3. When affected automation or script health also needs verification, create one further child gated on both the implementation and first verifier. Scope it to the named affected jobs and relevant recovery path, require exact-wrapper/manual evidence plus scheduler-triggered verification after any repair, and prove the migrated boundary no longer depends on the retired optional component.
4. Re-show each new card and verify its `todo` status, parent links, assignee, skills, and literal body requirements. The dependency engine—not an informal promise or extra cron—is the “after execution” guarantee.

Use a normal fixed graph for these verification/recovery cards; avoid goal-mode decomposition around a shared operational workspace.

## Architecture-boundary check before role selection

Before locking in profiles, handlers, or a new control plane for a goal-loop, inspect the supplied spec and known adjacent systems for an existing reusable primitive. A proposed coordinator / worker / verifier design can overlap with a pre-existing work-contract system such as AI.Contract.

Ask and settle the smallest consequential boundary question first:

```text
Should this goal use the existing contract/control-plane substrate,
or merely mirror its concepts inside Hermes Kanban?
```

Do not treat the visual similarity as cosmetic. The answer changes artifact ownership, durable identifiers, authority boundaries, evidence receipts, and the correct role routing. Record the chosen relationship as an explicit constraint in the goal contract before selecting coordinator/investigator/verifier profiles or creating boards.

## Profiles, handlers, and sources

In Hermes, the **profile is the operator-capable agent context**. Do not treat a handler as a separate agent identity floating above profiles.

### Evidence-work role pattern: Architect → Worker → Auditor

For a goal that builds or operates an evidence-driven orchestration system, use three separate, configurable role profiles by default:

- **Architect** maps sources, defines bounded packets/contracts, routes work, manages human gates, and synthesizes approved evidence. It never audits its own conclusions.
- **Worker** performs only the assigned packet and produces cited, durable artifacts.
- **Auditor** independently checks packet scope, source references, evidence classification, and acceptance criteria. It may run read-only inspection and safe deterministic validation commands in the project workspace; it may approve, request changes, or block with evidence. It does not perform broad remediation.

Use dedicated default profile names when the workflow warrants durable isolation (for example `foundry-architect`, `foundry-worker`, and `foundry-auditor`), but record names and mappings as configurable project policy—not hard-coded platform architecture. The Auditor is a project/domain-specific verification lane unless repeated deployments prove it should become a generic system role.

For a first pilot that relies on a small real corpus, the Architect records the selected read-only source set in the manifest before dispatching Workers. A recorded authorized work order covers normal bounded corpus selection and use; require a renewed human gate only for a material corpus/scope change, external side effect, destructive action, or genuine product decision.

Use this hierarchy:

- `assigned_profile` says which Hermes profile owns/operates the goal.
- `handler` says which profile-local behavior module handles this goal class.
- `sources` says which profile-local source/adapters the handler may use.

Example:

```json
{
  "assigned_profile": "project-manager",
  "handler": "project_flow",
  "sources": ["local_kanban"]
}
```

For the public GitHub repo, the generic `project-manager` demo profile is the right example because projects/tasks/blockers/review gates are broadly understandable without private deployment details. Private deployments can bind Karell's real profiles to real Kanban/ClickUp/GTasks sources outside the generic repo.

## Storage model

Prefer two durable tables:

1. `goal_loops` — one row per goal; the contract and current compact state.
2. `goal_loop_context` — append-only observations, decisions, actions, handoffs, and errors over time.

The history table should be append-only by default. Do not overwrite the trail that explains why the loop made decisions. Use the main goal row for compact working memory.

Minimum `goal_loops` fields:

- `id` / `goal_loop_id`
- `goal_key`
- `title`
- `description`
- `status`: active, paused, done, blocked, obsolete, failed
- `goal_type`: temporary, permanent, recurring
- `priority`
- `cadence_seconds`
- `next_check_at`
- `last_checked_at`
- `success_condition`
- `blocked_condition`
- `obsolete_condition`
- `safe_actions` JSON
- `requires_human_for` JSON
- `assigned_profile`
- `handler`
- `sources` JSON
- `work_requests` JSON
- `current_state` JSON
- `current_summary`
- `related_system`
- `related_ref`
- timestamps

Minimum `goal_loop_context` fields:

- `id`
- `goal_id`
- `observed_at`
- `source_type`
- `source_ref`
- `event_type`: observation, state_change, decision, action_taken, blocked, unblocked, completed, obsolete, error, handoff
- `summary`
- `details` JSON
- `impact`
- `recommended_next_action`
- `next_check_at`
- `created_task_ref`
- `triggered_goal_key`
- `actor`

## Operating loop

Each pass should:

1. Load the goal row.
2. Load recent context rows, not necessarily the full history.
3. Inspect the current source-of-truth systems.
4. Compare current state against success, blocked, and obsolete conditions.
5. Decide whether there is meaningful change.
6. Append a context row summarizing the observation/decision/action.
7. Update `current_state`, `current_summary`, status, `last_checked_at`, and `next_check_at`.
8. Take the next safe action that moves the goal forward; do not merely report that work exists when the goal contract authorizes action.
9. Create a human gate or blocked status when judgment/credentials/destructive/public/legal/financial/final-approval changes are required.
10. Stay silent unless notification policy says otherwise.

## Profile-handler doctrine

A serious goal-loop needs tuned profile-local handlers. Without them, the loop is only a stateful alarm clock. Do not claim autonomy or a goal is fully implemented if the runner only checks fields and writes context.

Runtime shape:

```text
goal contract
→ assigned Hermes profile
→ profile-local handler
→ profile-local sources/adapters
→ action log
→ dashboard / human gate
```

The checker answers: “Is the goal true right now?” The profile-local handler answers: “What safe action should I take next to make the goal more true?”

Handler rules:

- Prefer profile-local handlers over one giant generic agent blob: `goal-loop/handlers/project_flow.py`, `goal-loop/handlers/brand_deal.py`, `goal-loop/handlers/dashboard_watchdog.py`, etc.
- The goal contract must name the assigned profile, handler, sources, safe actions, human gates, and escalation policy.
- Handlers must be tuned to the goal class. A PM handler, brand-deal handler, finance handler, and infra watchdog have different safe actions and approval gates.
- Do not port a noisy cron 1:1 into goal-loop. Recast it as a desired-state goal with memory, duplicate suppression, safe actions, and clear human gates.
- When migrating an existing cron that already runs under a Hermes profile (for example a wrapper exporting `HERMES_PROFILE=project-manager`), use that existing profile as the operator-capable context. Create profile-local `goal-loop/handlers` and `goal-loop/sources` under the profile instead of inventing a detached/global operator.
- For broad goals, start with one narrow handler/source path and prove it is quieter/useful before migrating the entire old automation.
- “No handler, no autonomy” is the honest status. Infrastructure readiness is not handler readiness.

Example goal contract:

```yaml
assigned_profile: project-manager
handler: project_flow
sources: [kanban, gtasks]
safe_actions:
  - inspect_state
  - update_dashboard
  - move_obvious_kanban_status
  - create_worker_task
  - suppress_duplicate_alert
human_gates:
  - change_priority
  - cancel_project
  - send_external_message
  - make_financial_commitment
escalation_policy:
  notify_if: [human_needed, repeated_failure, stale_gt_72h, blocked_by_missing_access]
```

## Status doctrine

| Status | Meaning |
|---|---|
| active | Loop should continue checking. |
| paused | Do not run until resumed. |
| done | Temporary goal achieved. |
| blocked | Needs human input or external access before it can continue. |
| obsolete | Goal no longer matters or was superseded. |
| failed | Repeated errors or unrecoverable issue. |

Permanent goals usually do not become `done`; they report per-cycle health and remain active unless paused/obsolete.

## Human boundary doctrine

Do not build loops that act like unsupervised life managers. Loops should organize attention, not create chaos.

A loop may do safe, reversible, low-risk inspection or drafting work. It should stop for human input when:

- credentials, passwords, 2FA, or account ownership are involved;
- the action is destructive, expensive, public, legal, financial, or hard to undo;
- the source of truth conflicts;
- the goal contract is ambiguous in practice;
- the loop has repeated the same failed action;
- the recommended next action requires Karell's judgment.

## Document-based goal-loops for preserving valuable work

Use this pattern when Karell says valuable strategy/work gets lost if he forgets it, or asks for a goal-loop that "just helps me move this forward." The correct output is not a long chat explanation. Create a durable Google Doc as the human-readable project memory, link it from the goal-loop row (`related_system='google_doc'`, `related_ref=<doc url>`), and keep exactly one tiny next action visible.

Default shape:

```text
Goal title
Purpose
Operating rule: capture in the doc, not War & Peace in chat
Desired state
Current map / artifacts
Current next tiny action
Human gates
Safe autonomous actions
Log
```

Also create or update one Google Task for the current tiny human choice/review when appropriate. Keep the goal-loop active and recurring, but quiet: it should maintain the doc, append progress, and surface only the next gate or blocker. The final chat reply should be terse: goal id, doc link, task link if created, and the next tiny action.

Pitfall: do not turn a broad goal into a giant plan dump. For Karell, the value is preserved motion: durable doc + one next step + loop keeps it alive.

If Karell corrects the goal direction midstream, update the document and `goal_loop_context` as a `decision` or `correction`, then answer in one or two lines. If he says an upstream artifact is not ready yet, record known source locations and set the visible state to waiting; do not ask him for locations that are already known in memory/skills.

## Dashboard expectations

A goal-loop system should expose a lightweight dashboard showing operational state. The dashboard is for humans to see whether any goals have errors, problems, or need more information.

At minimum show:

- `goal_loop_id`
- title
- status
- goal type
- priority
- last checked
- next check
- current summary
- error/problem flag
- human-needed flag
- latest recommended next action
- related ref

The `goal_loop_id` is important because Karell should be able to start a new session and say:

```text
What does goal-loop 17 need?
```

or:

```text
Here is the missing info for goal-loop 17: ...
```

Then query the goal row plus recent context and continue from actual state.

## Good first targets

Start with tedious, recurring, low-risk work where failure is annoying but recoverable:

- research/news monitoring,
- content workflow readiness,
- Patreon/Skool posting checks,
- PRD → tickets → review loops,
- sales follow-up tracking,
- trip/logistics planning,
- recurring report health checks.

Avoid as first loops:

- banking,
- irreversible admin actions,
- legal/financial decisions,
- anything public or destructive without explicit gates.

## Repository/package hygiene

When maintaining a reusable `goal-loop` GitHub repository or packaged skill, keep it generic. The public/shared repo should contain goal-loop infrastructure, schemas, runner/operator patterns, dashboard code, generic examples, and bundled generic dependencies such as `task-interview`.

Do **not** commit user/business-specific goals, deployment notes, hostnames/IPs, credentials, profile names, brand/client workflows, or one-off examples unless they directly support goal-loop itself. Keep concrete deployment notes and private operating history in local references, private skills, or environment-specific docs outside the generic repo. If a real example is useful, convert it into a generic self-test or fictional/sample goal first.

Before pushing generic repo changes, grep the working tree for user/business-specific terms and replace/remove them. The bundled `task-interview` dependency should stay generic too: include the class-level SKILL.md, not unrelated session-specific interview references.

## Verification checklist

Before claiming a goal-loop is ready, distinguish **infrastructure readiness** from **handler readiness**. A database, dashboard, cron runner, and lock prove the infrastructure MVP; they do not prove full goal-loop autonomy. See `references/testing-and-operator-layer.md` for the testing split and pilot plan.

Before claiming a goal-loop is ready:

- [ ] Intake contract is complete or explicitly marked with open questions.
- [ ] Source-of-truth systems are named.
- [ ] Success, blocked, and obsolete conditions are defined.
- [ ] Safe actions and human gates are defined.
- [ ] Persistent storage path is defined.
- [ ] Loop pass leaves an append-only context record.
- [ ] Dashboard surface includes `goal_loop_id` and human-needed/error state.
- [ ] Notification policy avoids noisy repeated pings.
- [ ] A manual query path exists: “what does goal-loop X need?”
- [ ] For full implementation claims: at least one profile-local source/handler action path is tested, not just state evaluation.
- [ ] For broad goals: assigned profile, safe autonomous actions, and final-approval gates are recorded.

## Goal-mode Kanban workers: contract enforcement caveat

When a Kanban card is created with `goal_mode=true`, its `goal_max_turns` is a persistence budget, not a complete execution-control system. In the Hermes worker loop, an agent-created `kanban_block` or `kanban_complete` terminates the goal loop before later turns or judge continuations run.

For goal-owned Kanban work, prevent false early exits in the card contract and reconciliation process:

1. Treat the task body and durable user-authored task comments as canonical scope. Do not accept an agent’s unsupported claim of a narrower “brief-only” or “one-off” request as a scope override.
2. Require a blocked handoff to cite concrete external evidence: an unavailable credential, source-of-truth conflict, failed live verification, or an explicit human decision. Recoverable generation failures and routine scoped preflight are not human blockers.
3. Make completion evidence machine-checkable where possible: named artifacts, authoritative-record updates, re-reads, required statuses, and exact verification gates.
4. If a goal-mode card blocks despite a complete contract, inspect its body, comments, run summary, and `goal_mode`/`goal_max_turns`; classify an unsupported self-block as a contract-precedence failure and reconcile the same card rather than creating a duplicate.

## Common pitfalls

- Treating a goal-loop as a simple cron job with no memory.
- Interviewing forever instead of capturing the goal contract and moving on.
- Assuming every `task-interview` becomes a goal-loop.
- Rechecking without comparing against previous state.
- Overwriting history instead of appending context rows.
- Alerting on every pass instead of only on meaningful change or human need.
- Letting the loop take actions that should be human-gated.
- Forgetting an obsolete condition, causing undead automations.
- Letting profile/handler/operator work bypass Kanban. Any assignable work must become a deduplicated `Goal-[ID] ...` Kanban card, and blocked/problematic existing cards must be fixed before creating new ones.
- Letting a goal-mode parent stop at a generic `review-required` handoff when its contract does not require human approval. Repeat the smallest independent verification, then complete the parent with evidence matching only its own acceptance criteria. Do not say the parent is still awaiting its dependency-gated verifier in the completion summary: the goal judge can correctly classify that as unfinished. The child card remains the durable downstream gate and promotes after the parent is done.
- Over-abstracting into classic global registries/capability frameworks before the system has real use. Prefer Hermes-native profile-local handlers/sources first; add registries only when multiple real profiles need shared dispatch.
- Turning a chosen role model into a naming-convention tangent. If Karell has selected clear project roles, acknowledge the exact roles and their boundaries; do not call a generic convention a “correction” unless it actually changes the agreed design.
- Preserving backwards compatibility by reflex on an unused system. If Karell says the system has not been used yet, make the clean breaking schema/layout change instead of carrying compatibility aliases that teach the wrong model.

## Karell implementation defaults

When building Karell's concrete goal-loop system, the current default contract is:

- GitHub repo: `stemarie/goal-loop`.
- Store SQL scripts/migrations in the repo.
- Create a new MariaDB database on HOME NAS using existing saved credentials if available.
- Dashboard stack: PHP + vanilla HTML/CSS/JS.
- Dashboard deployment path: HOME NAS `/Web/goal-loop`.
- Dashboard MVP is read-only and LAN/VPN-only with no app login.
- Runner MVP is cron-driven every 15 minutes.
- Runner must be absolutely quiet unless there is an error or it truly needs human input that it cannot resolve after trying.
- Create the `goal-loop` skill in the repo and install/copy it into the local Hermes skill library.
- If Karell has confirmed the summarized contract and access exists, proceed to build/deploy rather than asking again.

## References

- `references/operator-profile-project-manager-pattern.md` — profile/handler/source split, generic `project-manager` public example, and expected demo behavior.
- `references/live-pm-profile-migration.md` — live migration pattern for replacing a paused profile-owned PM cron with a goal-loop using the existing `project-manager` profile as the operator.
- `references/kanban-work-assignment-throttle.md` — Kanban card rule for operator-assigned work: titles include `Goal-[ID]`, duplicate checks by purpose, and fix-existing-before-create behavior.
- `references/profile-local-handler-refactor.md` — design lesson from refactoring away from global operators/adapters into Hermes-native profile-local handlers and sources; includes breaking-change guidance for unused systems.
- `references/karell-goal-loop-project.md` — Karell-specific repo/dashboard expectations, database/dashboard decisions, SQL storage, and runner cadence.
- `references/mvp-deployment-and-verification.md` — first-build deployment notes: QNAP FTPS `/Web/goal-loop`, dashboard HTTP markers, MariaDB NAS-host grants, no-agent cron setup, and single-runner lock verification.
- `references/testing-and-operator-layer.md` — testing split between infrastructure MVP and real goal-operator behavior, plus first pilot recommendations.
- `references/live-runner-config-and-cron-recovery.md` — recovery pattern for paused/erroring goal-loop cron runners whose generic repo cleanup removed ignored live DB config; includes wrapper-regeneration and verification checklist.
- `references/context-foundry-phase1-intake.md` — paused, project-specific Context Foundry Phase 1 intake: settled role model, gates, terminal criteria, and exact next interview question.
