#!/usr/bin/env python3
"""Narrow authenticated Git transport for Context Foundry role profiles.

Hermes intentionally removes GitHub credentials from terminal subprocesses.
This helper is the explicitly approved bridge for Foundry's authenticated
GitHub reads and non-destructive branch delivery. It reads only the invoking
Foundry profile's private .env, never prints the credential, and supplies it
only to the git/askpass subprocess for one command.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

PROFILE_ROOT = Path("/home/karell/.hermes/profiles")
ALLOWED_PROFILES = frozenset({"foundry-architect", "foundry-worker", "foundry-auditor"})
OWNER = "stemarie"
SAFE_FETCH_FLAGS = frozenset({"--prune", "--quiet", "-q"})
SAFE_PUSH_FLAGS = frozenset({"--dry-run", "--porcelain", "--quiet", "-q"})
SAFE_LS_REMOTE_FLAGS = frozenset({"--heads", "--tags", "--refs", "--quiet", "-q"})


class GuardError(RuntimeError):
    """A requested operation lies outside this helper's transport contract."""


def profile_env_path() -> Path:
    raw_home = os.environ.get("HERMES_HOME", "")
    if not raw_home:
        raise GuardError("HERMES_HOME is required; invoke through a Foundry profile terminal")
    home = Path(raw_home).resolve()
    if home.parent != PROFILE_ROOT or home.name not in ALLOWED_PROFILES:
        raise GuardError("authenticated Git is restricted to the three Foundry profile homes")
    env_path = home / ".env"
    if not env_path.is_file():
        raise GuardError("profile credential file is unavailable")
    return env_path


def github_token(env_path: Path) -> str:
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "GITHUB_TOKEN":
            token = value.strip().strip('"').strip("'")
            if token:
                return token
    raise GuardError("profile has no GitHub token")


def git_output(args: list[str], cwd: Path) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=cwd, check=True, text=True, capture_output=True
    )
    return completed.stdout.strip()


def require_target_repo(cwd: Path) -> None:
    try:
        remote = git_output(["remote", "get-url", "origin"], cwd)
    except subprocess.CalledProcessError as exc:
        raise GuardError("repository must have an origin remote") from exc
    https = re.fullmatch(rf"https://github\.com/{re.escape(OWNER)}/[A-Za-z0-9_.-]+(?:\.git)?", remote)
    ssh = re.fullmatch(rf"git@github\.com:{re.escape(OWNER)}/[A-Za-z0-9_.-]+(?:\.git)?", remote)
    if not (https or ssh):
        raise GuardError("origin must be a stemarie GitHub repository")


def _split_flags_and_positionals(args: list[str], allowed_flags: frozenset[str]) -> list[str]:
    positionals: list[str] = []
    for arg in args:
        if arg.startswith("-"):
            if arg not in allowed_flags:
                raise GuardError(f"option not permitted: {arg}")
        else:
            positionals.append(arg)
    return positionals


def validate_fetch(args: list[str]) -> None:
    positionals = _split_flags_and_positionals(args, SAFE_FETCH_FLAGS)
    if not positionals or positionals[0] != "origin":
        raise GuardError("fetch must name origin")
    for ref in positionals[1:]:
        if not re.fullmatch(r"(?:refs/heads/)?[A-Za-z0-9._/-]+", ref):
            raise GuardError("fetch accepts only a branch reference")


def validate_ls_remote(args: list[str]) -> None:
    positionals = _split_flags_and_positionals(args, SAFE_LS_REMOTE_FLAGS)
    if not positionals or positionals[0] != "origin":
        raise GuardError("ls-remote must name origin")
    for ref in positionals[1:]:
        if not re.fullmatch(r"(?:refs/(?:heads|tags)/)?[A-Za-z0-9._/*?-]+", ref):
            raise GuardError("ls-remote accepts only a branch or tag reference")


def validate_push(args: list[str]) -> None:
    positionals = _split_flags_and_positionals(args, SAFE_PUSH_FLAGS)
    if len(positionals) < 2 or positionals[0] != "origin":
        raise GuardError("push requires origin and an explicit branch refspec")
    for refspec in positionals[1:]:
        if refspec.startswith("+") or ":" not in refspec:
            raise GuardError("push requires a non-force src:refs/heads/<branch> refspec")
        source, destination = refspec.split(":", 1)
        if not source or not re.fullmatch(r"(?:HEAD|[A-Za-z0-9._/-]+)", source):
            raise GuardError("push source must be HEAD or a local branch")
        if not re.fullmatch(r"refs/heads/[A-Za-z0-9._/-]+", destination):
            raise GuardError("push destination must be a branch; tags and deletion are forbidden")


def validate(command: str, args: list[str]) -> None:
    if command == "fetch":
        validate_fetch(args)
    elif command == "ls-remote":
        validate_ls_remote(args)
    elif command == "push":
        validate_push(args)
    else:
        raise GuardError("only fetch, ls-remote, and non-force branch push are permitted")


def askpass_file(directory: str) -> Path:
    path = Path(directory) / "foundry-git-askpass"
    path.write_text(
        "#!/bin/sh\n"
        "case \"${1:-}\" in\n"
        "  *Username*|*username*) printf '%s\\n' x-access-token ;;\n"
        "  *Password*|*password*) printf '%s\\n' \"${FOUNDRY_GIT_TOKEN:?}\" ;;\n"
        "  *) exit 1 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: foundry_authenticated_git.py {fetch|ls-remote|push} origin ...", file=sys.stderr)
        return 2
    command, args = argv[1], argv[2:]
    try:
        env_path = profile_env_path()
        validate(command, args)
        cwd = Path.cwd().resolve()
        require_target_repo(cwd)
        token = github_token(env_path)
    except GuardError as exc:
        print(f"foundry-auth-git: {exc}", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="foundry-git-") as directory:
        askpass = askpass_file(directory)
        child_env = os.environ.copy()
        child_env.update(
            {
                "GIT_ASKPASS": str(askpass),
                "GIT_TERMINAL_PROMPT": "0",
                "FOUNDRY_GIT_TOKEN": token,
            }
        )
        completed = subprocess.run(["git", command, *args], cwd=cwd, env=child_env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
