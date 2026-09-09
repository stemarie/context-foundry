#!/usr/bin/env python3
"""Install the source-managed Watchdog scanner wrapper without creating cron.

This installer writes only the public launcher at
~/.hermes/scripts/foundry_watchdog_scan.sh. It does not start a gateway, create
or alter cron, or read any private profile file.
"""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "profiles" / "foundry-watchdog" / "scripts" / "foundry_watchdog_scan.sh"
TARGET = Path.home() / ".hermes" / "scripts" / "foundry_watchdog_scan.sh"


def main() -> int:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"missing canonical wrapper: {SOURCE}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE, TARGET)
    TARGET.chmod(0o755)
    print(f"WATCHDOG_WRAPPER_INSTALLED path={TARGET}")
    print("cron_created=false gateway_started=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
