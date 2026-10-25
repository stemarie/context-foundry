# Shared operating rules

Read these rules, [WORK_CONTRACT.md](../WORK_CONTRACT.md), [WORKFLOW.md](../docs/WORKFLOW.md), applicable target repository instructions, and current human-defined scope before applying a role skill.

Also read the [AI.Contract interface mapping](AI_CONTRACT_INTERFACE.md). Verify the deployed interface before using its operations; the mapping identifies a tested source candidate, not an installed service.

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

## Shared GitHub circuit breaker

All GitHub access must respect the breaker for the affected connection across projects. Connection, authentication, rate-limit, and service failures trip it; ordinary request-specific errors remain local. While open, pause GitHub access and continue local work where possible. Do not bypass it through another CLI, API, or agent.

After cooldown a single coordinated probe may run; resume only on success, otherwise reopen. Human restoration uses the same shared state. If the runtime cannot enforce that shared gate, report the missing capability before claiming coordinated GitHub operation. Do not build a private per-agent substitute.

Do not infer success after an uncertain push, merge, or issue creation. Once access is restored, inspect authoritative remote state before retrying.

## Output

Return a concise summary naming project/contract/revision/attempt where available, actual stage, actions and evidence, limitations, and next owner/action. State whether records were persisted or remain drafts. Do not claim a live agent, schedule, lock, integration, or completed delivery based on instructions alone.
