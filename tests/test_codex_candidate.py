from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from foundry_runtime.codex_candidate import commit_candidate
from foundry_runtime.core import Barrier


class CodexCandidateTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name).resolve()
        self.git("init", "-q")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@localhost",
                 "commit", "--allow-empty", "-qm", "Base")
        self.client = Mock()
        self.client.authority.return_value = {"stage": "Implementing"}
        self.binding = {"actor": "worker"}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True).strip()

    def test_commit_only_selected_files(self):
        (self.root / "selected.txt").write_text("selected\n")
        (self.root / "unselected.txt").write_text("unselected\n")
        result = commit_candidate(self.client, self.binding, self.root,
                                  {"paths": ["selected.txt"], "summary": "Implement contract"})
        self.assertEqual(result["candidate_sha"], self.git("rev-parse", "HEAD"))
        self.assertEqual(self.git("show", "--format=", "--name-only", "HEAD"), "selected.txt")
        self.assertEqual(self.git("status", "--porcelain"), "?? unselected.txt")

    def test_paths_and_stale_attempt_fail_before_commit(self):
        head = self.git("rev-parse", "HEAD")
        for path in ("../other.txt", ".git/config", str(self.root / "file")):
            with self.assertRaises(Barrier):
                commit_candidate(self.client, self.binding, self.root, {"paths": [path], "summary": "Rejected"})
        self.client.authority.return_value = {"stage": "QA"}
        with self.assertRaises(Barrier):
            commit_candidate(self.client, self.binding, self.root, {"paths": ["file"], "summary": "Rejected"})
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
