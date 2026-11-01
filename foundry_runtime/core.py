"""Durable launch identity and a shared, connection-scoped remote transport gate."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time
import uuid


class Barrier(RuntimeError):
    """Authority, identity, connectivity or quiescence is not established."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class Journal:
    def __init__(self, path):
        self.path = str(Path(path).absolute())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS launches (
                  key TEXT PRIMARY KEY, binding TEXT NOT NULL, nonce TEXT NOT NULL,
                  pid INTEGER, started TEXT, finished REAL);
                CREATE TABLE IF NOT EXISTS connections (
                  alias TEXT PRIMARY KEY, state TEXT NOT NULL, until REAL NOT NULL,
                  owner TEXT, failures INTEGER NOT NULL, category TEXT);
                CREATE TABLE IF NOT EXISTS remote_operations (
                  identity TEXT PRIMARY KEY, alias TEXT NOT NULL, intent TEXT NOT NULL,
                  state TEXT NOT NULL, result TEXT);
            """)
        os.chmod(self.path, 0o600)

    @contextlib.contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def intent(self, binding):
        key = digest(binding)
        with self.transaction() as db:
            row = db.execute("SELECT * FROM launches WHERE key=?", (key,)).fetchone()
            if row:
                return dict(row), False
            nonce = uuid.uuid4().hex
            db.execute("INSERT INTO launches(key,binding,nonce) VALUES(?,?,?)",
                       (key, json.dumps(binding, sort_keys=True), nonce))
            return dict(db.execute("SELECT * FROM launches WHERE key=?", (key,)).fetchone()), True

    def get(self, key):
        with self.transaction() as db:
            row = db.execute("SELECT * FROM launches WHERE key=?", (key,)).fetchone()
            if not row:
                raise Barrier("unknown launch")
            return dict(row)

    def acknowledge(self, key, nonce):
        pid = os.getpid()
        started = process_identity(pid)
        with self.transaction() as db:
            row = db.execute("SELECT * FROM launches WHERE key=?", (key,)).fetchone()
            if not row or row["nonce"] != nonce or row["pid"] is not None:
                raise Barrier("launch acknowledgement conflict")
            db.execute("UPDATE launches SET pid=?,started=? WHERE key=?", (pid, started, key))

    def finish(self, key):
        with self.transaction() as db:
            db.execute("UPDATE launches SET finished=? WHERE key=?", (time.time(), key))

    def inspect(self, key):
        row = self.get(key)
        if row["pid"] is None:
            return "unknown"  # An intent is not proof that spawn did not happen.
        probe = subprocess.run(["/bin/ps", "-p", str(row["pid"]), "-o", "lstart=,stat=,command="],
                               capture_output=True, text=True)
        if probe.returncode != 0:
            # An absent leader does not prove its whole process group stopped.
            try:
                os.killpg(row["pid"], 0)
            except ProcessLookupError:
                return "stopped"
            except PermissionError:
                pass
            return "unknown"
        if row["started"] not in probe.stdout or row["nonce"] not in probe.stdout:
            return "unknown"  # Includes PID reuse; never signal that process.
        return "running"

    def stop(self, key, timeout=10):
        row = self.get(key)
        state = self.inspect(key)
        if state == "unknown":
            raise Barrier("execution identity unknown; recovery is blocked")
        if state == "stopped":
            return {"key": key, "stopped_confirmed": True}
        os.killpg(row["pid"], signal.SIGTERM)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self.inspect(key) == "stopped":
                return {"key": key, "stopped_confirmed": True}
            time.sleep(0.05)
        # Still verify the leader identity before escalating within its own group.
        if self.inspect(key) == "running":
            os.killpg(row["pid"], signal.SIGKILL)
        raise Barrier("stop sent; quiescence still requires reconciliation")


def process_identity(pid):
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "lstart="], capture_output=True, text=True, check=True)
    return result.stdout.strip()


class Gate:
    """One shared SQLite file and stable credential alias across all projects.

    Operation results must be safe identities (SHA/reference), never raw responses.
    A started write with no recorded response is uncertain and is reconciled first.
    """
    QUALIFYING = {"connection", "authentication", "rate_limit", "service"}

    def __init__(self, journal, alias):
        self.journal, self.alias = journal, alias

    def acquire(self, now=None):
        now = time.time() if now is None else now
        with self.journal.transaction() as db:
            row = db.execute("SELECT * FROM connections WHERE alias=?", (self.alias,)).fetchone()
            if not row:
                db.execute("INSERT INTO connections VALUES(?, 'closed',0,NULL,0,NULL)", (self.alias,))
                return None
            if row["state"] == "closed":
                return None
            if row["state"] == "half_open" or row["until"] > now:
                raise Barrier("shared GitHub connection paused")
            owner = uuid.uuid4().hex
            db.execute("UPDATE connections SET state='half_open',owner=? WHERE alias=?", (owner, self.alias))
            return owner

    def outcome(self, permit, category=None, retry_after=None, now=None):
        now = time.time() if now is None else now
        if category is not None and category not in self.QUALIFYING and category != "resource":
            raise ValueError("unsafe/unknown failure category")
        with self.journal.transaction() as db:
            row = db.execute("SELECT * FROM connections WHERE alias=?", (self.alias,)).fetchone()
            if not row or (permit is not None and row["owner"] != permit):
                raise Barrier("probe ownership lost")
            if row["state"] == "half_open" and permit is None:
                raise Barrier("not the shared probe owner")
            if category in self.QUALIFYING:
                failures = row["failures"] + 1
                delay = min(300, 30 * 2 ** min(failures - 1, 4))
                if retry_after is not None:
                    delay = max(delay, float(retry_after))
                db.execute("UPDATE connections SET state='open',until=?,owner=NULL,failures=?,category=? WHERE alias=?",
                           (now + delay, failures, category, self.alias))
            elif permit is not None:
                db.execute("UPDATE connections SET state='closed',until=0,owner=NULL,failures=0,category=NULL WHERE alias=?", (self.alias,))
            # A late success from before a failure must not close an open breaker.

    def operator_probe(self, now=None):
        with self.journal.transaction() as db:
            db.execute("UPDATE connections SET until=0 WHERE alias=? AND state='open'", (self.alias,))
        return self.acquire(now)

    def run(self, identity, intent, operation, reconcile=None):
        hashed = digest(intent)
        # A cached identity is local evidence, never a successful recovery probe.
        with self.journal.transaction() as db:
            prior = db.execute("SELECT * FROM remote_operations WHERE identity=?", (identity,)).fetchone()
            if prior and (prior["alias"] != self.alias or prior["intent"] != hashed):
                raise Barrier("remote operation identity conflict")
            if prior and prior["state"] == "complete":
                return json.loads(prior["result"])
        permit = self.acquire()
        with self.journal.transaction() as db:
            prior = db.execute("SELECT * FROM remote_operations WHERE identity=?", (identity,)).fetchone()
            if prior and (prior["alias"] != self.alias or prior["intent"] != hashed):
                raise Barrier("remote operation identity conflict")
            if not prior:
                db.execute("INSERT INTO remote_operations VALUES(?,?,?,'started',NULL)", (identity, self.alias, hashed))
        try:
            if prior:
                if prior['state'] == 'complete':
                    return json.loads(prior['result'])
                if reconcile is None:
                    raise Barrier("remote write uncertain; authoritative read required")
                result = reconcile()
                if result is None:
                    raise Barrier("remote outcome remains unknown")
            else:
                result = operation()
            encoded = json.dumps(result)
            with self.journal.transaction() as db:
                db.execute("UPDATE remote_operations SET state='complete',result=? WHERE identity=?", (encoded, identity))
            self.outcome(permit)
            return result
        except RemoteFailure as exc:
            self.outcome(permit, exc.category, exc.retry_after)
            raise Barrier("remote operation failed; reconcile before retry") from None


class RemoteFailure(Exception):
    def __init__(self, category, retry_after=None):
        self.category, self.retry_after = category, retry_after
