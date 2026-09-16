#!/usr/bin/env python3
"""Run the canonical installed-Architect full-chain preflight validator."""
from __future__ import annotations

import importlib.util
from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[1] / "profiles/foundry-architect/adapters/full_chain_preflight.py"
spec = importlib.util.spec_from_file_location("foundry_full_chain_preflight_adapter", CANONICAL)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

validate_manifest = module.validate_manifest
validate_envelope = module.validate_envelope


def main() -> int:
    return module.main()


if __name__ == "__main__":
    raise SystemExit(main())
