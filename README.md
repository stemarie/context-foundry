# Context Foundry

Context Foundry provides agent skills and a bounded runtime for turning an approved software goal into implemented, independently checked, and verified repository changes. The native workflow uses AI.Contract to track execution. A separate standalone skill creates GitHub issue work orders without that service.

The skills define responsibilities and handoffs. `foundry_runtime/` implements the exercised local Hermes process, workspace, check, recovery, and GitHub transport controls. Installing skills alone does not connect a machine or start execution.

## Choose a workflow

| Goal | Entry point | Requirements and result |
| --- | --- | --- |
| Explore requirements or design | `foundry-explore` | Installed OpenSpec exploration skill; returns analysis without starting implementation. |
| Create a proposal | `foundry-propose` | Installed OpenSpec proposal skill and its CLI prerequisites; produces planning artifacts. |
| Create one native work contract | `foundry-create-workorder` | AI.Contract project and approved milestone horizon; authors or reuses a bounded revision without dispatching it. |
| Execute one native cycle | `foundry-loop` | Configured service, actors, runtime, and delivery access; proceeds through implementation, independent QA, and verified delivery. |
| Progress toward an approved goal | `foundry-start` | Same execution prerequisites; resumes existing work and repeats bounded cycles, at most five by default. |
| Create a GitHub issue for Codex | [foundry-create-gh-workorder](standalone-skills/foundry-create-gh-workorder/SKILL.md) | Target repository and GitHub access; creates an issue or returns a draft. Does not implement or dispatch. |

