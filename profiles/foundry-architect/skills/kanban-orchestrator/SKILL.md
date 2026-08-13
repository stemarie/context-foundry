---
name: kanban-orchestrator
description: Decomposition playbook + specialist-roster conventions + anti-temptation rules for an orchestrator profile routing work through Kanban. The "don't do the work yourself" rule and the basic lifecycle are auto-injected into every kanban worker's system prompt; this skill is the deeper playbook when you're specifically playing the orchestrator role.
version: 2.0.0
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing]
    related_skills: [kanban-worker]
---

# Kanban Orchestrator — Decomposition Playbook

> The **core worker lifecycle** (including the `kanban_create` fan-out pattern and the "decompose, don't execute" rule) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill is the deeper playbook when you're an orchestrator profile whose whole job is routing.

## When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

## The anti-temptation rules

Your job description says "route, don't execute." The rules that enforce that:

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web for implementation. If you find yourself "just fixing this quickly" — stop and create a task for the right specialist.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **If no specialist fits, ask the user which profile to create.** Do not default to doing it yourself under "close enough."
- **Decompose, route, and summarize — that's the whole job.**

## The standard specialist roster (convention)

The roster below is illustrative, not proof that a profile exists. **Before assigning any card, run `hermes profile list` (or the equivalent live profile lookup) and verify the exact assignee exists.** Never create a ready card for a conventional name such as `backend-eng` merely because it appears in this table. If the intended specialist is absent, route to an existing suitable profile (often `default`) or ask about creating one. After creation, run Kanban diagnostics or re-show the card; a ready card with an invalid assignee is stranded, not underway. If this mistake is discovered, reassign the same card, record the reason, dispatch once, and verify it reaches `running`.

These names are useful starting points only. Adjust to the profiles that actually exist.

For Karell's business-specific worker profiles and the profile creation/verification recipe, see `references/specialist-profile-roster-and-usage.md`. Current high-value profiles include `scto-producer`, `brand-deal-ops`, and `finance-receivables`; prefer routing narrow Kanban cards to them instead of starting extra gateway bots.

For task-id forensic questions like “what is the problem with `t_<hex>`,” use `references/stuck-card-forensics.md`: combine live card state, worker logs, session history, generated run artifacts, cron/PM monitor output, and external source-of-truth verification before answering.

When a research-routing philosophy changes or Karell defers an existing research backlog, use `references/research-backlog-policy-and-date-deferral.md`. It covers the three surfaces that must change (future ingress, incomplete cards, and in-flight workers), verified policy-override context, ready/running/blocked distinctions, date-release markers, and safe maintenance-window bulk transitions.

For Trello, distinguish abandoned Kanban mirror machinery from general Trello API credentials; see `references/abandoned-trello-mirror-and-credentials.md`. For the SCTO newsletter board lane contract and Friday 2pm scheduling handoff, see `references/scto-newsletter-trello-lanes.md`. For explicitly authorized discard-and-reinitialize recovery after SQLite corruption, use `references/kanban-fresh-reset.md`; it covers service shutdown, no-holder checks, empty DB initialization, verification, selective cron resumption, and one-time helper cleanup.

| Profile | Does | Typical workspace |
|---|---|---|
| `researcher` | Reads sources, gathers facts, writes findings | `scratch` |
| `analyst` | Synthesizes, ranks, de-dupes. Consumes multiple `researcher` outputs | `scratch` |
| `writer` | Drafts prose in the user's voice | `scratch` or `dir:` into their Obsidian vault |
| `reviewer` | Reads output, leaves findings, gates approval | `scratch` |
| `backend-eng` | Writes server-side code | `worktree` |
| `frontend-eng` | Writes client-side code | `worktree` |
| `ops` | Runs scripts, manages services, handles deployments | `dir:` into ops scripts repo |
| `pm` | Writes specs, acceptance criteria | `scratch` |
| `scto-producer` | The Serious CTO content-pipeline producer: ClickUp/Drive artifact orchestration, SCRIPT package checks, status routing, stuck-card diagnosis, and approval-gated handoffs | `dir:/home/karell/.hermes` |

## Engineering cards for media-editing automation

When routing implementation of video-cutting tools, encode media-fidelity limits and recovery artifacts explicitly rather than asking generically for “lossless FFmpeg editing.” Require a cleaned master, numbered source-derived good-take clips, an edit-decision manifest, source checksum verification, and an explicit `copy`/`match`/`auto` fidelity policy. Use `references/video-editing-automation-card-spec.md` for the reusable card shape and acceptance gates.

## Document-first implementation intake

When Karell provides a long implementation specification and explicitly says to save it in a Google Doc **before doing anything with it**, treat the document save as a hard sequencing gate:

1. Create a native Google Doc in the Hermes documentation folder (`1oNxZW4uQXhLL_Vt0_L6uf3DVkoTpfjQn`) using a clear project title.
2. Insert the complete specification rather than a shortened summary. Re-fetch the Doc and Drive metadata to verify its title, parent folder, and distinctive content markers before reporting success.
3. Do not inspect infrastructure, clone a repository, create a project directory, create a Kanban card, or begin implementation until the document save is verified.
4. Once a repository URL and a direct request for an implementation card arrive, create one durable `ready` card (not parked triage) assigned to a live verified profile. Include the Doc URL, repository URL, intended local directory, hard security boundary, acceptance gates, explicit no-deploy rule, and final-report receipt requirements in the card body.
5. Use an idempotency key for the project implementation card. Re-show it and verify task ID, assignee, status, workspace, body links, and forced skills before claiming it exists.

This keeps the source of truth and the worker’s scope auditable across retries and sessions.

## Decomposition playbook

### Step 1 — Understand the goal

Ask clarifying questions if the goal is ambiguous. Cheap to ask; expensive to spawn the wrong fleet.

### Step 2 — Sketch the task graph

Before creating anything, draft the graph out loud (in your response to the user). Example for "Analyze whether we should migrate to Postgres":

```
T1  researcher        research: Postgres cost vs current
T2  researcher        research: Postgres performance vs current
T3  analyst           synthesize migration recommendation       parents: T1, T2
T4  writer            draft decision memo                       parents: T3
```

Show this to the user. Let them correct it before you create anything.

### Step 3 — Create tasks and link

```python
t1 = kanban_create(
    title="research: Postgres cost vs current",
    assignee="researcher",
    body="Compare estimated infrastructure costs, migration costs, and ongoing ops costs over a 3-year window. Sources: AWS/GCP pricing, team time estimates, current Postgres bills from peers.",
    tenant=os.environ.get("HERMES_TENANT"),
)["task_id"]

t2 = kanban_create(
    title="research: Postgres performance vs current",
    assignee="researcher",
    body="Compare query latency, throughput, and scaling characteristics at our expected data volume (~500GB, 10k QPS peak). Sources: benchmark papers, public case studies, pgbench results if easy.",
)["task_id"]

t3 = kanban_create(
    title="synthesize migration recommendation",
    assignee="analyst",
    body="Read the findings from T1 (cost) and T2 (performance). Produce a 1-page recommendation with explicit trade-offs and a go/no-go call.",
    parents=[t1, t2],
)["task_id"]

t4 = kanban_create(
    title="draft decision memo",
    assignee="writer",
    body="Turn the analyst's recommendation into a 2-page memo for the CTO. Match the tone of previous decision memos in the team's knowledge base.",
    parents=[t3],
)["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`, then auto-promote to `ready`. No manual coordination needed; the dispatcher and dependency engine handle it.

### Step 4 — Complete your own task

If you were spawned as a task yourself (e.g. `planner` profile was assigned `T0: "investigate Postgres migration"`), mark it done with a summary of what you created:

```python
kanban_complete(
    summary="decomposed into T1-T4: 2 researchers parallel, 1 analyst on their outputs, 1 writer on the recommendation",
    metadata={
        "task_graph": {
            "T1": {"assignee": "researcher", "parents": []},
            "T2": {"assignee": "researcher", "parents": []},
            "T3": {"assignee": "analyst", "parents": ["T1", "T2"]},
            "T4": {"assignee": "writer", "parents": ["T3"]},
        },
    },
)
```

### Step 5 — Report back to the user

Tell them what you created in plain prose:

> I've queued 4 tasks:
> - **T1** (researcher): cost comparison
> - **T2** (researcher): performance comparison, in parallel with T1
> - **T3** (analyst): synthesizes T1 + T2 into a recommendation
> - **T4** (writer): turns T3 into a CTO memo
>
> The dispatcher will pick up T1 and T2 now. T3 starts when both finish. You'll get a gateway ping when T4 completes. Use the dashboard or `hermes kanban tail <id>` to follow along.

## Verifier cards gated on a parent discovery task

When Karell requests a verifier for a discovery or implementation phase, create it as a dependent child rather than a parallel task:

