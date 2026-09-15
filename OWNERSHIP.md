# Context Foundry ownership boundary

Context Foundry is the canonical home for:

- Architect / Worker / Auditor / Watchdog profile definitions;
- profile metadata, non-secret config, role instructions, gateway-port policy, and role-local skills;
- portable recovery, delivery, and validation guidance that remains profile/skill-only and does not activate runtime automation.

AI.Contract is an independent Go service. It owns only its service source, API/schema/runtime behavior, tests, and service documentation. It does not own, install, validate, or require Foundry profiles or skills.

## Independent use

- A user can clone and operate **AI.Contract** as a standalone service without a Foundry profile, kit, gateway, or Kanban board.
- A user can clone and operate **Context Foundry** profiles and its portable contract-orchestration kit without an AI.Contract checkout or running AI.Contract service.

Historical Phase 1 evidence may cite AI.Contract because it was a read-only research corpus at that time. Those historical citations are evidence records, not a current runtime, installation, or ownership dependency.

## Direct maintenance and product recovery

Karell-authorized Foundry profile, skill, adapter, and process maintenance is performed directly in source; do not create Kanban maintenance cards or a repair-card chain. A requested GitHub issue tracks these changes and their independent verification, not a new product contract. In the governed installation, AI.Contract remains the sole work-contract plane; GitHub implementation issues do not grant authority.

The Watchdog's read-only recovery evidence never authorizes a product write. Resolve current contract scope and authenticated remote state before selecting a correction. Historical completed repair cards, a Kanban `done` state, and an already merged candidate cannot substitute for current authorization or a structured independent PASS. Unresolved incidents remain inspectable even when duplicate notifications are suppressed.

`skills/improve-foundry-temp/SKILL.md` is the source copy of the default assistant's manually invoked review skill. It does not enable a scheduler or another profile. Deploy it only to the explicitly authorized default-assistant skill location; the profile synchronizer does not install it.

## Profile deployment

From the Context Foundry repository root:

```sh
python3 scripts/sync_foundry_profiles.py --apply
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/check_foundry_gateway_ports.py
python3 -m unittest discover -s tests -v
```

The sync tool manages only `profile.yaml`, non-secret `config.yaml`, `SOUL.md`, and declared skills. It excludes all credentials and runtime state. The separate Watchdog wrapper installer writes only `~/.hermes/scripts/foundry_watchdog_scan.sh`; it does not create cron or start a gateway.
