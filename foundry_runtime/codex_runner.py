"""Event-driven Coordinator for local Codex Architect, Worker and QA sessions."""

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import fcntl
import os
from pathlib import Path
import queue
import subprocess
import threading
import uuid

from .codex_delivery import Delivery
from .codex_session import CodexSessions
from .core import Barrier, Journal, digest
from .events import workflow_events
from .local_connection import orderly_sigterm, private_json
from .runtime import Client, ServiceUnavailable, parse_service_time


@dataclass(frozen=True)
class Actor:
    name: str
    home: Path
    client: Client


class Coordinator:
    def __init__(self, config, sessions):
        self.config = config
        self.sessions = sessions
        self.project_id = config["project_id"]
        self.milestone_id = config["milestone_id"]
        self.checkout = Path(config["checkout"]).resolve(strict=True)
        self.root = Path(sessions.journal.path).parent / "worktrees" / self.project_id
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.client = self.actor(config["coordinator"], "coordinator").client
        self.architect = self.actor(config["architect"], "architect")
        self.workers = self.pool(config["workers"], "writer")
        self.reviewers = self.pool(config["reviewers"], "auditor")
        names = [self.architect.name, *self.workers, *self.reviewers]
        if len(set(names)) != len(names) or not self.workers or not self.reviewers:
            raise Barrier("require distinct configured Architect, Workers and QA identities")
        homes = [actor.home for actor in (self.architect, *self.workers.values(), *self.reviewers.values())]
        if len(set(homes)) != len(homes):
            raise Barrier("each Codex actor requires a separate configuration home")
        self.active = {}
        self.wake = lambda: None
        delivery = config.get("delivery")
        self.delivery = Delivery(self, delivery) if delivery else None
        for key, binding in self.sessions.recorded(self.project_id):
            state = self.sessions.inspect(key)
            if state == "unknown":
                raise Barrier("previous Codex launch is uncertain: " + key)
            if state == "running":
                self.active[key] = (binding["role"], binding.get("attempt_id"), binding["actor"], binding["turn_id"])

    def actor(self, entry, role):
        credential = private_json(entry["credential"])
        if set(credential["scopes"]) != {"read", "write", role} or not credential["token"]:
            raise Barrier("credential lacks the configured role scope")
        return Actor(credential["name"], Path(entry.get("codex_home", ".")).resolve(),
                     Client(self.config["origin"], credential["token"]))

    def pool(self, entries, role):
        actors = [self.actor(entry, role) for entry in entries]
        if len({actor.name for actor in actors}) != len(actors):
            raise Barrier("duplicate configured actor")
        return {actor.name: actor for actor in actors}

    def work(self, operation, *, client=None, mutation=False, **fields):
        command = {"project_id": self.project_id, **fields}
        if mutation:
            command.setdefault("idempotency_key", uuid.uuid4().hex)
        return (self.client if client is None else client).workflow(operation, command)

    def jobs(self):
        jobs, after = [], 0
        while True:
            page = self.work("list", after=after, limit=100).get("jobs", [])
            jobs.extend(page)
            if len(page) < 100:
                return jobs
            after = page[-1]["queue_sequence"]

    def git(self, *args):
        return subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args],
                              cwd=self.checkout, text=True, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()

    def workspace(self, kind, identity, sha):
        path = self.root / (kind + "-" + str(uuid.UUID(identity)))
        if not path.exists():
            self.git("worktree", "add", "--detach", str(path), sha)
        worktrees = self.git("worktree", "list", "--porcelain").splitlines()
        if "worktree " + str(path) not in worktrees:
            raise Barrier("expected a registered attempt worktree")
        if kind == "qa":
            actual = self.git("-C", str(path), "rev-parse", "HEAD")
            if actual != sha or self.git("-C", str(path), "status", "--porcelain", "--untracked-files=all"):
                raise Barrier("QA worktree must match the clean assigned candidate")
        return path

    def project(self):
        path = "/api/v1/projects/" + self.project_id
        project = self.client.call(path, method="GET")["project"]
        milestone = self.client.call(path + "/milestones/" + self.milestone_id, method="GET")["milestone"]
        origin = self.git("remote", "get-url", "origin")
        expected = "https://github.com/" + project["repository"]
        if origin not in (expected, expected + ".git"):
            raise Barrier("checkout remote does not match the AI.Contract project")
        if milestone["ordinal"] > project["planning_through"]:
            raise Barrier("milestone is outside the approved planning boundary")
        return project

    @staticmethod
    def binding(job):
        return dict(contract_id=job["contract_id"], revision=job["revision"]["number"],
                    digest=job["revision"]["digest"], attempt_id=job["attempt"]["id"])

    def launch(self, role, actor, turn, workspace, **binding):
        payload = dict(role=role, project_id=self.project_id, milestone_id=self.milestone_id,
                       actor=actor.name, turn_id=turn, **binding)
        key = self.sessions.start(payload, workspace, actor.home)
        state = self.sessions.inspect(key)
        if state == "unknown":
            raise Barrier("Codex session ownership is uncertain")
        if state == "running":
            self.active[key] = (role, binding.get("attempt_id"), actor.name, turn)
        return key, state

    def actor_busy_on_other_turn(self, name, turn):
        return any(actor == name and active_turn != turn for _, _, actor, active_turn in self.active.values())

    def fresh(self, job):
        current = self.work("get", contract_id=job["contract_id"])["job"]
        return current if current == job else None

    def handle_job(self, job):
        stage = job["stage"]
        if stage not in ("Implementing", "QA"):
            return
        job = self.fresh(job)
        if job is None:
            return
        binding = self.binding(job)
        attempt_id = binding["attempt_id"]
        attempt = job["attempt"]
        worker = self.workers.get(attempt["worker"])
        if worker is None:
            raise Barrier("active assignment belongs to an unconfigured Worker")
        if parse_service_time(attempt["expires_at"]) <= datetime.now(timezone.utc):
            raise Barrier("attempt lease expired and needs stopped-confirmed recovery: " + attempt_id)
        if stage == "Implementing":
            candidate_id = job.get("candidate", {}).get("id", "initial")
            turn = attempt_id + ":" + candidate_id
            if self.actor_busy_on_other_turn(worker.name, turn):
                return
            worker.client.authority(dict(binding, project_id=self.project_id, actor=worker.name), "worker")
            path = self.workspace("worker", attempt_id, self.config.get("base_ref", "refs/remotes/origin/main"))
            key, state = self.launch("worker", worker, turn, path, **binding)
        elif job.get("reviewer"):
            reviewer = self.reviewers.get(job["reviewer"])
            if reviewer is None:
                raise Barrier("active assignment belongs to an unconfigured reviewer")
            candidate = job["candidate"]
            if self.actor_busy_on_other_turn(reviewer.name, candidate["id"]):
                return
            binding.update(candidate_id=candidate["id"], candidate_sha=candidate["sha"])
            reviewer.client.authority(dict(binding, project_id=self.project_id, actor=reviewer.name), "qa")
            path = self.workspace("qa", candidate["id"], candidate["sha"])
            key, state = self.launch("qa", reviewer, candidate["id"], path, **binding)
        else:
            return
        if state == "running":
            self.work("record", mutation=True, idempotency_key="codex-launch-" + key,
                      evidence="Codex role process acknowledged: " + key, **self.binding(job))
        elif self.fresh(job) is not None:
            raise Barrier("Codex session stopped before persisting its role handoff: " + key)

    def reconcile(self):
        project = self.project()
        settings = self.work("agents")
        configured = {(agent["actor"], agent["role"]) for agent in settings.get("agents", [])}
        if not ({(name, "worker") for name in self.workers} |
                {(name, "qa") for name in self.reviewers}) <= configured:
            raise Barrier("runner actors must be registered in AI.Contract")
        target = settings.get("queue_target")
        if target is None:
            raise Barrier("AI.Contract queue target must be configured")
        jobs = self.jobs()
        if self.delivery:
            if project["repository"] != self.delivery.repository:
                raise Barrier("delivery configuration does not match project authority")
            self.delivery.schedule(jobs)
        for job in jobs:
            self.handle_job(job)
        busy = {actor for _, _, actor, _ in self.active.values()}
        for reviewer in self.reviewers:
            if reviewer in busy:
                continue
            assigned = self.work("assign_qa", mutation=True, reviewer=reviewer)
            if not assigned.get("idle"):
                self.handle_job(assigned["job"])
        busy = {actor for _, _, actor, _ in self.active.values()}
        for worker in self.workers:
            if worker in busy:
                continue
            assigned = self.work("reserve", mutation=True, worker=worker, lease_seconds=300)
            if not assigned.get("idle"):
                self.handle_job(assigned["job"])
        # Retain a stable Architect turn while this Ready backlog remains unchanged.
        ready = [(job["contract_id"], job["revision"]["digest"]) for job in jobs if job["stage"] == "Ready"]
        if len(ready) < target and self.architect.name not in busy:
            turn = digest([self.milestone_id, project["boundary_revision"], target, ready,
                           [(job["contract_id"], job["stage"]) for job in jobs]])
            key, state = self.launch("architect", self.architect, turn, self.checkout,
                                     available_capacity=target - len(ready))
            if state == "stopped" and self.sessions.result(key) != 0:
                raise Barrier("Architect session failed: " + key)

    def maintenance(self):
        changed = False
        for key in tuple(self.active):
            state = self.sessions.inspect(key)
            if state == "unknown":
                raise Barrier("Codex session ownership is uncertain: " + key)
            if state == "stopped":
                del self.active[key]
                changed = True
        for worker in self.workers.values():
            assigned = self.work("assignments", client=worker.client).get("jobs", [])
            for job in assigned:
                if job["stage"] not in ("Implementing", "QA"):
                    continue
                expires = parse_service_time(job["attempt"]["expires_at"])
                remaining = (expires - datetime.now(timezone.utc)).total_seconds()
                if remaining <= 0:
                    for key, (_, attempt_id, _, _) in tuple(self.active.items()):
                        if attempt_id == job["attempt"]["id"]:
                            self.sessions.stop(key)
                    raise Barrier("lease expired; reconcile before recovering the attempt")
                if remaining <= 120:
                    self.work("heartbeat", client=worker.client, mutation=True,
                              lease_seconds=300, **self.binding(job))
        return changed

    def watch(self):
        pending = queue.Queue()
        stop = threading.Event()
        wake_pending = threading.Event()

        def wake():
            if not wake_pending.is_set():
                wake_pending.set()
                pending.put("wake")

        def subscribe():
            while not stop.is_set():
                try:
                    with workflow_events(self.client, self.project_id) as events:
                        wake()
                        for _ in events:
                            if stop.is_set():
                                return
                            wake()
                except ServiceUnavailable:
                    stop.wait(2)
                except Exception as exc:
                    pending.put(exc)
                    return

        self.wake = wake
        threading.Thread(target=subscribe, daemon=True).start()
        try:
            while True:
                try:
                    message = pending.get(timeout=10)
                except queue.Empty:
                    if self.maintenance():
                        self.reconcile()
                    continue
                if message != "wake":
                    raise message
                wake_pending.clear()
                self.maintenance()
                self.reconcile()
        finally:
            stop.set()
            if self.delivery:
                self.delivery.join()


def cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, help="private JSON runner configuration")
    args = parser.parse_args()
    try:
        config = private_json(args.config)
        for key in ("project_id", "milestone_id"):
            if str(uuid.UUID(config[key])) != config[key]:
                raise Barrier("expected canonical project and milestone UUIDs")
        journal = Journal(config["journal"])
        lock_path = Path(journal.path).parent / ("codex-runner-" + config["project_id"] + ".lock")
        with lock_path.open("a") as lock:
            os.chmod(lock_path, 0o600)
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Barrier("another runner owns this project's local runtime") from None
            sessions = CodexSessions(journal, config["codex"], config["skills"])
            with orderly_sigterm():
                Coordinator(config, sessions).watch()
    except KeyboardInterrupt:
        return 130
    except (Barrier, KeyError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"Foundry runner blocked: {type(exc).__name__}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
