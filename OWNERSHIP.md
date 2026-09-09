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

## Profile deployment

From the Context Foundry repository root:

```sh
python3 scripts/sync_foundry_profiles.py --apply
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/check_foundry_gateway_ports.py
python3 -m unittest discover -s tests -v
```

The sync tool manages only `profile.yaml`, non-secret `config.yaml`, `SOUL.md`, and declared skills. It excludes all credentials and runtime state. The separate Watchdog wrapper installer writes only `~/.hermes/scripts/foundry_watchdog_scan.sh`; it does not create cron or start a gateway.
