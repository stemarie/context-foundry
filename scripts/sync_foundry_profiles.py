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
PROFILES = ("foundry-architect", "foundry-worker", "foundry-auditor", "foundry-brainiac", "foundry-watchdog")
INSTALLED_ROOT = Path.home() / ".hermes" / "profiles"
BASE_ASSETS = (Path("profile.yaml"), Path("config.yaml"), Path("SOUL.md"), Path("ROLE-CONTRACT.md"))
DISCOVERED_ASSET_GLOBS = ("skills/*/SKILL.md", "adapters/*.py", "schemas/*.json", "scripts/*")
REQUIRED_PROFILE_ASSETS = {
    "foundry-auditor": (
        Path("adapters/closure_auditor.py"),
        Path("schemas/closure_auditor_packet.schema.json"),
    ),
}


def assets(profile: str) -> list[Path]:
    source = ROOT / "profiles" / profile
    found = list(BASE_ASSETS)
    for pattern in DISCOVERED_ASSET_GLOBS:
        found.extend(sorted(path.relative_to(source) for path in source.glob(pattern)))
    return found


def validate_source(profile: str) -> list[str]:
    source = ROOT / "profiles" / profile
    errors: list[str] = []
    for required in (*BASE_ASSETS, *REQUIRED_PROFILE_ASSETS.get(profile, ())):
        if not (source / required).is_file():
            errors.append(f"missing repository asset: {profile}/{required}")
    for relative in assets(profile):
        if not (source / relative).is_file():
            errors.append(f"missing discovered repository asset: {profile}/{relative}")
    return errors


def copy_managed_asset(source: Path, target: Path, relative: Path) -> None:
    """Copy canonical content without discarding the private platforms block.

    Runtime API configuration belongs only to the installed profile. Canonical
    configs deliberately do not declare a ``platforms:`` section, so preserve
    that installed suffix verbatim while refreshing the source-managed prefix.
    """
    if relative != Path("config.yaml") or not target.is_file():
        shutil.copyfile(source, target)
        return
    installed = target.read_text(encoding="utf-8")
    marker = "platforms:\n"
    private_suffix = installed[installed.index(marker):] if marker in installed else ""
    source_text = source.read_text(encoding="utf-8")
    target.write_text(source_text + private_suffix, encoding="utf-8")


def managed_asset_matches(source: Path, target: Path, relative: Path) -> bool:
    if not target.is_file():
        return False
    if relative != Path("config.yaml"):
        return filecmp.cmp(source, target, shallow=False)
    source_text = source.read_text(encoding="utf-8")
    target_text = target.read_text(encoding="utf-8")
    suffix = target_text.removeprefix(source_text)
    return target_text.startswith(source_text) and (not suffix or suffix.startswith("platforms:\n"))


def sync(profile: str, apply: bool, installed_root: Path = INSTALLED_ROOT) -> list[str]:
    source_root = ROOT / "profiles" / profile
    target_root = installed_root / profile
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
            copy_managed_asset(source, target, relative)
            target.chmod(source.stat().st_mode & 0o777)
        if not managed_asset_matches(source, target, relative):
            errors.append(f"drift: {profile}/{relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--apply", action="store_true")
    action.add_argument("--check-source", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []
    for profile in PROFILES:
        errors.extend(validate_source(profile) if args.check_source else sync(profile, args.apply))
    if errors:
        print("PROFILE_KIT_INVALID")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    print("PROFILE_KIT_VALID")
    mode = "apply" if args.apply else "check-source" if args.check_source else "check"
    print(f"mode={mode} profiles={len(PROFILES)}")
    print("source_of_truth=profiles/")
    print("excluded=credentials,runtime_state,logs,caches,databases,sessions,gateway_process_state")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
