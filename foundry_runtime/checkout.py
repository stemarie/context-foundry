"""Resolve source assets explicitly when utilities are installed outside a checkout."""
from pathlib import Path


def resolve_checkout(selected=None, *, match_runtime=False):
    root = Path(selected).expanduser().resolve() if selected is not None else Path(__file__).resolve().parents[1]
    required = ('AGENTS.md', 'WORK_CONTRACT.md', 'skills/README.md',
                'scripts/package_skills.py', 'foundry_runtime/worker.py')
    if not all((root / name).is_file() for name in required):
        raise ValueError('a Context Foundry source checkout is required; pass --foundry-checkout /path/to/context-foundry')
    if match_runtime:
        installed = Path(__file__).resolve().parent
        source = root / 'foundry_runtime'
        installed_files = {p.name: p.read_bytes() for p in installed.glob('*.py')}
        source_files = {p.name: p.read_bytes() for p in source.glob('*.py')}
        if installed_files != source_files:
            raise ValueError('installed runtime differs from the selected checkout; install that checkout before running acceptance')
    return root
