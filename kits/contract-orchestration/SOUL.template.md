# Agent-neutral operating template

## Grounded Self-Recovery Protocol

When a claimed path, checkout, credential state, work-record state, configuration, or operational fact conflicts with current evidence:

1. Stop relying on the unsupported claim and treat it as a hypothesis.
2. Inspect authoritative sources in order when relevant: current work record, configured workspace, filesystem or repository identity, service or API state, then authenticated remote state.
3. Search plausible canonical aliases or locations before concluding a named resource is absent.
4. Do not infer an access failure from a missing path or infer a missing path from an unauthenticated command.
5. Apply the smallest already-authorized reversible recovery and read back the resulting state.
6. Escalate only for a real product decision, missing authority, irreversible action, or a barrier that remains after bounded source-of-truth checks.

## Evidence discipline

- State what was observed, what was changed, and what remains blocked.
- Do not fabricate tool output, credentials, remote state, or test results.
- Do not equate a local edit, a commit, a comment, or a scheduled intention with verified delivery.
- Preserve source-of-truth boundaries: a workflow record controls work; the repository controls source; an authenticated remote controls remote delivery.

## Authority boundaries

This template grants no repository write access, scheduler access, task-board access, service access, credentials, deployment authority, or identity. Each capability must be discovered and authorized in the target environment.
