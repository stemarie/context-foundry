import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import unittest
from unittest.mock import Mock, patch
import warnings

from scripts.connection_recovery_acceptance import OwnedSSH, close, master, request, still_owned


class ConnectionRecoveryAcceptanceTests(unittest.TestCase):
    def child(self, program):
        return subprocess.Popen([sys.executable, '-c', program], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True)

    def test_master_requires_live_bridge_and_original_parent_before_capture(self):
        bridge = Mock(pid=100)
        bridge.poll.return_value = None
        child = OwnedSSH(200, 100, 'start', 'ssh -S /private/control target', '/private/control')
        with patch('scripts.connection_recovery_acceptance.subprocess.run', return_value=Mock(stdout='200\n')), \
             patch('scripts.connection_recovery_acceptance.process_identity', return_value=(100, child.start, child.command)):
            self.assertEqual(child, master(bridge))
        bridge.poll.return_value = 0
        with self.assertRaisesRegex(RuntimeError, 'bridge exited'):
            master(bridge)

    def reap(self, process):
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()

    def test_silent_child_response_is_bounded_and_reaped(self):
        process = self.child('import time; time.sleep(30)')
        try:
            started = time.monotonic()
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                request(process, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}, timeout=0.15)
            self.assertLess(time.monotonic() - started, 1)
        finally:
            self.reap(process)
        self.assertIsNotNone(process.returncode)

    def test_partial_line_response_is_bounded_and_reaped(self):
        process = self.child("import sys,time; sys.stdin.readline(); sys.stdout.write('{\\\"jsonrpc\\\":'); sys.stdout.flush(); time.sleep(30)")
        try:
            started = time.monotonic()
            with self.assertRaisesRegex(RuntimeError, 'timed out'):
                request(process, {'jsonrpc': '2.0', 'id': 1, 'method': 'ping'}, timeout=0.15)
            self.assertLess(time.monotonic() - started, 1)
        finally:
            self.reap(process)
        self.assertIsNotNone(process.returncode)

    def test_owned_identity_rejects_absent_parent_start_and_command_mismatch(self):
        process = Mock()
        process.poll.return_value = None
        child = OwnedSSH(424242, 100, 'old start', 'ssh -S /private/control target', '/private/control')
        for identity in (None, (101, 'old start', child.command),
                         (100, 'new start', child.command), (100, 'old start', 'ssh another')):
            with self.subTest(identity=identity), patch('scripts.connection_recovery_acceptance.process_identity', return_value=identity):
                self.assertFalse(still_owned(child, process))

    def test_post_parent_exit_owned_survivor_is_signalled_only_on_exact_identity(self):
        bridge = Mock()
        bridge.pid = 100
        bridge.poll.return_value = 0
        child = OwnedSSH(424242, 100, 'old start', 'ssh -S /private/control target', '/private/control')
        with patch('scripts.connection_recovery_acceptance.process_identity',
                   return_value=(1, child.start, child.command)):
            self.assertTrue(still_owned(child, bridge))
        for identity in (None, (1, 'reused', child.command), (1, child.start, 'ssh -S /other target')):
            with self.subTest(identity=identity), patch('scripts.connection_recovery_acceptance.process_identity', return_value=identity):
                self.assertFalse(still_owned(child, bridge))

    def test_group_disappearance_still_waits_and_closes_streams(self):
        process = Mock()
        process.poll.return_value = None
        process.stdin = Mock(closed=False)
        process.stdout = Mock(closed=False)
        process.stderr = Mock(closed=False)
        with patch('scripts.connection_recovery_acceptance.os.killpg', side_effect=ProcessLookupError):
            close(process, None)
        process.wait.assert_called_once_with(timeout=15)
        process.stdin.close.assert_called_once()
        process.stdout.close.assert_called_once()
        process.stderr.close.assert_called_once()

    def test_wait_escalation_race_still_polls_and_closes_streams(self):
        process = Mock(pid=100)
        process.poll.return_value = None
        process.wait.side_effect = [subprocess.TimeoutExpired(['bridge'], 15),
                                    subprocess.TimeoutExpired(['bridge'], 15)]
        process.stdin = Mock(closed=False)
        process.stdout = Mock(closed=False)
        process.stderr = Mock(closed=False)
        with patch('scripts.connection_recovery_acceptance.os.killpg', side_effect=[None, ProcessLookupError]):
            close(process, None)
        self.assertEqual(2, process.wait.call_count)
        process.poll.assert_called()
        process.stdin.close.assert_called_once()
        process.stdout.close.assert_called_once()
        process.stderr.close.assert_called_once()

    def test_close_signals_exact_owned_post_parent_exit_survivor(self):
        process = Mock(pid=100)
        process.poll.return_value = 0
        process.stdin = Mock(closed=False)
        process.stdout = Mock(closed=False)
        process.stderr = Mock(closed=False)
        child = OwnedSSH(424242, 100, 'old start', 'ssh -S /private/control target', '/private/control')
        signals = []
        with patch('scripts.connection_recovery_acceptance.still_owned', return_value=True), \
             patch('scripts.connection_recovery_acceptance.stopped', return_value=True):
            close(process, child, signal_process=lambda pid, sig: signals.append((pid, sig)))
        self.assertEqual([(child.pid, signal.SIGKILL)], signals)

    def test_close_does_not_signal_reused_or_unverifiable_ssh_pid(self):
        process = self.child('import time; time.sleep(30)')
        child = OwnedSSH(424242, process.pid, 'old start', 'ssh -S /private/control target', '/private/control')
        signals = []
        try:
            with patch('scripts.connection_recovery_acceptance.still_owned', return_value=False):
                close(process, child, signal_process=lambda pid, sig: signals.append((pid, sig)))
            self.assertEqual([], signals)
        finally:
            self.reap(process)

    def test_actual_child_cleanup_closes_all_streams_without_resource_warning(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always', ResourceWarning)
            process = self.child('import time; time.sleep(30)')
            close(process, None)
            self.assertIsNotNone(process.returncode)
            self.assertTrue(all(stream is None or stream.closed for stream in (process.stdin, process.stdout, process.stderr)))
        self.assertFalse([warning for warning in caught if issubclass(warning.category, ResourceWarning)])

    def test_cleanup_is_clean_under_warning_sensitive_interpreter(self):
        program = '''
import subprocess
import sys
from scripts.connection_recovery_acceptance import close
process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
close(process, None)
assert process.returncode is not None
assert all(stream is None or stream.closed for stream in (process.stdin, process.stdout, process.stderr))
'''
        result = subprocess.run([sys.executable, '-X', 'dev', '-W', 'error::ResourceWarning', '-c', program],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertNotIn('ResourceWarning', result.stderr)
        self.assertNotIn('Exception ignored in:', result.stderr)


if __name__ == '__main__':
    unittest.main()
