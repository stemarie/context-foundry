import json
from pathlib import Path
import tempfile
import threading
import unittest

from foundry_runtime.core import Barrier, Gate, Journal, RemoteFailure
from foundry_runtime.runtime import checked_path, parse_service_time


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.journal = Journal(self.root / 'runtime.sqlite')

    def tearDown(self):
        self.temp.cleanup()

    def test_launch_intent_replay_and_missing_handle_remain_unknown(self):
        binding = {'origin': 'http://127.0.0.1:1', 'project_id': 'p', 'contract_id': 'c',
                   'revision': 1, 'digest': 'digest', 'attempt_id': 'attempt', 'actor': 'worker'}
        first, created = self.journal.intent(binding)
        self.assertTrue(created)
        restarted = Journal(self.journal.path)
        replay, created = restarted.intent(binding)
        self.assertFalse(created)
        self.assertEqual(first, replay)
        self.assertEqual('unknown', restarted.inspect(first['key']))
        with self.assertRaises(Barrier):
            restarted.stop(first['key'])
        changed, created = restarted.intent({**binding, 'attempt_id': 'new-attempt'})
        self.assertTrue(created)
        self.assertNotEqual(first['key'], changed['key'])

    def test_shared_breaker_single_probe_backoff_and_resource_errors(self):
        one = Gate(self.journal, 'shared-test-connection')
        two = Gate(Journal(self.journal.path), 'shared-test-connection')
        one.outcome(one.acquire(now=0), 'rate_limit', retry_after=90, now=0)
        with self.assertRaises(Barrier):
            two.acquire(now=89)
        permits = []
        lock = threading.Lock()
        def probe(gate):
            try:
                value = gate.acquire(now=91)
                with lock:
                    permits.append(value)
            except Barrier:
                pass
        threads = [threading.Thread(target=probe, args=(g,)) for g in (one, two)]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(1, len(permits))
        one.outcome(permits[0], 'connection', now=91)
        with self.assertRaises(Barrier):
            two.acquire(now=100)
        permit = two.operator_probe(now=101)
        two.outcome(permit, 'resource', now=101)
        self.assertIsNone(one.acquire(now=102))
        one.outcome(None, 'service', now=102)
        one.outcome(None, now=103)  # A late successful operation cannot close it.
        with self.assertRaises(Barrier):
            two.acquire(now=104)

    def test_uncertain_remote_write_reconciles_without_duplicate(self):
        gate = Gate(self.journal, 'shared')
        calls = []
        def write():
            calls.append('created remotely')
            raise RemoteFailure('connection')
        with self.assertRaises(Barrier):
            gate.run('final-history', {'contract': 'c'}, write)
        probe = gate.operator_probe()
        gate.outcome(probe)
        result = gate.run('final-history', {'contract': 'c'}, write, reconcile=lambda: {'issue': 7})
        self.assertEqual({'issue': 7}, result)
        self.assertEqual(['created remotely'], calls)
        self.assertEqual(result, gate.run('final-history', {'contract': 'c'}, write))
        with self.assertRaises(Barrier):
            gate.run('final-history', {'contract': 'other'}, write)

    def test_service_timestamp_variable_nanosecond_precision(self):
        for fraction in ('1', '12', '123', '12345', '123456', '123456789'):
            value = parse_service_time('2026-11-01T15:01:23.' + fraction + 'Z')
            self.assertEqual(int(fraction[:6].ljust(6, '0')), value.microsecond)
            self.assertIsNotNone(value.tzinfo)

    def test_file_capabilities_reject_escape_symlink_and_git_metadata(self):
        workspace = self.root / 'worker'
        workspace.mkdir()
        self.assertEqual(workspace / 'allowed.txt', checked_path(workspace, 'allowed.txt'))
        for value in ('../other', '/etc/passwd', '.git/config', 'dir/.git-credentials'):
            with self.assertRaises(Barrier):
                checked_path(workspace, value)
        (workspace / 'outside').symlink_to(self.root / 'secret')
        with self.assertRaises(Barrier):
            checked_path(workspace, 'outside')


if __name__ == '__main__':
    unittest.main()
