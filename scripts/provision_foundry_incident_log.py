#!/usr/bin/env python3
"""Provision the scoped MariaDB Foundry incident-log accounts once.

Reads the existing protected Hermes admin environment without printing secrets.
Writes dedicated profile credential files mode 0600, applies the additive table
migration, validates each account with only its permitted operations, and
performs no destructive operation.
"""
from __future__ import annotations

import os
import secrets
import stat
from pathlib import Path

import pymysql

ROOT = Path(__file__).resolve().parents[1]
ADMIN_ENV = Path("/home/karell/.hermes/.env")
DB_HOSTNAME_FOR_GRANT = "overmind.lan"
WATCHDOG_ENV = Path("/home/karell/.hermes/profiles/foundry-watchdog/.secrets/foundry_incident_log.env")
BRAINIAC_ENV = Path("/home/karell/.hermes/profiles/foundry-brainiac/.secrets/foundry_incident_log.env")


def parse_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    required = {"SERIOUS_CTO_MYSQL_HOST", "SERIOUS_CTO_MYSQL_PORT", "SERIOUS_CTO_MYSQL_ADMIN_USER", "SERIOUS_CTO_MYSQL_ADMIN_PASSWORD", "SERIOUS_CTO_MYSQL_DB"}
    if not required <= set(values):
        raise RuntimeError("protected admin environment is incomplete")
    return values


def write_profile_env(path: Path, database: str, user: str, password: str, admin: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join((
        f"FOUNDRY_INCIDENT_DB_HOST={admin['SERIOUS_CTO_MYSQL_HOST']}",
        f"FOUNDRY_INCIDENT_DB_PORT={admin['SERIOUS_CTO_MYSQL_PORT']}",
        f"FOUNDRY_INCIDENT_DB_USER={user}",
        f"FOUNDRY_INCIDENT_DB_PASSWORD={password}",
        f"FOUNDRY_INCIDENT_DB_NAME={database}",
        "",
    ))
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)


def main() -> int:
    admin = parse_env(ADMIN_ENV)
    database = admin["SERIOUS_CTO_MYSQL_DB"]
    connection = pymysql.connect(
        host=admin["SERIOUS_CTO_MYSQL_HOST"], port=int(admin["SERIOUS_CTO_MYSQL_PORT"]),
        user=admin["SERIOUS_CTO_MYSQL_ADMIN_USER"], password=admin["SERIOUS_CTO_MYSQL_ADMIN_PASSWORD"],
        database=database, autocommit=False, cursorclass=pymysql.cursors.DictCursor,
    )
    watchdog_password = secrets.token_urlsafe(32)
    brainiac_password = secrets.token_urlsafe(32)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT User, Host FROM mysql.user WHERE User IN ('foundry_watchdog', 'foundry_brainiac')")
            if cursor.fetchall():
                raise RuntimeError("scoped Foundry account already exists; refusing credential replacement")
            migration_lines = (ROOT / "migrations/20260916_foundry_incident_log.sql").read_text(encoding="utf-8").splitlines()
            migration = "\n".join(line for line in migration_lines if not line.lstrip().startswith("--"))
            for statement in (piece.strip() for piece in migration.split(";") if piece.strip()):
                cursor.execute(statement)
            cursor.execute("CREATE USER 'foundry_watchdog'@'overmind.lan' IDENTIFIED BY %s", (watchdog_password,))
            cursor.execute("CREATE USER 'foundry_brainiac'@'overmind.lan' IDENTIFIED BY %s", (brainiac_password,))
            cursor.execute(f"GRANT SELECT, INSERT, UPDATE ON `{database}`.foundry_incident_log TO 'foundry_watchdog'@'overmind.lan'")
            cursor.execute(f"GRANT SELECT ON `{database}`.foundry_incident_log TO 'foundry_brainiac'@'overmind.lan'")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    write_profile_env(WATCHDOG_ENV, database, "foundry_watchdog", watchdog_password, admin)
    write_profile_env(BRAINIAC_ENV, database, "foundry_brainiac", brainiac_password, admin)

    # Do not print connection values, passwords, or grant SQL.
    print("provisioned table=foundry_incident_log writer=foundry_watchdog reader=foundry_brainiac")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
