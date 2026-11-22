"""Alternative source defaults must reach commands without weakening guards."""
import subprocess
import json
import shlex
import sys
import tempfile
import threading
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from foundry_runtime import constants as settings
from foundry_runtime.core import Barrier, Gate, Journal
from foundry_runtime.local_connection import tunnel
from foundry_runtime.remote import GitHub
from foundry_runtime.runtime import Tools, text_page
from scripts.docker_service_fixture import DockerService


class ConstantsTests(unittest.TestCase):
    def test_docker_fixture_uses_selected_identity_path_and_container_port(self):
        commands = []

        def docker(fixture, *args):
            commands.append(args)
            if args[:2] == ('image', 'inspect'):
                return json.dumps([{'Id': 'fixture-image', 'Config': {'User': '12345'}}])
            if args[0] == 'inspect':
                return json.dumps([{'Image': 'fixture-image', 'Config': {'User': '12345:12345'}}])
            if 'token' in args:
                return 'token=fixture-only'
            return 'fixture-container'

        with tempfile.TemporaryDirectory() as root, \
             patch.multiple(settings, FIXTURE_CONTAINER_UID='12345', FIXTURE_CONTAINER_USER='12345:12345',
                            FIXTURE_CONTAINER_PORT=9090, FIXTURE_STATE_DIRECTORY='/state with spaces'), \
             patch.object(DockerService, 'docker', new=docker), \
             patch('scripts.docker_service_fixture.urllib.request.urlopen') as ready:
            ready.return_value.__enter__.return_value.status = 200
            fixture = DockerService('fixture-host', 'fixture-image', root)
            self.assertEqual(fixture.url, fixture.start())
        shell = next(args[-1] for args in commands if '-c' in args)
        self.assertEqual(['chown', '12345:12345', '/state with spaces', '&&', 'chmod', '700', '/state with spaces'],
                         shlex.split(shell))
        started = next(args for args in commands if '-d' in args)
        self.assertEqual('12345:12345', started[started.index('--user') + 1])
        self.assertTrue(started[started.index('-p') + 1].endswith(':9090'))

    def test_tunnel_uses_same_endpoint_for_validation_forwarding_and_origin(self):
        with tempfile.TemporaryDirectory() as root:
            sock = Mock()
            sock.getsockname.return_value = ('127.0.0.2', 43210)
            socket_context = Mock()
            socket_context.__enter__ = Mock(return_value=sock)
            socket_context.__exit__ = Mock(return_value=False)
            process = Mock()
            process.poll.return_value = None

            def launched(argv, **kwargs):
                Path(argv[argv.index('-S') + 1]).touch()
                return process

            config = {'ssh': {'target': 'operator@fixture', 'remote_host': '192.0.2.10',
                              'remote_port': 19090, 'identity_file': '/private/fixture-key'}}
            with patch.multiple(settings, COMMISSIONED_SSH_TARGET='operator@fixture',
                                SERVICE_LOOPBACK_HOST='192.0.2.10', SERVICE_PORT=19090,
                                LOCAL_BIND_HOST='127.0.0.2', MACOS_TEMP_DIRECTORY=root), \
                 patch('foundry_runtime.local_connection.socket.socket', return_value=socket_context), \
                 patch('foundry_runtime.local_connection.subprocess.Popen', side_effect=launched) as start, \
                 patch('foundry_runtime.local_connection.subprocess.run', return_value=Mock(returncode=0)), \
                 patch('foundry_runtime.local_connection._stop_owned_tunnel', return_value=True) as stop:
                with tunnel(config) as origin:
                    self.assertEqual('http://127.0.0.2:43210', origin)
                    command = start.call_args.args[0]
                    self.assertEqual('127.0.0.2:43210:192.0.2.10:19090', command[command.index('-L') + 1])
                    self.assertEqual('operator@fixture', command[-1])
                    control = command[command.index('-S') + 1]
                    self.assertTrue(Path(control).is_file())
                sock.bind.assert_called_once_with(('127.0.0.2', 0))
                stop.assert_called_once_with(process, control, 'operator@fixture')
                self.assertFalse(Path(control).parent.exists())

    def test_tunnel_rejects_mismatched_endpoint_before_starting_process(self):
        valid = {'target': settings.COMMISSIONED_SSH_TARGET,
                 'remote_host': settings.SERVICE_LOOPBACK_HOST, 'remote_port': settings.SERVICE_PORT}
        for key, value in [('target', 'other@fixture'), ('remote_host', '192.0.2.20'),
                           ('remote_port', settings.SERVICE_PORT + 1)]:
            with self.subTest(key=key), patch('foundry_runtime.local_connection.subprocess.Popen') as start:
                with self.assertRaises(Barrier):
                    with tunnel({'ssh': dict(valid, **{key: value})}):
                        self.fail('mismatched endpoint was accepted')
                start.assert_not_called()

    def test_delivery_branch_and_generated_hook_follow_constants(self):
        execute = subprocess.run
        with tempfile.TemporaryDirectory() as root, \
             patch.multiple(settings, AUTHORIZED_DELIVERY_REPOSITORY='fixture/project',
                            DELIVERY_BRANCH='review', GITHUB_ORIGIN='https://git.example.test',
                            HOOK_PYTHON_EXECUTABLE=sys.executable), \
             patch('foundry_runtime.remote.local_git', return_value='https://git.example.test/fixture/project.git'):
            github = GitHub(Gate(Journal(Path(root) / 'runtime.sqlite'), 'fixture'), root, 'fixture/project')
            with self.assertRaises(Barrier):
                GitHub(github.gate, root, 'unapproved/project')
            expected, candidate = 'a' * 40, 'b' * 40
            remote_head = [expected]
            commands = []

            def command(argv, cwd):
                commands.append(argv)
                if 'ls-remote' in argv:
                    self.assertEqual('refs/heads/review', argv[-1])
                    return remote_head[0] + ' refs/heads/review'
                if 'push' in argv:
                    self.assertEqual(candidate + ':refs/heads/review', argv[-1])
                    self.assertFalse(any(value.startswith('--force') for value in argv))
                    hook = Path(next(value.split('=', 1)[1] for value in argv
                                     if value.startswith('core.hooksPath='))) / 'pre-push'
                    self.assertTrue(hook.read_text().startswith('#!' + sys.executable + '\n'))
                    row = f'refs/heads/local {candidate} refs/heads/review {expected}\n'
                    self.assertEqual(0, execute([sys.executable, str(hook)], input=row,
                                               text=True, capture_output=True).returncode)
                    wrong = row.replace('refs/heads/review', 'refs/heads/main')
                    self.assertNotEqual(0, execute([sys.executable, str(hook)], input=wrong,
                                                  text=True, capture_output=True).returncode)
                    remote_head[0] = candidate
                    return ''
                raise AssertionError(argv)

            with patch('foundry_runtime.remote.command', side_effect=command), \
                 patch('foundry_runtime.remote.subprocess.run', return_value=Mock(returncode=0)):
                self.assertEqual(candidate, github.push(candidate, expected, lambda: None)['sha'])
            self.assertEqual(1, sum('push' in command for command in commands))

    def test_text_and_workspace_limits_follow_constants(self):
        with patch.object(settings, 'TEXT_PAGE_MAX_CHARACTERS', 4):
            self.assertEqual('abcd', text_page('abcdef', {}, 'content')['content'])
            with self.assertRaises(Barrier):
                text_page('abcdef', {'limit': 5}, 'content')
        with tempfile.TemporaryDirectory() as root:
            tools = Tools.__new__(Tools)
            tools.role = 'worker'
            tools.binding = {}
            tools.workspace = Path(root)
            tools.calls = []
            tools.lock = threading.RLock()
            tools.client = Mock()
            tools.client.authority.return_value = {'stage': 'Implementing'}
            with patch.object(settings, 'WRITE_MAX_BYTES', 4):
                self.assertEqual({'written': 'sample.txt'}, tools.invoke('write', {'path': 'sample.txt', 'content': 'abcd'}))
                with self.assertRaises(Barrier):
                    tools.invoke('write', {'path': 'sample.txt', 'content': 'abcde'})
                self.assertEqual('abcd', (tools.workspace / 'sample.txt').read_text())


if __name__ == '__main__':
    unittest.main()
