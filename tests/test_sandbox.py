"""Actual host controls; excluded from sandboxed candidate-only checks."""
from pathlib import Path
import sys
import tempfile
import unittest
from foundry_runtime.runtime import restricted_check

@unittest.skipUnless(sys.platform == 'darwin', 'verified macOS backend only')
class SandboxTests(unittest.TestCase):
    def test_check_runs_but_network_fork_and_other_home_reads_fail(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as root:
            root = Path(root)
            workspace, scratch = root/'workspace', root/'scratch'
            workspace.mkdir(); scratch.mkdir()
            secret = root/'other-actor-secret'; secret.write_text('fixture-secret')
            script = '''import socket,os
from pathlib import Path
blocked=[]
for action in [lambda:socket.create_connection(('127.0.0.1',9)),lambda:os.fork(),lambda:Path(%r).read_text()]:
 try:action()
 except (PermissionError,OSError):blocked.append(True)
 else:raise AssertionError('capability escaped')
assert len(blocked)==3
print('network, fork and foreign file reads denied')
''' % str(secret)
            result=restricted_check(workspace,['/Library/Developer/CommandLineTools/usr/bin/python3','-E','-s','-c',script],scratch)
            self.assertTrue(result['passed'],result)

if __name__=='__main__':unittest.main()