1. Preflight the requested verifier assignee with `hermes profile list`. Use the requested specialist when it exists; otherwise use `default`. Do not silently route it to the producer whose work it must independently verify.
2. Use `--parent <discovery-task-id>` so the verifier begins in `todo` and cannot run until the discovery task is `done`; do not merely mention the parent in the body.
3. Make the body self-contained: enumerate the exact rubric, require evidence from real inspected files/paths rather than reported claims, forbid implementation work, and constrain the terminal result to `PASS` or `REQUEST_CHANGES`. For `REQUEST_CHANGES`, require an exact comment on the parent or a linked correction card.
4. Preserve literal requirements when creating through the CLI. The create command accepts `--body`, `--priority`, and `--max-runtime`; use an argument array or small Python wrapper for long Unicode-rich bodies rather than shell interpolation. A created card body is not generally editable through the ordinary Kanban CLI, so re-show it immediately and correct a malformed newly-created card before reporting it.
5. Verify with `hermes kanban show <verifier-id> --json`: confirm title, assignee, `task.status`, and `parents`. Current show JSON may omit max runtime; retain successful creation output, or use safe read-only operational inspection when exact runtime confirmation is required.

## Common patterns

**Fan-out + fan-in (research → synthesize):** N `researcher` tasks with no parents, one `analyst` task with all of them as parents.

**Pipeline with gates:** `pm → backend-eng → reviewer`. Each stage's `parents=[previous_task]`. Reviewer blocks or completes; if reviewer blocks, the operator unblocks with feedback and respawns.

**Same-profile queue:** 50 tasks, all assigned to `translator`, no dependencies between them. Dispatcher serializes — translator processes them in priority order, accumulating experience in their own memory.

### Priority cohorts for intake vs. production

The dispatcher sorts numeric priority **descending**. Use an explicit priority at task creation for heterogeneous queues; changing a card's status is not a substitute for correct rank.

For Karell's current content policy:

- Research/intake cards: `-10` (low)
- Direct video-intake handoffs: `75`
- SCRIPT/video-production package cards: `100`

Patch the creator scripts/cron paths so future cards inherit the policy. To reprioritize an existing cohort, use the supported Kanban dashboard bulk-update surface (`POST /api/plugins/kanban/tasks/bulk` with `{ids, priority}`) or its authenticated UI equivalent — **never raw SQLite writes**. Scope the cohort by live status/assignee/title first, then verify targeted count, zero per-card failures, unchanged status, `reprioritized` audit events, and SQLite integrity. If a deliberately parked cohort is released, bulk-transition only that cohort from `scheduled` to `ready`; retain priority so production work remains ahead of intake.

**Human-in-the-loop:** Any task can `kanban_block()` to wait for input. Dispatcher respawns after `/unblock`. The comment thread carries the full context.

## User Preferences

- **Keep Kanban/automation planning terse and action-shaped** — Karell does not want “War & Peace” explanations. For approval/design questions, lead with the recommendation, 2–5 clear next steps, and the exact approval phrase/options. Avoid exhaustive branch dumps unless he explicitly asks for the full graph or trade-off analysis.
- **Capability questions are not execution authorization** — when Karell asks “can you…?” or “would it be possible to…?”, answer capability and ask whether he wants it done before creating files, credentials, cron jobs, boards, integrations, or other artifacts. Treat only direct imperatives like “do it”, “set it up”, “send it”, “create…”, “run…”, or “please find/get…” as action authorization.
- **Kanban incident answers must stay evidence-led and non-repetitive.** Once Karell has explicitly acknowledged generic external-writer or storage caveats, do not repeat them as boilerplate. Lead with what the logs/source actually establish, what they rule out, and the next discriminating source path or test. For timestamp overlays, direct-write path mapping, and the single-write-token option, use `references/kanban-sqlite-incident-analysis.md`.
- **For complex creator/product/community builds, keep Karell on one active item at a time** — use Kanban cards/dependencies to preserve the whole workflow, but do not make the user juggle website, forms, DNS, payment, curriculum, community rituals, Skool pinned posts, Q&A loops, and review decisions simultaneously. Park future human tasks as blocked/gated cards with exact handoff triggers and clear handoff requirements. When reporting next steps, give the single next user action unless Karell asks for the full graph. For user-only work that cannot be handled as a simple chat question, create Google Tasks instead of dumping a long to-do list in chat; keep simple questions/approvals in chat.
- **For product/package outcome sets, create durable artifacts before routing cards** — when an interview produces multiple named outcomes (premium package, GPT instructions, Skool post, one-page summary, etc.), first create/verify the Google Docs or other source artifacts in the right folder with a consistent prefix. Then create one Kanban card per outcome, with the same prefix, the exact artifact URL in the body, the shared folder URL, and acceptance criteria. This keeps the board tied to real deliverables instead of abstract todo cards.
- **Karell prefers in-conversation execution for one-off tasks** — don't push one-off tasks to Kanban workers or suggest delegation when the task is simple enough to do directly. Reserve Kanban for multi-step autonomous background work.
- **Ask before creating new Kanban boards** — even when a dedicated board would isolate a batch nicely, get explicit clearance from Karell first. If not cleared, use the current/default board or ask a concise confirmation question before `hermes kanban boards create` / board-scoped task creation.
- **If you say a stage is “underway” on Kanban, make it visible on the active board** — do not rely on a completed worker task as proof of underway work if the user expects to see an open card. For phase gates, create or maintain a visible review/triage/checkpoint task that points to the completed artifact and blocks the next stage until approval.
- **Review means human approval in Karell’s mental model** — if the UI has a Review column, do not casually park approval-required content work in `Blocked` without explaining the limitation. For cards like Tone docs, scripts, thumbnails, and other artifacts Karell must approve, make the board/comment semantics say `Karell Review` / `Human Review` / `approval required`. If the current backend only offers sticky human handoff through `kanban_block`, phrase it as “blocked for Karell review,” not “blocked because failed,” and consider a follow-up UX fix instead of treating the Review column as irrelevant.
- **Respect explicit no-review instructions** — when Karell says not to block cards for his review unless something is needed from him, encode that in every child card and do not let workers use `review-required` as a default completion gate. For implementation/deployment cards, workers should run verification and complete the card themselves. If a worker blocks only for generic human review despite that instruction, re-run the smallest verification yourself, complete the card with `human_review_not_required_by_user`, and continue the dependency chain.
- **When Karell explicitly asks Kanban to “make it all happen,” create the full dependency chain and define the real final readiness gate.** For code/repo/device workflows, the last card should not be “push completed” if Karell expects to load/run it locally. Encode downstream dependencies such as inspect → implement → push/verify remote HEAD → pull/build on target machine → clean checkout/build succeeded. Only report the workflow done when the final card’s completion criteria match the user’s stated ready state (for example: repo updated, target machine at the same commit, local tree clean, `xcodebuild` passed).
- **One-release autonomous backfills require an explicit execution contract.** When Karell says that a single “release it” should complete a large historical/batch recovery, the root card must state: the durable system of record versus Kanban’s control-plane role; source-manifest and idempotency requirements; the atomic `0..N` admission rule; reject/quarantine behavior that does not create a generic human-review stop; a bounded shard size; required child-card priority inherited from the root (use `-10` for research intake unless he says otherwise); and a final verifier dependent on all shards. The root may complete only after it has created and verified the graph; the final verifier owns the truthful terminal receipt. Do not create the finalizer as a child of the root if root completion would gate it incorrectly.

### Manifest-indexed backfills: freeze range semantics before fan-out

For a shard graph driven by a frozen manifest, make the index convention executable before creating or dispatching the fleet:

1. Declare whether ordinals are zero-based or one-based in the root and every child card. Compute each child range from one canonical formula; do not hand-type both a human brief label and runner `--start-ordinal`/`--end-ordinal` range.
2. Generate and verify a coverage matrix before dispatch: each manifest ordinal `0..N-1` appears exactly once; every child has at most the agreed shard size; and no range is outside bounds. Include the literal source keys in the generated card body only after matching them to the same computed endpoints.
3. The worker must record the literal executed manifest ordinal range in its completion receipt. The final verifier must compare actual receipt `manifest_ordinal` values—not card titles or worker prose—against the frozen manifest and fail on any gap, overlap, or out-of-range receipt.
4. If an off-by-one defect is discovered after writes begin, immediately contain future fan-out through official dependency/status operations, preserve immutable receipts and mappings, and create one linked reconciliation card. It must audit coverage, process only genuinely missing source entries with hash verification, and add explicit overrides before any shard resumes. Never delete or overwrite receipts/mappings merely to make card labels look consistent.

## Pitfalls

**Verifying whether a requested card batch actually got created.** If a prior session planned Kanban cards but hit a setup/DB/CLI failure mid-creation, do not infer creation from the conversation plan or from a later related external artifact. Verify the live board directly, including archived rows, with broad title/body searches for the distinctive card names. Also check session history around the attempted creation to identify the exact failure point. Report external artifacts separately: for example, an n8n workflow may exist even when the requested Kanban cards were never inserted. If the DB was corrupt and later repaired, search the repaired board plus archived rows before saying “not found.”

