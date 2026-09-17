# Completion receipt: <WORK_TITLE>

- Work record: <WORK_RECORD_URL>
- Revision: <CANDIDATE_OR_MERGED_SHA>
- Integration disposition: `<candidate_only | direct_main_required | human_approval_required>`
- Verified base / candidate branch / candidate SHA: `<BASE_SHA>` / `<BRANCH>` / `<CANDIDATE_SHA>`
- Candidate audit: `<VERDICT_AND_EXACT_SHA>` — PASS certifies the exact candidate SHA and scoped evidence only; it does not certify direct-main integration, deployment, or milestone completion.
- Delivered SHA / default-branch read-back: `<DELIVERED_SHA_OR_NONE>` / `<AUTHENTICATED_DEFAULT_BRANCH_SHA_OR_NONE>`
- Post-delivery checks: <COMMANDS_AND_OUTCOMES_OR_NOT_APPLICABLE>
- Changed paths: <CHANGED_PATHS>
- Runtime/disposable cleanup: <CLEANUP_EVIDENCE>
- Independent contents review: <REVIEW_RESULT>
- Deferred or non-goals: <DEFERRED_WORK>
- Disposition owner and next decision: `<NAMED_OWNER>` — <CONCRETE_NEXT_ACTION_AND_DATE_OR_TRIGGER>

A `candidate_only` receipt must also record its explicit hold reason. A `direct_main_required` receipt cannot report a milestone closed until the exact audited candidate is read back from the authenticated bound default branch and post-delivery checks are recorded. A `human_approval_required` receipt must name the requested direct-main approval and approver.

A receipt reports evidence; it does not grant additional authority.
