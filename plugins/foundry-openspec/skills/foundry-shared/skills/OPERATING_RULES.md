# Shared operating rules

Read these rules, [WORK_CONTRACT.md](../WORK_CONTRACT.md), [WORKFLOW.md](../docs/WORKFLOW.md), applicable target repository instructions, and current human-defined scope before applying a role skill.

Also read the [AI.Contract interface mapping](AI_CONTRACT_INTERFACE.md). Verify the deployed interface before using its operations; the mapping identifies a tested source candidate, not an installed service.

Apply [request routing](ROUTING.md) before selecting an entry point. Explicit current user scope comes first; otherwise retain verified project policy and the current stage. Missing native access never selects a fallback executor.

## Source and capability checks

1. Resolve AI.Contract project identity, its one repository binding, target branch, scope, current executable revision, resolved delivery policy, and actor authorization from authoritative sources.
2. Verify only the capabilities needed for the next operation against the connected service interface and behavior. A source README is not proof of deployment version or live access. Do not invent endpoints, tools, project IDs, evidence fields, or successful transitions.
3. Inspect current repository state and relevant code/tests before claiming facts. Preserve unrelated changes. Use existing authorized access rather than treating absence of one CLI as proof of inaccessible service.
4. If a prerequisite is absent, report: affected project/contract/attempt/revision, intended operation, observed evidence, missing capability or decision, next action/owner if known, and safe work completed. Persist a blocker only through a supported authorized operation; otherwise return it directly.
5. Preparation drafts are permitted when requested, but have no service identity, queue membership, reservation, or execution authority. Never claim publication or readiness was persisted.

## State and authority

AI.Contract alone owns live contracts, dependencies, claims, assignments, and evidence. GitHub issues are final historical references. Service-owned Markdown projections must not be edited directly.

For authorized work in AI.Contract and Context Foundry, the owner requires direct commits to main and no pull requests. Follow the repository's AGENTS.md delivery instructions and record history after delivery. This overrides earlier PR-based handoff examples.

Human scope bounds Architect authorship. Worker discretion covers routine implementation choices within scope. Coordinator integrates according to resolved delivery authority. QA independently verifies. None may bypass explicit approval requirements. QA accepted is not Done; Done requires integration and required successful post-integration checks.

Executable revision/digest and execution attempt are distinct from the service's contract-format version. Verify current assignment and revision before writes and evidence submission. Material changes require a new immutable revision and reassessment, preserving history. Reject stale authority; do not silently retarget an attempt.

## Isolation, recovery, and evidence

Use isolated worktrees/branches per attempt. A contract has one assigned Worker; declared shared-resource conflicts are excluded during execution. Integration is serialized into the target branch. Expiry never proves termination: resolve or stop the previous process before reassignment.

Record actual checks, outcomes, acceptance evidence, candidate identity, failures, skips, and limitations. Append evidence; do not overwrite past receipts. Reconcile uncertain mutations by idempotency/identity before retrying. If persistence fails, retain reportable evidence without treating it as accepted service state; pause the dependent transition and reconcile safely.

Separate QA actors from implementers, even if they share a GitHub login. The service/runtime must establish actor and attempt identity; do not infer independence from a role label alone.

## Repair and stop decisions

During authorized execution, diagnose and repair ordinary in-scope implementation, local setup and test failures by default, then rerun relevant verification within the current stage/cycle. No separate repair permission is required. Follow any stricter user stop policy and existing runtime/time/cycle limits. Audit-only and planning-only requests retain their boundaries.

A failed required check blocks the dependent submission, acceptance, delivery or completion transition until it is genuinely satisfied; keep that gate closed while repair proceeds. Preserve the failure evidence and criteria. Worker repairs product code; QA records findings independently and reviews each changed candidate afresh. Coordinator routes corrections and retains current ownership; no role gains another role's powers from a failure.

For uncertain launch, submission, push or other mutation outcomes, reconcile authoritative identity/state before retrying. Reuse the original operation identity for the same uncertain operation and honor durable intents, shared transport gates, cooldowns and stopped-process proofs. A timeout does not prove a write failed or a process stopped. A breaker may pause remote work while permitted local diagnosis continues.

After an unsuccessful attempt, use the observed result to choose a useful next diagnostic or correction. Repeated failure without new evidence or a plausible different approach triggers reassessment through the existing roles, not blind retries or an arbitrary correction-round limit. Reassess routine technical approaches within scope without another user approval; return material requirement/architecture changes to Architect through Coordinator. If no useful authorized next action remains, report the concrete blocker and attempts/evidence instead of claiming completion.

Stop affected writes/transitions when current authority is missing, expired or revoked, execution identity cannot be reconciled, or a required capability/prerequisite cannot be restored within existing permissions. Escalate a genuine unresolved product decision or missing authority precisely. At a runtime limit, return a truthful checkpoint with remaining work and safe resume conditions; do not extend the limit, launch an implicit replacement or start a successor from an incomplete cycle. After failed post-integration checks, preserve the actual delivered state, withhold Done and follow supported authorized recovery; rollback, destructive changes and deployment need their existing authority.

## Autonomous work selection

For discretionary audits and successor work, assess value against the approved goal before creating a contract. Identify a realistic trigger, concrete consequence, supporting evidence and uncertainty, exposure through supported workflows, credible misuse or operational conditions, and proportionate implementation/verification cost. Keep the assessment brief and qualitative; do not invent probabilities or precise effort estimates. Use bounded investigation when missing evidence can cheaply resolve the decision. A reproducer proves possibility; assess its practical relevance separately. Rare failures with severe consequences can justify action without observed incidents or an unsafe live reproduction.

Select material work whose expected benefit justifies its cost. During authorized execution, route it through Architect, Coordinator, Worker and independent QA under existing permissions, then continue without asking the user to approve routine prioritization. Leave low-value observations alone; do not automatically turn them into issues, backlog entries or successor contracts. Escalate only a genuine unresolved product decision or missing authority; report unavailable capabilities as concrete blockers.

Inspect primary workflows, known failures and operational friction first. Expand investigation when evidence supports a useful next question. There is no finding quota, queue-filling obligation or need to exhaust every hypothetical edge case. Stop discretionary expansion when no worthwhile in-scope outcome remains, and report that conclusion briefly without a new approval request. Reassess only when new evidence or authorized scope warrants it.

Keep this judgment separate from explicit requirements and active contracts. Required acceptance criteria, checks and independent QA still apply; do not waive failures, abandon assigned work, or claim the goal complete because remaining requirements seem low value. Return material contract changes through the existing reassessment process. An audit-only or planning-only request authorizes only that scope, regardless of a finding's impact.

## Shared GitHub circuit breaker

All GitHub access must respect the breaker for the affected connection across projects. Connection, authentication, rate-limit, and service failures trip it; ordinary request-specific errors remain local. While open, pause GitHub access and continue local work where possible. Do not bypass it through another CLI, API, or agent.

After cooldown a single coordinated probe may run; resume only on success, otherwise reopen. Human restoration uses the same shared state. If the runtime cannot enforce that shared gate, report the missing capability before claiming coordinated GitHub operation. Do not build a private per-agent substitute.

Do not infer success after an uncertain push, merge, or issue creation. Once access is restored, inspect authoritative remote state before retrying.

## Output

Return a concise summary naming project/contract/revision/attempt where available, actual stage, actions and evidence, limitations, and next owner/action. State whether records were persisted or remain drafts. Do not claim a live agent, schedule, lock, integration, or completed delivery based on instructions alone.