**Cards are plans, not guarantees.** When Karell asks whether a future operational guarantee is now true (for example “will MariaDB always be up to date within 7 days?”), distinguish clearly between: cards created, cards dispatched/running, cards completed, external workflow active, and actual verified production behavior. Do not let a dependency graph sound like an implemented SLA. If the final guarantee depends on a scheduled automation, verify that the relevant root card is done, the workflow/cron is active, schedule node enabled, and at least one manual or scheduled run has passed before saying “yes.” If only cards exist, answer “planned, not active yet,” and name the exact missing card/workflow activation gate.

**Mid-run requirement or architecture changes.** A comment added to a running card is durable audit context, but it is not proof that the already-oriented worker will re-read it before completing. When Karell materially changes deployment topology, destructive scope, source of truth, or a final acceptance gate while the card is running:

1. Inspect the live card and run state first.
2. Add one concise `FINAL ... OVERRIDE` comment that explicitly supersedes earlier contradictory comments and states the complete new boundary.
3. If the worker is already implementing or verifying the old architecture, reclaim the same card so it cannot complete against stale acceptance criteria.
4. Let the dispatcher start a fresh run on the same card; re-show it and verify the old run is `reclaimed`, the new run is `running`/`ready`, and the final override is present.
5. Apply the same override to dependent cards before they promote.

Do not stack vague corrections such as “actually, only the pages” and expect a worker to reconstruct the final design. State ownership for UI, API/backend, database/state, scheduler, collectors, and brain explicitly. Preserve useful prior work in the shared workspace, but require the new run to verify the final topology rather than accepting stale smoke-test evidence.

**Answering “what’s up with this card?”** Inspect the card (`kanban show <id>`) and give a concise operational summary: title, current status, blocker or next gate, important artifacts/files, verification already run, and parent/child dependency state. If the card is blocked with `review-required`, say it is waiting for human approval rather than implying failure. Do not dump the full event log unless asked.

**Superseded duplicate cards.** If live inspection shows a blocked card’s actual work was already completed through a parallel/replacement card, identify it as a stale duplicate rather than presenting the historical blocker as active. When Karell explicitly approves cleanup, preserve the audit trail: add a concise comment naming the completing replacement card and its output, archive the duplicate with `hermes kanban archive <task_id>`, then re-show it and verify `status: archived`. Prefer archival over hard deletion when the card remains in a dependency chain; hard deletion requires deliberate link/graph cleanup.

If the failure is a startup/setup issue that has a deterministic recovery path — especially `Unknown skill(s): <name>` for a specialist profile — repair it immediately instead of merely explaining it. Copy/install the missing local skill into the target profile, smoke-test the exact forced skill list under that profile, comment the repair, unblock/requeue the same card, run one bounded dispatch when appropriate, and report the live status. Offering the user “option 1 or 2” here is too passive; Karell expects the agent to apply the obvious safe recovery.

If the worker log shows `Error: Unknown skill(s): <name>`, do not merely present “install/copy the skill” as an option. Treat it as recoverable profile setup: find the skill in the default or trusted local profile, copy it into the assignee profile preserving category path, smoke-test the assignee with the forced skill list, add a recovery comment, unblock/requeue, and run one bounded dispatcher pass. Only ask the user if the skill truly does not exist locally or the intended replacement is ambiguous.

If the question comes indirectly from another agent/profile or only supplies a bare task id, do a forensic pass instead of trusting the visible block reason alone. Use the live card, `/home/karell/.hermes/kanban/logs/<id>.log`, session search, generated run JSON, cron/PM monitor output, and any mapped external source of truth. Then separate obsolete blockers from the latest persisted blocker. For example, a card may first fail on script length, then later be blocked because a ClickUp Script field points to a Google Doc that now returns 404; report the current missing/inaccessible doc as the real problem and mention the old issue only if it explains prior state.

**Answering “what does this card need?”** When Karell asks what a specific Kanban card needs, inspect the card (`kanban show <id>`) and answer with only the actionable blocker/gate, not the full audit trail. If the card is blocked with `review-required`, say it needs human/code approval and list only the minimum changed files/verification facts needed for the approval decision. Do not re-explain the whole pipeline unless asked.

If the card is a root/PM coordinator card blocked on child work, verify every child it names before echoing the block reason. A root card can retain a stale blocker after all child cards and final-readiness gates are done. If all children are done and final readiness passed, answer that the root needs manual completion/cleanup, not more execution. If Karell asks whether to move it to done, complete it with a result summarizing child ids, final-readiness evidence, and that the old blocker was stale.

When Karell says he moved a specific card to ready and wants to “see what happens,” do not assume the dispatcher picked that card. Run a bounded dispatch, then inspect the target card itself and the spawned task id. Report whether the target dispatched, re-blocked, or another ready card was spawned first. If a capacity-aware dispatch reports `Spawned: 0`, do not immediately call Kanban broken: inspect `kanban show <id>`, `kanban runs <id>`, `kanban list --status running --json`, and `kanban diagnostics --json`. The card may simply be waiting behind active workers or the gateway dispatcher tick; distinguish “not spawned this pass” from “blocked/crashed.”

**Coordinator-capacity deadlock recovery.** A long-running root orchestrator assigned to the same profile as one of its serialized implementation children can consume that profile’s only worker slot indefinitely: the child is `ready`, dispatch says `Spawned: 0`, and no external dependency is actually blocking it. Confirm this with the child’s `ready` state plus the root’s active run and profile concurrency. Do not complete the root merely to free capacity—it must monitor terminal child outcomes. Reassign the ready implementation child to an available, capable worker profile, add a concise recovery comment carrying any verified local prerequisite invocation, then bounded-dispatch and re-show the child to confirm it is `running`. For toolchain-related blockers, first look for an already-present compatible toolchain/cache and provide its invocation path before approving or downloading another copy; record the reusable invocation, not a transient missing-PATH symptom.

### Root coordinator continuations while children are active

A continuation/judge prompt can arrive while the root coordinator and a serialized child both remain `running`. Do not manufacture a root terminal state merely to satisfy the prompt: the root acceptance contract still requires terminal child outcomes. Instead:

1. Inspect the active child and its successor/dependency state; confirm the worker PID/run is live and distinguish `todo` (dependency-gated) from a stranded `ready` card.
2. Perform a non-conflicting concrete check in the shared checkout (for example, the current test suite, clean `git status`, or commit/remote evidence). Do not edit files the child is actively writing. For database/state-machine work, also read negative tests critically: a rejection fixture must satisfy every unrelated required field/foreign key so it exercises the named invariant rather than failing for an accidental prerequisite. Treat skipped integration tests as **not executed**, never as passing evidence merely because the command exits 0.
3. Record a concise Kanban comment with the observed commit/test evidence and next gate. Re-show the successor after a parent completes so automatic promotion is verified rather than assumed.
4. If local verification itself produces disposable build outputs, remove only those generated artifacts before yielding the shared checkout; never alter the child's source changes.
5. Keep the root `running` until all required cards are terminal. `kanban_complete` is only for the aggregate receipt; `kanban_block` is only for a real external dependency/decision, not ordinary child progress. In particular, do not block the root merely because an active child has reached a later integration prerequisite (such as a real database endpoint) while that child still owns source delivery and verification.
6. If a Kanban lifecycle tool refuses a root-state mutation because another active run owns the lease, treat that refusal as claim contention, not permission to force a terminal state. Re-show the root and active child; if their worker PIDs/runs are live, add one concise evidence-and-next-gate comment for the owner and stop retrying lifecycle mutations. Do not work around it with raw DB or a competing CLI mutation; the active owner remains responsible for its eventual block/complete action.

### Sequential completion notifications. When a worker completion event says “check the result or decide the next step,” first inspect the completed card, its concrete artifacts/verification evidence, and the live ready/running queue. Accept only when the stated gates actually pass. If a same-assignee queue has no running card and a next card is ready, run one bounded dispatch and re-show the intended successor. **Use a capacity-aware `--max`: the CLI interprets it as the total in-flight cap, not “spawn this many.”** Read the live `kanban.max_in_progress` value and pass that (or a larger verified cap); `--max 1` will correctly no-op whenever any unrelated card is already running. If a dispatch reports no spawn, inspect the target card, live running count, and configured caps before calling it stuck. The gateway may promote/claim the successor between those commands: `Spawned: 0` plus a `running` successor means it is already underway, not a dispatch failure. Report the observed next-card state precisely; do not claim you dispatched it unless the dispatch output actually spawned it. Keep the notification reply to one compact verification summary and the real next queue state.

### Completion-triggered loop continuation

For a long-running project that has an existing periodic loop, support immediate continuation only through an explicit, scoped completion trigger—not by polling more aggressively or starting another dispatcher. Hermes emits `kanban_task_completed` only after the terminal state is durable and dependent readiness is recomputed. A user plugin may observe that event and request the **existing** project cron job through the official cron trigger surface.

