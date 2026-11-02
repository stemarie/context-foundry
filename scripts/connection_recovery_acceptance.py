#!/usr/bin/env python3
"""Host-only proof for the commissioned BEE1 read-only bridge.

Run this only after QA has accepted the exact candidate. It starts disposable
local bridge/SSH children against BEE1's existing listener and never restarts,
mutates, deploys, or reconfigures BEE1.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
TARGET = "karell@192.168.1.176"


def outside_checkout(path: Path) -> Path:
    path = path.resolve()
    if path.is_relative_to(ROOT):
        raise SystemExit("config and output must be outside the checkout")
    return path


def wait_for(predicate, seconds: float = 20):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise RuntimeError("timed out waiting for owned bridge state")


def alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def bridge(config: Path) -> subprocess.Popen:
    entry = (
        "import sys; sys.path.insert(0, " + repr(str(ROOT)) + "); "
        "from foundry_runtime.local_connection import main; main()"
    )
    return subprocess.Popen(
        [sys.executable, "-I", "-B", "-c", entry, "--config", str(config), "mcp-reader"],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, start_new_session=True,
    )


def request(process: subprocess.Popen, payload: dict, timeout: float = 20) -> dict:
    """Read one response with bounded readiness and bytes, never blocking readline."""
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(json.dumps(payload) + "\n")
    process.stdin.flush()
    stream = process.stdout.buffer
    deadline = time.monotonic() + timeout
    received = bytearray()
    while time.monotonic() < deadline:
        readable, _, _ = select.select([stream], [], [], max(0, deadline - time.monotonic()))
        if not readable:
            break
        chunk = os.read(stream.fileno(), 4096)
        if not chunk:
            raise RuntimeError("owned bridge closed before response")
        received.extend(chunk)
        if b"\n" in received:
            line, _, _rest = bytes(received).partition(b"\n")
            return json.loads(line)
    raise RuntimeError("timed out waiting for owned bridge response")


def master(process: subprocess.Popen) -> tuple[int, str]:
    """Find this bridge's SSH child without putting private paths in evidence."""
    def find():
        children = subprocess.run(["pgrep", "-P", str(process.pid)], capture_output=True, text=True, check=False)
        for value in children.stdout.split():
            command = subprocess.run(["ps", "-ww", "-o", "command=", "-p", value], capture_output=True, text=True, check=False).stdout
            if command.lstrip().startswith("ssh "):
                bits = command.split()
                return int(value), bits[bits.index("-S") + 1]
        return None
    return wait_for(find)


def stopped(pid: int) -> bool:
    return wait_for(lambda: not alive(pid), 10)


def close(process: subprocess.Popen, ssh_pid: int | None) -> None:
    """Reap only children created by this proof, including a suspended master."""
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=15)
        except ProcessLookupError:
            pass
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
    if ssh_pid is not None and alive(ssh_pid):
        os.kill(ssh_pid, signal.SIGKILL)
        stopped(ssh_pid)


def scenario(config: Path, kind: str, evidence: dict, checkpoint) -> dict:
    process = bridge(config)
    ssh_pid = None
    record = {"name": kind, "bridge_pid": process.pid, "cleanup": "pending"}
    evidence["scenarios"].append(record)
    checkpoint()  # Preserve redacted owned-child identity before any teardown.
    try:
        initialized = request(process, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        assert initialized["id"] == 1
        discovery = request(process, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        assert len(discovery["result"]["tools"]) == 16
        rejected = request(process, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "workflow_submit"}})
        assert rejected["result"]["isError"]
        ssh_pid, control = master(process)
        if kind == "disconnect":
            subprocess.run(["ssh", "-S", control, "-O", "exit", TARGET], capture_output=True, timeout=8, check=False)
            error = request(process, {"jsonrpc": "2.0", "id": 7002, "method": "ping"})
            assert error["id"] == 7002
            assert error["error"]["message"] == "private service request unavailable"
        elif kind == "suspended-eof":
            os.kill(ssh_pid, signal.SIGSTOP)
            assert process.stdin is not None
            process.stdin.close()
            process.wait(timeout=20)
            stopped(ssh_pid)
        elif kind == "direct-sigterm":
            # This targets only the owned bridge; it must reap its owned SSH child.
            os.kill(process.pid, signal.SIGTERM)
            process.wait(timeout=20)
            stopped(ssh_pid)
        elif kind == "group-sigterm":
            # Exercise the separately documented process-group shutdown path.
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=20)
            stopped(ssh_pid)
        else:
            assert process.stdin is not None
            process.stdin.close()
            process.wait(timeout=20)
            stopped(ssh_pid)
        record.update({"bridge_exit": process.returncode, "ssh_reaped_before_cleanup": not alive(ssh_pid)})
    finally:
        close(process, ssh_pid)
        record["cleanup"] = "complete"
        record["ssh_reaped_after_cleanup"] = ssh_pid is None or not alive(ssh_pid)
        checkpoint()
    return record


def write_evidence(path: Path, evidence: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(evidence, sort_keys=True, indent=2) + "\n")
    os.chmod(path, 0o600)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config, output = outside_checkout(args.config), outside_checkout(args.output)
    if not config.is_file():
        raise SystemExit("private config does not exist")
    evidence = {"proof": "connection-recovery", "service": "BEE1 existing read-only endpoint", "scenarios": []}
    checkpoint = lambda: write_evidence(output, evidence)
    try:
        for name in ("eof", "direct-sigterm", "group-sigterm", "disconnect", "suspended-eof"):
            scenario(config, name, evidence, checkpoint)
    except Exception as exc:
        evidence["failure"] = {"category": type(exc).__name__}
        checkpoint()
        raise
    checkpoint()


if __name__ == "__main__":
    main()
