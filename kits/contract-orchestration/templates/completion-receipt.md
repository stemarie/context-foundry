# Completion receipt: <WORK_TITLE>

- Work record: <WORK_RECORD_URL>
- Revision: <CANDIDATE_OR_MERGED_SHA>
- Integration disposition: `<candidate_only | merge_required | human_approval_required>`
- Verified base / candidate branch / candidate SHA: `<BASE_SHA>` / `<BRANCH>` / `<CANDIDATE_SHA>`
- Candidate audit: `<VERDICT_AND_EXACT_SHA>` — PASS certifies the exact candidate SHA and scoped evidence only; it does not certify PR integration, deployment, or milestone completion.
- Pull request / merged SHA / default-branch read-back: `<PR_URL_OR_NONE>` / `<MERGED_SHA_OR_NONE>` / `<AUTHENTICATED_DEFAULT_BRANCH_SHA_OR_NONE>`
- Post-merge checks: <COMMANDS_AND_OUTCOMES_OR_NOT_APPLICABLE>
- Changed paths: <CHANGED_PATHS>
- Runtime/disposable cleanup: <CLEANUP_EVIDENCE>
- Independent contents review: <REVIEW_RESULT>
- Deferred or non-goals: <DEFERRED_WORK>
- Disposition owner and next decision: `<NAMED_OWNER>` — <CONCRETE_NEXT_ACTION_AND_DATE_OR_TRIGGER>

A `candidate_only` receipt must also record its explicit hold reason. A `merge_required` receipt cannot report a milestone closed until the merged integration is read back from the authenticated bound default branch and post-merge checks are recorded. A `human_approval_required` receipt must name the requested approval and approver.

A receipt reports evidence; it does not grant additional authority.