Required guardrails:

1. Opt in per project/card with an unambiguous job ID and project marker; completion of unrelated cards is ignored.
2. Trigger only after the card's own acceptance receipt is complete. A `done` label without remote/test/cleanup evidence is not an acceleration signal.
3. Coalesce duplicates: one in-flight or recently requested continuation per loop. Repeated lifecycle events must have no additional effect.
4. Keep the normal periodic job enabled as a fallback. The trigger reduces latency; it must not become a single point of failure.
5. Record every accepted/suppressed trigger with card ID, loop job ID, and reason. If the hook fails, log it and rely on the periodic run; never crash the card worker or mutate Kanban state outside official APIs.
6. Verify the installed path with a controlled eligible completion and read back the cron execution record. A marker or manual cron fire alone is not proof that the event path works.

### Root-project terminal notification and remote-machine handoff

When Karell asks for one Telegram signal after a fan-out implementation graph is fully executed, subscribe the **root orchestrator card** (not every child) with `hermes kanban notify-subscribe <root-id> --platform telegram --chat-id <origin-chat-id> --notifier-profile default`. Verify it with `notify-list`. The root card body must require its worker to remain non-terminal until every child is terminal, then complete itself with a truthful aggregate `success` or `not successful` receipt. Do not make the root a parent of its children: that would dependency-gate them and deadlock the notification.

If Karell says he will resume development on another machine after the graph runs, immediately add one concise `FINAL HANDOFF OVERRIDE` comment to the live root card. State the named target, the authoritative handoff surface (normally the GitHub remote), and the final receipt required: verified remote branch/commit, exact pull/setup/test commands for the target, and any local prerequisites. Re-show the root to verify the comment landed. Do not rely on the originating worker's local workspace as a handoff artifact.

**Approving blocked review cards.**

If Karell says “approve <task_id>” but the card's latest block reason is a validation/runtime failure rather than `review-required`, do **not** complete it. Treat it as a recovery request: explain briefly that it is not an approval gate, reassign to the right specialist if needed, add a recovery note, and promote/requeue it for fixup.

**In-conversation implementation cards must be blocked atomically at creation.** When Karell explicitly asks for a Kanban card but Overmind will execute the work directly in the active conversation, create the card with `--initial-status blocked` and an audit note such as “active in-conversation implementation; do not dispatch.” Do not create it as `ready` and then block it in a second command: the dispatcher can claim and spawn a duplicate worker in the gap. If a worker was already spawned, reclaim/terminate it, inspect the shared workspace for concurrent edits, preserve any useful test-first work only after review, and verify the card has no live worker before continuing. Avoid `--initial-status running` for this audit pattern; `running` implies a worker claim and may be normalized back to dispatchable state.

**Reassignment vs. new task.** If a reviewer blocks with "needs changes," create a NEW task linked from the reviewer's task — don't re-run the same task with a stern look. The new task is assigned to the original implementer profile.

**No orphaned technical blockers.** A card that has delivered its intended artifacts but is blocked by a separate repair (for example, a Drive/Docs index-write conflict) must not sit waiting for vague human review or inaction. When diagnosing it, inspect parents, children, and linked cards for a concrete remediation owner. If none exists, call it an **orphaned blocker**, not a user-review gate. The correct graph is: `repair card → verify external state → resume/complete affected card`. Do not silently mark work complete when the missing sync is a durable source-of-truth gap. If Karell explicitly asks to create or repair it, create one bounded recovery card with the external identifier/error, a non-destructive probe first, acceptance evidence, and an explicit parent/child link; otherwise report the absent recovery path concisely.

### Reproducible runtime capsules for implementation cards

For cards that need a compiler, database, container, or integration suite, put a **runnable verification capsule** in the card body before dispatching: the canonical command, required environment variables, test-service start/stop command, and a deterministic fallback when the preferred runtime is unavailable. Prefer repo-owned scripts/Compose over assumptions about a worker's `PATH` or daemon access. A worker that cannot use the preferred runtime must try the documented fallback and record its result before blocking; a missing global binary alone is not a valid blocker.

**Comments are not a runtime capsule.** A fresh/reassigned worker may not re-read an older recovery comment before it blocks again. When a known local toolchain or disposable integration runtime is required, put its exact invocation (for example a PATH prefix), test URL/start-stop recipe, and secret-safe credential mechanism in the original card body or a linked repo-owned support file. On a false setup block, repeat that capsule in the requeue instruction, then re-show the new run and verify it consumed the fallback. If a shared checkout contains incomplete/untracked files from a duplicate worker, treat resulting compile failures as contamination, not as acceptance evidence; contain the duplicate and preserve/quarantine its artifacts before the authoritative verification run.

Keep production deployment separate from development verification. A Compose database used for tests is a disposable development dependency; it does not imply a production host, a production deployment, or permission to create one. Do not assume a home lab is a production target.

### Clean-worktree final integration and remote delivery

When a serialized shared checkout contains protected uncommitted work from a prior/duplicate worker, the final verifier must **not** reset it, stage it, or use it as proof of the assembled delivery. Instead:

1. Create or reuse an isolated clean worktree/clone at the authenticated remote base SHA.
2. Replay only the reviewed scoped commits into that isolated worktree; inspect the resulting diff before testing.
3. Run the complete final suite there, including any disposable integration runtime.
4. Push only from the clean worktree using the secret-safe one-shot credential path; verify remote SHA with both fetch and authenticated remote lookup.
5. Leave the contaminated shared checkout untouched and tell downstream workers to treat it as non-authoritative until separately reconciled.

This preserves concurrent artifacts while making final test and delivery evidence reproducible. The final handoff should name the **remote SHA**, not the stale shared-checkout HEAD.

### Circuit-breaker contract for Karell

Karell's policy is strict: **`blocked` means a concrete issue the agent cannot presently fix.** It is never a generic review state, a missing-PATH diagnosis, a safety hold, or a permanent wait for him unless he explicitly requests human gating.

**Contract-invalidating discrepancies are not blocks.** When a reproducible live probe proves a linked work order has a false premise, contradictory acceptance/non-goals, incompatible scope, or is superseded by current product/specification state, record one `[contract-invalidated:<fingerprint>]` receipt, close the Issue as `not_planned`, archive its execution card, and return the project loop to a fresh audit. Do not requeue or amend the invalidated card, and do not create a presumed replacement before that audit selects a new bounded discrepancy. An unchanged invalidation fingerprint must be quiet on later loop ticks.

For every card that might need a circuit breaker, encode and verify a recovery path before blocking: bounded retry/reclaim, an alternate local tool/runtime, credential/profile repair, dependency cleanup, or a newly-created linked remediation card. Put the exact command/path/owner in a concise card comment, then use `kanban unblock` (for a terminal blocked run) or `kanban reclaim` (for a live run) and re-show the card. If a coordinator safety hold is needed while repairing a runaway graph, it must be temporary and have an agent-operated exit condition; do not leave it as a user-facing blocker. In status reports, distinguish a dependency-gated `todo` from a true block and lead with whether Karell needs to do anything.

### Pending-card audits and date-deferred backlogs

When Karell asks to check all pending cards or prevent pointless blockers, audit the **entire nonterminal board**, not only the named card. Classify `running`, `ready`, `todo`, `scheduled`, and `blocked` separately:

1. **Blocked:** inspect the concrete reason, latest run, comments, and links. A true external repair or decision is valid; a generic `review-required` gate is not valid when the card explicitly says no generic human review. Independently repeat the smallest stated verification and inspect the live integration/config if relevant, then complete it with an audit receipt instead of leaving it blocked.
2. **Todo:** inspect every parent. It is valid only while a parent is nonterminal; otherwise promote/dispatch it.
3. **Ready:** verify the assignee exists and distinguish a card queued behind a live per-profile/global concurrency cap from a stranded card.
4. **Running:** check current run/heartbeat state. A child in `todo` is not by itself a blocker for its parent.
5. **Scheduled:** distinguish ordinary queue intake from a timed deferral. `scheduled` alone is not an automatic release mechanism.

For a **date-deferred** backlog, prose such as “release after July 22” is insufficient. The deployed due-card unblocker scans only cards whose status is `scheduled` **and** whose comments/events contain `UNBLOCK_AFTER_UTC=<ISO-8601 UTC timestamp>`. Use the official scheduler state for every card in the cohort:

```text
hermes kanban schedule <task-id> \
  "DEFERRED_... Do not start before <local date/time>. UNBLOCK_AFTER_UTC=<timestamp>."
```

