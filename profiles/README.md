# Versioned Foundry profile kit

This directory is the **canonical, reviewable source of truth** for the Architect, Worker, Auditor, and Brainiac Context Foundry profiles. Context Foundry owns the profile definitions and its contract-orchestration/recovery skill material; AI.Contract owns only its Go service and its service contract.

- profile description and model/toolset template;
- versioned role contracts and all role-local skills, including recovery and error-correction guidance now owned by Context Foundry;
- API-server port allocation and gateway policy.

## Deliberately excluded

Do **not** commit runtime or private profile state: `.env` values, API keys, bot tokens, OAuth data, state/SQLite databases, cache, logs, usage ledgers, sessions, temporary files, or gateway PID/service state.

## Source and deployment rule

`profiles/` is canonical. The installed copies under `~/.hermes/profiles/foundry-*` must match it for declarative files. Use:

```bash
python3 scripts/sync_foundry_profiles.py --check-source
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/sync_foundry_profiles.py --apply
python3 scripts/sync_foundry_profiles.py --check
```

`--check-source` validates the complete repository-managed source kit without inspecting installed profile state. `--apply` copies only canonical non-secret profile assets: `profile.yaml`, `config.yaml`, `SOUL.md`, `ROLE-CONTRACT.md`, declared `skills/*/SKILL.md` files, and declared `adapters/*.py` files. It removes superseded managed skill directories, but never reads, writes, prints, or replaces `.env`, credentials, databases, sessions, logs, caches, or gateway process state.

## Gateway ports

The profiles are allowed to run independent Hermes gateways. Their optional local API-server listeners are reserved as:

| Profile | Loopback port | Default state |
|---|---:|---|
| `foundry-architect` | `8643` | disabled until explicitly enabled |
| `foundry-worker` | `8644` | disabled until explicitly enabled |
| `foundry-auditor` | `8645` | disabled until explicitly enabled |
| `foundry-brainiac` | none | no gateway; inactive unless separately operator-installed |

They use unique systemd user units (`hermes-gateway-<profile>.service`), so the gateway processes themselves do not clash. Before enabling an API server, configure that profile's own `.env` with a unique `API_SERVER_KEY`, enable it there, run `python3 scripts/check_foundry_gateway_ports.py`, then start/restart only that profile's gateway. Do not copy the default profile's credentials into a Foundry profile.
