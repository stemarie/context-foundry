"""Verified direct-main delivery for an explicitly configured Codex runner."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import threading

from .core import Barrier, Gate, digest
from .remote import GitHub


class Delivery:
    def __init__(self, coordinator, config):
        self.runner = coordinator
        self.repository = config["repository"]
        self.checks = config["checks"]
        if not self.checks or any(not isinstance(argv, list) or not argv or
                                  any(not isinstance(arg, str) or not arg for arg in argv)
                                  for argv in self.checks):
            raise Barrier("delivery requires explicit verification commands")
        self.github = GitHub(Gate(coordinator.sessions.journal, config["connection_alias"]),
                             coordinator.checkout, self.repository,
                             authorized_repository=self.repository)
        self.thread = None
        self.finished = threading.Event()
        self.failure = None

    def _identity(self, job):
        return digest([self.runner.project_id, job["contract_id"], job["attempt"]["id"],
                       job["revision"]["digest"], job["candidate"]["id"]])

    def _intent(self, job):
        return self.runner.root / ("delivery-" + self._identity(job) + ".json")

    def next(self, jobs):
        stages = ("Integrating", "QA accepted")
        for stage in stages:
            for job in jobs:
                if job["stage"] != stage:
                    continue
                attempt = job["attempt"]["id"]
                busy = any(active_attempt == attempt for _, active_attempt, _, _ in self.runner.active.values())
                # Native integration is serialized. An existing owner takes priority.
                if stage == "Integrating" and not self._intent(job).exists():
                    raise Barrier("existing integration lacks a local delivery intent")
                if not busy:
                    return job
                if stage == "Integrating":
                    return None
        return next((job for job in jobs if job["stage"] == "Done" and job.get("candidate") and
                     not job.get("history_reference") and self._intent(job).exists()), None)

    def schedule(self, jobs):
        if self.failure:
            raise self.failure
        if self.thread is not None and not self.finished.is_set():
            return
        job = self.next(jobs)
        if job is None:
            return
        self.finished.clear()
        self.thread = threading.Thread(target=self._run, args=(job,), name="foundry-delivery")
        self.thread.start()

    def join(self):
        if self.thread is not None:
            self.thread.join()

    def _run(self, job):
        try:
            self.deliver(job)
        except Exception as exc:
            self.failure = exc
        finally:
            self.finished.set()
            self.runner.wake()

    def bound(self, job):
        return dict(self.runner.binding(job), candidate_id=job["candidate"]["id"],
                    candidate_sha=job["candidate"]["sha"])

    def deliver(self, job):
        self.runner.project()
        binding = self.bound(job)
        candidate = binding["candidate_sha"]
        path = self._intent(job)
        with self.github.integration():
            def current():
                actual = self.runner.work("get", contract_id=binding["contract_id"])["job"]
                if self.bound(actual) != binding or actual.get("accepted_candidate_id") != binding["candidate_id"]:
                    raise Barrier("exact QA-accepted candidate changed")
                return actual

            def authority():
                if current()["stage"] != "Integrating":
                    raise Barrier("integration ownership changed")

            job = current()
            if job["stage"] == "Done":
                self.publish_history(job)
                return
            if job["stage"] not in ("QA accepted", "Integrating"):
                raise Barrier("delivery requires QA acceptance")
            checkout = self.runner.workspace("deliver", job["candidate"]["id"], candidate)
            if path.exists():
                intent = json.loads(path.read_text())
            else:
                if job["stage"] != "QA accepted":
                    raise Barrier("cannot reconstruct an uncertain integration")
                self.github.fetch()
                expected = self.github.head()
                self.runner.git("-C", str(checkout), "checkout", "--detach", expected)
                self.runner.git("-C", str(checkout), "-c", "user.name=Foundry Coordinator",
                                "-c", "user.email=foundry-coordinator@localhost",
                                "merge", "--no-edit", candidate)
                target = self.runner.git("-C", str(checkout), "rev-parse", "HEAD")
                intent = {"expected": expected, "target": target, "binding": binding}
                with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
                    json.dump(intent, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                    Path(stream.name).replace(path)
            if intent["binding"] != binding:
                raise Barrier("local delivery intent no longer matches native binding")
            target, expected = intent["target"], intent["expected"]
            self.runner.git("-C", str(checkout), "checkout", "--detach", target)
            self.runner.git("-C", str(checkout), "merge-base", "--is-ancestor", candidate, target)
            if self.runner.git("-C", str(checkout), "status", "--porcelain", "--untracked-files=all"):
                raise Barrier("integration worktree contains unverified changes")

            if job["stage"] == "QA accepted":
                self.runner.work("integrate", mutation=True, idempotency_key="integrate-" + self._identity(job),
                                 **binding)
            authority()
            head = self.github.head()
            if head not in (expected, target):
                raise Barrier("remote target advanced; integration requires reconciliation")
            if head != target:
                self.verify(checkout, target, binding, "pre-integration")
                self.github.push(target, expected, authority)
            if self.github.head() != target:
                raise Barrier("remote target does not match intended delivery")
            self.verify(checkout, target, binding, "post-integration")
            if self.github.head() != target:
                raise Barrier("remote target changed during verification")
            authority()
            result = self.runner.work(
                "complete", mutation=True, idempotency_key="complete-" + self._identity(job),
                target_sha=target, reference=f"https://github.com/{self.repository}/commit/{target}",
                checks_passed=True, evidence="Remote target matched and configured post-integration checks passed.",
                **binding)["job"]
            if result["stage"] != "Done":
                raise Barrier("native completion was not persisted")
            self.publish_history(result)

    def verify(self, checkout, target, binding, stage):
        for index, argv in enumerate(self.checks, 1):
            result = subprocess.run(argv, cwd=checkout, check=False, timeout=300)
            if result.returncode:
                self.runner.work("record", mutation=True, evidence=(
                    f"{stage} command {index} failed with exit {result.returncode}."), **binding)
                raise Barrier(f"{stage} verification failed")
        head = self.runner.git("-C", str(checkout), "rev-parse", "HEAD")
        dirty = self.runner.git("-C", str(checkout), "status", "--porcelain", "--untracked-files=all")
        if head != target or dirty:
            raise Barrier(f"{stage} checks changed the verified tree")

    def publish_history(self, job):
        binding = self.bound(job)
        marker = "foundry-contract:" + self.runner.project_id + ":" + job["contract_id"]
        reference = job["integration_reference"]
        history = self.github.historical_issue(marker, "Delivered: " + job["revision"]["title"],
            f"Contract {job['contract_id']} revision {binding['revision']} and attempt {binding['attempt_id']}.\n\n"
            f"Accepted candidate {binding['candidate_sha']}. Verified target {reference}.")
        self.github.close_history(history["url"])
        self.runner.work("publish_history", mutation=True, idempotency_key="history-" + self._identity(job),
                         reference=history["url"], **binding)
