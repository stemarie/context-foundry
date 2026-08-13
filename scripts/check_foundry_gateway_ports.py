#!/usr/bin/env python3
"""Verify that Context Foundry's reserved local API-server ports are distinct and free.

The script makes no network or configuration changes. It checks the port plan
in the versioned templates against local TCP bind availability.
"""
from __future__ import annotations

import re
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ("foundry-architect", "foundry-worker", "foundry-auditor")


def main() -> int:
    planned: dict[int, str] = {}
    errors: list[str] = []
    for profile in PROFILES:
        path = ROOT / "profiles" / "gateway-ports.yaml"
        raw = path.read_text(encoding="utf-8")
        pair = re.search(rf"^\s+{re.escape(profile)}:\s*(\d+)\s*$", raw, re.MULTILINE)
        host_match = re.search(r"^\s+bind_host:\s*([^\s#]+)\s*$", raw, re.MULTILINE)
        if not pair or not host_match:
            errors.append(f"invalid gateway port plan for: {profile}")
            continue
        port = int(pair.group(1))
        host = host_match.group(1)
        if port in planned:
            errors.append(f"duplicate reservation: {port} for {planned[port]} and {profile}")
            continue
        planned[port] = profile
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind((host, port))
            print(f"AVAILABLE profile={profile} host={host} port={port}")
        except OSError as exc:
            errors.append(f"occupied profile={profile} host={host} port={port}: {exc}")
        finally:
            sock.close()
    if errors:
        print("GATEWAY_PORT_PLAN_INVALID", file=sys.stderr)
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"GATEWAY_PORT_PLAN_VALID profiles={len(planned)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
