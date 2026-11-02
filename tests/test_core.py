import json
from pathlib import Path
import tempfile
import threading
import time
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

    def test_known_not_applied_recovery_enforces_cooldown_and_current_generation(self):
        gate = Gate(self.journal, 'shared')
        with self.assertRaises(Barrier):
            gate.run('close:url', {'url': 'url'}, lambda: (_ for _ in ()).throw(RemoteFailure('resource')))
        permit = gate.acquire()
        gate.outcome(permit, 'rate_limit', retry_after=60, now=time.time())
        with self.assertRaises(Barrier):
            gate.recover_known_not_applied('close:url', {'url': 'url'}, lambda: {'proof': True},
                                           lambda: self.fail('cooldown retry'), lambda: {'closed': True})
        with self.journal.transaction() as db:
            db.execute("UPDATE connections SET state='closed',until=0,server_until=0,owner=NULL,owner_pid=NULL WHERE alias=?",
                       ('shared',))
        def stale_proof():
            gate.outcome(None, 'service')
            return {'proof': True}
        with self.assertRaises(Barrier):
            gate.recover_known_not_applied('close:url', {'url': 'url'}, stale_proof,
                                           lambda: self.fail('stale retry'), lambda: {'closed': True})

    def test_operation_owner_excludes_parallel_recovery_callbacks(self):
        gate = Gate(self.journal, 'shared')
        with self.assertRaises(Barrier):
            gate.run('close:url', {'url': 'url'}, lambda: (_ for _ in ()).throw(RemoteFailure('resource')))
        entered, release = threading.Event(), threading.Event()
        writes, outcomes = [], []
        def prove():
            entered.set()
            self.assertTrue(release.wait(1))
            return {'proof': True}
        def recover():
            try:
                gate.recover_known_not_applied('close:url', {'url': 'url'}, prove,
                                                lambda: writes.append('write'), lambda: {'closed': True})
                outcomes.append('recovered')
            except Barrier:
                outcomes.append('blocked')
        first = threading.Thread(target=recover)
        second = threading.Thread(target=recover)
        first.start()
        self.assertTrue(entered.wait(1))
        second.start()
        second.join(1)
        release.set()
        first.join(1)
        self.assertEqual(['write'], writes)
        self.assertEqual(['blocked', 'recovered'], sorted(outcomes))

    def test_operation_owner_blocks_recovery_while_original_is_paused_before_transport(self):
        gate = Gate(self.journal, 'shared')
        entered, release = threading.Event(), threading.Event()
        writes = []
        def original():
            entered.set()
            self.assertTrue(release.wait(1))
            raise RemoteFailure('resource')
        errors = []
        def run_original():
            try:
                gate.run('close:url', {'url': 'url'}, original)
            except Barrier:
                return
            except BaseException as exc:
                errors.append(exc)
        worker = threading.Thread(target=run_original)
        worker.start()
        self.assertTrue(entered.wait(1))
        with self.assertRaises(Barrier):
            gate.recover_known_not_applied('close:url', {'url': 'url'},
                                           lambda: {'proof': True},
                                           lambda: writes.append('duplicate'),
                                           lambda: {'closed': True})
        release.set()
        worker.join(1)
        self.assertFalse(worker.is_alive())
        self.assertEqual([], errors)
        self.assertEqual([], writes)

    def test_new_alias_tracking_and_legacy_confirmation_preserve_breaker_state(self):
        modern = Gate(self.journal, 'modern')
        modern.acquire()
        with self.journal.transaction() as db:
            self.assertEqual(1, db.execute('SELECT transport_tracking FROM connections WHERE alias=?', ('modern',)).fetchone()[0])
        legacy = Gate(self.journal, 'legacy')
        legacy.acquire()
        with self.journal.transaction() as db:
            db.execute("UPDATE connections SET transport_tracking=0,generation=9,until=123,server_until=456 WHERE alias=?", ('legacy',))
        with self.assertRaises(Barrier):
            legacy.confirm_legacy_quiescence('operator evidence')
        evidence = 'operator confirmed every legacy callback and transport stopped'
        self.assertEqual({'alias': 'legacy', 'evidence': evidence},
                         legacy.confirm_legacy_quiescence(evidence, confirmed_stopped=True))
        with self.journal.transaction() as db:
            row = db.execute('SELECT * FROM connections WHERE alias=?', ('legacy',)).fetchone()
            self.assertEqual((1, 10, 'closed', 123, 456),
                             (row['transport_tracking'], row['generation'], row['state'], row['until'], row['server_until']))
            self.assertEqual(evidence, db.execute('SELECT evidence FROM legacy_quiescence_confirmations').fetchone()[0])

    def test_recovery_blocks_foreign_legacy_half_open_before_proof(self):
        gate = Gate(self.journal, 'shared')
        with self.assertRaises(Barrier):
            gate.run('close:url', {'url': 'url'}, lambda: (_ for _ in ()).throw(RemoteFailure('resource')))
        foreign = Gate(self.journal, 'foreign')
        foreign.acquire()
        with self.journal.transaction() as db:
            db.execute("UPDATE connections SET state='half_open',transport_tracking=0,owner='legacy-probe',owner_pid=NULL WHERE alias=?", ('foreign',))
        actions = []
        with self.assertRaises(Barrier):
            gate.recover_known_not_applied('close:url', {'url': 'url'},
                                           lambda: actions.append('proof') or {'never_closed': True},
                                           lambda: actions.append('write'), lambda: {'closed': True})
        self.assertEqual([], actions)

    def test_recovery_blocks_unconfirmed_closed_legacy_alias_before_proof(self):
        gate = Gate(self.journal, 'shared')
        with self.assertRaises(Barrier):
            gate.run('close:url', {'url': 'url'}, lambda: (_ for _ in ()).throw(RemoteFailure('resource')))
        legacy = Gate(self.journal, 'legacy')
        legacy.acquire()
        with self.journal.transaction() as db:
            db.execute("UPDATE connections SET transport_tracking=0 WHERE alias=?", ('legacy',))
        actions = []
        with self.assertRaises(Barrier):
            gate.recover_known_not_applied('close:url', {'url': 'url'},
                                           lambda: actions.append('proof') or {'never_closed': True},
                                           lambda: actions.append('write'), lambda: {'closed': True})
        self.assertEqual([], actions)
        legacy.confirm_legacy_quiescence('operator confirmed legacy callbacks and transports stopped',
                                         confirmed_stopped=True)
        self.assertEqual({'closed': True},
                         gate.recover_known_not_applied('close:url', {'url': 'url'},
                                                        lambda: actions.append('proof') or {'never_closed': True},
                                                        lambda: actions.append('write'), lambda: {'closed': True}))
        self.assertEqual(['proof', 'write'], actions)

    def test_service_timestamp_variable_nanosecond_precision(self):
        for digits in range(1, 10):
            fraction = '123456789'[:digits]
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
