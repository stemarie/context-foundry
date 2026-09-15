# Foundry recovery verification — 2026-09-15

Tracking: https://github.com/stemarie/context-foundry/issues/24

## Scope and authority

Karell authorized direct Foundry recovery improvements, verification, and GitHub publication with a linked issue. No Kanban maintenance cards. This repair does not authorize product implementation, retroactively authorize a merge, or release old Delivery/Closure packets.

## Product reconciliation (authenticated API and fresh Git clone)

- Repository: `stemarie/mentorship-platform`.
- Current main: `5bd0dfe42d1cdce1614330fd5892204f22d9cfcb`.
- PR #8 is merged; merge commit equals current main. URL: https://github.com/stemarie/mentorship-platform/pull/8
- Operational tracker #7 remains open: https://github.com/stemarie/mentorship-platform/issues/7
- Immutable work contract: https://github.com/stemarie/AI.Contract/issues/49
- Contract body SHA-256: `1222556a81e1add182f13b360f8cf99868ea9f3b7f8cb56df5dc6edb5dcb0cfe`.
- Frozen contract base: `597ba40434cf718a560396f38305ec182c8345c4`, no longer current main.
- Diff from that base changes only `README.md` and `docs/phase-0/event-permission-baseline.md`.

### Executed checks

- `git diff --check 597ba40434cf718a560396f38305ec182c8345c4..HEAD`: exit 0.
- `go test ./...`: exit 0; web and worker commands report no test files, existing `internal/app` tests pass. This is foundation regression coverage, not evidence of implemented mentorship workflows.
- `go vet ./...`: exit 0.
- Exactly one README link to the artifact.
- All 13 named event rows have the event plus five nonempty required fields.
- All six exact permission invariants present.
- Five-role/six-resource matrix and unresolved design seams inspected.

### Disposition

The documentation exists on main and satisfies the inspected content checks. That does not establish lawful delivery/closure under #49: its explicit completion gate keeps tracker #7 open and requires a separate fresh contract-authorized delivery/closure decision before any main update, tracker comment, or closure. An existing merge is evidence of state, not evidence of authorization.

No next product implementation is authorized by #49; identity, persistence, permissions implementation, UI workflows, deployment, and real-data handling are explicitly excluded. Do not revive its frozen-base instructions or describe this repair as a delivered mentorship product increment.

**Owner:** Karell for the acceptance/authority decision; Overmind for evidence-backed reconciliation. **Concrete next decision:** authorize a fresh reconciliation/closure scope bound to the already merged `5bd0dfe…`, without replaying delivery. The next product implementation needs a separately bounded AI.Contract scope after that disposition. Neither authorization is inferred by this maintenance change.

## Board evidence and preservation

At inspection, `context-foundry` had 13 blocked and 9 dependency-gated todo cards; ready and running were empty. `t_03c77aab` is done with root run 697 carrying `REQUEST_CHANGES`, not PASS. It identified credential acquisition before complete local Closure lineage validation. Older `t_e5a43d39` run 690 carries `REQUEST_CHANGES` for real-envelope incompatibility, and its comments explicitly describe later replacement work; it is not independent evidence of a current failure or release authority by itself.

These records must remain visible as evidence. They are not all new incidents requiring new cards. Old or completed repair cards cannot suppress an unresolved newer audit. No existing card was unblocked or marked complete in this maintenance run. Archival is deferred until each branch's supersession and surviving evidence path are verified; aggregate blocked counts alone cannot justify archival.

## Independent reconciliation and legacy safety review

A separate read-only reviewer reran uncached `go test -count=1 ./...`, `go vet ./...`, diff checks, and deterministic content checks. It confirmed the 13 event rows, five roles × six resources, exact permission invariants, and documentation-only scope. The reviewer did not independently authenticate GitHub; remote evidence above is the operator's authenticated read-back.

The reviewer also exercised the previously installed exact-#49 Closure repair: 9 source tests, 5 installed Closure tests, and 24 isolated negative entrypoint checks passed. The operator independently rechecked source/install byte parity: SHA-256 `976296ef6750f74d7eaa9f3cb412b3fca27bd213389cd1a5e6c0bb7888890a9f`. That adapter remains pinned to candidate `860d094a6a843c91d10972b04c50f1a7b9b74cb9`; it rejects substitution of current main. This is narrow maintenance evidence, not a full-chain capability PASS or permission to close tracker #7.

Independent disposition: content acceptance supported; closure and next implementation are not authorized by the available evidence. A fresh reconciliation-only contract may accept already-merged main and condition tracker closure on authenticated read-back plus independent audit, without further implementation.

## Verification boundaries

Policy-string assertions only verify that role instructions contain the boundary; they are not proof of recovery behavior. Behavioral replay tests must exercise structured receipts, role/contract parsing, current repair lineage, action classification, ambiguity, repeated scans, and restart identity. The scanner is read-only: action output is a decision/evidence request, never a grant of product-write authority.

## Source verification and rollout hold

The corrected source suite passed **119 tests and 12 subtests**. Source-kit validation, shell syntax, and diff whitespace checks passed. A live read-only source scan retained `t_03c77aab` / run 697 / `REQUEST_CHANGES` as an unresolved direct-maintenance observation. Its ordinary notification snapshot contained 82 nonarchived records and 62 actions; archived history remained available only through explicit inspection, without generating actions. These are observations awaiting disposition, not newly authorized tasks.

The first independent scanner review returned REQUEST_CHANGES. Its reproductions were converted to behavioral regression tests and corrected; a fresh review is required against the final source before rollout.

**Rollout is held.** The tool's protected `SOUL.md` write-approval prompt timed out; no alternate write path was used. Architect/Worker/Auditor SOUL policy still contains inherited generic GitHub-or-AI.Contract wording, and the Architect's core skill retains a blanket board-operation prohibition. Those contradictions require explicit protected-file approval and scoped policy alignment before installation. This source publication is a draft, not a claim that Foundry is operationally recovered.

No updated Watchdog/role files were installed during this run. The default assistant's manual review skill was updated directly and its source copy is included here. GitHub issue #24 carries the publication and independent-review receipts. Tracker #7, AI.Contract #49, product main, scheduler cadence, services, and Kanban task states were not changed.
