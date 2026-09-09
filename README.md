# Context Foundry

Context Foundry is the canonical home for reusable Hermes profiles and role-local skills; see [`OWNERSHIP.md`](OWNERSHIP.md). It provides source-controlled role boundaries, non-secret templates, synchronization, and deterministic validation—not a control plane, monitor, or automation runtime.

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
- **Watchdog** (`foundry-watchdog`) — scans only the `context-foundry` board for contract-identified lifecycle changes and routes defined recovery through the Architect. It cannot author contracts, edit source, operate GitHub, access credentials, alter cron/profile configuration, audit, deliver, or close.

Architect, Worker, and Auditor have only their packet-defined repository/Issue authority. Watchdog has neither repository nor GitHub authority. Kanban is the durable control plane and permits only one active repository writer. The Auditor may not pass evidence or audit rules it materially authored or changed.

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
profiles/     Canonical role profile definitions, including the board-only Watchdog; no runtime state
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

`profiles/` is the canonical Architect, Worker, Auditor, Brainiac, and Watchdog profile package: role contracts, `profile.yaml`, non-secret `config.yaml`, `SOUL.md`, gateway-port policy where applicable, and every role-local skill. `kits/contract-orchestration/` is the canonical portable work-contract/recovery/orchestration kit. Both are owned by Context Foundry and can be used without AI.Contract. Credentials, runtime databases, logs, caches, sessions, and gateway process state are deliberately excluded.

```bash
python3 scripts/sync_foundry_profiles.py --check-source
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/check_foundry_gateway_ports.py
python3 -m unittest discover -s tests -v
```

The profiles may run independent gateways. Their optional loopback API-server ports are reserved as Architect `8643`, Worker `8644`, and Auditor `8645`; all start disabled. Before enabling one, configure a unique `API_SERVER_KEY` only in that profile’s private `.env`, run the port check, and start/restart only that profile’s gateway. Do not copy credentials between profiles.

### Watchdog installation and operation

Source synchronization installs only the canonical non-secret Watchdog kit; it does not start a gateway, create a cron job, or write scanner state. After a successful source sync, the separately authorized operator may install the scheduler-visible wrapper:

```bash
python3 scripts/install_foundry_watchdog_wrapper.py
~/.hermes/scripts/foundry_watchdog_scan.sh
```

The wrapper invokes the installed profile scanner and writes its digest only under `~/.hermes/profiles/foundry-watchdog/state/`. A profile-owned Hermes cron and any Watchdog gateway startup are separate operator actions; neither is created by source sync or the wrapper installer. Read-only verification commands are:

```bash
python3 scripts/sync_foundry_profiles.py --check
test -x ~/.hermes/scripts/foundry_watchdog_scan.sh
~/.hermes/scripts/foundry_watchdog_scan.sh
```

## Generic reusable skill pack

The profile kit includes generic reusable skills: Architect has `context-foundry-intake`, `context-foundry-map`, `context-foundry-synthesis`, `context-foundry-retrospective`, and `foundry-release-brief`; Worker has `context-foundry-evidence` and `foundry-release-delivery`; Auditor has `context-foundry-evidence-audit` and `foundry-release-audit` alongside its independent recovery and delivery-audit skills. Release coordination remains role guidance, not a runtime: Architect creates only the initial issue, Worker performs approved delivery, and Auditor independently gates publication and closure. This pack does not install a control-plane runtime, dependency graph automation, heartbeat/checkpoint behavior, cron/monitor, gateway, or external automation.

## Terminal Phase 1 record

Phase 1 is **verified and complete**. The required artifacts, valid cited evidence, independent Auditor `PASS`, and Architect synthesis are recorded in `state/phase-1.json`. Its temporary recovery cron was removed; that terminal result did not enable a monitor, health job, recursive expansion, gateway, or other runtime capability.
