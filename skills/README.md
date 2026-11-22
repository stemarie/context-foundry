# Native Foundry skills

This directory contains thirteen native Foundry skills: four roles, eight entry points, and one OpenSpec adapter. They use AI.Contract for execution authority and evidence. The standalone `foundry-create-gh-workorder` skill lives under `standalone-skills/` in the owning repository and is installed separately.

## Choose an entry point

| Skill | Purpose and stopping point |
| --- | --- |
| [foundry-explore](foundry-explore/SKILL.md) | Invoke installed OpenSpec exploration; stop at analysis. |
| [foundry-propose](foundry-propose/SKILL.md) | Invoke installed OpenSpec proposal creation; stop at planning artifacts. |
| [foundry-create-workorder](foundry-create-workorder/SKILL.md) | Author or reuse a bounded native milestone contract/revision; verify readiness without dispatch. |
| [foundry-loop](foundry-loop/SKILL.md) | Complete exactly one authorized native cycle through verified delivery and history. |
| [foundry-start](foundry-start/SKILL.md) | Resume and repeat cycles toward an approved goal; at most five by default unless the user sets another limit. |
| [foundry-implement](foundry-implement/SKILL.md) | Implement an existing actor-bound Worker assignment and submit evidence. |
| [foundry-audit](foundry-audit/SKILL.md) | Independently review an assigned candidate; also supports explicitly read-only repository/history audits. |
| [foundry-commit](foundry-commit/SKILL.md) | Deliver an exact QA-accepted candidate, verify it, record native Done, and publish history. |
| [openspec-foundry](openspec-foundry/SKILL.md) | Map OpenSpec requirements/tasks to native contracts and evidence without creating another executor. |

## Roles

| Role | Responsibility |
| --- | --- |
| [Architect](foundry-architect/SKILL.md) | Inspect evidence, author bounded contracts within human scope, declare dependencies/conflicts, and reassess material changes. |
| [Coordinator](foundry-coordinator/SKILL.md) | Reserve eligible work, launch configured actors, recover executions, assign independent QA, serialize integration, and record outcomes. |
| [Worker](foundry-worker/SKILL.md) | Implement its assigned revision in isolation, verify behavior, submit evidence, and address corrections. |
| [QA](foundry-qa/SKILL.md) | Review the exact candidate independently and return acceptance, reproducible corrections, or a concrete blocker. |

Loading a role skill does not create an actor identity. Workers cannot self-claim or self-approve; QA cannot patch the candidate it judges. Coordinator delivery follows the target repository's authority and policy.

## Shared instructions and installation

Native execution skills use the [AI.Contract interface mapping](AI_CONTRACT_INTERFACE.md), [operating rules](OPERATING_RULES.md), [work contract](../WORK_CONTRACT.md), and [workflow decisions](../docs/WORKFLOW.md). Read the references required by the selected skill. The explore/propose wrappers preserve OpenSpec planning boundaries.

Keep the complete reference layout. From the owning repository root, `scripts/package_skills.py --destination <directory>` renders native skills and shared references; `--verify-only` checks source/rendered hashes and links. Install the OpenSpec planning dependencies before rendering a new destination: bundled copies are under `plugins/foundry-openspec/skills/openspec-*`. The renderer preserves those official skills and unrelated files.

Source paths refer to the repository. Rendered paths refer to the generated pack, including `foundry-shared/`. Copying only SKILL.md files breaks shared references. Refresh the host and verify each skill resolves to the intended copy without shadowing.

The combined plugin contains these thirteen native skills plus twelve official OpenSpec planning skills. It supplies instructions, not a machine connection or credentials. Reinstall through the owning source/release workflow rather than editing a versioned cache. Follow the [Hermes setup guide](../docs/HERMES_HANDOFF.md) for local discovery and actor setup.

## Execution prerequisites

Resolve the approved goal, repository/delivery policy, AI.Contract connection/project, milestone horizon, queue target, Worker/QA pools, and actor-bound credential references before a live run. Verify the deployed native interface. Generic contract status updates and serial-chain PASS-to-Done behavior do not replace native revisions, attempts, or integration.

Execution also needs a supported launch/stop/health adapter, isolated workspaces, independent QA snapshots, required check commands, and a shared GitHub gate. The exercised backend is the bounded local macOS Hermes adapter in [LOCAL_RUNTIME.md](../docs/LOCAL_RUNTIME.md). Its restricted checks do not support every build system; other backends require their own verification.

The [commissioned BEE1 guide](../docs/LOCAL_COMMISSIONED_WORKFLOW.md) describes an existing host-specific read-only MCP connection and private operator setup. Verify current access and credential validity. A globally exposed reader connection cannot perform role mutations. Historical setup evidence is distinct from current live capability.

## Requests and outcomes

Use `foundry-propose` for planning, `foundry-create-workorder` for native authorship only, `foundry-loop` for one cycle, or `foundry-start` for bounded progress. Include project/repository, approved goal, cycle limit when needed, and existing policy references. OpenSpec-backed work also identifies the selected change/store.

The sequence is Draft → Ready → Implementing → QA → QA accepted → Integrating → Done. Ready is distinct from dispatch eligibility. Corrections remain within the current cycle; changed candidates need fresh QA. Done requires integration and successful verification. Expiry never proves the old process stopped. Reconcile uncertain launch, submission, and remote outcomes before retrying.

Report actual project/contract/revision/attempt and candidate identities, stage, checks, delivery/history references, and blockers. Distinguish drafts, local implementation, QA acceptance, delivery, and native Done. A returned bounded invocation is not a background scheduler.

Missing service/runtime capabilities produce a specific blocker. They do not authorize a GitHub issue queue, local shadow state, new actors, extra scope, or deployment. Standalone issue handoffs use the separately named skill and still follow target-project instructions.

## Verification

From the repository root:

```sh
python3 scripts/package_skills.py --destination plugins/foundry-openspec/skills
python3 -m unittest discover -s tests -p test_skill_packaging.py -v
```

Review generated changes and hash manifests. Packaging proves reference integrity and preservation, not runtime behavior. See [manual review scenarios](../docs/SKILL_REVIEW.md), [real-agent acceptance](../docs/HERMES_ACCEPTANCE_2026-11-01.md), [connection receipt acceptance](../docs/CONNECTION_RECOVERY_ACCEPTANCE_2026-11-02.md), and the [operator quickstart](../docs/RUNTIME_QUICKSTART.md) for their verification scopes. Historical reports retain their original sources and boundaries.