- Apply the marker to **every** deferred card, not just a sample.
- If an early worker claim re-blocks a deferred card, re-run `kanban schedule` with the same marker; `blocked` cards are invisible to the due-card unblocker.
- **Premature-release forensic pattern:** when a deferred cohort appears as `blocked`, inspect several cards’ event timelines. The signature `scheduled → unblocked → claimed/spawned → worker blocked` means the cards were released early and workers correctly refused the work; it is not a research, credential, or human-review failure. State this plainly to Karell: the intended state is `scheduled`, not `blocked`, and nothing is required from him. Identify the anomalous release action separately from the worker’s protective block. Do not blame the due-unblocker without inspecting its deployed marker check: it must only release `scheduled` cards with `UNBLOCK_AFTER_UTC <= now`. Restore every affected card with `kanban schedule` using the same marker, then run its `--report` mode to verify the cohort is `pending` until due.
- Verify the exact deployed due-unblocker with `--report`: every deferred card should appear under `pending` before its time, with no errors; after the date it must appear under `unblocked_due` and receive a bounded dispatch pass.
- For bulk recovery, use official `hermes kanban schedule` commands/API and re-list status/marker counts afterward. Never write task status/events directly in SQLite.

For Karell, report a compact table: count audited, cards repaired, legitimate remaining blockers with their exact decision, dependency-gated todos, and queued/running work. Lead with “nothing needed from you” unless a real decision remains.

**Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first. Mixing them up demotes the wrong task to `todo`.

**Shell quoting for card titles/bodies.** Do not create Kanban cards through `eval` or one big shell string when the title/body contains `$`, backticks, quotes, URLs, or Markdown. Shell expansion can silently corrupt user text — for example `$20k/month` can become `0k/month`. Prefer an argument-array call (`subprocess.run([...])`), a CLI option that reads body from a file if available, or a small Python wrapper. After creation, inspect `kanban show <id>` and verify the title/body preserved the important literal text before reporting success.

**Don't pre-create the whole graph if the shape depends on intermediate findings.** If T3's structure depends on what T1 and T2 find, let T3 exist as a "synthesize findings" task whose own first step is to read parent handoffs and plan the rest. Orchestrators can spawn orchestrators.

