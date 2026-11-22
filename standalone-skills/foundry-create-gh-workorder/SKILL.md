---
name: foundry-create-gh-workorder
description: Turn a project goal, specification, bug, or next-step request into a bounded work order for a Codex agent, published as a GitHub issue in that project's repository. Use when asked to architect or define a unit of work, write a work contract, or create an executable development issue. Supports draft-only requests; does not implement or dispatch the work.
---

# GitHub Work Order Architect

Create one self-contained, executable unit of work. Use the project's GitHub issue as the work contract and handoff. Require no separate contract service, Hermes configuration, orchestration board, or agent-role infrastructure.

## Ground the work

1. Resolve the project repository from the user's request, current project, or verified Git remote. Never default to a repository from an unrelated conversation. Ask only if the target is genuinely ambiguous.
2. Inspect applicable AGENTS.md instructions, relevant specifications, README, actual code, tests, and current branch/commit. Check related issues and open PRs for completed, duplicate, dependent, or overlapping work. Use available GitHub tools, or an authenticated GitHub CLI when appropriate.
3. Distinguish implemented behavior, documented intentions, and unverified claims. Read referenced requirements needed for this work. If access is missing, state exactly what could not be verified; do not fabricate repository evidence.
4. Preserve the user's requested goal. When asked for the next task, choose the smallest coherent outcome that advances the project based on its actual state. Do not substitute unrelated cleanup or a generic planning exercise.

## Define an executable unit

- Prefer an end-to-end slice with an observable outcome. A focused bug fix, infrastructure prerequisite, investigation, or design decision can also be a unit when that is the actual need.
- Bound the work by behavior, responsibility, and affected components. Identify likely files as guidance, not an arbitrary allowlist; use strict path boundaries only when required by project instructions or concurrent work.
- Include necessary migrations, tests, and documentation for the outcome. Exclude opportunistic refactors, extra features, and unrelated infrastructure.
- Make routine reversible implementation choices within established conventions. Record rationale and leave the implementer useful discretion. Do not turn every library, filename, or internal design choice into an approval gate.
- Respect real project and user approval requirements. For a blocking product or architecture decision, present a concrete recommendation, alternatives, and the exact decision needed. Do not label an implementation order Ready when it depends on an unresolved decision.
- If research is the work, define the decision it must enable, evidence required, bounded scope, and a stopping condition. Its deliverable must recommend a choice, not merely repeat that choices are deferred.
- If the request spans multiple independently deliverable outcomes, publish only the first useful unit by default and briefly identify successors. Create a series only when requested, with explicit dependencies and no conflicting ownership.

## Issue body

Use a concise title such as `Work order: <observable outcome>`. Scale the detail to the risk and complexity. Include the following information in plain Markdown; combine short sections where useful and omit irrelevant boilerplate.

### Outcome and reason

State what will be different and why it matters to the user or project.

### Current state and sources

Record repository, target branch, inspected commit SHA, relevant paths, and source links. Explain the actual gap. Include the necessary requirements in the issue so the implementer need not reconstruct this conversation. The commit is an evidence baseline, not an instruction to overwrite newer work.

### Scope and boundaries

Describe included behavior and affected components, explicit non-goals, compatibility constraints, and relevant permission/data boundaries. Identify dependencies by verified issue or PR links where available.

### Implementation guidance

State chosen approaches and their rationale, existing patterns to reuse, and choices left to Codex. Distinguish requirements from suggestions. Include only enough detail to avoid material ambiguity; do not prewrite every implementation step.

### Acceptance criteria

Use checkboxes describing observable outcomes and meaningful failure cases. Make each criterion independently assessable. Include relevant negative cases for access control, invalid inputs, retries, or regressions when the scope warrants them. Avoid vague criteria such as 'works correctly' or 'all tests pass' as substitutes for behavior.

### Verification

Give repository-grounded commands and expected results, or describe the checks that must be added if no harness exists. Mark proposed commands as proposed. Distinguish tests, static review, and runtime validation; never claim a check was executed when it was only inspected. Require tests proportional to the change and its risk, not a ceremonial universal suite.

### Codex handoff and completion

Include these instructions, adapted to the project's conventions:

- Read this issue and applicable repository instructions, then compare the current target branch with the recorded baseline. Preserve intervening work. Stop for clarification only if drift changes the requested outcome, scope, or required decisions.
- Implement this bounded outcome and perform the specified verification. Report a concrete blocker if required access or dependencies are missing; do not silently substitute another task.
- Deliver through the repository's established review workflow. Where branch push and PR creation are authorized and supported, open a PR referencing this issue; otherwise provide a reviewable diff and precise handoff.
- Report changed behavior, acceptance evidence, checks actually run, any failed or skipped checks, and remaining limitations. Completion means the specified outcome is demonstrated, not merely that code was written.
- Do not merge, deploy, publish releases, alter production data, or close the issue solely because implementation is finished. Follow explicit authorization and the repository's completion policy. Do not infer permission from the issue's existence.

State readiness as `Ready` or `Blocked`, with the specific unmet dependency or decision if blocked. Separate implementation readiness from permission to perform external actions. Do not invent assignees, labels, deadlines, approvals, or independent-audit requirements.

## Publish and verify

1. Finish the concrete title and body before any permission question. A user request to create a GitHub work order authorizes creating that issue in the resolved repository; do not ask again. A request to draft or discuss an order does not authorize publication. Creating this skill alone does not authorize creating a project issue.
2. Check for an equivalent issue before creation. Reuse an existing order when it already satisfies the request. Update it only when authorized and preserve discussion and unrelated content. Flag material scope changes to an in-progress order rather than silently redefining its contract.
3. Create using the available structured GitHub issue tool. With CLI, use a body file, not interpolated shell text. If the request times out, look for the exact issue before retrying so that an uncertain response does not create duplicates.
4. Read back the created or updated issue. Verify repository, title, body, and returned URL. If publication is unavailable, provide the complete draft and explain the blocker without claiming creation.
5. Return the issue link, the outcome, and any genuine blocker briefly. Stop at the handoff; do not start implementation, dispatch agents, create additional work orders, or operate a lifecycle system unless separately requested.
