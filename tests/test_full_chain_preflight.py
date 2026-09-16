import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/foundry_full_chain_preflight.py"
ENVELOPE_FIXTURE = ROOT / "tests/fixtures/full_kanban_show_envelope.json"
spec = importlib.util.spec_from_file_location("foundry_full_chain_preflight", SCRIPT)
assert spec and spec.loader
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)

CONTRACT_ID = "3f8a1d07-3b2e-4ce8-b5ac-8363d13bf7c2"
BASE_SHA = "5bd0dfe42d1cdce1614330fd5892204f22d9cfcb"


def role(role, assignee, title, parents, skills):
    return {
        "role": role,
        "assignee": assignee,
        "title": title,
        "parent_roles": parents,
        "skills": skills,
        "role_read_receipt": "PASS",
        "body": f"AI.Contract: `{CONTRACT_ID}` revision 1\nRole: {role}\nReceipt pointer: preflight-only",
    }


def realistic_show_envelope():
    return json.loads(ENVELOPE_FIXTURE.read_text(encoding="utf-8"))


def valid_manifest():
    return {
        "contract": {"id": CONTRACT_ID, "revision": 1},
        "required_sources": [
            {"id": "technical-spec", "read_receipt": "PASS"},
            {"id": "approved-choices", "read_receipt": "PASS"},
        ],
        "target": {
            "repository": "stemarie/mentorship-platform",
            "origin": "https://github.com/stemarie/mentorship-platform.git",
            "api_target": "https://api.github.com/repos/stemarie/mentorship-platform",
            "branch": "main",
            "workspace_clean": True,
            "base_sha": BASE_SHA,
        },
        "kanban_show_envelope": realistic_show_envelope(),
        "roles": [
            role("Architect", "foundry-architect", "Architect: execute contract", [], ["context-foundry-architect"]),
            role("Worker", "foundry-worker", "Worker: produce evidence", ["Architect"], ["context-foundry-worker"]),
            role("Candidate Auditor", "foundry-auditor", "Candidate Auditor: verify evidence", ["Worker"], ["context-foundry-auditor"]),
        ],
        "continuation": {
            "on_pass": "release_next_governed_stage",
            "on_request_changes": "architect_repair_selection",
            "on_blocked": "architect_evidence_recovery",
        },
    }


class FullChainPreflightTests(unittest.TestCase):
    def test_valid_manifest_passes_without_external_write(self):
        receipt = preflight.validate_manifest(valid_manifest())
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertFalse(receipt["external_writes"])
        self.assertEqual(receipt["validated_roles"], ["Architect", "Worker", "Candidate Auditor"])

    def test_cli_emits_machine_readable_pass_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps(valid_manifest()), encoding="utf-8")
            result = subprocess.run([sys.executable, SCRIPT, "--manifest", manifest], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["verdict"], "PASS")

    def test_inaccessible_required_source_blocks_before_chain_release(self):
        manifest = valid_manifest()
        manifest["required_sources"][1]["read_receipt"] = "HTTP_401"
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "SOURCE_UNAVAILABLE")

    def test_missing_contract_marker_or_literal_header_is_rejected(self):
        manifest = valid_manifest()
        manifest["roles"][1]["body"] = f"AI.Contract: `{CONTRACT_ID}` revision 1\nRole: Worker missing marker"
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "MALFORMED_PACKET")

    def test_wrong_candidate_auditor_title_is_rejected(self):
        manifest = valid_manifest()
        manifest["roles"][2]["title"] = "Auditor: verify evidence"
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "MALFORMED_PACKET")

    def test_missing_role_bound_reader_is_a_capability_failure(self):
        manifest = valid_manifest()
        manifest["roles"][1]["role_read_receipt"] = "MISSING"
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "CAPABILITY_UNAVAILABLE")

    def test_missing_forced_skill_is_a_capability_failure(self):
        manifest = valid_manifest()
        manifest["roles"][1]["skills"] = ["invented-worker-skill"]
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "CAPABILITY_UNAVAILABLE")

    def test_invalid_parent_lineage_is_rejected(self):
        manifest = valid_manifest()
        manifest["roles"][2]["parent_roles"] = ["Architect"]
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "MALFORMED_PACKET")

    def test_dirty_or_mismatched_workspace_is_rejected(self):
        manifest = valid_manifest()
        manifest["target"]["workspace_clean"] = False
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "WORKSPACE_MISMATCH")

    def test_sha_label_or_parser_mismatch_is_rejected(self):
        manifest = valid_manifest()
        manifest["target"]["base_sha"] = "SHA-256: " + BASE_SHA
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "WORKSPACE_MISMATCH")

    def test_task_nested_metadata_is_not_accepted_as_a_root_run_receipt(self):
        manifest = valid_manifest()
        manifest["kanban_show_envelope"] = {
            "task": {"metadata": {"preflight_receipt": "PASS"}},
            "parents": [],
            "runs": [{"metadata": None}],
        }
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "MALFORMED_PACKET")

    def test_continuations_must_be_distinct(self):
        manifest = valid_manifest()
        manifest["continuation"]["on_blocked"] = manifest["continuation"]["on_request_changes"]
        receipt = preflight.validate_manifest(manifest)
        self.assertEqual(receipt["verdict"], "MALFORMED_PACKET")


if __name__ == "__main__":
    unittest.main()