**Tenant inheritance.** If `HERMES_TENANT` is set in your env, pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create` call so child tasks stay in the same namespace.

**External task intake should exhaust the configured automation path before declaring a blocker.** When Karell gives a direct external task ID (for example a ClickUp task) and asks for a Kanban card/update, first inspect the external task through the configured integration/API/MCP path. Browser login pages and local approval prompts are not enough to call the work blocked if a normal trusted automation surface exists. For deterministic read/update/card-create operations, a no-agent script run through the scheduler can be an acceptable execution surface when the interactive session cannot run local code directly. Always verify the external field and the created Kanban row before reporting success.

**External-source rollback is not Kanban cleanup.** If a Kanban card represents work against an external system (e.g. a ClickUp task) and the external task must be moved back upstream, do that external status change first and verify it — but do **not** imply the Kanban cards were removed, archived, or resolved unless you actually archive/complete/unblock them. Report both states separately: external task status and Kanban card status. Ask before archiving duplicate/stale cards unless the user explicitly requested cleanup.

**Do not accept a worker's credential-blocker at face value when the card is recoverable.** If a card is blocked on GitHub push/auth, API auth, Codex auth, or similar execution credentials, verify the standard token sources yourself before telling Karell it needs human credential work. For GitHub cards, load `github-operations` and check configured env/token sources (without printing secrets) such as `/home/karell/.hermes/.env` `GITHUB_TOKEN`; retry with token-only push patterns before leaving the card blocked. For `openai-codex` worker crashes, remember the active/default conversation can have valid Codex auth while the specialist profile has stale/exhausted profile-local auth. Check both default and target profile auth stores, reset provider exhaustion, copy/import the valid `openai-codex` provider state into the target profile when appropriate, and when the failure was `Codex token refresh failed: Invalid refresh token` proactively rotate/refresh the OAuth tokens in **both** the default and target profile auth stores before declaring auth repaired; a smoke test can pass on a still-near-expiry access token while the next worker refresh fails if the stored refresh token is stale. Then smoke-test the exact target profile with `/opt/hermes/.venv/bin/hermes -p <profile> chat --provider openai-codex -q 'Reply with exactly: ok' -Q --toolsets safe` before unblocking. Add a recovery comment, unblock, and verify the card reaches `running` or records a fresh blocker. If `hermes kanban dispatch --json` returns no spawns after unblocking, check configured `kanban.max_spawn` / `kanban.max_in_progress` caps and existing running workers before assuming the card is still broken; `max_spawn` is a live concurrency cap, and the JSON output may not make cap skips obvious. If recovery succeeds, complete/requeue with the verification evidence and remove the stale blocker from the user's next-action list.

**Blocked reason is not the whole audit.** When the user asks why external-backed Kanban cards are blocked, use the Kanban blocked reason as a lead, then verify the relevant external system fields before classifying. Example: Serious CTO writer cards may block with “Script field already contains a value”; to answer whether they are blocked due to existing script and tone, fetch the ClickUp task and inspect Script/Tone fields directly, then separate “Script only,” “Script + Tone,” and unrelated failures like factual-audit blocks. If the user then asks to reset/delete the blocking artifact, also inspect the external artifact store (e.g. the task's Drive `Directory` folder), because a failed worker may have created an unlinked artifact that is not present in the ClickUp field. Only unblock after the external field/artifact state has been verified.

**`todo` can mean an external pipeline is stalled, not merely Kanban is waiting.** If the user says cards/items are in `todo` and “aren't looking like they are about to move,” treat that as an intervention request, not a passive monitoring request. Do not only promote/reclaim/dispatch the Kanban rows. First map each card to its external system of record and the automation that is supposed to advance it (e.g. ClickUp status + custom fields + cron/script prompts). Verify the external task status/fields and the cron/script routing rules, then patch the durable automation path if the status transition is impossible or wrong. For Serious CTO pipeline work, this often means checking that ClickUp `Type` routing matches the intended stage path (for example, `Public / Short` should bypass feedback/AI-script stages when configured that way) and updating the Python processor plus cron prompt/skill docs together. If items are waiting for a scheduled processor (for example long-form tasks in `AI SCRIPT` waiting on `daily_ai_video_script_processor.py`), inspect the run conditions and, when safe, trigger a bounded manual run rather than telling Karell to wait for cron. After any manual run, verify the external task fields/status directly (not just the run log) before declaring movement. Report separately: Kanban card state, external task state, automation changes made, and any remaining items still awaiting a downstream worker.

Trello `SCTO - Research Intake` is a bounded decision/router surface, not cold storage. Visible lanes are `Review`, `Synthesis`, `Video`, `Newsletter`, `Research`, `Test`, `Knowledge`, and transition-only `Completed`. `Reference only`, `Keep Parked`, `Keep Review`, and `Abandon` outcomes stay in Drive/OKF or Trello archive rather than visible lanes. `Review` is only for a real Karell decision; named clusters use `Synthesis`; deterministic recommendations use the established router lanes; Business/Infrastructure/Strategic revisit material maps to bounded inert `Knowledge`. Successful router handling archives source cards after audit comments. Labels remain single-purpose hints, not topic tags.

**Research Intake volume governance.** The visible Trello board must remain a bounded decision-and-routing surface, not the durable research library. Before calling a large board a backlog, audit the live lane counts and cross-tab `Review type`, `Recommended move`, and `Actionability`; explicitly count cards that truly say `Manual review by Karell`. `Reference only`, `Keep Parked`, `Keep Review`, and `Abandon` should normally remain in Drive/index storage rather than becoming visible Review cards. Deterministic recommendations should bypass fake human review and route under the existing authorization policy. A redesign request is not cleanup authorization: present the target model and exact reversible cleanup first, then wait for Karell's approval. After approved cleanup, patch the producer and verify the board after another producer cycle so it cannot silently refill. See `references/trello-research-intake-volume-governance.md` for audit fields, WIP defaults, intake gates, and the safe recovery sequence. For full bulk-compaction procedure—including backup hashes, consumer pausing, central ingress gating, dry-run manifests, concurrent-arrival reconciliation, reversible list/card archival, and scheduler-path verification—use `references/trello-board-compaction-and-ingress-control.md`.

**Triage means parked, not permission to investigate.** Karell expects cards in `triage` to remain inert for later human decision unless he explicitly says to decompose, promote, execute, investigate now, or otherwise start work. Do not treat a triage card's body or “next action” text as authorization to create implementation cards or run workers. After creating a user-requested triage card, re-show it and verify it is still `triage`, has the intended assignee, and has no parent/child links. If an auto-decomposer/specifier promotes or decomposes it anyway, repair immediately: archive generated child cards, restore the root card to `triage`, clear dependency links, add an audit comment, and verify DB integrity/status before reporting. If asked to clean up a triage card that accidentally spawned work, restore the root card to `triage`, clear parent/child links, and remove generated child cards/artifacts rather than leaving them archived on the active board.

**Explicit “don’t do anything yet” holds.** When Karell wants work represented on Kanban but explicitly forbids starting it, create one root card atomically with `--initial-status blocked` rather than `--triage`: a triage specifier may promote/decompose it. The body must say `Karell hold: do not dispatch, inspect sources, create children, or write external state until explicitly released`, name the intended first *non-writing* deliverable, and use an idempotency key. Re-show the card and verify `status=blocked`, no run, and no children. Because gateway promotion can race a post-create read, re-check the event/run state before moving on; if it was promoted, immediately block it and verify the worker PID is cleared, no children remain, and the protected external count/state is unchanged. `blocked` is valid here because Karell explicitly requested the human gate; do not invent a generic review gate in other cases.

**Research recommendations are not execution authority.** Blind Research For Me cards and parked Trello research results are search/understand/categorize artifacts, even when the final decision says `Test` or `Build`. Do not let a researcher/orchestrator auto-spawn executable tests, implementation cards, Codex/Claude CLI experiments, branches, scripts, cron jobs, Google Tasks, ClickUp tasks, or external-system changes from research alone. A `Test` decision means “here is the proposed harness/scope/success metric for a future approved test,” not “run it now.” Current Trello routing uses `SCTO - Research Intake / Test` as an ingestion lane only; the silent cron `Trello Research Intake Test → Test Lab router` (`trello_test_lab_router_silent.sh`) moves those cards to `SCTO - Test Lab / Candidates`. `Candidates` is still quarantine/scoping, not execution approval. When Karell asks to move "new stuff" or clearly test-worthy Trello cards into the Test lane, use the conservative cleanup pattern in `references/trello-test-lane-cleanup.md`: match explicit body recommendations such as `Final decision: Test`, `Recommended move: Test`, or bounded `test/benchmark/spike/pilot` decision lines; do not move cards merely because a title contains `tested`/`benchmark`; leave `Completed` and `Abandon` untouched unless explicitly told otherwise; add audit comments and verify zero clear candidates remain outside `Test`. The current design direction is additive side-by-side testing where possible: supervised low-damage tests may create comparison artifacts beside the current workflow (e.g. extra thumbnail candidates for review) without overwriting, publishing, sending, deleting, or moving production state. Treat this as a design direction until an explicit execution policy is implemented. If a premature execution card already exists, narrow it back to research-only scope: comment the correction, reassign to the research profile if appropriate, unblock/requeue only for categorization/understanding work, and explicitly forbid runtime experiments until Karell or a human promotion lane authorizes them.

**Harness gap matters.** When a research item proposes evaluating agent/tooling behavior but there is no established harness for that class of experiment, do not improvise an operational smoke test inside Overmind/default. Record the missing harness as the next decision: what isolation, fixtures, credentials, success metrics, receipts, and human gates would be required before any execution is safe. Overmind can classify and design the harness; it should not become the ad-hoc harness.

**Live Kanban DB surgery is forbidden except through the safe repair wrapper.** Do not run `REINDEX`, `.recover`, `VACUUM`, direct SQLite writes, copy-over, or `rm kanban.db-wal/kanban.db-shm` against `/home/karell/.hermes/kanban.db` while gateway/dashboard/dispatchers/workers may be running. For ordinary task operations, use `hermes kanban ...` or Kanban tools. For read-only diagnostics, use `file:/home/karell/.hermes/kanban.db?mode=ro` where direct SQLite inspection is unavoidable. If integrity fails, first stop mutation sources/cron, then use `/home/karell/.hermes/scripts/kanban_repair_safe.sh --repair`, which stops services, backs up DB+WAL/SHM, repairs a copy, verifies `quick_check` and `integrity_check`, atomically swaps, and restarts services. Never let individual workers improvise DB repairs. See `references/kanban-sqlite-corruption-safe-repair.md` for the session-derived safe-repair pattern, health-check pause behavior, MariaDB/Postgres boundary, and the distinct blank-status logical-repair pattern.

**Logical Kanban row corruption is not the same as SQLite corruption.** If `quick_check` and `integrity_check` are `ok` but stats show a blank status bucket (`"": N`) or health checks report invalid assignees for completed work, classify it as logical row damage. Do not run physical repair just because the board looks wrong. First back up the DB/WAL/SHM, then inspect blank-status rows and their `task_runs`/`task_events`. If a blank row has a completed run, restore only task metadata from that history (`status='done'`, created/completed timestamps, result/summary, skills from the `created` event), clear stale claim/failure fields, and add an audit event/comment such as `logical_repair`. Re-run stats plus `quick_check`/`integrity_check`; verify the blank bucket is gone. If no completed run exists, do not invent completion — use normal Kanban recovery or ask.

For logical **SQL-dump** restores, treat dump parsing, constraint validation, artifact preservation, candidate construction, and notifier-replay prevention as separate gates. Use `references/logical-sql-dump-restoration-audit.md`; in particular, audit semicolons inside comments/literals correctly, never import a CREATE-TABLE dump into a live board, and start a restored board with both dispatcher and notifier disabled until explicit post-restore validation and cursor policy are complete.

**Runaway decomposition cleanup.** When Karell says a Kanban item “went wild” or asks to purge/reverse/delete associated cards, treat it as destructive cleanup authorization for that workflow, but still protect the database: back up `kanban.db` and the affected workspace first. Use official Kanban CLI/API paths where possible; if direct SQLite cleanup is unavoidable, stop mutation sources first or use the safe repair/maintenance window pattern above. Then identify the connected graph from `task_links`, stop any running worker PIDs for those cards, purge generated workspace files, delete comments/events/runs/attachments/links/tasks for generated cards, and leave only the intended root triage card with a concise cleanup comment.

**Post-delivery review remediation.** When an independent review finds a concrete defect after a card has committed or pushed, use `references/review-findings-after-delivery.md`. It covers preserving concurrent checkout work, forward-only migration remediation, executable regression evidence, and a separate verified corrective delivery.

**Prevent runaway decomposition before it starts.** For a predesigned, serialized implementation graph that shares a `dir:` checkout, create leaf implementation cards **without goal mode**. A goal-loop card can interpret a transient capability/credential/integration failure as a reason to auto-decompose, then create a second implementation graph whose children edit the same checkout and race the authoritative path. Reserve goal mode for genuine planning/coordinator work in a non-writing or isolated workspace; use normal cards plus explicit parent links for coding, verification, and delivery stages.

If this has already happened, archive status alone is not containment: an already-spawned worker can remain alive and continue creating files. Recover in this order:

1. Inspect the intended card, every generated descendant, their links/runs, and live worker PIDs; distinguish the authoritative chain from auto-created duplicates.
2. Reclaim active duplicate cards, then verify their worker PIDs have exited. If a stale worker remains alive after reclaim/archive, terminate that worker before touching the shared checkout.
3. Preserve unrelated/untracked work before cleanup (for example with a labelled Git stash or an external patch), then unlink duplicate parent/child edges from the authoritative chain and archive the duplicate cards.
4. Re-check the whole board for newly generated cards and live worker processes; a goal-loop may have spawned a second wave after the first audit.
5. Re-run the smallest real verification and remote-delivery check for the authoritative work, then complete only the authoritative card with the concrete evidence.

Do not leave a root coordinator blocked merely as a substitute for fixing an auto-decomposer fault. Either disable goal mode before its next dispatch or keep it non-dispatchable only while the concrete graph cleanup/reconfiguration is actively underway.

Do not stop at the first connected-graph cleanup. A triage root that was already decomposed can respawn a new wave with completely new task ids moments later, and those new cards may not be in the original graph you inspected. After cleanup, wait briefly and search the whole board by the workflow’s distinctive title/body terms (for example the root’s domain keywords), not just by the old ids. If new cards appear, kill their worker PIDs, delete their rows/links/runs/events/logs, and repeat until: only the intended root remains, its status is `triage`, it has no parent/child links, no matching generated cards exist anywhere on the board, no worker processes mention the deleted ids, and the shared workspace contains only intentional survivor files. If the workspace is shared by several runaway workflows, use logs/backups to identify artifacts; when Karell says “nuke/undo anything associated,” remove orphaned artifacts too rather than leaving stale deliverables that imply the work still exists.

Run `pragma integrity_check`; if an index warning appears after manual SQLite cleanup, `REINDEX` and verify again before reporting success. If CLI `archive --rm` leaves archived rows behind or creates ambiguity, use direct SQLite deletion only after a fresh backup, then verify zero rows across `tasks`, `task_links`, `task_comments`, `task_events`, `task_runs`, and `task_attachments` for all deleted ids.

**Archived-card retention cleanup.** To prevent one huge manual archive purge from making the dashboard sluggish, use a recurring maintenance job rather than waiting for 900+ archived cards. The safe pattern is: select only `status='archived'` cards whose latest explicit `task_events.kind='archived'` timestamp is older than the retention window (for example 14 days), skip rows with active claim/current run/worker pid, cap deletes per run, back up `/home/karell/.hermes/kanban.db` first, purge via `hermes kanban archive --rm` in batches, and run `quick_check`/`integrity_check` before and after. Do not use `created_at` as the retention cutoff; old cards can be archived recently and should survive until the archived retention window expires.

For user requests phrased like “delete all archived kanban cards over N days old up to M cards” or “same command,” treat it as direct destructive cleanup authorization for the same board/retention/cap pattern. Use a Python `sqlite3` script if the `sqlite3` CLI is unavailable: run `PRAGMA quick_check` and `PRAGMA integrity_check`, count candidates with `max(task_events.created_at) where kind='archived'`, then if `purge_count > 0` create a timestamped SQLite backup under `/home/karell/.hermes/kanban/backups/`, purge selected ids in chunks with `/opt/hermes/.venv/bin/hermes kanban archive --rm ...`, verify selected ids are gone, report remaining archived count, and re-run both PRAGMAs. Keep the final report terse: deleted count, cutoff, backup path, remaining archived, and verification. If no candidates are eligible, report `Deleted: 0` and verification; do not fabricate work or broaden the cutoff to make progress.

**Board name is not task type.** Do not infer that cards are KDP/book/product tasks just because they sit on a board named `serious-cto-kdp` or another legacy/misleading board slug. Verify the underlying external task/list/status/custom fields before naming the work type. If cards appear on the wrong board, say that explicitly and separate the board-location problem from the task-domain problem.

**Consolidating/deleting boards must include archived board directories.** `hermes kanban boards list` only shows active boards, but prior `boards rm` operations may have moved populated boards under `/home/karell/.hermes/kanban/boards/_archived/...`. When the user asks to consolidate all Kanban data into default, inspect every `/home/karell/.hermes/kanban/boards/**/kanban.db` (including `_archived`) and migrate tasks plus comments, events, links, runs, logs, and workspaces into `/home/karell/.hermes/kanban.db` + `/home/karell/.hermes/kanban/{logs,workspaces}` before deleting board directories. Preserve task IDs when there are no collisions, remap `task_runs.id` for `task_events.run_id`, update scratch `workspace_path`, and add a provenance event such as `consolidated_from_board`. Back up `/home/karell/.hermes/kanban.db` and `/home/karell/.hermes/kanban/boards` first. After migration, delete the whole `/home/karell/.hermes/kanban/boards` tree if the user explicitly asked to delete other boards; otherwise `boards rm --delete`/`boards list` can leave or recreate empty board DBs.

**Human review vs. Review column semantics.** The Kanban backend has historically overloaded `blocked` for worker-initiated human handoffs (`review-required: ...`), while the `review` status/column may be wired to automated review-agent workflows (for example code/PR review). `review` is a first-class built-in Hermes Kanban status/column, not a custom column; the current backend status set includes `triage`, `todo`, `scheduled`, `ready`, `running`, `blocked`, `review`, `done`, and `archived`, and the dashboard displays `review` alongside the other visible board columns. Karell reasonably expects a visible `Review` column to mean human approval, not “blocked/stuck.” When creating or managing approval-gated content work:

- Use wording that makes the human approval gate explicit (`Karell Review`, `Needs Karell Approval`, or `review-required`).
- If the tooling forces a `blocked` handoff for human input, say so plainly instead of pretending it is the same as `Review`.
- Do not leave approval cards looking like failures/stalls; add a clear comment with artifact URL, verification summary, and exact approval/revision ask.
- If creating a multi-card workflow, show the dependency graph first when asked, then create cards with parent links so downstream work cannot dispatch early.

**Approval-gate handling after Karell says “approved.”** Treat approval as permission to pass the human-review gate, not as a request for a full independent audit unless he asks for that. Before completing the card, re-run the worker’s stated verification commands or the smallest equivalent check, then complete the Kanban card with a concise summary: “Human review approved by Karell; verification X/Y passed; no production statuses moved” (when applicable). This usually promotes child cards automatically. If the promoted child stays `ready` and the user’s intent is to keep the MVP/pipeline moving, immediately run one capacity-aware dispatcher pass (`hermes kanban dispatch --max <current-global-cap>`) and verify the child is `running` or explain why it did not dispatch. If verification fails, do not complete; report the exact blocker and leave/re-block the card for fixup. Keep the reply brief: card id, done/blocked state, and current board counts.

**Finding the next MVP stuck card.** When Karell asks for the “next MVP stuck card,” inspect the active board for the MVP chain in dependency/status order, not just all blocked cards by creation order. Prefer the earliest blocked/review-required card whose parents are done; if none are blocked, report the next `ready`/`running` MVP card. For review-required PM MVP cards, summarize only: card id/title, the one decision needed, verification already run, durable artifact links (Drive folder/doc/PR) if relevant, and a recommendation. If Karell asks for a link to inspect an artifact, provide the direct Drive/GitHub URL immediately without re-explaining the card.

**ClickUp Books outline-to-manuscript routing.** When Karell asks to process open ClickUp Books tasks, treat it as a sequential external-system workflow, not a single generic writing card. For each book: inspect the ClickUp task through the configured integration/MCP/API path, use `task-interview` only for unknowns, create and verify an outline Google Doc linked to the ClickUp `Outline` field, then create a manuscript-generation Kanban card assigned to the appropriate producer/writer profile with skills `novel-writer` and `google-workspace`. The manuscript card must create/verify the final book Google Doc and update/re-read the ClickUp `Book URL` field before completion. Process one book to this handoff point before moving to the next open book.

**SCTO profile routing.** Assign Serious CTO content-pipeline execution/review cards to `scto-producer` rather than the general `default` profile when the work is about ClickUp Content Planning, Drive/Docs artifacts, Script/Tone/package generation, status routing, stuck-card diagnosis, or approval-gated SCTO handoffs. Keep `default` as Overmind/orchestrator for user-facing decisions and cross-domain routing.

**Cron/profile operating model.** Keep the default profile as the gateway/cron control tower unless there is a strong reason to split schedulers. Deterministic no-agent cron scripts should scan/update/log and create idempotent Kanban cards for judgment work; specialist profiles should normally execute those cards rather than run their own gateway bots or duplicate cron loops. Use routing like: `scto-producer` for SCTO content, `brand-deal-ops` for sponsor/deal work, and `finance-receivables` for invoices/payments. Add a small silent automation-health cron that reports only abnormalities: cron errors/delivery errors/overdue jobs, unexpected paused jobs, blocked/stuck/stale Kanban cards, and invalid assignees.

**Shared-board dispatcher ownership.** When profiles share one Kanban board, only the default/control-plane gateway should use `kanban.dispatch_in_gateway: true`; set it false on specialist profiles. Otherwise every gateway can claim the same ready work, including future-deferred cards. For the full cohort-repair and s6 restart procedure, see `references/shared-board-multi-gateway-dispatch-recovery.md`. For immediate cohort releases, recurring night-window gates, persistence requirements, and plain-English user phrasing, see `references/scheduled-windows-and-release-control.md`.

**Enabling dispatcher settings from a gateway conversation.** `kanban.dispatch_in_gateway` and concurrency settings are persisted with `hermes config set`, but a running gateway normally needs a restart before its periodic dispatcher rereads them. The gateway intentionally refuses self-restart when called from within its own process; do **not** bypass that guard by changing environment variables, killing the gateway, or scheduling a workaround restart. Instead: (1) persist and read back `dispatch_in_gateway`, `max_in_progress`, `max_spawn`, and `max_in_progress_per_profile`; (2) use one normal bounded `hermes kanban dispatch --max <global cap> --json` pass to prove the desired queue can start safely now; (3) verify the actual `running` card and each `skipped_per_profile_capped` result; and (4) tell the remote Telegram user that one `/restart` is required to activate continuous gateway dispatch. Do not invent a second cron/daemon dispatcher just to avoid the required gateway restart.

**Diagnosing “why is dispatch not ticking?”** Do not blame a card, capacity, or a presumed gateway bug without checking the runtime boundary. Inspect: (a) live board counts and a non-mutating `dispatch --dry-run`; (b) gateway PID/start time versus `config.yaml` mtime; (c) `HERMES_KANBAN_DISPATCH_IN_GATEWAY` in that process environment; and (d) the singleton `.dispatcher.lock` holder. In the installed source, `gateway/kanban_watchers.py::_kanban_dispatcher_watcher` reads `dispatch_in_gateway` once at boot and exits if it is false. Therefore, if the config was changed after the gateway started, there is no disabling env override, no competing lock holder, and dry-run finds an eligible card, the restart requirement is confirmed—not merely suspected. Cite the installed-source lines and upstream Kanban documentation when reporting that causal conclusion.

When all ready cards share one assignee, a global capacity of two does not authorize two workers: the per-profile cap correctly serializes that cohort. After a card completes, inspect its real completion receipt before a bounded next dispatch; only then advance the next eligible same-profile card.

**Superseded configuration/recovery cards.** A later explicit user policy overrides an older card body, even when the old card says it was permanently authorized. For example, if an older blocked card asks for a higher concurrency limit and Karell later sets a lower current cap, do not execute the stale target or leave a fake `needs_input` blocker. Read the current effective config, add one `FINAL POLICY OVERRIDE` comment naming the old and new values, then archive the obsolete card (rather than marking its unfulfilled original objective done) if it has no active run or dependency obligation. Re-show the archived card and current board counts; preserve the audit trail.

### Evaluating a second agent-control plane

A platform can be technically compatible with Hermes while still being a poor production addition if it duplicates task/issue state, scheduling, assignment, worker lifecycle, notifications, and recovery.

For Karell's Hermes Kanban setup, Kanban remains the source of truth and the default profile remains its sole dispatcher. Do **not** connect another writable task board or scheduler to the live workflow unless a one-way integration and explicit ownership boundary have been designed and verified. Two writable control planes create ambiguous state, duplicate dispatch, and broken recovery semantics.

A second platform may be evaluated in a disposable isolated workspace only. Promote it only when it owns a deliberately separate class of work (for example, a multi-machine coding fleet), or when it has a proven integration that preserves one declared source of truth. In a capability review, distinguish “the Hermes runtime works” from “the platform fits this orchestration architecture.”

For Trello `Synthesis` watchers, cron creates idempotent Kanban cards rather than synthesizing inline. Keep the source Trello card in `Synthesis` with a task-marker comment until the worker writes the decision brief and routes it. Score 1–2 archives to `Completed`, 3 uses `Review` only for a real Karell decision, and 4–5 routes to `Video`, `Newsletter`, `Knowledge`, `Research`, or `Test`. Do not recreate a visible `Working`, `Abandon`, `Strategy`, or `Infrastructure` storage lane.

**Kanban SQLite corruption / backend migration questions.** If Kanban reports repeated `Refusing to open corrupt kanban DB`, malformed SQLite errors, or recurring `REINDEX`/`.recover` repairs, do not lead with a container architecture or storage-migration plan. First inspect the live DB/process topology, then acquire the exact upstream Hermes source for the installed commit and trace the lock/WAL/repair code plus its history. Do not infer that multiple profile gateways are concurrent dispatchers without checking each profile's `dispatch_in_gateway` setting and process environment. Reproduce any suspected race only against a disposable `HERMES_HOME`, never the live board. For container-recreation-safe forensics, source-first diagnosis, single-dispatch ownership, persistent integrity guarding, candidate-only restore, and custom-image deployment, use `references/kanban-container-recreation-hardening.md`. Current Hermes Kanban is SQLite-backed; `HERMES_KANBAN_DB` is a SQLite file path, not a MariaDB/Postgres DSN, so moving Kanban to MariaDB/Postgres is a code change and local edits under `/opt/hermes` are discarded by a bare upstream container pull unless maintained as a fork/custom image. For the detailed SQLite backend limits, see `references/kanban-sqlite-corruption-and-backend-limits.md`. For evidence-led upstream issue review—especially current WAL false-positive and maintenance-owner risks—use `references/upstream-sqlite-corruption-triage.md`. Do not equate historical source fixes or a closed issue with a fully resolved corruption class; label conclusions as confirmed local evidence, installed-source evidence, upstream report, or reproduced cause.

**Reducing noisy Kanban monitoring in Telegram.** If Karell says general Hermes/Kanban monitoring messages are noisy, first inspect active notification subscriptions before changing cron schedules or worker behavior. Use `hermes kanban notify-list`; if there is a stale task subscription delivering event streams into the Telegram DM/topic, remove it with `hermes kanban notify-unsubscribe <task_id> --platform <platform> --chat-id <chat_id> [--thread-id <thread_id>]`, then verify `notify-list` is empty or only contains intentional subscriptions. Do not pause PM/health crons as the first move when the noise is actually a per-task event subscription.

**Remote/Gateway users may not have CLI access.** If the user is on Telegram or another gateway, do not tell them to use a local terminal as the primary path. Give slash-command equivalents:

```text
/kanban assign <task_id> default
/kanban dispatch --max <current-global-cap>
/kanban --board <board-slug> assign <task_id> default
/kanban --board <board-slug> dispatch --max <current-global-cap>
```

If the HTML Kanban UI lacks an Assign control, explain that assignment is still available through `/kanban assign` in the chat, or offer to perform the assignment yourself from the conversation.

**Noisy Kanban monitoring on gateway.** When Karell says Hermes/Kanban monitoring messages are too noisy, first separate durable cron/digest noise from per-task event subscriptions. Use `hermes kanban notify-list` to find task subscriptions in the current Telegram/DM source, inspect whether the subscribed task is still active, and remove stale/noisy subscriptions with `hermes kanban notify-unsubscribe <task_id> --platform <platform> --chat-id <chat_id> [--thread-id <thread_id>]` before changing cron schedules or disabling monitors. Verify `notify-list` is empty or only contains intentionally subscribed active tasks. Leave PM/automation health crons alone unless they are actually producing non-actionable output; they should report only abnormalities.

**Creating a visible card when normal Kanban helpers are unavailable.** Prefer the official Kanban CLI/API/tooling whenever available. If a gateway request is a direct imperative to create a card and the normal helper path is unavailable in the current execution context, use the canonical Kanban database only as a last-resort fallback, and keep the insert minimal and auditable:

1. Inspect the `tasks`, `task_events`, and `task_comments` schema first; do not assume columns.
2. Generate a collision-free `t_<8hex>` id.
3. Insert a `tasks` row with `status='ready'` for dispatchable work (or `triage` only when the user explicitly parks it), correct `assignee`, `created_by='user'`, `created_at`, `workspace_kind`, `workspace_path`, and JSON `skills` where relevant.
4. Create the scratch workspace directory if `workspace_kind='scratch'`.
5. Add a `task_events` row of kind `created` whose payload mirrors normal CLI creation metadata.
6. Add a concise `task_comments` row noting the user request/source.
7. Re-read the row plus event/comment counts before reporting success.

Do not use this fallback for graph/dependency-heavy work, destructive changes, or board consolidation; repair the official tooling or ask for the right execution surface instead.

**Google Workspace/content cards assigned to a non-default profile need auth and skill verification before handoff.** When creating a Kanban card that asks a specialist profile to read/write Google Docs or Drive, do not assume the active profile's OAuth token or the loaded profile's skill library is visible inside the worker profile. Include exact Doc IDs/URLs in the body, force-load `google-workspace` and the domain skills, and either verify that the target profile can authenticate and resolve those skills or add a clear recovery comment. The durable fix is profile-local Google Workspace auth/token setup and profile-local skill availability for that specialist profile; if the worker fails on auth or `Unknown skill(s)`, repair the profile setup, add a recovery comment, requeue the same card, and verify it dispatches instead of telling the user the doc work is underway.

## Recovering stuck workers

When a worker profile keeps crashing, hallucinating, or getting blocked by its own mistakes (usually: wrong model, missing skill, broken credential), the kanban dashboard flags the task with a ⚠ badge and opens a **Recovery** section in the drawer. Three primary actions:

1. **Reclaim** (or `hermes kanban reclaim <task_id>`) — abort the running worker immediately and reset the task to `ready`. The existing claim TTL is ~15 min; this is the fast path out.
2. **Reassign** (or `hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch the task to a different profile and let the dispatcher pick it up with a fresh worker.
3. **Change profile model** — the dashboard prints a copy-paste hint for `hermes -p <profile> model` since profile config lives on disk; edit it in a terminal, then Reclaim to retry with the new model.

