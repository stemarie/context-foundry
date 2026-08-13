#!/usr/bin/env python3
"""Run one idempotent Context Foundry Phase 1 recovery/continuation tick."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/karell/context-foundry")
BOARD = "context-foundry"
HERMES = "/home/karell/.local/bin/hermes"
STATE_PATH = ROOT / "state" / "phase-1.json"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [HERMES, "kanban", "--board", BOARD, *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def load_state() -> dict:
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def cards() -> list[dict]:
    result = run("list", "--json")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return json.loads(result.stdout)


def main() -> int:
    state = load_state()
    if state.get("status") != "active":
        return 0
    all_cards = cards()
    active = [c for c in all_cards if c.get("status") in {"ready", "running", "review"}]
    if active:
        return 0
    if state.get("corpus_approval") != "approved":
        # The corpus-review card is the visible human gate. Never dispatch Worker work before it closes.
        return 0
    # After explicit approval, the Architect owns creating/recovering the Worker/Auditor/synthesis sequence.
    # This no-agent recovery tick stays intentionally conservative and only dispatches already-ready work.
    result = run("dispatch", "--max", "1", "--json")
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"context-foundry recovery tick failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
