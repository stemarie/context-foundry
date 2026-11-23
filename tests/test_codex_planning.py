import hashlib
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from foundry_runtime.codex_planning import BlockedPlanning, Planning, specification_bytes


class CodexPlanningTest(unittest.TestCase):
    def test_git_reads_pinned_commit_instead_of_working_tree(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=root, text=True).strip()
            git("init", "-q")
            (root / "docs").mkdir()
            path = root / "docs" / "spec.md"
            path.write_text("# Pinned\n")
            git("add", "docs/spec.md")
            git("-c", "user.name=fixture", "-c", "user.email=fixture@localhost", "commit", "-qm", "pin")
            revision = git("rev-parse", "HEAD")
            path.write_text("# Uncommitted\n")
            spec = {"kind": "git", "source_revision": revision, "source_path": "docs/spec.md"}
            self.assertEqual(specification_bytes(spec, root), b"# Pinned\n")
            with self.assertRaises(BlockedPlanning):
                specification_bytes(dict(spec, source_path="missing.md"), root)

    def test_snapshot_must_match_digest(self):
        content = "# Approved\n"
        spec = {"kind": "snapshot", "snapshot_markdown": content,
                "snapshot_sha256": hashlib.sha256(content.encode()).hexdigest()}
        self.assertEqual(specification_bytes(spec, None), content.encode())
        with self.assertRaises(BlockedPlanning):
            specification_bytes(dict(spec, snapshot_markdown="replacement"), None)

    def setUp(self):
        self.project = "00000000-0000-4000-8000-000000000001"
        self.milestone = "00000000-0000-4000-8000-000000000002"
        self.request = {"id": "00000000-0000-4000-8000-000000000003", "project_id": self.project,
                        "milestone_id": self.milestone, "specification_id": "spec",
                        "architect": "architect", "coordinator": "coordinator"}
        self.runner = SimpleNamespace(
            architect=SimpleNamespace(name="architect"), coordinator=SimpleNamespace(name="coordinator"),
            active={}, project_id=self.project, checkout=Path("/project"), sessions=Mock(),
            launch=Mock(), work=Mock(), client=Mock(),
        )
        self.runner.sessions.recorded.return_value = []
        self.plan = Planning(self.runner)
        self.plan.requests = Mock(return_value=[self.request])
        self.plan.check_milestone = Mock()
        self.plan.materialize = Mock(return_value={"planning_request_id": self.request["id"]})
        self.plan.finish = Mock()
        self.project_view = {"id": self.project, "planning_through": 1}

    def test_same_claim_does_not_launch_again_after_reconnect(self):
        self.plan.advance(self.project_view, 3)
        self.runner.launch.assert_called_once()
        self.runner.sessions.recorded.return_value = [
            ("session", {"actor": "architect", "turn_id": self.request["id"]}),
        ]
        self.runner.sessions.inspect.return_value = "running"
        self.plan.advance(self.project_view, 1)
        self.runner.launch.assert_called_once()
        self.plan.finish.assert_not_called()
        self.runner.sessions.inspect.return_value = "stopped"
        self.request["architect_evidence"] = "Ready revision persisted"
        self.plan.advance(self.project_view, 1)
        self.assertEqual(self.plan.finish.call_args.args[1], "Completed")

    def test_missing_source_blocks_without_launch(self):
        self.plan.materialize.side_effect = BlockedPlanning("missing")
        self.plan.advance(self.project_view, 3)
        self.runner.launch.assert_not_called()
        self.plan.finish.assert_called_once_with(self.request, "Blocked", "missing")

    def test_stage_empty_without_request(self):
        self.plan.requests.return_value = []
        self.plan.advance(self.project_view, 3)
        self.runner.launch.assert_not_called()
        self.runner.work.assert_not_called()
