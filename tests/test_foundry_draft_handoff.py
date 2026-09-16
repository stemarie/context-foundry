import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FINALIZER_PATH = ROOT / "profiles/foundry-watchdog/scripts/foundry_draft_handoff.py"


def load_finalizer():
    spec = importlib.util.spec_from_file_location("foundry_draft_handoff", FINALIZER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DraftHandoffFinalizerTests(unittest.TestCase):
    def packet(self):
        authorization = {
            "repository": "stemarie/AI.Contract",
            "origin": "https://github.com/stemarie/AI.Contract.git",
            "api_target": "https://api.github.com/repos/stemarie/AI.Contract",
            "branch": "main",
            "issue_title": "Contract: Phase 0 decisions",
            "issue_body": "# bounded contract\n",
        }
        return "<!-- FOUNDRY_ARCHITECT_ISSUE_AUTHORIZATION_V1\n" + json.dumps(authorization, separators=(",", ":")) + "\n-->"

    def test_creates_one_exact_execution_child_and_reads_it_back(self):
        finalizer = load_finalizer()
        packet = self.packet()
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / ".hermes/kanban/boards/context-foundry/attachments/t_draft/phase0-contract-packet.md"
            artifact.parent.mkdir(parents=True)
            artifact.write_text(packet, encoding="utf-8")
            draft = {
                "task": {
                    "id": "t_draft",
                    "status": "done",
                    "title": "Architect: draft executable contract",
                    "body": "FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution",
                },
                "children": [],
                "events": [{"kind": "completed", "payload": {"artifacts": [str(artifact)]}}],
            }
            seen = {"create": None}

            def run(command, **kwargs):
                if command[-3:] == ["show", "t_draft", "--json"]:
                    return subprocess.CompletedProcess(command, 0, json.dumps(draft), "")
                if "create" in command:
                    seen["create"] = command
                    return subprocess.CompletedProcess(command, 0, json.dumps({"id": "t_execution"}), "")
                if command[-3:] == ["show", "t_execution", "--json"]:
                    body = command[command.index("--body") + 1] if "--body" in command else ""
                    execution = {
                        "task": {"id": "t_execution", "body": seen["create"][seen["create"].index("--body") + 1]},
                        "parents": ["t_draft"],
                    }
                    return subprocess.CompletedProcess(command, 0, json.dumps(execution), "")
                raise AssertionError(command)

            with patch.object(finalizer.Path, "home", return_value=Path(directory)), patch.object(finalizer.subprocess, "run", side_effect=run):
                result = finalizer.finalize("t_draft")

            self.assertEqual(result["status"], "created")
            self.assertEqual(seen["create"][seen["create"].index("--body") + 1], packet)
            self.assertTrue(any(item.startswith("foundry-draft-handoff:t_draft:") for item in seen["create"]))

    def test_existing_execution_child_is_a_noop(self):
        finalizer = load_finalizer()
        draft = {
            "task": {
                "id": "t_draft",
                "status": "done",
                "title": "Architect: draft executable contract",
                "body": "FOUNDRY_DRAFT_HANDOFF_V1\nHandoff kind: contract_execution",
            },
            "children": ["t_execution"],
            "events": [],
        }

        def run(command, **kwargs):
            if command[-3:] == ["show", "t_draft", "--json"]:
                return subprocess.CompletedProcess(command, 0, json.dumps(draft), "")
            if command[-3:] == ["show", "t_execution", "--json"]:
                return subprocess.CompletedProcess(command, 0, json.dumps({"task": {"title": "Architect: execute contract", "status": "ready"}}), "")
            raise AssertionError(command)

        with patch.object(finalizer.subprocess, "run", side_effect=run):
            self.assertEqual(finalizer.finalize("t_draft"), {"status": "already_routed", "draft_id": "t_draft"})


if __name__ == "__main__":
    unittest.main()
