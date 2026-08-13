#!/usr/bin/env python3
"""Verify or apply the canonical Context Foundry profile kit.

The repository owns role instructions, non-secret config, profile metadata, and
all role-local skills. Credentials and runtime state remain profile-local and
are never read, copied, printed, or committed by this tool.
"""
from __future__ import annotations

import argparse
import filecmp
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("foundry-architect", "foundry-worker", "foundry-auditor")
INSTALLED_ROOT = Path.home() / ".hermes" / "profiles"
BASE_ASSETS = (Path("profile.yaml"), Path("config.yaml"), Path("SOUL.md"))


def assets(profile: str) -> list[Path]:
    source = ROOT / "profiles" / profile
    found = list(BASE_ASSETS)
    found.extend(sorted(path.relative_to(source) for path in (source / "skills").glob("*/SKILL.md")))
    return found


def validate_source(profile: str) -> list[str]:
    source = ROOT / "profiles" / profile
    errors: list[str] = []
    for required in (*BASE_ASSETS, Path("ROLE-CONTRACT.md")):
        if not (source / required).is_file():
            errors.append(f"missing repository asset: {profile}/{required}")
    return errors


def sync(profile: str, apply: bool) -> list[str]:
    source_root = ROOT / "profiles" / profile
    target_root = INSTALLED_ROOT / profile
    errors = validate_source(profile)
    if not target_root.is_dir():
        return errors + [f"missing installed profile: {profile}"]
    expected = {relative.as_posix() for relative in assets(profile)}
    if apply:
        # Remove only managed role-skill directories absent from the canonical
        # kit. Runtime metadata under skills/.hub is intentionally untouched.
        skills_root = target_root / "skills"
        if skills_root.is_dir():
            for installed in skills_root.glob("*/SKILL.md"):
                relative = installed.relative_to(target_root).as_posix()
                if relative not in expected:
                    shutil.rmtree(installed.parent)
    for relative in assets(profile):
        source = source_root / relative
        target = target_root / relative
        if not source.is_file():
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
    errors: list[str] = []
    for profile in PROFILES:
        errors.extend(sync(profile, args.apply))
    if errors:
        print("PROFILE_KIT_INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PROFILE_KIT_VALID")
    print(f"mode={'apply' if args.apply else 'check'} profiles={len(PROFILES)}")
    print("source_of_truth=profiles/")
    print("excluded=credentials,runtime_state,logs,caches,databases,sessions,gateway_process_state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
