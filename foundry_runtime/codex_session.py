"""Local, journaled Codex sessions for the Foundry Coordinator."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time

if __package__:
    from .core import Barrier, Journal

ROLES = ("architect", "worker", "qa", "deliver", "operate")


class CodexSessions:
    def __init__(self, journal, executable, skills):
        self.journal = journal
        self.executable = Path(executable).resolve(strict=True)
        self.skills = Path(skills).resolve(strict=True)
        self.children = {}

    def start(self, binding, workspace, codex_home):
        role = binding.get("role")
        if role not in ROLES or not binding.get("project_id") or not binding.get("turn_id"):
            raise Barrier("Codex session requires a role, project and stable turn identity")
        workspace = Path(workspace).resolve(strict=True)
        codex_home = Path(codex_home).resolve(strict=True)
        skill = self.skills / ("foundry-runtime-" + role) / "SKILL.md"
        if not workspace.is_dir() or not codex_home.is_dir() or not skill.is_file():
            raise Barrier("Codex session workspace, configuration or role skill is missing")
        trusted_paths = (self.executable, self.skills, codex_home, Path(__file__).resolve())
        if any(workspace == path or workspace in path.parents for path in trusted_paths):
            raise Barrier("Codex executable, runtime and role configuration must be outside the worktree")

        row, created = self.journal.intent({"adapter": "codex", **binding})
        key = row["key"]
        if not created:
            if self.inspect(key) == "unknown":
                raise Barrier("previous Codex launch is uncertain")
            return key

        root = self._root(key)
        root.mkdir(mode=0o700, parents=True)
        sandbox = "read-only" if role in ("architect", "qa", "operate") else "workspace-write"
        args = [str(self.executable), "exec", "--sandbox", sandbox, "--cd", str(workspace), "--json", "-"]
        prompt = (
            f"Read {skill} and invoke the core role skill it references. "
            "Use the configured role's AI.Contract connection. "
            f"Verify this invocation against current service state.\n{json.dumps(binding)}\n"
        )
        env = {name: os.environ[name] for name in ("HOME", "LANG", "PATH", "TERM") if name in os.environ}
        env["CODEX_HOME"] = str(codex_home)
        command = [sys.executable, "-I", "-B", str(Path(__file__).resolve()), self.journal.path,
                   key, row["nonce"], *args]
        with (root / "session.log").open("xb") as stream:
            child = subprocess.Popen(command, cwd=workspace, env=env, start_new_session=True,
                                     stdin=subprocess.PIPE, stdout=stream, stderr=stream, text=True)
        self.children[key] = child
        try:
            child.stdin.write(prompt)
        finally:
            child.stdin.close()
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if self.journal.get(key)["pid"] is not None:
                return key
            if child.poll() is not None:
                break
            time.sleep(0.02)
        raise Barrier("Codex launch acknowledgement is missing")

    def recorded(self, project_id):
        with self.journal.transaction() as db:
            rows = db.execute("SELECT key,binding FROM launches WHERE finished IS NULL").fetchall()
        for row in rows:
            binding = json.loads(row["binding"])
            if binding.get("adapter") == "codex" and binding.get("project_id") == project_id:
                yield row["key"], binding

    def _root(self, key):
        return Path(self.journal.path).parent / "codex-sessions" / key

    def inspect(self, key):
        if key in self.children:
            self.children[key].poll()
        return self.journal.inspect(key)

    def stop(self, key):
        # Reap children owned by this controller while Journal proves group exit.
        if key in self.children:
            child = self.children[key]
            if self.inspect(key) == "running":
                import signal
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        return self.journal.stop(key)

    def result(self, key):
        if self.inspect(key) != "stopped":
            return None
        path = self._root(key) / "exit.json"
        return json.loads(path.read_text())["returncode"] if path.is_file() else None


def _child(argv):
    journal_path, key, nonce, *command = argv
    journal = Journal(journal_path)
    prompt = sys.stdin.read()
    journal.acknowledge(key, nonce)
    status = subprocess.run(command, input=prompt, text=True, check=False).returncode
    root = Path(journal.path).parent / "codex-sessions" / key
    path = root / "exit.tmp"
    path.write_text(json.dumps({"returncode": status}))
    path.replace(root / "exit.json")
    journal.finish(key)


if __name__ == "__main__":
    # Isolated Python ignores candidate-controlled import paths.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from foundry_runtime.core import Barrier, Journal

    _child(sys.argv[1:])
