"""Checkout selection and import safety for installed operator commands."""
import argparse
import importlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from foundry_runtime.checkout import resolve_checkout


ROOT = Path(__file__).resolve().parents[1]


class InstallationTests(unittest.TestCase):
    def test_checkout_selection_is_explicit_and_never_guesses_from_cwd(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError, '--foundry-checkout'):
                resolve_checkout(root)
        self.assertEqual(ROOT, resolve_checkout(ROOT))
        self.assertEqual(ROOT, resolve_checkout())

    def test_acceptance_rejects_source_runtime_drift(self):
        with tempfile.TemporaryDirectory() as root:
            target = Path(root)
            for name in ['AGENTS.md', 'WORK_CONTRACT.md', 'skills/README.md', 'scripts/package_skills.py']:
                file = target / name
                file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, file)
            shutil.copytree(ROOT / 'foundry_runtime', target / 'foundry_runtime', ignore=shutil.ignore_patterns('__pycache__'))
            self.assertEqual(target, resolve_checkout(target, match_runtime=True))
            worker = target / 'foundry_runtime/worker.py'
            worker.write_text(worker.read_text() + '\n# divergent runtime\n')
            with self.assertRaisesRegex(ValueError, 'runtime differs'):
                resolve_checkout(target, match_runtime=True)

    def test_importing_all_cli_modules_does_not_parse_arguments_or_start_work(self):
        names = ['acceptance_preflight', 'breaker_acceptance', 'connection_recovery_acceptance',
                 'followup_acceptance', 'native_version_acceptance', 'package_skills', 'real_agent_acceptance']
        with patch.object(argparse.ArgumentParser, 'parse_args', side_effect=AssertionError('import parsed CLI arguments')):
            for name in names:
                module = importlib.import_module('scripts.' + name)
                importlib.reload(module)
                self.assertTrue(callable(module.main))


if __name__ == '__main__':
    unittest.main()
