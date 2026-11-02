import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from scripts.connection_recovery_acceptance import request


class ConnectionRecoveryAcceptanceTests(unittest.TestCase):
    def child(self, program):
        return subprocess.Popen([sys.executable, '-c', program], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)

    def reap(self, process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

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


if __name__ == '__main__':
    unittest.main()
