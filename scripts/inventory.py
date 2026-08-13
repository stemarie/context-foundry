#!/usr/bin/env python3
"""Create a deterministic manifest for explicitly supplied local files."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source", action="append", required=True, type=Path)
    parser.add_argument("--trust-class", default="internal", choices=["trusted", "internal", "external-untrusted"])
    args = parser.parse_args()

    captured_at = dt.datetime.now(dt.timezone.utc).isoformat()
    sources = []
    for ordinal, raw_path in enumerate(args.source, start=1):
        path = raw_path.expanduser().resolve()
        if not path.is_file():
            raise SystemExit(f"not a regular file: {path}")
        sources.append({
            "source_id": f"src-{ordinal:03d}",
            "type": "file",
            "locator": str(path),
            "title": path.name,
            "trust_class": args.trust_class,
            "content_hash": sha256(path),
            "captured_at": captured_at,
            "modified_at": dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).isoformat(),
            "extract_path": None,
            "index_path": None,
            "access_policy": "read-only",
            "retention": "project",
            "notes": "Manifested by deterministic local inventory; source content remains read-only."
        })
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps({"version": 1, "sources": sources}, indent=2) + "\n")
    print(json.dumps({"manifest": str(args.manifest), "source_count": len(sources)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
