"""Relocation and preservation tests for installed skill references."""
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest

SPEC=importlib.util.spec_from_file_location('package_skills',Path(__file__).resolve().parents[1]/'scripts/package_skills.py')
PACK=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(PACK)

class SkillPackagingTests(unittest.TestCase):
    def seed(self,destination):
        for path in (PACK.ROOT/'plugins/foundry-openspec/skills').glob('openspec-*/SKILL.md'):
            if path.parent.name=='openspec-foundry':continue
            target=destination/path.parent.name/'SKILL.md';target.parent.mkdir(parents=True);shutil.copy2(path,target)

    def test_rendered_pack_relocates_with_complete_references(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);first=root/'first';self.seed(first)
            PACK.render(first);PACK.verify(first)
            second=root/'elsewhere'/'skills';second.parent.mkdir();shutil.move(str(first),second)
            self.assertTrue(PACK.verify(second))
            shared=second/'foundry-shared/WORK_CONTRACT.md';self.assertTrue(shared.is_file());shared.unlink()
            with self.assertRaises(ValueError):PACK.verify(second)

    def test_verify_rejects_stale_source_and_rendered_content(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);self.seed(root);PACK.render(root)
            installed=root/'foundry-worker'/'SKILL.md'
            installed.write_text(installed.read_text()+'stale installed content\n')
            with self.assertRaisesRegex(ValueError,'installed content drift'):
                PACK.verify(root)
            PACK.render(root)
            manifest=root/'foundry-shared'/'installation.json'
            data=json.loads(manifest.read_text());source=next(iter(data['source_sha256']))
            data['source_sha256'][source]='0'*64;manifest.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'stale source reference'):
                PACK.verify(root)

        with tempfile.TemporaryDirectory() as name:
            root=Path(name);self.seed(root)
            paths=list(root.glob('openspec-*/SKILL.md'));before={p:p.read_bytes() for p in paths}
            unrelated=root/'unrelated'/'SKILL.md';unrelated.parent.mkdir();unrelated.write_text('untouched user skill')
            PACK.render(root);PACK.verify(root)
            self.assertEqual(before,{p:p.read_bytes() for p in paths})
            self.assertEqual('untouched user skill',unrelated.read_text())

if __name__=='__main__':unittest.main()