The native pack contains thirteen Foundry roles, entry points, and the OpenSpec adapter. The [Foundry + OpenSpec plugin](https://chatgpt.com/plugins/plugins_6ae66b5a7f38819197cb595683297669), release **1.1.3**, combines these with twelve OpenSpec planning skills: 25 discoverable skills in total. The GitHub work-order skill is installed separately, outside native-pack discovery. See the [complete native skill index](skills/README.md).

## Native workflow

1. The human defines the goal, repository, milestones, and planning horizon.
2. Architect authors bounded contracts with dependencies, conflict boundaries, acceptance criteria, and delivery policy.
3. Coordinator atomically reserves eligible work in AI.Contract and launches a configured Worker in an isolated worktree.
4. Worker implements its assignment, runs required checks, and submits an exact candidate and evidence.
5. A separate QA actor independently checks that candidate. Corrections return to the assigned Worker; changed candidates need renewed QA.
6. Coordinator serializes integration, delivers under the target repository policy, verifies the remote and postchecks, and records native Done.
7. A historical GitHub issue records delivery or cancellation and links the evidence.

| Component | Owns |
| --- | --- |
| AI.Contract | Native projects, scope, revisions, dependencies, reservations, attempts, candidates, verdicts, and completion state |
| Context Foundry | Role instructions, local process/workspace isolation, runtime reconciliation, selected checks, Git transport, and connection health |
| OpenSpec | Requirements, proposals, design, and task/scenario mapping |
| GitHub | Source and native workflow delivery history; issue handoffs when using the separate standalone skill |

QA acceptance is not Done: completion requires integration and successful verification. Lease expiry is not proof a process stopped; recovery must reconcile or stop the old execution before assigning another writer. Read the [work contract](WORK_CONTRACT.md), [workflow decisions](docs/WORKFLOW.md), and [operating rules](skills/OPERATING_RULES.md) for the full handoffs.

## Install and discover the skills

For combined planning and native execution, install the Foundry + OpenSpec plugin in the intended host. Verify that required skills and shared references are readable. Its source is in `plugins/foundry-openspec/`; installation does not provision AI.Contract credentials, a runtime, or OpenSpec CLI.

For local Hermes setup, keep a complete checkout and follow the [Hermes handoff](docs/HERMES_HANDOFF.md). Its existing `skills.external_dirs` configuration can load the source directory; preserve other configured directories. Source planning wrappers also need their OpenSpec dependencies available through the host skill loader.

To prepare a portable directory containing the bundled OpenSpec dependencies, run these commands **from the repository root**, replacing the staging path with a writable directory:

```sh
foundry_pack_dir=/absolute/path/to/staging/foundry-skills
mkdir -p "$foundry_pack_dir"
cp -R plugins/foundry-openspec/skills/openspec-* "$foundry_pack_dir/"
python3 scripts/package_skills.py --destination "$foundry_pack_dir"
python3 scripts/package_skills.py --destination "$foundry_pack_dir" --verify-only
```

Load the whole generated directory through the host's supported installation mechanism. For Hermes, add its absolute path to the existing `skills.external_dirs` list. Preserve `foundry-shared/`: copying individual native SKILL.md files breaks references. Refresh the host and check for duplicate or shadowing names. Edit owning source rather than a versioned plugin cache.

For GitHub-only handoffs, install the complete `standalone-skills/foundry-create-gh-workorder/` directory through the host skill installer. It needs no native shared pack, AI.Contract connection, or Hermes runtime. If the renamed personal skill is already installed, use that copy rather than installing a duplicate.

## Configure native execution

Resolve the following from the intended service and operator host before requesting a run:

- A reachable AI.Contract deployment supporting the [native workflow interface](skills/AI_CONTRACT_INTERFACE.md), with read access and required role mutations.
- A project bound to one repository, approved milestones and planning horizon, an explicit queue target, and registered Worker and separate QA pools.
- Actor-bound credential references, a prepared Hermes interpreter/source and model route, isolated workspace/home locations, and launch/stop/health support.
- Authorized repository delivery, required checks, and one shared GitHub connection journal/gate across affected Coordinators.
- OpenSpec CLI and the selected change/store when using its planning or task mapping. Inspect installed CLI help and retain schema prerequisites.

Keep credential values outside skills, contracts, and logs. A read-only MCP connection cannot reserve work, submit candidates, or record verdicts; those operations require role-bound clients and runtime identities.

For the previously commissioned operator host, use the [BEE1 operating guide](docs/LOCAL_COMMISSIONED_WORKFLOW.md). It documents private configuration, the read-only bridge, role-bound access, status checks, and recovery. Its paths and connection constraints are host-specific; verify current access and credential validity before use. It is not a portable service installer.

The exercised Worker/QA backend uses macOS `sandbox-exec`, a prepared Hermes environment, and restricted operator-selected checks. Arbitrary builds requiring network or child processes, other operating systems, and other runtime backends require their own implementation and verification. Read the [runtime interface](docs/LOCAL_RUNTIME.md) and [operator quickstart](docs/RUNTIME_QUICKSTART.md).

## Request work

These prompts are examples for a host with the named skills loaded. Replace placeholders with verified project, repository, and goal context.

**Plan:**

> Use foundry-explore to examine requirements for <goal> in <repository>. Report decisions and missing evidence. Do not start implementation.

> Use foundry-propose to prepare an OpenSpec proposal for <goal> in the selected project/store. Stop after planning artifacts.

**Execute after native setup:**

> Use foundry-start for <AI.Contract project> and <repository> to reach <approved goal>. Stay within the existing milestone horizon, resume unfinished work first, and use at most three cycles. Follow repository delivery policy. No deployment.

Use `foundry-loop` for exactly one cycle. A missing prerequisite produces a concrete blocker, not a substitute issue queue. A returned invocation does not continue in the background.

**Create a standalone GitHub handoff:**

> Use foundry-create-gh-workorder to inspect <repository> and create the next bounded GitHub issue toward <goal>. Include acceptance criteria and verification. Stop after publishing the issue.

For a draft, request “draft only; do not publish.” This skill does not assign a native Worker, start implementation, merge, or deploy. The target project's instructions and delivery policy still apply.

## Verify changes

For packaging changes, run from the repository root:

```sh
python3 scripts/package_skills.py --destination plugins/foundry-openspec/skills
python3 -m unittest discover -s tests -p test_skill_packaging.py -v
```

Rendering refreshes generated native files and their hash manifest in the checkout; review that diff before delivery. For runtime changes, follow the relevant acceptance runbook and run the full host suite on the supported macOS operator host:

```sh
PYTHONDONTWRITEBYTECODE=1 TMPDIR=/private/tmp python3 -m unittest discover -s tests -v
```

`scripts/acceptance_preflight.py` checks supplied service/Hermes prerequisites without launching an agent or proving delivery. Real-agent acceptance scripts can make model calls and perform authorized repository delivery; inspect their arguments and scope first.

Recorded evidence includes [single and concurrent real-agent acceptance](docs/HERMES_ACCEPTANCE_2026-11-01.md), [audit-gap closure](docs/HERMES_GAP_CLOSURE_2026-11-01.md), [command admission and integration recovery](docs/COMMAND_ADMISSION_PROOFS_2026-11-01.md), and [connection recovery and check receipts](docs/CONNECTION_RECOVERY_ACCEPTANCE_2026-11-02.md). Later stock-runtime and final verification outcomes are linked in historical issues [#49](https://github.com/stemarie/context-foundry/issues/49) and [#50](https://github.com/stemarie/context-foundry/issues/50). These record their stated sources and hosts; they are not a health check of today's service.

The runtime is operator-invoked and bounded. This repository does not install an unattended controller, recurring scheduler, or production deployment. The earlier profile-based implementation is preserved on [archive/pre-reset-2026-10-25](https://github.com/stemarie/context-foundry/tree/archive/pre-reset-2026-10-25).
