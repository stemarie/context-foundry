#!/usr/bin/env python3
"""Safely verify or apply versioned Context Foundry profile assets.

Only declarative role skills and profile.yaml are synchronized. Runtime state,
credentials, gateway state, logs, caches, databases, and SOUL.md are excluded.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("foundry-architect", "foundry-worker", "foundry-auditor")
INSTALLED_ROOT = Path.home() / ".hermes" / "profiles"


def assets(profile: str) -> list[Path]:
    source = ROOT / "profiles" / profile
    found = [Path("profile.yaml")]
    found.extend(sorted(path.relative_to(source) for path in (source / "skills").glob("*/SKILL.md")))
    return found


def sync(profile: str, apply: bool) -> list[str]:
    source_root = ROOT / "profiles" / profile
    target_root = INSTALLED_ROOT / profile
    errors: list[str] = []
    if not target_root.is_dir():
        return [f"missing installed profile: {profile}"]
    for relative in assets(profile):
        source = source_root / relative
        target = target_root / relative
        if not source.is_file():
            errors.append(f"missing repository asset: {profile}/{relative}")
            continue
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            target.chmod(0o644)
        if not target.is_file() or not filecmp.cmp(source, target, shallow=False):
            errors.append(f"drift: {profile}/{relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    errors = []
    for profile in PROFILES:
        errors.extend(sync(profile, args.apply))
    if errors:
        print("PROFILE_KIT_INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PROFILE_KIT_VALID")
    print(f"mode={'apply' if args.apply else 'check'} profiles={len(PROFILES)}")
    print("excluded=credentials,runtime_state,logs,caches,databases,SOUL.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
