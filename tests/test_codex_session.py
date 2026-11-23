import json
import os
import signal
from pathlib import Path
import sys
import tempfile
import unittest

from foundry_runtime.codex_session import CodexSessions
from foundry_runtime.core import Journal
from foundry_runtime.runtime import Client


@unittest.skipUnless(os.name == "posix", "requires Unix process groups")
class CodexSessionsTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        root = self.root = Path(temp.name)
        self.workspace = root / "worktree"
        self.home = root / "role-home"
        self.workspace.mkdir()
        self.home.mkdir()
        self.journal = Journal(root / "journal.sqlite")
        self.binary = root / "codex"
        self.skills = Path(__file__).resolve().parents[1] / "skills"
        self.binding = {"role": "worker", "project_id": "project", "turn_id": "attempt"}

    def launcher(self, statement):
        self.binary.write_text(
            f"#!{sys.executable}\nimport os, sys, time, json\n"
            "prompt = sys.stdin.read()\n"
            "with open('invocation.json', 'w') as result:\n"
            "    json.dump(dict(args=sys.argv[1:], home=os.environ['CODEX_HOME'], prompt=prompt), result)\n"
            + statement + "\n"
        )
        self.binary.chmod(0o700)
        return CodexSessions(self.journal, self.binary, self.skills)

    def test_launch_arguments_result_and_replay(self):
        launch = self.launcher("sys.exit(7)")
        key = launch.start(self.binding, self.workspace, self.home)
        self.assertEqual(launch.children[key].wait(timeout=5), 0)
        self.assertEqual(launch.result(key), 7)
        invocation = json.loads((self.workspace / "invocation.json").read_text())
        self.assertEqual(invocation["home"], str(self.home))
        self.assertEqual(invocation["args"],
                         ["exec", "--sandbox", "workspace-write", "--cd", str(self.workspace), "--json", "-"])
        self.assertIn("foundry-runtime-worker/SKILL.md", invocation["prompt"])
        restarted = CodexSessions(self.journal, self.binary, self.skills)
        self.assertEqual(restarted.start(self.binding, self.workspace, self.home), key)
        self.assertEqual(restarted.result(key), 7)
        self.assertFalse(restarted.children)

    def test_inspect_running_session_after_restart_and_stop(self):
        launch = self.launcher("time.sleep(25)")
        key = launch.start(self.binding, self.workspace, self.home)
        child = launch.children[key]
        self.addCleanup(child.wait, 5)
        self.addCleanup(lambda: child.kill() if child.poll() is None else None)
        restarted = CodexSessions(self.journal, self.binary, self.skills)
        self.assertEqual(restarted.inspect(key), "running")
        self.assertTrue(launch.stop(key)["stopped_confirmed"])
        self.assertEqual(restarted.inspect(key), "stopped")
        self.assertEqual(restarted.result(key), -signal.SIGTERM)

    def test_role_token_is_passed_outside_argv_and_prompt(self):
        launch = self.launcher("sys.exit(0)")
        secret = "disposable-test-role-token"
        key = launch.start(self.binding, self.workspace, self.home,
                           client=Client("http://127.0.0.1:8080", secret))
        self.assertEqual(launch.children[key].wait(timeout=5), 0)
        invocation = (self.workspace / "invocation.json").read_text()
        self.assertNotIn(secret, invocation)
        self.assertIn("bearer_token_env_var", invocation)
        self.assertIn("shell_environment_policy.exclude", invocation)
        self.assertIn("foundry_candidate.enabled_tools", invocation)
