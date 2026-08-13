#!/usr/bin/env python3
"""Validate a Context Foundry evidence artifact against its work packet."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

VALID_CLASSIFICATIONS = {"fact", "inference", "recommendation", "unknown"}
VALID_CONFIDENCE = {"high", "medium", "low"}


def fail(message: str) -> None:
    raise SystemExit(f"INVALID: {message}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    args = parser.parse_args()

    evidence = json.loads(args.evidence.read_text())
    packet_text = args.packet.read_text()
    packet_id = evidence.get("packet_id")
    question = evidence.get("question")
    if not isinstance(packet_id, str) or not packet_id:
        fail("missing packet_id")
    if f"packet_id: {packet_id}" not in packet_text:
        fail("packet_id does not match packet")
    if not isinstance(question, str) or not question:
        fail("missing question")
    if f"question: {question}" not in packet_text:
        fail("question does not match packet")
    claims = evidence.get("claims")
    if not isinstance(claims, list) or not claims:
        fail("claims must be a non-empty list")
    for claim in claims:
        if claim.get("classification") not in VALID_CLASSIFICATIONS:
            fail(f"invalid classification in {claim.get('claim_id')}")
        if claim.get("confidence") not in VALID_CONFIDENCE:
            fail(f"invalid confidence in {claim.get('claim_id')}")
        if not isinstance(claim.get("limitations"), list):
            fail(f"missing limitations in {claim.get('claim_id')}")
        evidence_rows = claim.get("evidence")
        if claim["classification"] == "fact" and not evidence_rows:
            fail(f"uncited fact: {claim.get('claim_id')}")
        if evidence_rows:
            for row in evidence_rows:
                for key in ("source_id", "location", "excerpt", "observed_at"):
                    if not isinstance(row.get(key), str) or not row[key]:
                        fail(f"missing {key} in {claim.get('claim_id')}")
    print(json.dumps({"status": "valid", "packet_id": packet_id, "claim_count": len(claims)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
