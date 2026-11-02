import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from foundry_runtime.core import Barrier
from foundry_runtime.runtime import Tools


class FocusedEditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name) / 'workspace'
        self.workspace.mkdir()
        self.path = self.workspace / 'large.txt'
        self.path.write_text('prefix\\nunique old text\\nsuffix\\n')
        self.tools = Tools.__new__(Tools)
        self.tools.role = 'worker'
        self.tools.workspace = self.workspace
        self.tools.binding = {'project_id': 'p', 'contract_id': 'c'}
        self.tools.client = Mock()
        self.tools.client.authority.return_value = {'stage': 'Implementing'}
        self.tools.calls = []
        self.tools.checks = {'passed': True}

    def tearDown(self):
        self.temp.cleanup()

    def edit(self, replacements, digest=None):
        current = self.path.read_text()
        return self.tools._invoke('edit', {'path': 'large.txt',
            'expected_digest': digest or hashlib.sha256(current.encode()).hexdigest(),
            'replacements': replacements})

    def test_exact_literal_edit_is_atomic_and_clears_checks(self):
        result = self.edit([{'old': 'unique old text', 'new': 'replacement'}])
        self.assertEqual('large.txt', result['edited'])
        self.assertEqual('prefix\\nreplacement\\nsuffix\\n', self.path.read_text())
        self.assertIsNone(self.tools.checks)

    def test_stale_ambiguous_and_invalid_edits_leave_file_unchanged(self):
        original = self.path.read_text()
        for replacements, digest in (([{'old': 'missing', 'new': 'x'}], None),
                                     ([{'old': 'unique old text', 'new': ''}], 'stale'),
                                     ([{'old': '', 'new': 'x'}], None),
                                     ([{'old': 'unique old text', 'new': 'x'}, {'old': 'unique old text', 'new': 'y'}], None)):
            with self.subTest(replacements=replacements, digest=digest):
                with self.assertRaises(Barrier):
                    self.edit(replacements, digest)
                self.assertEqual(original, self.path.read_text())

    def test_qa_and_traversal_are_denied(self):
        self.tools.role = 'qa'
        with self.assertRaises(Barrier):
            self.edit([{'old': 'unique old text', 'new': 'x'}])
        self.tools.role = 'worker'
        with self.assertRaises(Barrier):
            self.tools._invoke('edit', {'path': '../outside', 'expected_digest': 'x',
                'replacements': [{'old': 'x', 'new': 'y'}]})


if __name__ == '__main__':
    unittest.main()
