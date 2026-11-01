"""Durable launch identity and a shared, connection-scoped remote transport gate."""
from __future__ import annotations

import contextlib
import contextvars
import hashlib
import json
import os
from pathlib import Path
import signal
import sqlite3
import subprocess
import time
import uuid


active_gate = contextvars.ContextVar('active_transport_gate', default=None)


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
        # Additive local transport metadata; never assignment/queue authority.
        with self.transaction() as db:
            fields = {row[1] for row in db.execute('PRAGMA table_info(connections)')}
            if 'owner_pid' not in fields:
                db.execute('ALTER TABLE connections ADD COLUMN owner_pid INTEGER')
            if 'server_until' not in fields:
                db.execute('ALTER TABLE connections ADD COLUMN server_until REAL NOT NULL DEFAULT 0')
            if 'transport_tracking' not in fields:
                db.execute('ALTER TABLE connections ADD COLUMN transport_tracking INTEGER NOT NULL DEFAULT 0')
            db.execute("CREATE TABLE IF NOT EXISTS submissions (identity TEXT PRIMARY KEY, intent TEXT NOT NULL, payload TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS transports (identity TEXT PRIMARY KEY, alias TEXT NOT NULL, pid INTEGER)")
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

    def quiescent(self, db, identity=None):
        # Acknowledgement precedes exec in a new session. An absent leader is
        # insufficient: its process group can still contain an orphaned Git child.
        rows = db.execute('SELECT identity,pid FROM transports WHERE alias=?', (self.alias,)).fetchall()
        for row in rows:
            if identity is not None and row['identity'] != identity:
                continue
            if row['pid'] is None:
                raise Barrier('transport launch unknown; explicit reconciliation required')
            try:
                os.killpg(row['pid'], 0)
            except ProcessLookupError:
                db.execute('DELETE FROM transports WHERE identity=?', (row['identity'],))
            except PermissionError:
                raise Barrier('transport process group is not observable') from None
            else:
                raise Barrier('prior transport process group is not stopped')

    def transport_intent(self):
        identity = uuid.uuid4().hex
        with self.journal.transaction() as db:
            db.execute('INSERT INTO transports VALUES(?,?,NULL)', (identity, self.alias))
        return identity

    def transport_finished(self, identity, not_started=False):
        with self.journal.transaction() as db:
            if not_started:
                db.execute('DELETE FROM transports WHERE identity=? AND pid IS NULL', (identity,))
                return
            self.quiescent(db, identity)

    def acquire(self, now=None):
        now = time.time() if now is None else now
        with self.journal.transaction() as db:
            row = db.execute("SELECT * FROM connections WHERE alias=?", (self.alias,)).fetchone()
            if not row:
                db.execute("INSERT INTO connections(alias,state,until,owner,failures,category) VALUES(?, 'closed',0,NULL,0,NULL)", (self.alias,))
                return None
            if row["state"] == "closed":
                return None
            if row["state"] == "half_open" or row["until"] > now:
                raise Barrier("shared GitHub connection paused")
            self.quiescent(db)
            owner = uuid.uuid4().hex
            db.execute("UPDATE connections SET state='half_open',owner=?,owner_pid=?,transport_tracking=1 WHERE alias=?", (owner, os.getpid(), self.alias))
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
                db.execute("UPDATE connections SET state='open',until=?,server_until=?,owner=NULL,owner_pid=NULL,failures=?,category=? WHERE alias=?",
                           (max(row['until'], row['server_until'], now + delay), max(row["server_until"], now + float(retry_after or 0)), failures, category, self.alias))
            elif permit is not None:
                db.execute("UPDATE connections SET state='closed',until=0,server_until=0,owner=NULL,owner_pid=NULL,failures=0,category=NULL WHERE alias=?", (self.alias,))
            # A late success from before a failure must not close an open breaker.

    def release_probe(self, permit):
        """An exited callback is quiescent, but did not establish connection health."""
        if permit is None:
            return
        with self.journal.transaction() as db:
            try:
                self.quiescent(db)
            except Barrier:
                return  # Retain ownership until the transport group is proven stopped.
            db.execute("UPDATE connections SET state='open',owner=NULL,owner_pid=NULL WHERE alias=? AND state='half_open' AND owner=?",
                       (self.alias, permit))

    def operator_probe(self, now=None):
        now = time.time() if now is None else now
        with self.journal.transaction() as db:
            row = db.execute('SELECT * FROM connections WHERE alias=?', (self.alias,)).fetchone()
            if row and row['state'] == 'half_open':
                # Dead controllers may leave remote subprocesses behind. Older
                # journals lack that tracking and cannot establish quiescence.
                if not row['transport_tracking']:
                    raise Barrier('legacy transport quiescence unknown; explicit reconciliation required')
                pid = row['owner_pid']
                if pid is None:
                    raise Barrier('legacy probe owner is unknown; explicit reconciliation required')
                try:
                    os.kill(pid, 0)
                except PermissionError:
                    raise Barrier('probe process identity is not observable') from None
                except ProcessLookupError:
                    self.quiescent(db)
                    db.execute("UPDATE connections SET state='open',owner=NULL,owner_pid=NULL WHERE alias=? AND owner=?",
                               (self.alias, row['owner']))
                else:
                    raise Barrier('shared probe owner is still alive')
            db.execute("UPDATE connections SET until=server_until WHERE alias=? AND state='open'", (self.alias,))
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
        token = active_gate.set(self)
        try:
            with self.journal.transaction() as db:
                prior = db.execute("SELECT * FROM remote_operations WHERE identity=?", (identity,)).fetchone()
                if prior and (prior["alias"] != self.alias or prior["intent"] != hashed):
                    raise Barrier("remote operation identity conflict")
                if not prior:
                    db.execute("INSERT INTO remote_operations VALUES(?,?,?,'started',NULL)", (identity, self.alias, hashed))
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
        finally:
            active_gate.reset(token)
            self.release_probe(permit)


class RemoteFailure(Exception):
    def __init__(self, category, retry_after=None):
        self.category, self.retry_after = category, retry_after
