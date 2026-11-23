import contextlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from foundry_runtime.codex_delivery import Delivery
from foundry_runtime.codex_runner import Coordinator
from foundry_runtime.core import Barrier


class CodexDeliveryTest(unittest.TestCase):
    def setUp(self):
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        self.target, self.base, self.candidate = "1" * 40, "2" * 40, "3" * 40
        job = self.job = {
            "attempt": {"id": "attempt"}, "contract_id": "contract",
            "revision": {"digest": "digest", "number": 1, "title": "Title"},
            "candidate": {"id": "candidate", "sha": self.candidate},
            "accepted_candidate_id": "candidate", "stage": "QA accepted",
        }
        runner = self.runner = SimpleNamespace(
            project_id="project", root=Path(root.name), active={},
            binding=Coordinator.binding, workspace=Mock(return_value=Path(root.name)),
            git=Mock(side_effect=self.git), work=Mock(side_effect=self.service), project=Mock(),
        )
        delivery = self.delivery = Delivery.__new__(Delivery)
        delivery.runner = runner
        delivery.repository = "o/r"
        delivery.checks = [["true"]]
        delivery.github = Mock()
        delivery.github.integration.side_effect = contextlib.nullcontext
        self.head = self.base
        delivery.github.head.side_effect = lambda: self.head

        def push(target, expected, authority):
            self.assertEqual(expected, self.base)
            self.assertEqual(target, self.target)
            authority()
            self.head = target

        delivery.github.push.side_effect = push
        delivery.github.historical_issue.return_value = {"url": "https://github.com/o/r/issues/1"}
        self.calls = []

    def git(self, *args):
        return self.target if "rev-parse" in args else ""

    def service(self, op, **args):
        self.calls.append(op)
        if op == "integrate":
            self.job["stage"] = "Integrating"
        if op == "complete":
            self.assertEqual(self.job["stage"], "Integrating")
            self.assertEqual(args["target_sha"], self.target)
            self.job.update(stage="Done", integration_reference=args["reference"])
        return {"job": dict(self.job)}

    def test_verify_then_complete_and_publish(self):
        self.delivery.deliver(self.job)
        self.assertEqual(self.job["stage"], "Done")
        self.assertLess(self.calls.index("integrate"), self.calls.index("complete"))
        self.assertLess(self.calls.index("complete"), self.calls.index("publish_history"))
        self.delivery.github.close_history.assert_called_once_with("https://github.com/o/r/issues/1")

    def test_failed_postcheck_leaves_integrating_and_retries_without_repush(self):
        verify = self.delivery.verify

        def reject(checkout, target, binding, stage):
            if stage == "post-integration":
                raise Barrier("failed postcheck")
            verify(checkout, target, binding, stage)

        self.delivery.verify = reject
        with self.assertRaisesRegex(Barrier, "failed postcheck"):
            self.delivery.deliver(self.job)
        self.assertNotIn("complete", self.calls)
        self.assertEqual(self.job["stage"], "Integrating")
        self.delivery.verify = verify
        self.delivery.deliver(self.job)
        self.delivery.github.push.assert_called_once()
        self.assertEqual(self.job["stage"], "Done")
