# Request routing

Select the workflow before acting. Resolve the target project from the current request and verified context; inspect its instructions, established execution policy and current work/stage. The presence of a skill, OpenSpec artifacts, a GitHub issue or an accessible tool does not by itself select an executor.

1. Honor explicit current user intent, named workflow and scope first, including read-only, draft-only and planning-only limits. A named skill never overrides a narrower no-write instruction. A deliberate change of workflow must preserve or reconcile active work; it does not silently migrate assignments or bypass their acceptance gates.
2. Otherwise retain the project's verified workflow and current stage. For "continue" or "resume," use the established activity and incomplete work rather than starting a different planning or execution system. Do not ask again when current context and policy already decide.
3. If the choice remains materially ambiguous after available inspection, ask one focused question about the intended workflow or stage before publishing or executing. Do not guess from similarly named skills, an unrelated project, or which service is easiest to access. Plain development requests in projects with no established Foundry/OpenSpec workflow can use the normal repository workflow without installing either system.

| Request and established context | Route and stopping point |
| --- | --- |
| Create a work order in an AI.Contract-native project, or explicitly request a native contract | `foundry-create-workorder`: author/reuse the bounded native revision and readiness only. No reservation, launch or implementation. Draft-only stays unpublished. |
| Explicitly request a GitHub issue work-order handoff, or request a work order under a verified issue-based project policy | `foundry-create-gh-workorder`, installed separately: one issue handoff, or an unpublished draft when requested. It grants no native assignment or execution. |
| Start/resume authorized native Foundry delivery | `foundry-start` for the outer run, or `foundry-loop` for an explicitly requested single cycle. Reconcile current work first. |
| Implement/continue the current actor-bound native Worker assignment | `foundry-implement` and Worker under the existing assignment; Coordinator owns reservation/launch. A generic request does not create actor authority. |
| Audit only, with no changes or publication | `foundry-audit` in read-only mode, with no native QA identity or verdict mutation. An assigned native acceptance review uses the independent QA path instead. |
| Explore or propose through Foundry | `foundry-explore` / `foundry-propose` delegate to OpenSpec planning and stop at the requested analysis/artifacts. |
| Continue existing OpenSpec planning, or select standalone OpenSpec by explicit request or verified project policy outside a Foundry cycle | Use the corresponding installed OpenSpec skill and preserve its planning/apply/verify/archive boundary and selected store. "Continue" alone does not turn planning into implementation. |
| Implement an OpenSpec change within an established native Foundry run | Keep `foundry-start` / the current native assignment as executor; use `openspec-foundry` for requirement/task mapping. Do not run OpenSpec apply as a second executor. |

After routing, verify the chosen workflow's actual capabilities and authority. Missing AI.Contract access, credentials or runtime is a concrete native prerequisite, not permission to fall back to GitHub issue execution, standalone OpenSpec apply or a local shadow queue. Preserve useful drafts/read-only analysis within the user's scope and report the blocker. A deliberate alternate workflow must be requested and authorized; availability alone never chooses it.

Read only the selected skill and its required references. Preserve its side-effect limits, existing user permissions, role separation and delivery policy. Routing never creates execution, publication or deployment authority.
