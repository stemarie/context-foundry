import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "profiles/foundry-architect/adapters/phase0_full_chain_preflight.py"
spec = importlib.util.spec_from_file_location("phase0_full_chain_preflight", PATH)
assert spec and spec.loader
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)


class Phase0FullChainPreflightTests(unittest.TestCase):
    def setUp(self):
        self.card = {
            "id": "t_deadbeef", "assignee": "foundry-architect",
            "title": "Architect: execute Phase 0 contract packet", "status": "running",
            "workspace_path": "/tmp/mentorship-platform",
            "body": "\n".join((
                "<!-- FOUNDRY_ARCHITECT_AICONTRACT_AUTHORIZATION_V1",
                json.dumps({"repository":"stemarie/AI.Contract","api_target":"https://api.github.com/repos/stemarie/AI.Contract","issue_title":"Contract: Phase 0","issue_body":"contract"}, sort_keys=True), "-->",
                "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1",
                json.dumps({"repository":"stemarie/mentorship-platform","origin":"https://github.com/stemarie/mentorship-platform.git","api_target":"https://api.github.com/repos/stemarie/mentorship-platform","branch":"main","issue_title":"Phase 0","issue_body":"tracker"}, sort_keys=True), "-->",
                "<!-- FOUNDRY_PHASE0_FULL_CHAIN_PREFLIGHT_V1",
                json.dumps({"repository":"stemarie/mentorship-platform","origin":"https://github.com/stemarie/mentorship-platform.git","branch":"main","frozen_base":"a" * 40,"document_ids":["1C8tLVdqncOkTbaIkfXfrn7U8lzr-XeZQyM7SikqO7M8","1B5hQiaKm6KCZLv0kDe4FQS_18ZReePDq8_yMusA0L98"]}, sort_keys=True), "-->"
            )),
        }

    def git(self, workspace, *args):
        self.assertEqual(workspace, "/tmp/mentorship-platform")
        if args == ("remote", "get-url", "origin"):
            return "https://github.com/stemarie/mentorship-platform.git"
        if args == ("ls-remote", "origin", "refs/heads/main"):
            return "a" * 40 + "\trefs/heads/main"
        self.fail(args)

    def test_passes_only_exact_authorized_target_binding(self):
        result = adapter.preflight(self.card, self.git)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["target"]["repository"], "stemarie/mentorship-platform")
        self.assertNotIn("tracker", json.dumps(result))

    def test_rejects_missing_preflight_block_wrong_origin_and_wrong_base(self):
        with self.assertRaisesRegex(adapter.PreflightError, "preflight authorization"):
            adapter.preflight({**self.card, "body": self.card["body"].replace("FOUNDRY_PHASE0_FULL_CHAIN_PREFLIGHT_V1", "MISSING", 1)}, self.git)
        with self.assertRaisesRegex(adapter.PreflightError, "workspace origin"):
            adapter.preflight({**self.card, "workspace_path": "/tmp/other"}, lambda *_: "https://github.com/stemarie/other.git")
        with self.assertRaisesRegex(adapter.PreflightError, "frozen base"):
            adapter.preflight(self.card, lambda workspace, *args: "https://github.com/stemarie/mentorship-platform.git" if args[0] == "remote" else "b" * 40 + "\trefs/heads/main")


if __name__ == "__main__":
    unittest.main()
