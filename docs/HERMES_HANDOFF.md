# Hermes handoff: install, implement, and prove Foundry

This is the entry point to give Hermes. Read both repositories' AGENTS.md first. Authorized changes go directly to main with non-force expected-head updates; do not create PRs. GitHub issues record final delivery/cancellation, never live coordination.

## Current state

| Component | Status |
| --- | --- |
| AI.Contract projects/milestones and native workflow | Implemented, merged, tested over HTTP/MCP |
| Architect, Coordinator, Worker, QA skill source | Available with shared rules and API mapping |
| Installed Hermes connection on your host | Must be inspected/configured |
| Runtime launch/stop/identity/workspace adapter | Still needs implementation and testing |
| Shared GitHub circuit breaker | Still needs implementation and testing |
| Real one-contract and parallel-agent acceptance | Still needs demonstration |

The service mock clients use mock execution attestations. They are not evidence that Hermes workers ran. This guide authorizes no production deployment by itself; use the actual operator task and existing permissions.

## Required inputs

Resolve from the user's task and verified local configuration before asking for anything missing:

- AI.Contract and Context Foundry checkout paths and revisions.
- Installed Hermes version/source revision, active home/config, model route, and working terminal/backend.
- Intended AI.Contract deployment/origin, reachable by the Coordinator and children.
- Secret references for each service actor and the GitHub connection; never values in these documents.
- Target project repository, human-defined milestones/criteria, authorized planning horizon, and delivery policy.
- Configured Worker and independent QA actor names, queue target, and supported runtime resource limits.
- A writable runtime bookkeeping directory and isolated workspace root.

Ask only for a genuinely unresolved host, credential, scope, or deployment decision. Make routine reversible implementation choices within the approved scope without repeated confirmation.

## Read in this order

1. [Service setup](https://github.com/stemarie/AI.Contract/blob/main/docs/hermes-service-setup.md) and [native service operations](https://github.com/stemarie/AI.Contract/blob/main/docs/native-workflow.md).
2. [Work contract](../WORK_CONTRACT.md), [workflow decisions](WORKFLOW.md), and [shared rules](../skills/OPERATING_RULES.md).
3. [Skill-to-API mapping](../skills/AI_CONTRACT_INTERFACE.md) and all four role SKILL.md files.
4. [Hermes runtime adapter specification](HERMES_RUNTIME_ADAPTER.md).
5. [Real-agent acceptance runbook](HERMES_ACCEPTANCE.md).

Keep the repositories separate: AI.Contract owns service/schema/API/persistence; Context Foundry owns skills/runtime orchestration and GitHub transport health. Do not restore the archived profiles, Watchdog/Kanban control plane, or a competing queue.

## Verify installed Hermes capabilities

The upstream reference inspected for these instructions is [4ea8d23cc9f527332ccb1d55359b27741b6ea51b](https://github.com/NousResearch/hermes-agent/tree/4ea8d23cc9f527332ccb1d55359b27741b6ea51b). Installed versions can differ. Inspect the local CLI help, skills/MCP documentation, tool schemas, and implementation before relying on a feature.

At that reference, Hermes supports skills.external_dirs, environment substitution in MCP URL/headers, and delegate_task actions spawn/list/steer/stop. Delegation's role label is not an AI.Contract identity or permission grant. Parent tool/capability inheritance must be checked; do not assume child credential isolation.

Use existing native delegation if it meets the adapter tests. If its current lifecycle/identity behavior cannot meet them, implement the smallest wrapper or isolated worker process path necessary; do not invent command flags or claim persistent handles survive a restart without testing.

## Install the skill source without breaking references

Keep the complete Context Foundry checkout available. Prefer adding its absolute skills directory to the existing Hermes config:

```yaml
skills:
  external_dirs:
    - /absolute/path/to/context-foundry/skills
```

Merge this entry with existing external_dirs. Do not replace the rest of config.yaml or move only the four SKILL.md files: they reference shared files and the repository-root contract. If a skill-view interface restricts parent traversal, read those shared documents through an authorized filesystem tool at the verified checkout path.

Start a fresh Hermes session, or use that installed version's supported refresh. Verify that all four foundry-* skills are discovered and resolve to this checkout, with no shadowing copies. Read each skill and its shared references successfully. Record the source revision.

If external_dirs is unsupported, use the installed version's documented installation mechanism while preserving the entire dependency layout, and verify discovery/readability. Do not create persistent role profiles to work around packaging. Updating skill files is a source change subject to the repository's delivery rules.

## Connect the Coordinator, then isolate child actors

Follow service setup for the real origin, scoped tokens, project, milestones, horizon, and pools. Add only the Coordinator's service credential to its MCP context. Verify actual tool discovery and a native read.

The Worker and QA contexts must receive their own actor-bound API/MCP clients through the runtime adapter. Merely loading a different skill or setting a prompt role does not change the bearer identity. Do not expose all roles' credentials/connections to every child.

The GitHub credential is separate from AI.Contract tokens and model-provider authentication. Preserve existing configured authentication; absence of a particular CLI is not proof that access is unavailable. GitHub operations must use the shared circuit gate described in the adapter spec.

## Implement the missing runtime piece

Create the smallest adapter meeting [the specification](HERMES_RUNTIME_ADAPTER.md), with meaningful tests and actual installed-Hermes probes. Exact filenames and local design are implementation choices. Keep all queue/assignment/contract decisions in AI.Contract; store only runtime handles, launch reconciliation, and transport-breaker health locally.

Start with a bounded invocation of the Coordinator. Do not install a cron, gateway, daemon, or a second dispatcher unless requested. A Coordinator that returns is not a background system; report its checkpoint and next invocation/event honestly.

Use preparation drafts and direct user-authorized bootstrap work if the adapter needed to execute a contract is itself missing. Do not fabricate a service assignment or claim the skill-driven runtime already carried out its own bootstrap.

## Copyable task for Hermes

Replace the input placeholders before treating this as a live execution instruction:

> Read AGENTS.md in both checkouts and docs/HERMES_HANDOFF.md in Context Foundry. Our goal is to run the existing four skills as an assembly line using AI.Contract's native project queue. AI.Contract checkout: <path>; Foundry checkout: <path>; Hermes runtime/home: <verified location>; service origin: <origin>; project and approved milestones/horizon: <scope reference>; actor/credential references: <references only>; GitHub connection: <reference>; authorized deployment target/actions: <explicit scope>.
>
> Verify installed Hermes capabilities and the deployed service, install/discover the full skill pack, and implement the missing runtime adapter and shared GitHub breaker to the linked specification. Reuse supported native delegation where it satisfies identity, lifecycle, and recovery tests. Do not create role profiles, Kanban coordination, another queue, PRs, or an unsolicited recurring scheduler. Make routine reversible choices within scope. Report concrete missing access or product decisions after completing independent work that is possible.
>
> Run the linked acceptance sequence: one real contract through independent QA and direct-main delivery, then two independent contracts with overlapping execution. Record real commands, candidate/target revisions, service receipts, process/identity/worktree evidence, and historical issue links. Do not mark Done from a summary, mock receipt, or pushed branch. Stop at the authorized milestone boundary and report remaining limitations.

## Completion

For implementation, deliver tested source directly to main and create final historical issues. For live setup, also demonstrate the acceptance runbook on the actual runtime and intended service. Report code readiness, deployment readiness, and real execution separately. Missing runtime access can block live proof without preventing a reviewable adapter implementation.
