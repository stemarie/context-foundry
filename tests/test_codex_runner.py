from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from foundry_runtime.codex_runner import Coordinator
from foundry_runtime.core import Barrier


def job(stage="Implementing", worker="worker-a", candidate=None, reviewer=""):
    value = {
        "contract_id": "contract",
        "stage": stage,
        "revision": {"number": 1, "digest": "digest"},
        "attempt": {"worker": worker, "id": "attempt",
                    "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=4)).isoformat()},
        "reviewer": reviewer,
    }
    if candidate:
        value["candidate"] = {"id": candidate, "sha": "a" * 40}
    return value


def actor(name):
    return SimpleNamespace(name=name, client=Mock())


class CodexCoordinatorTest(unittest.TestCase):
    def setUp(self):
        c = Coordinator.__new__(Coordinator)
        self.coordinator = c
        c.project_id = "project"
        c.milestone_id = "milestone"
        c.config = {}
        c.checkout = Path("/checkout")
        c.sessions = Mock()
        c.active = {}
        c.architect = actor("architect")
        c.workers = {name: actor(name) for name in ("worker-a", "worker-b")}
        c.reviewers = {"qa-a": actor("qa-a")}
        c.workspace = Mock(return_value=Path("/worktree"))
        c.work = Mock()
        c.launch = Mock(return_value=("launch", "running"))
        c.fresh = Mock(side_effect=lambda current: current)

    def test_correction_uses_same_attempt_and_changes_turn_identity(self):
        c = self.coordinator
        c.handle_job(job())
        c.handle_job(job(candidate="candidate-one"))
        self.assertEqual([call.args[2] for call in c.launch.call_args_list],
                         ["attempt:initial", "attempt:candidate-one"])
        self.assertEqual([call.args[1] for call in c.workspace.call_args_list],
                         ["attempt", "attempt"])
        c.active["previous"] = ("worker", "attempt", "worker-a", "attempt:initial")
        c.launch.reset_mock()
        c.handle_job(job(candidate="candidate-one"))
        c.launch.assert_not_called()

    def test_qa_uses_exact_candidate_and_distinct_reviewer(self):
        c = self.coordinator
        c.handle_job(job("QA", candidate="candidate-one", reviewer="qa-a"))
        c.workspace.assert_called_once_with("qa", "candidate-one", "a" * 40)
        self.assertEqual(c.launch.call_args.args[1].name, "qa-a")
        self.assertEqual(c.launch.call_args.kwargs["candidate_id"], "candidate-one")

    def test_aborted_worker_cannot_advance_without_persisted_handoff(self):
        c = self.coordinator
        c.launch.return_value = ("launch", "stopped")
        with self.assertRaisesRegex(Barrier, "persisting its role handoff"):
            c.handle_job(job())

    def test_reconcile_reserves_both_worker_slots_and_replenishes(self):
        c = self.coordinator
        c.project = Mock(return_value={"boundary_revision": 1})
        c.jobs = Mock(return_value=[])
        c.handle_job = Mock()
        dispatched = [job(), job(worker="worker-b")]

        def service(op, **fields):
            if op == "agents":
                return {"queue_target": 2, "agents": [
                    {"actor": "worker-a", "role": "worker"}, {"actor": "worker-b", "role": "worker"},
                    {"actor": "qa-a", "role": "qa"},
                ]}
            if op == "assign_qa":
                return {"idle": True}
            return {"job": dispatched.pop(0)}

        c.work.side_effect = service
        c.reconcile()
        self.assertEqual([call.args[0]["attempt"]["worker"] for call in c.handle_job.call_args_list],
                         ["worker-a", "worker-b"])
        self.assertEqual(c.launch.call_args.args[0], "architect")
        self.assertEqual(c.launch.call_args.kwargs["available_capacity"], 2)
