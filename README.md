# Context Foundry

Context Foundry defines and implements an **AI.Contract-backed workflow for coordinated software delivery**. A human sets the goal and scope; Architect, Coordinator, Worker, and independent QA roles turn that scope into bounded work contracts, isolated implementation, checked candidates, and verified repository delivery. The workflow supports parallel work where dependencies and declared conflicts permit it.

The workflow is expressed through thirteen shared `SKILL.md` skills usable by Codex and Hermes. AI.Contract owns execution state; OpenSpec supplies planning and requirement mapping. The same instructions are packaged with OpenSpec skills for ChatGPT. The skills describe the process and its responsibilities; `foundry_runtime/` supplies the exercised process, workspace, check, recovery, and GitHub delivery controls.

The central requirement is evidence-backed completion: an agent's summary, a passing review, or a pushed branch is insufficient. Independent QA must apply to the exact candidate, delivery must preserve intervening work, and required checks must succeed before AI.Contract records Done. Recovery must reconcile uncertain operations and prevent competing writers.

## Current implementation and limits

The shared instructions are reusable. The bundled execution implementation is a bounded, operator-driven Hermes/macOS setup with specific target restrictions. It is not yet a general-purpose controller that can be installed and pointed at any repository.

| Area | What the repository currently provides |
| --- | --- |
| Skills | Thirteen shared native definitions; recorded discovery in Codex and Hermes. Loading them does not provision execution capabilities. |
| Worker/QA runtime | Tested Hermes processes on macOS with isolated workspaces, actor-bound access, independent QA, and restricted operator-selected checks. A Codex Worker/QA execution backend is not demonstrated here. |
| Repository delivery | The bundled [GitHub adapter](foundry_runtime/remote.py) explicitly permits only `stemarie/context-foundry`. Another target requires an authorized code change and verification, not just a different configuration value. |
| Service connection | The [commissioned connection adapter](foundry_runtime/local_connection.py) enforces the private BEE1 SSH endpoint. It is not a generic connection installer. |
| Coordination | Role procedures and operator-invoked runtime building blocks. The operator supplies current assignment/configuration and performs bounded coordination; there is no finished generic controller or unattended continuation. |
| Other environments | Other operating systems, less restricted build systems, and additional execution backends require implementation and their own evidence. |

The separately installed GitHub work-order skill is a small planning/handoff utility. It does not replace AI.Contract or implement a second Foundry execution system.

## Choose a workflow

| Goal | Entry point | Requirements and result |
| --- | --- | --- |
| Explore requirements or design | `foundry-explore` | Installed OpenSpec exploration skill; returns analysis without starting implementation. |
| Create a proposal | `foundry-propose` | Installed OpenSpec proposal skill and its CLI prerequisites; produces planning artifacts. |
| Create one native work contract | `foundry-create-workorder` | AI.Contract project and approved milestone horizon; authors or reuses a bounded revision without dispatching it. |
| Execute one native cycle | `foundry-loop` | Directs one implementation/QA/delivery cycle through supported operator/runtime capabilities; the bundled implementation has the restrictions above. |
| Progress toward an approved goal | `foundry-start` | Directs bounded repetition through the same supported capabilities; resumes existing work and allows at most five cycles by default. |
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

For Codex or ChatGPT accounts with access, the Foundry + OpenSpec plugin supplies the combined planning and native workflow instructions. The linked account plugin is private, not a public installation available to every repository reader. Its source bundle is in `plugins/foundry-openspec/` for local packaging and installation through a supported host mechanism. Verify that skills and references are readable. Installing instructions does not provision AI.Contract credentials, a runtime, or OpenSpec CLI.

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

For the existing supported operator route, resolve the following from the service and host before requesting a run. For a different repository or connection, first adapt and verify the relevant bundled adapters; these prerequisites alone do not remove their code-enforced restrictions.

- A reachable AI.Contract deployment supporting the [native workflow interface](skills/AI_CONTRACT_INTERFACE.md), with read access and required role mutations.
- A project bound to one repository, approved milestones and planning horizon, an explicit queue target, and registered Worker and separate QA pools.
- Actor-bound credential references, a prepared Hermes interpreter/source and model route, isolated workspace/home locations, and launch/stop/health support.
- Authorized repository delivery, required checks, and one shared GitHub connection journal/gate across affected Coordinators.
- OpenSpec CLI and the selected change/store when using its planning or task mapping. Inspect installed CLI help and retain schema prerequisites.

Keep credential values outside skills, contracts, and logs. A read-only MCP connection cannot reserve work, submit candidates, or record verdicts; those operations require role-bound clients and runtime identities.

For the previously commissioned operator host, use the [BEE1 operating guide](docs/LOCAL_COMMISSIONED_WORKFLOW.md). It documents private configuration, the read-only bridge, role-bound access, status checks, and recovery. Its paths and connection constraints are host-specific; verify current access and credential validity before use. It is not a portable service installer.

The exercised Worker/QA backend uses macOS `sandbox-exec`, a prepared Hermes environment, and restricted operator-selected checks. Arbitrary builds requiring network or child processes, other operating systems, and other runtime backends require their own implementation and verification. Read the [runtime interface](docs/LOCAL_RUNTIME.md) and [operator quickstart](docs/RUNTIME_QUICKSTART.md).

## Request work

These prompts select skill procedures; they are not executable CLI commands or a substitute for runtime setup. Replace placeholders with verified project, repository, and goal context. Planning and the standalone GitHub handoff can be used independently of the native execution adapter.

**Plan:**

> Use foundry-explore to examine requirements for <goal> in <repository>. Report decisions and missing evidence. Do not start implementation.

> Use foundry-propose to prepare an OpenSpec proposal for <goal> in the selected project/store. Stop after planning artifacts.

**Execute after native setup:**

Use the existing supported operator route and delivery target, or an independently implemented and verified replacement. Changing the repository placeholder alone does not extend the bundled adapter's allowlist.

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
