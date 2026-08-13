#!/usr/bin/env python3
"""Deterministic validator for the portable hands-off development kit."""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "README.md": ("## Lifecycle", "## State vocabulary", "## Portable adoption"),
    "AGENT.md": ("## Coordinator preflight", "## Implementation worker", "exactly one active writer", "contract_version", "body_markdown", "must not infer"),
    "SOUL.template.md": ("## Grounded Self-Recovery Protocol", "smallest already-authorized reversible recovery"),
    "skills/discrepancy-to-delivery.md": ("## Optional continuation accelerator", "periodic or manual audit loop"),
    "skills/verified-implementation-delivery.md": ("## Recovery fallback", "authenticated remote"),
    "skills/card-orchestration.md": ("## Continuation adaptation", "one writer"),
    "templates/README.md": ("contract-template.md", "issue-work-contract.md", "implementation-card.md", "Secret-safe environment example"),
    "templates/contract-template.md": ("## Objective", "## Authority", "## In scope", "## Required implementation details", "## Acceptance criteria", "## Verification", "## Delivery", "## Explicit non-goals", "## Safety boundaries", "## Idempotency key", "authorized Architect", "does not change any target service API, schema, or runtime"),
    "templates/issue-work-contract.md": ("## Acceptance criteria", "## Idempotency key"),
    "templates/implementation-card.md": ("exactly one active writer", "completion receipt"),
    "templates/completion-receipt.md": ("Remote comparison", "Deferred or non-goals"),
    "templates/continuation-marker-config.md": ("Optional accelerator contract", "periodic/manual continuation"),
    "templates/environment.example": ("[REDACTED]", "<REPOSITORY_URL>"),
    "adapters/README.md": ("## Hermes Kanban and cron mapping", "periodic or manual continuation"),
    "adapters/generic.md": ("# Generic adaptation path", "Do not assume"),
    "skills/contract-authoring.md": ("## Trigger", "## Prerequisites", "## Authoring procedure", "## Consumer procedure", "## Editable, versioned convention rule", "## Pitfalls", "## Verification", "contract_version", "body_markdown", "cannot override either"),
    "manifest.md": ("# Traceability manifest", "concurrent checkout writers", "contract-template.md", "contract-authoring"),
    "verification/README.md": ("Local deterministic validation", "--self-test"),
    "verification/validate.py": ("Deterministic validator", "REQUIRED"),
}
LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")
TOKEN = re.compile(r"\b(?:g" + r"hp|gho|github_pat)_[A-Za-z0-9_]{20,}\b")
PRIVATE_PATH = re.compile(r"/(?:home|Users)/[^/]+/")
FALSE_INSTALL = re.compile(r"(?:event[- ]trigger(?:ed)?|card[- ]completion).{0,100}(?:runtime|hook).{0,80}\bis\s+installed\b", re.I | re.S)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative, markers in REQUIRED.items():
        path = root / relative
        if not path.is_file():
            errors.append(f"missing required artifact: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for marker in markers:
            if marker not in text:
                errors.append(f"missing required section/text in {relative}: {marker}")
        # The validator contains literal negative-test fixtures. Validate its
        # structural markers but do not interpret those fixtures as kit prose.
        if relative != "verification/validate.py":
            if TOKEN.search(text):
                errors.append(f"prohibited token-shaped value in {relative}")
            if PRIVATE_PATH.search(text):
                errors.append(f"prohibited private machine path in {relative}")
            if FALSE_INSTALL.search(text):
                errors.append(f"false installed event-trigger claim in {relative}")
        if path.suffix == ".md":
            for raw_target in LINK.findall(text):
                target = raw_target.split("#", 1)[0]
                if not target or "://" in target or target.startswith("#"):
                    continue
                resolved = (path.parent / target).resolve()
                try:
                    resolved.relative_to(root.resolve())
                except ValueError:
                    errors.append(f"link escapes kit in {relative}: {raw_target}")
                    continue
                if not resolved.is_file():
                    errors.append(f"broken relative link in {relative}: {raw_target}")
    return errors


def expect_failure(root: Path, mutate, label: str) -> list[str]:
    mutate(root)
    errors = validate(root)
    if errors:
        return []
    return [f"self-test did not reject {label}"]


def self_test() -> list[str]:
    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        problems += expect_failure(sandbox, lambda r: (r / "AGENT.md").unlink(), "missing artifact")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        problems += expect_failure(sandbox, lambda r: (r / "templates/contract-template.md").unlink(), "missing contract template")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        problems += expect_failure(sandbox, lambda r: (r / "skills/contract-authoring.md").write_text("# incomplete\n", encoding="utf-8"), "incomplete contract-authoring skill")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        problems += expect_failure(sandbox, lambda r: (r / "README.md").write_text("# incomplete\n", encoding="utf-8"), "missing section")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        problems += expect_failure(sandbox, lambda r: (r / "README.md").write_text((r / "README.md").read_text(encoding="utf-8") + "\n[bad](missing.md)\n", encoding="utf-8"), "broken link")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        secret = "g" + "hp_" + "A" * 36
        problems += expect_failure(sandbox, lambda r: (r / "README.md").write_text((r / "README.md").read_text(encoding="utf-8") + "\n" + secret + "\n", encoding="utf-8"), "token-shaped value")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        private_path = "/" + "home/example/private"
        problems += expect_failure(sandbox, lambda r: (r / "README.md").write_text((r / "README.md").read_text(encoding="utf-8") + "\n" + private_path + "\n", encoding="utf-8"), "private path")
    with tempfile.TemporaryDirectory(prefix="hands-off-kit-") as directory:
        sandbox = Path(directory) / "kit"
        shutil.copytree(KIT, sandbox)
        claim = "event-trigger continuation runtime " + "is installed"
        problems += expect_failure(sandbox, lambda r: (r / "README.md").write_text((r / "README.md").read_text(encoding="utf-8") + "\n" + claim + "\n", encoding="utf-8"), "installed event claim")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--root", type=Path, default=KIT)
    args = parser.parse_args()
    errors = validate(args.root.resolve())
    if args.self_test and not errors:
        errors.extend(self_test())
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
