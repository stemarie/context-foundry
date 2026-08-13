# CF-P1 Pilot Corpus Selection Receipt

## Status

**Corpus authorization:** covered by Karell's Phase 1 work order.
**Selection timestamp:** 2026-08-13T20:55:28+00:00
**Read-only constraint:** all selected artifacts may be read, searched, and boundedly extracted only. No source execution or changes to AI.Contract are authorized.

## Pilot question

How should AI.Contract's current Coordinator/Worker model be extended into Architect/Worker/Auditor, based on the approved pilot corpus?

## Exact selected corpus

| Source ID | Artifact | Purpose in pilot | Trust class | SHA-256 |
|---|---|---|---|---|
| `src-P1-001` | `config/foundry.yaml` | Defines this Phase 1 pilot's role boundaries, approval gate, and terminal criteria. | `trusted` | `712f076108d3ee569fd9e00bec605152f3a805b1a063f3855facd650f16f98f4` |
| `src-P1-002` | `/home/karell/AI.Contract/README.md` | Establishes the current AI.Contract service, canonical-record, projection, and access boundaries. | `internal` | `424f2101d6bcbc1b9b2ba9262fba0b37dbb85b64ff14f863b175852ff617b132` |
| `src-P1-003` | `/home/karell/AI.Contract/automation/hands-off-development/AGENT.md` | Establishes the current Coordinator/implementation-worker responsibilities, single-writer rule, verification, and recovery model. | `internal` | `baa75c6b717be666711fe02e5c5af36eef9091940df38ac385b82c3adb13a168` |
| `src-P1-004` | `/home/karell/AI.Contract/automation/hands-off-development/skills/card-orchestration.md` | Establishes current card dependency, receipt, and continuation safeguards. | `internal` | `c4d0c5270097f2086e8b9ecb9f66705654e11eda9e797c100c2ae3e407a2a172` |

The canonical machine-readable inventory, absolute locators, modification times, access policy, retention, and hashes are in `sources/manifest.json`. `packets/CF-P1-role-model.md` is constrained to precisely these four IDs.

## Selection rationale

This four-source set is within the configured 3–5-source range and provides: (1) the Foundry pilot's governing boundary, (2) AI.Contract's current service/data boundary, (3) the current Coordinator/Worker behavioral contract, and (4) the current durable-card/continuation safeguards. It is small enough for a bounded evidence packet while varied enough to distinguish factual current-state observations from a recommendation for the proposed Architect/Worker/Auditor extension.

## Execution authority and next action

Karell’s authorized Phase 1 work order covers selection and use of this bounded, read-only corpus. Worker execution may proceed without a separate corpus approval. The manifest and packet remain frozen to the hashes above; a material corpus change still requires re-inventory and Architect review.

The next action is Worker evidence production, followed by an independent Auditor verdict and Architect synthesis.
