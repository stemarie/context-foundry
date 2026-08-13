# Versioned Foundry profile kit

This directory is the **reviewable source of truth** for the declarative parts of the three Context Foundry profiles:

- profile description and model/toolset template;
- versioned role contracts and all role-local skills (including the AI.Contract recovery/error-correction skills);
- API-server port allocation and gateway policy.

## Deliberately excluded

Do **not** commit runtime or private profile state: `.env` values, API keys, bot tokens, OAuth data, state/SQLite databases, cache, logs, usage ledgers, sessions, temporary files, or gateway PID/service state.

## Source and deployment rule

`profiles/` is canonical. The installed copies under `~/.hermes/profiles/foundry-*` must match it for declarative files. Use:

```bash
python3 scripts/sync_foundry_profiles.py --check
python3 scripts/sync_foundry_profiles.py --apply
python3 scripts/sync_foundry_profiles.py --check
```

`--apply` deliberately copies only `profile.yaml` and the declared `skills/*/SKILL.md` files. The versioned configuration files are templates checked against the safe installed subset; runtime configuration, credentials, and state are never replaced. It never reads, writes, prints, or replaces `.env` files.

## Gateway ports

The profiles are allowed to run independent Hermes gateways. Their optional local API-server listeners are reserved as:

| Profile | Loopback port | Default state |
|---|---:|---|
| `foundry-architect` | `8643` | disabled until explicitly enabled |
| `foundry-worker` | `8644` | disabled until explicitly enabled |
| `foundry-auditor` | `8645` | disabled until explicitly enabled |

They use unique systemd user units (`hermes-gateway-<profile>.service`), so the gateway processes themselves do not clash. Before enabling an API server, configure that profile's own `.env` with a unique `API_SERVER_KEY`, enable it there, run `python3 scripts/check_foundry_gateway_ports.py`, then start/restart only that profile's gateway. Do not copy the default profile's credentials into a Foundry profile.
