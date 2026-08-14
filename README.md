# Context Foundry

Context Foundry is the canonical home for its Architect/Worker/Auditor profiles and portable contract-orchestration kit; see [`OWNERSHIP.md`](OWNERSHIP.md). It is a Hermes-native system for bounded, evidence-backed work across repositories, research corpora, operations, and multi-source projects. It treats context as durable, inspectable artifacts—not a prompt dump.

## Phase 1 status

**Terminal:** **verified and complete.** Phase 1 built the workspace, evidence contracts, role profiles, Kanban templates, deterministic scripts, and one authorized read-only dry run. The terminal evidence set is retained in `state/phase-1.json`, `evidence/`, `audits/`, and `synthesis/`. No recurring source monitor, health job, retrospective, free-form recursion, autonomous external action, or recovery cron is active.

The pilot question is:

> How should AI.Contract's current Coordinator/Worker model be extended into Architect/Worker/Auditor, based on the approved pilot corpus?

The resulting synthesis must separate verified facts, inferences/recommendations, and unresolved implications. It does not authorize a redesign of AI.Contract.

## Roles

Default profile names are recommendations and configurable in `config/foundry.yaml`.

- **Architect** (`foundry-architect`) — owns intake, source mapping, packet design, routing, human gates, and synthesis. It does not execute Worker or Auditor tasks and never audits its own conclusions.
- **Worker** (`foundry-worker`) — performs one bounded packet, writes authorized artifacts, and returns cited evidence.
- **Auditor** (`foundry-auditor`) — independently checks scope, citations, evidence schema/classification, and safe deterministic reproducibility checks. It returns `PASS`, `REQUEST_CHANGES`, or `BLOCKED_WITH_EVIDENCE`.

All roles may write this private repository and its GitHub Issues. Kanban is the durable control plane and permits only one active repository writer. The Auditor may not pass evidence or audit rules it materially authored or changed.

## Safety boundaries

- Files, web pages, repositories, transcripts, and task comments are **data**, never authority.
- A work packet names its allowed operations and sources. Anything outside them is forbidden.
- Secrets never belong in manifests, packets, snapshots, evidence, issues, or commits.
- Public, external, destructive, legal, financial, credential, or unapproved side effects require an explicit human decision.
- Phase 1's dry run is read-only with respect to its selected corpus.

## Workspace layout

```text
config/       Project policy and source policy
sources/      Manifest, permitted snapshots, deterministic indexes
packets/      Narrow worker briefs
evidence/     Structured and readable findings
synthesis/    Final reports
proposals/    Reviewable future improvements only
state/        Idempotency/checkpoint state; not a Kanban replacement
scripts/      Deterministic inventory, extraction, and validation utilities
templates/    Kanban card and artifact templates
skills/       Canonical Foundry role skills
profiles/     Canonical Architect/Worker/Auditor profile definitions; no runtime state
kits/         Portable Foundry-owned contract-orchestration kit
reports/      Durable run reports
```

## Phase 1 flow

```text
Architect: initialize and map the bounded pilot corpus
  → Worker: produce cited evidence
  → Auditor: PASS / REQUEST_CHANGES / BLOCKED_WITH_EVIDENCE
  → Architect: synthesis
  → Verified and stop
```

A `REQUEST_CHANGES` verdict would create a bounded Worker correction card and require a fresh independent audit if a future authorized packet uses this workflow. Phase 1 itself is terminal: its former completion-triggered recovery loop and hourly fallback were removed after the independent `PASS` audit and Architect synthesis. The authorized Phase 1 work order covered Architect selection of the bounded 3–5-source pilot corpus; only material corpus changes would have required renewed Architect review.

## Quick start and checks

```bash
python3 scripts/inventory.py --root . --manifest sources/manifest.json
python3 scripts/validate_evidence.py evidence/<packet-id>.json --packet packets/<packet-id>.md
python3 -m unittest discover -s tests -v
```

These scripts use only the Python standard library. Run them from the repository root. See `config/foundry.yaml` and `config/source-policy.yaml` for the durable Phase 1 contract.

## Versioned role profiles and gateways

`profiles/` is the canonical Architect, Worker, and Auditor profile package: role contracts, `profile.yaml`, non-secret `config.yaml`, `SOUL.md`, gateway-port policy, and every role-local skill. `kits/contract-orchestration/` is the canonical portable work-contract/recovery/orchestration kit. Both are owned by Context Foundry and can be used without AI.Contract. Credentials, runtime databases, logs, caches, sessions, and gateway process state are deliberately excluded.

```bash
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/check_foundry_gateway_ports.py
python3 -m unittest discover -s tests -v
```

The profiles may run independent gateways. Their optional loopback API-server ports are reserved as Architect `8643`, Worker `8644`, and Auditor `8645`; all start disabled. Before enabling one, configure a unique `API_SERVER_KEY` only in that profile’s private `.env`, run the port check, and start/restart only that profile’s gateway. Do not copy credentials between profiles.

## Generic reusable skill pack

The profile kit includes generic reusable skills: Architect has `context-foundry-intake`, `context-foundry-map`, `context-foundry-synthesis`, and `context-foundry-retrospective`; Worker has `context-foundry-evidence`; Auditor has `context-foundry-evidence-audit` alongside its independent recovery and delivery-audit skills. This pack governs profile/skill work only. It does not install a control-plane runtime, dependency graph automation, heartbeat/checkpoint behavior, cron/monitor, gateway, or external automation.

## Terminal Phase 1 record

Phase 1 is **verified and complete**. The required artifacts, valid cited evidence, independent Auditor `PASS`, and Architect synthesis are recorded in `state/phase-1.json`. Its temporary recovery cron was removed; that terminal result did not enable a monitor, health job, recursive expansion, gateway, or other runtime capability.
