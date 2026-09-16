import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

ADAPTER = Path(__file__).resolve().parents[1] / "phase0_full_chain_audit_read.py"
SPEC = importlib.util.spec_from_file_location("phase0_audit_read", ADAPTER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TOKEN = "test-token-never-output"


class Response(io.StringIO):
    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False


class Phase0AuditReadTest(unittest.TestCase):
    def setUp(self):
        self.original_packet_hash = MODULE.PACKET_SHA256
        self.original_contract_hash = MODULE.CONTRACT_SHA256
        self.original_tracker_hash = MODULE.TRACKER_SHA256
        MODULE.PACKET_SHA256 = hashlib.sha256(MODULE.PACKET_BODY.encode()).hexdigest()
        MODULE.CONTRACT_SHA256 = hashlib.sha256((MODULE.CANONICAL_MARKER + "\n" + MODULE.PHASE_MARKER).encode()).hexdigest()
        MODULE.TRACKER_SHA256 = hashlib.sha256((MODULE.TRACKER_MARKER + "\n" + MODULE.CONTRACT_URL).encode()).hexdigest()
        self.addCleanup(setattr, MODULE, "PACKET_SHA256", self.original_packet_hash)
        self.addCleanup(setattr, MODULE, "CONTRACT_SHA256", self.original_contract_hash)
        self.addCleanup(setattr, MODULE, "TRACKER_SHA256", self.original_tracker_hash)

    def envelope(self):
        return {
            "task": {
                "id": MODULE.TASK_ID,
                "assignee": "foundry-auditor",
                "title": MODULE.TITLE,
                "body": MODULE.PACKET_BODY,
                "status": "blocked",
            },
            "parents": [MODULE.PARENT_ID],
        }

    def data(self):
        contract = MODULE.CANONICAL_MARKER + "\n" + MODULE.PHASE_MARKER
        tracker = MODULE.TRACKER_MARKER + "\n" + MODULE.CONTRACT_URL
        return {
            MODULE.CONTRACT_ENDPOINT: {"number": 50, "html_url": MODULE.CONTRACT_URL, "state": "open", "body": contract},
            MODULE.TRACKER_ENDPOINT: {"number": 9, "html_url": MODULE.TRACKER_URL, "title": MODULE.TRACKER_TITLE, "state": "open", "body": tracker},
        }

    def test_exact_card_reads_only_bound_contract_and_tracker(self):
        seen = []
        def opener(request, timeout):
            seen.append(request)
            return Response(json.dumps(self.data()[request.full_url]))
        receipt = MODULE.read({"HERMES_KANBAN_TASK": MODULE.TASK_ID}, lambda _: self.envelope(), lambda: TOKEN, opener)
        self.assertEqual(receipt["verdict"], "PASS")
        self.assertEqual({request.get_method() for request in seen}, {"GET"})
        self.assertEqual({request.full_url for request in seen}, {MODULE.CONTRACT_ENDPOINT, MODULE.TRACKER_ENDPOINT})
        self.assertNotIn(TOKEN, json.dumps(receipt, sort_keys=True))

    def test_substituted_card_fails_before_credential(self):
        envelope = self.envelope()
        envelope["task"]["assignee"] = "foundry-architect"
        with self.assertRaisesRegex(MODULE.ReadError, "card-shape"):
            MODULE.read({"HERMES_KANBAN_TASK": MODULE.TASK_ID}, lambda _: envelope, lambda: self.fail("credential"))


if __name__ == "__main__":
    unittest.main()
