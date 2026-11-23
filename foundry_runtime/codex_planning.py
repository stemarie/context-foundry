"""Resolve approved specifications and supervise native Architect requests."""

import hashlib
from pathlib import Path
import re
import subprocess
import tempfile
import uuid

from .core import Barrier
from .runtime import ServiceError


class BlockedPlanning(Barrier):
    pass


MAX_SPEC_BYTES = 65536


def specification_bytes(spec, checkout):
    if spec["kind"] == "snapshot":
        content = spec["snapshot_markdown"].encode("utf-8")
        if hashlib.sha256(content).hexdigest() != spec["snapshot_sha256"]:
            raise BlockedPlanning("Attached snapshot digest does not match its content.")
    elif spec["kind"] == "git":
        revision, path = spec["source_revision"], spec["source_path"]
        if (not re.fullmatch("[0-9a-f]{40}", revision) or Path(path).is_absolute() or
                ".." in Path(path).parts or "\\" in path or ":" in path or not path):
            raise BlockedPlanning("Attached Git reference is invalid.")

        def git(*args):
            return subprocess.check_output(["git", "--literal-pathspecs", *args], cwd=checkout,
                                           stderr=subprocess.DEVNULL, timeout=15)

        try:
            if git("cat-file", "-t", revision).strip() != b"commit":
                raise BlockedPlanning("Pinned Git revision is not a commit.")
            entry = git("ls-tree", "-z", revision, "--", path).rstrip(b"\0")
            meta, name = entry.split(b"\t", 1)
            mode, kind, object_id = meta.split()
            if kind != b"blob" or mode not in (b"100644", b"100755") or name != path.encode():
                raise BlockedPlanning("Pinned Git path is not a regular specification file.")
            blob = object_id.decode("ascii")
            if int(git("cat-file", "-s", blob)) > MAX_SPEC_BYTES:
                raise BlockedPlanning("Pinned Git specification exceeds the supported size.")
            content = git("cat-file", "blob", blob)
        except (OSError, ValueError, subprocess.SubprocessError):
            raise BlockedPlanning("Pinned Git specification could not be read from the registered checkout.") from None
    else:
        raise BlockedPlanning("Attached specification source type is unsupported.")
    try:
        if len(content) > MAX_SPEC_BYTES or b"\0" in content or not content.decode("utf-8").strip():
            raise ValueError
    except ValueError:
        raise BlockedPlanning("Specification must be nonblank UTF-8 Markdown within the size limit.") from None
    return content


class Planning:
    def __init__(self, runner):
        self.runner = runner

    def requests(self, status):
        return self.runner.work("planning_list", planning_status=status, limit=1).get("planning_requests", [])

    def check_milestone(self, request, project):
        path = "/api/v1/projects/" + request["project_id"] + "/milestones/" + request["milestone_id"]
        milestone = self.runner.client.call(path, method="GET")["milestone"]
        if milestone["project_id"] != project["id"] or milestone["ordinal"] > project["planning_through"]:
            raise BlockedPlanning("Requested milestone is outside the approved planning boundary.")

    def finish(self, request, status, evidence):
        result = self.runner.work("planning_finish", mutation=True, planning_request_id=request["id"],
                                  planning_status=status, evidence=evidence,
                                  idempotency_key="codex-plan-" + status.lower() + "-" + request["id"])
        if result["planning_request"]["status"] != status:
            raise Barrier("Architect planning outcome was not persisted")

    def materialize(self, request):
        spec = self.runner.work("spec_get", specification_id=request["specification_id"])["specification"]
        if (spec["id"], spec["project_id"], spec["milestone_id"]) != (
                request["specification_id"], request["project_id"], request["milestone_id"]):
            raise BlockedPlanning("Attached specification does not match the requested milestone.")
        content = specification_bytes(spec, self.runner.checkout)
        source_hash = hashlib.sha256(content).hexdigest()
        folder = self.runner.root / ("planning-" + str(uuid.UUID(request["id"])))
        folder.mkdir(mode=0o700, exist_ok=True)
        destination = folder / "specification.md"
        if destination.exists():
            if destination.read_bytes() != content:
                raise BlockedPlanning("Local planning snapshot diverged from the pinned source.")
        else:
            with tempfile.NamedTemporaryFile(dir=folder, delete=False) as stream:
                stream.write(content)
                stream.flush()
                Path(stream.name).replace(destination)
        return {
            "planning_request_id": request["id"],
            "specification_id": spec["id"],
            "spec_snapshot_path": str(destination),
            "spec_source_revision": spec["source_revision"],
            "spec_source_reference": spec.get("source_url") or spec.get("source_path"),
            "spec_snapshot_sha256": source_hash,
            "spec_section": spec.get("section", ""),
        }

    def advance(self, project, capacity):
        running = self.requests("Running")
        if running:
            request = running[0]
            if (request["coordinator"] != self.runner.coordinator.name or
                    request["architect"] != self.runner.architect.name):
                raise Barrier("running planning request belongs to a different Coordinator or Architect")
        else:
            if capacity < 1 or any(role == "architect" for role, *_ in self.runner.active.values()):
                return
            pending = self.requests("Pending")
            if not pending:
                return
            request = pending[0]
            try:
                request = self.runner.work("planning_claim", mutation=True, planning_request_id=request["id"],
                                           agent=self.runner.architect.name,
                                           idempotency_key="codex-plan-claim-" + request["id"])["planning_request"]
            except ServiceError as exc:
                if exc.code != "planning_boundary_exceeded":
                    raise
                self.finish(request, "Blocked", "Requested milestone is outside the approved planning boundary.")
                return

        launches = list(self.runner.sessions.recorded(self.runner.project_id, planning_request_id=request["id"]))
        if len(launches) > 1:
            raise Barrier("multiple local launches for one planning request require reconciliation")
        key, state = None, None
        if launches:
            key, binding = launches[0]
            if binding.get("actor") != request["architect"] or binding.get("turn_id") != request["id"]:
                raise Barrier("recorded Architect launch does not match current ownership")
            state = self.runner.sessions.inspect(key)
            if state == "unknown":
                raise Barrier("Architect process ownership is uncertain for request " + request["id"])

        try:
            self.check_milestone(request, project)
            if state == "running":
                return
            if state == "stopped":
                if request.get("architect_evidence"):
                    self.finish(request, "Completed", "Verified durable Architect handoff for the pinned specification.")
                else:
                    self.finish(request, "Blocked", "Architect stopped before recording the required planning report.")
                return
            if request.get("architect_evidence"):
                raise BlockedPlanning("Planning report has no matching local launch record.")
            if capacity < 1:
                return
            context = self.materialize(request)
        except BlockedPlanning as exc:
            if state == "running":
                self.runner.sessions.stop(key)
            self.finish(request, "Blocked", str(exc))
            return
        self.runner.launch("architect", self.runner.architect, request["id"], self.runner.checkout,
                           milestone_id=request["milestone_id"], available_capacity=capacity, **context)
