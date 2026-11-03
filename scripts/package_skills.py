#!/usr/bin/env python3
"""Render native Foundry skills with relocatable shared-reference closure."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil

ROOT=Path(__file__).resolve().parents[1]
OWN=sorted(p for p in (ROOT/'skills').iterdir() if p.is_dir() and (p/'SKILL.md').is_file())
LINK=re.compile(r'\]\(([^)\s]+)\)')


def render(destination):
    destination=Path(destination).resolve();destination.mkdir(parents=True,exist_ok=True)
    mapped={p/'SKILL.md':destination/p.name/'SKILL.md' for p in OWN}
    pending=list(mapped);done=set();hashes={}
    while pending:
        source=pending.pop()
        if source in done:continue
        done.add(source);target=mapped[source];target.parent.mkdir(parents=True,exist_ok=True)
        raw=source.read_text()
        def link(match):
            value=match[1]
            if ':' in value or value.startswith('#'):return match[0]
            path,sep,anchor=value.partition('#')
            referenced=(source.parent/path).resolve()
            if not referenced.is_relative_to(ROOT):raise ValueError('reference escapes source pack')
            if not referenced.is_file():
                if referenced.name=='SKILL.md' and referenced.parent.name.startswith('openspec-'):
                    installed=destination/referenced.parent.name/'SKILL.md'
                    if not installed.is_file():raise ValueError('required OpenSpec dependency absent: '+referenced.parent.name)
                    return ']('+os.path.relpath(installed,target.parent)+(sep+anchor if sep else '')+')'
                raise ValueError('missing source reference: '+str(referenced.relative_to(ROOT)))
            if referenced not in mapped:
                mapped[referenced]=destination/'foundry-shared'/referenced.relative_to(ROOT)
                if referenced.suffix=='.md':pending.append(referenced)
                else:
                    mapped[referenced].parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(referenced,mapped[referenced])
            return ']('+os.path.relpath(mapped[referenced],target.parent)+(sep+anchor if sep else '')+')'
        target.write_text(LINK.sub(link,raw));hashes[str(source.relative_to(ROOT))]=hashlib.sha256(raw.encode()).hexdigest()
    for skill in OWN:
        for name in ['agents','assets']:
            if (skill/name).exists():shutil.copytree(skill/name,destination/skill.name/name,dirs_exist_ok=True)
    rendered = {}
    for skill in OWN:
        for path in (destination/skill.name).rglob('*'):
            if path.is_file():
                rendered[str(path.relative_to(destination))] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in (destination/'foundry-shared').rglob('*'):
        if path.is_file() and path.name != 'installation.json':
            rendered[str(path.relative_to(destination))] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest={'source_repository':'https://github.com/stemarie/context-foundry','source_sha256':hashes,
              'rendered_sha256':rendered,'skills':[p.name for p in OWN]}
    (destination/'foundry-shared').mkdir(exist_ok=True)
    (destination/'foundry-shared/installation.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    return manifest


def verify(destination):
    destination=Path(destination).resolve()
    allowed=destination.parent if (destination.parent/'plugin.json').is_file() else destination
    files=list((destination/'foundry-shared').rglob('*.md'))
    for skill in OWN:files.extend((destination/skill.name).rglob('*.md'))
    for source in files:
        for value in LINK.findall(source.read_text()):
            if ':' in value or value.startswith('#'):continue
            path=(source.parent/value.split('#')[0]).resolve()
            if not path.is_relative_to(allowed) or not path.is_file():raise ValueError('broken installed reference: '+str(source)+' -> '+value)
    for skill in OWN:
        if not (destination/skill.name/'SKILL.md').is_file():raise ValueError('missing installed skill')
    manifest_path = destination/'foundry-shared/installation.json'
    if not manifest_path.is_file():raise ValueError('missing installed manifest')
    manifest = json.loads(manifest_path.read_text())
    expected_sources = manifest.get('source_sha256')
    expected_rendered = manifest.get('rendered_sha256')
    if not isinstance(expected_sources, dict) or not isinstance(expected_rendered, dict):
        raise ValueError('installed manifest lacks source or rendered hashes')
    for source, expected in expected_sources.items():
        path = ROOT/source
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('stale source reference: '+source)
    for installed, expected in expected_rendered.items():
        path = destination/installed
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError('installed content drift: '+installed)
    return True

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--destination',type=Path,required=True);parser.add_argument('--verify-only',action='store_true');args=parser.parse_args()
    if not args.verify_only:render(args.destination)
    verify(args.destination);print('PASS native Foundry skill pack and shared references')
