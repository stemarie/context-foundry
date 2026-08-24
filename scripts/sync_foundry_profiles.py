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


def _split_runtime_api_server(raw: str) -> tuple[str, str]:
    """Remove the live-only platforms.api_server block without parsing secrets.

    API-server enablement and its key are installed runtime state, not a
    source-controlled Foundry template. Keep them out of byte-level drift and
    out of --apply replacement while preserving every other config byte.
    """
    kept: list[str] = []
    runtime: list[str] = []
    skipping = False
    for line in raw.splitlines(keepends=True):
        if line == "  api_server:\n":
            skipping = True
        if skipping:
            if line != "  api_server:\n" and line.startswith("  ") and not line.startswith("    ") and line.strip():
                skipping = False
            else:
                runtime.append(line)
                continue
        kept.append(line)
    return "".join(kept), "".join(runtime)


def _config_matches(source: Path, target: Path) -> bool:
    if not target.is_file():
        return False
    canonical, _ = _split_runtime_api_server(source.read_text(encoding="utf-8"))
    installed, _ = _split_runtime_api_server(target.read_text(encoding="utf-8"))
    return canonical == installed


def _copy_config_preserving_runtime(source: Path, target: Path) -> None:
    canonical, _ = _split_runtime_api_server(source.read_text(encoding="utf-8"))
    runtime = ""
    if target.is_file():
        _, runtime = _split_runtime_api_server(target.read_text(encoding="utf-8"))
    if runtime:
        lines = canonical.splitlines(keepends=True)
        try:
            start = next(index for index, line in enumerate(lines) if line == "platforms:\n")
        except StopIteration as exc:
            raise ValueError(f"canonical config has no platforms block: {source}") from exc
        end = next(
            (index for index in range(start + 1, len(lines)) if lines[index] and not lines[index][0].isspace()),
            len(lines),
        )
        lines[end:end] = runtime.splitlines(keepends=True)
        canonical = "".join(lines)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(canonical, encoding="utf-8")
    target.chmod(0o644)


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
        if relative == Path("config.yaml"):
            if apply:
                _copy_config_preserving_runtime(source, target)
            matches = _config_matches(source, target)
        else:
            if apply:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                target.chmod(0o644)
            matches = target.is_file() and filecmp.cmp(source, target, shallow=False)
        if not matches:
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
