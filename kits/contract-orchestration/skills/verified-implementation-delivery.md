# Skill template: verified implementation and delivery

## Trigger

Use for a bounded, authoritative work contract that has a named repository, branch rule, acceptance criteria, and verification gates.

## Procedure

1. Read the latest contract and specification; inspect branch, status, and remote baseline.
2. Make only scoped changes and preserve unrelated work.
3. Run every required test, lint, build, runtime probe, and cleanup check. Record the real command and outcome.
4. Review the exact diff and ensure it has no accidental secrets, paths, generated debris, or scope expansion.
5. Select and record one integration disposition for every source change: `candidate_only`, `direct_main_required`, or `human_approval_required`. Default to `direct_main_required` when delivery authority exists. Bind the authenticated base SHA, candidate branch/SHA, disposition owner, and concrete next decision. A pushed candidate is only `candidate produced`; a Candidate Auditor PASS makes it `candidate verified`, never delivered or complete.
6. Commit and push only when explicitly authorized. Never use force delivery unless separately authorized. For `direct_main_required`, independently audit the exact candidate, then non-force fast-forward it to the authenticated bound default branch, read that branch back, and run recorded post-delivery checks before delivery/closure. Never create, update, review, or merge a pull request. For `human_approval_required`, stop before direct delivery and named approver authorization. `candidate_only` requires a stated hold reason, owner, and dated/concrete next decision and can never close a product milestone.
7. Verify local revision equals the authenticated remote default branch and fetched tracking branch for direct-main delivery. A local commit is not delivery proof.
8. Write and re-read a completion receipt. State the disposition and lifecycle state: `candidate produced`, `candidate verified`, `integration pending`, `integrated on main`, or `milestone closed`. Terminal completion follows verified integration where required, not a local commit.

## Contract invalidation

Before treating a failed acceptance gate as a blocking execution problem, determine whether it can be repaired inside the accepted scope. A reproducible live probe that proves the work order has a false premise, conflicting acceptance/non-goals, incompatible scope, or has been superseded by the current specification/product invalidates the contract.

For invalidation, record one `[contract-invalidated:<fingerprint>]` receipt with the authoritative sources, exact probe/outcome, and conflicting clauses; close the work record as `not_planned` rather than `completed`; archive the linked execution card; and return the coordinator to a fresh current-spec/repository audit. Do not retry unchanged work, silently expand the contract, or presume the replacement. The fresh audit alone may select a next bounded contract.

## Recovery fallback

When immediate continuation is unavailable or fails, leave a durable receipt and let the next periodic or manual audit decide the next bounded action. An unchanged invalidation fingerprint is a silent state, not a reason to re-notify or redispatch.

## Non-claims

This template does not assume a hosting provider, repository credential, pull-request workflow, deployment system, runtime fixture, or scheduler.