### Tasks stuck in a non-dispatchable `pending` state

Sometimes the board can show work as stalled even though `stats` reports neither `todo`, `ready`, `running`, nor `blocked`; inspect the full JSON list and assignee counts before assuming there is nothing to recover. If tasks appear as `status: "pending"`, they are not dispatchable by the normal dispatcher, and `promote` may reject them because it only handles `todo`/`blocked`.

Recovery pattern:

1. Verify scope precisely: board slug, task ids, current status, assignee, claim fields, recent events/runs/logs.
2. Prefer normal recovery first (`reclaim`, `promote`, `unblock`, `reassign --reclaim`) when the status allows it.
3. If the task is truly in `pending` with no active claim/current run and normal CLI recovery refuses it, make a SQLite backup of that board DB before manual repair.
4. Minimal repair: set only the stuck tasks to `ready`, clear stale claim/current-run fields, reset consecutive failure count if needed, and append an audit event/comment explaining the manual recovery and pointing workers at any useful prior log/draft.
5. Immediately run `kanban dispatch --max N`, then verify `stats`, `list --status running --json`, and `diagnostics --json`.

Do not present this as completion of the underlying work. Report separate states: “cards requeued/dispatched” vs. “research/docs/code not yet complete.” If a worker log contains a partial artifact from the failed run, add a recovery comment so the next worker can reuse it instead of starting blind.

Hallucination warnings appear on tasks where a worker's `kanban_complete(created_cards=[...])` claim included card ids that don't exist or weren't created by the worker's profile (the gate blocks the completion), or where the free-form summary references `t_<hex>` ids that don't resolve (advisory prose scan, non-blocking). Both produce audit events that persist even after recovery actions — the trail stays for debugging.
