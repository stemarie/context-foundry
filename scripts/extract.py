#!/usr/bin/env python3
"""Extract bounded UTF-8 text from a manifest source into a project artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--max-chars", type=int, default=20000)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text())
    source = next((s for s in manifest["sources"] if s["source_id"] == args.source_id), None)
    if source is None:
        raise SystemExit(f"unknown source_id: {args.source_id}")
    if source["type"] != "file" or source["access_policy"] != "read-only":
        raise SystemExit("Phase 1 extractor supports only read-only file sources")
    text = Path(source["locator"]).read_text(encoding="utf-8", errors="replace")
    text = text[:args.max_chars]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"source_id": args.source_id, "output": str(args.output), "characters": len(text)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
