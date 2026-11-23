"""Minimal Worker-only MCP tool for committing files in the assigned worktree."""

import json
import os
from pathlib import Path
import subprocess
import sys

if __package__:
    from .core import Barrier
    from .local_connection import request_id
    from .runtime import Client


TOOL = {
    "name": "commit_candidate",
    "description": "Commit selected, already verified files in this assigned Worker worktree.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "paths": {"type": "array", "items": {"type": "string"}, "minItems": 1},
            "summary": {"type": "string", "minLength": 1},
        },
        "required": ["paths", "summary"],
        "additionalProperties": False,
    },
}


def commit_candidate(client, binding, workspace, arguments):
    job = client.authority(binding, "worker")
    if job["stage"] != "Implementing":
        raise Barrier("no live implementation authority")
    paths = arguments["paths"]
    summary = arguments["summary"]
    if (not isinstance(paths, list) or not 1 <= len(paths) <= 200 or
            not isinstance(summary, str) or not summary.strip() or len(summary) > 500 or "\0" in summary):
        raise Barrier("invalid candidate commit arguments")
    for relative in paths:
        if not isinstance(relative, str) or not relative or "\0" in relative:
            raise Barrier("invalid candidate path")
        path = Path(relative)
        absolute = workspace / path
        if (path.is_absolute() or any(part in (".git", "..") for part in path.parts) or
                not absolute.resolve().is_relative_to(workspace) or absolute == workspace or absolute.is_dir()):
            raise Barrier("candidate path must be a file within the assigned worktree")

    def git(*args):
        return subprocess.run(
            ["git", "--literal-pathspecs", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
            cwd=workspace, capture_output=True, text=True, check=True, timeout=30,
        ).stdout.strip()

    if Path(git("rev-parse", "--show-toplevel")).resolve() != workspace:
        raise Barrier("candidate workspace is not the assigned Git root")
    if git("diff", "--cached", "--name-only"):
        raise Barrier("candidate worktree has an existing staged change")
    git("diff", "--check", "--", *paths)
    git("add", "-A", "--", *paths)
    try:
        name = binding["actor"]
        git("-c", "user.name=" + name, "-c", "user.email=foundry-worker@localhost",
            "commit", "--no-gpg-sign", "-m", summary)
    except BaseException:
        git("restore", "--staged", "--", *paths)
        raise
    return {"candidate_sha": git("rev-parse", "HEAD")}


def rpc(message, client, binding, workspace):
    identifier = request_id(message)
    if identifier is None:
        return None
    result = {"jsonrpc": "2.0", "id": identifier}
    method = message.get("method")
    params = message.get("params") or {}
    if method == "initialize":
        result["result"] = {
            "protocolVersion": params.get("protocolVersion", "2024-11-05"),
            "serverInfo": {"name": "foundry-candidate", "version": "1"},
            "capabilities": {"tools": {}},
        }
    elif method == "ping":
        result["result"] = {}
    elif method == "tools/list":
        result["result"] = {"tools": [TOOL]}
    elif method == "tools/call" and params.get("name") == TOOL["name"]:
        try:
            content = commit_candidate(client, binding, workspace, params["arguments"])
            result["result"] = {"content": [{"type": "text", "text": json.dumps(content)}]}
        except (Barrier, KeyError, ValueError, OSError, subprocess.SubprocessError):
            result["result"] = {"isError": True, "content": [
                {"type": "text", "text": "Candidate commit rejected. Inspect assignment and worktree."},
            ]}
    else:
        result["error"] = {"code": -32601, "message": "method unavailable"}
    return result


def main():
    origin, workspace, raw_binding = sys.argv[1:]
    client = Client(origin, os.environ.pop("FOUNDRY_ROLE_TOKEN"))
    binding = json.loads(raw_binding)
    workspace = Path(workspace).resolve(strict=True)
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = rpc(message, client, binding, workspace)
        except (ValueError, AttributeError, TypeError):
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "invalid request"}}
        if response is not None:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from foundry_runtime.core import Barrier
    from foundry_runtime.local_connection import request_id
    from foundry_runtime.runtime import Client

    main()
