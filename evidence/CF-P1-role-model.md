# CF-P1 role-model evidence

- Packet: `CF-P1-role-model`
- Question: How should AI.Contract's current Coordinator/Worker model be extended into Architect/Worker/Auditor, based on the approved pilot corpus?
- Observed at: `2026-08-13T21:09:21Z`

## Source-integrity result

| Source ID | Result |
|---|---|
| src-P1-001 | **Mismatch**: manifest `712f076108d3ee569fd9e00bec605152f3a805b1a063f3855facd650f16f98f4`; observed `34654ab46894281572f855663754853cc66d67c6f070e318d0984149c4412875` |
| src-P1-002 | Match |
| src-P1-003 | Match |
| src-P1-004 | Match |

`src-P1-001` is not used for the role-model conclusion.

## Facts

1. **F-001 — fact, high confidence.** The shared checkout has exactly one active writer, and the Coordinator serializes implementation and verification work. [src-P1-003, `AGENT.md:5-9`, observed `2026-08-13T21:09:21Z`] Excerpt: “The shared checkout has exactly one active writer. The coordinator serializes implementation and verification work; it does not launch competing writers.”
2. **F-002 — fact, high confidence.** Coordinator preflight reads the work record/specification, examines repository and remote state, checks duplicates and active writers, then writes an authoritative scoped contract before assigning one implementation writer. [src-P1-003, `AGENT.md:11-17`, observed `2026-08-13T21:09:21Z`]
3. **F-003 — fact, high confidence.** The implementation worker performs only the stated change, runs required verification, checks final diff/status, and adds/re-reads a completion receipt. [src-P1-003, `AGENT.md:19-26`, observed `2026-08-13T21:09:21Z`]
4. **F-004 — fact, high confidence.** Cards are control records rather than proof; dependencies must be explicit, one writer is required, and a terminal receipt includes changed paths, commands/outcomes, cleanup, delivery evidence, and deferred work. [src-P1-004, `card-orchestration.md:7-14`, observed `2026-08-13T21:09:21Z`]
5. **F-005 — fact, high confidence.** SQLite is canonical and Markdown is deterministic/service-owned; direct filesystem writes are prohibited. [src-P1-002, `README.md:29-33`, observed `2026-08-13T21:09:21Z`]

## Inference

- **I-001 — inference, high confidence.** Current Coordinator preflight maps naturally to an Architect role and the implementation-worker responsibilities map to Worker, because the contract separates authoritative planning/dispatch from bounded execution. [src-P1-003, `AGENT.md:11-26`, observed `2026-08-13T21:09:21Z`] This is an interpretation; the corpus does not explicitly define Architect.

## Recommendation

- **R-001 — recommendation, medium confidence.** Define Architect as sole authority for preflight, scope, acceptance criteria, dependencies, dispatch, and invalidation; retain the Worker as sole implementation writer; add an Auditor to independently check Worker receipt, final diff/status, required command outcomes, and cited evidence before terminal acceptance. Keep the Auditor read-only regarding the implementation checkout unless a new scoped contract grants remediation authority. This preserves the single-writer rule [src-P1-003, `AGENT.md:5-9,11-26`] and distinguishes proof from card state [src-P1-004, `card-orchestration.md:9-14`]. The exact Auditor authority/interface remains a design decision.

## Unknown

- **U-001 — unknown, high confidence.** Whether `src-P1-001` currently represents the approved hash-pinned Phase 1 contract is unknown: its observed SHA-256 differs from its manifest hash. [src-P1-001, `sources/manifest.json:5-17`; hash observation, observed `2026-08-13T21:09:21Z`]

## Limitations

- `src-P1-001` failed hash verification and is excluded from the conclusion.
- The corpus is documentation only. No live AI.Contract execution, code inspection, or external state was examined.
- This packet produces evidence only; it neither implements nor approves the role-model extension.

## Conclusion

The bounded corpus supports retaining single-writer execution and receipt-based verification while separating current Coordinator planning/dispatch duties into Architect and adding a read-only independent Auditor acceptance gate. Final design authority remains outside this evidence packet.
