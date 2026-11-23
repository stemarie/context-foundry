"""Local, journaled Codex sessions for the Foundry Coordinator."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

if __package__:
    from .core import Barrier, Journal

ROLES = ("architect", "worker", "qa", "deliver", "operate")
READ_TOOLS = ["project_get", "milestone_get", "milestone_list", "milestone_contract_list",
              "contract_assignment", "contract_get", "workflow_agents", "workflow_list",
              "workflow_get", "workflow_assignments", "workflow_history"]
ROLE_WRITES = {
    "architect": ["milestone_contract_create", "workflow_define", "workflow_ready"],
    "worker": ["workflow_submit", "workflow_heartbeat"],
    "qa": ["workflow_verdict"],
    "deliver": ["workflow_integrate", "workflow_complete", "workflow_publish_history", "workflow_record"],
    "operate": [],
}


class CodexSessions:
    def __init__(self, journal, executable, skills):
        self.journal = journal
        self.executable = Path(executable).resolve(strict=True)
        self.skills = Path(skills).resolve(strict=True)
        self.children = {}

    def start(self, binding, workspace, codex_home, *, client=None):
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
        args = [str(self.executable), "exec", "--sandbox", sandbox, "--cd", str(workspace), "--json"]
        prompt = (
            f"Read {skill} and invoke the core role skill it references. "
            "Use the configured role's AI.Contract connection. "
            f"Verify this invocation against current service state.\n{json.dumps(binding)}\n"
        )
        env = {name: os.environ[name] for name in ("HOME", "LANG", "PATH", "TERM", "XDG_RUNTIME_DIR") if name in os.environ}
        env["CODEX_HOME"] = str(codex_home)
        if client is not None:
            env["FOUNDRY_ROLE_TOKEN"] = client.token
            overrides = {
                "mcp_servers.ai_contract.url": client.origin + "/mcp",
                "mcp_servers.ai_contract.bearer_token_env_var": "FOUNDRY_ROLE_TOKEN",
                "mcp_servers.ai_contract.required": True,
                "mcp_servers.ai_contract.enabled_tools": READ_TOOLS + ROLE_WRITES[role],
                "mcp_servers.ai_contract.default_tools_approval_mode": "approve",
                "shell_environment_policy.exclude": ["FOUNDRY_ROLE_TOKEN"],
            }
            if role == "worker":
                broker = Path(__file__).with_name("codex_candidate.py").resolve(strict=True)
                overrides.update({
                    "mcp_servers.foundry_candidate.command": sys.executable,
                    "mcp_servers.foundry_candidate.args": [
                        "-I", "-B", str(broker), client.origin, str(workspace), json.dumps(binding),
                    ],
                    "mcp_servers.foundry_candidate.env_vars": ["FOUNDRY_ROLE_TOKEN"],
                    "mcp_servers.foundry_candidate.required": True,
                    "mcp_servers.foundry_candidate.enabled_tools": ["commit_candidate"],
                    "mcp_servers.foundry_candidate.default_tools_approval_mode": "approve",
                })
            for setting, value in overrides.items():
                serialized = str(value).lower() if isinstance(value, bool) else json.dumps(value)
                args.extend(("-c", setting + "=" + serialized))
        args.append("-")
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

    def recorded(self, project_id, *, attempt_id=None):
        with self.journal.transaction() as db:
            if attempt_id is None:
                rows = db.execute("SELECT key,binding FROM launches WHERE finished IS NULL").fetchall()
            else:
                rows = db.execute(
                    "SELECT key,binding FROM launches WHERE json_extract(binding,'$.attempt_id')=?",
                    (attempt_id,),
                ).fetchall()
        for row in rows:
            binding = json.loads(row["binding"])
            if binding.get("adapter") == "codex" and binding.get("project_id") == project_id:
                yield row["key"], binding

    def _root(self, key):
        return Path(self.journal.path).parent / "codex-sessions" / key

    def inspect(self, key):
        child = self.children.get(key)
        if child is not None:
            child.poll()
        state = self.journal.inspect(key)
        if state == "unknown" and self.journal.get(key)["pid"] is not None:
            # The wrapper can exit between poll and ps, before it is reaped.
            # Recheck without signalling or replacing that execution.
            time.sleep(0.05)
            if child is not None:
                child.poll()
            state = self.journal.inspect(key)
        return state

    def stop(self, key):
        # Reap children owned by this controller while Journal proves group exit.
        if key in self.children:
            child = self.children[key]
            if self.inspect(key) == "running":
                try:
                    os.killpg(child.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
            if child.poll() is not None:
                deadline = time.monotonic() + 5
                while self.inspect(key) == "unknown" and time.monotonic() < deadline:
                    time.sleep(0.02)
        return self.journal.stop(key)

    def result(self, key):
        if self.inspect(key) != "stopped":
            return None
        path = self._root(key) / "exit.json"
        return json.loads(path.read_text())["returncode"] if path.is_file() else None


def _child(argv):
    journal_path, key, nonce, *command = argv
    # Keep the session leader identifiable while Codex handles group SIGTERM.
    stopping = False

    def request_stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, request_stop)
    journal = Journal(journal_path)
    prompt = sys.stdin.read()
    journal.acknowledge(key, nonce)
    status = -signal.SIGTERM
    if not stopping:
        with subprocess.Popen(command, stdin=subprocess.PIPE, text=True) as child:
            if stopping:
                child.terminate()
            child.communicate(prompt)
            status = child.returncode
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
