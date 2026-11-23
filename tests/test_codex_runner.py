import contextlib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import threading
import unittest
from unittest.mock import Mock, patch

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
        c.delivery = None
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

    def test_expired_owned_attempt_recovers_only_after_confirmed_stop(self):
        c = self.coordinator
        expired = job()
        expired["attempt"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        c.sessions.recorded.return_value = [("key", {"role": "worker", "actor": "worker-a"})]
        c.sessions.inspect.side_effect = ["running", "stopped"]
        c.work.return_value = {"job": expired}
        self.assertTrue(c.recover_expired(expired))
        c.sessions.stop.assert_called_once_with("key")
        self.assertEqual(c.work.call_args.args, ("recover",))
        self.assertTrue(c.work.call_args.kwargs["stopped_confirmed"])

    def test_unknown_or_unowned_expired_attempt_blocks_without_recovery(self):
        c = self.coordinator
        expired = job()
        expired["attempt"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        c.work.return_value = {"job": expired}
        for records in ([], [("unknown", {"role": "worker", "actor": "worker-a"})]):
            c.sessions.recorded.return_value = records
            c.sessions.inspect.return_value = "unknown"
            with self.assertRaises(Barrier):
                c.recover_expired(expired)
        c.sessions.stop.assert_not_called()
        self.assertTrue(all(call.args == ("get",) for call in c.work.call_args_list))

    def test_expiry_recovery_does_not_override_a_renewed_lease(self):
        c = self.coordinator
        old = job()
        old["attempt"]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        c.sessions.recorded.return_value = [("key", {"role": "worker", "actor": "worker-a"})]
        c.sessions.inspect.return_value = "stopped"
        c.work.return_value = {"job": job()}
        self.assertFalse(c.recover_expired(old))
        c.work.assert_called_once_with("get", contract_id="contract")

    def test_local_wake_waits_for_subscription_acknowledgement(self):
        c = self.coordinator
        c.client = Mock()
        entered, acknowledge, maintained, dispatched, stop = (threading.Event() for _ in range(5))

        @contextlib.contextmanager
        def subscribe(*_args):
            entered.set()
            if not acknowledge.wait(2):
                raise RuntimeError("fixture did not enable subscription")
            def idle():
                if not stop.wait(2):
                    yield None
            yield idle()

        def maintenance():
            maintained.set()
            return True

        def reconcile():
            dispatched.set()
            stop.set()

        c.maintenance = maintenance
        c.reconcile = reconcile
        with patch("foundry_runtime.codex_runner.workflow_events", subscribe):
            thread = threading.Thread(target=c.watch, args=(stop,), daemon=True)
            thread.start()
            try:
                self.assertTrue(entered.wait(2))
                c.wake()
                self.assertTrue(maintained.wait(2))
                self.assertFalse(dispatched.is_set())
                acknowledge.set()
                self.assertTrue(dispatched.wait(2))
            finally:
                stop.set()
                acknowledge.set()
                thread.join(2)
            self.assertFalse(thread.is_alive())
