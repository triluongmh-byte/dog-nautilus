"""Flatten Bambu Studio system profiles (resolve 'inherits') into build/case/docs/profiles/*.json so the CLI
gets the full A1 values (256x256 bed). Usage: profiles.py (from the workspace root)."""
import json
from pathlib import Path
R = Path('/Applications/BambuStudio.app/Contents/Resources/profiles/BBL')


def flat(kind, name):
    d = json.loads((R / kind / f'{name}.json').read_text())
    parent = d.get('inherits')
    base = flat(kind, parent) if parent else {}
    base.update({k: v for k, v in d.items() if k != 'inherits'})
    return base


def build(root=Path.cwd()):
    out = root / 'build/case/docs/profiles'; out.mkdir(parents=True, exist_ok=True)
    paths = []
    for kind, name in (('machine', 'Bambu Lab A1 0.4 nozzle'), ('process', '0.20mm Standard @BBL A1'),
                       ('filament', 'Generic PETG @BBL A1')):
        d = flat(kind, name); d['name'] = name; d['from'] = 'system'
        if kind == 'machine':
            d['curr_bed_type'] = 'Textured PEI Plate'   # PETG is not allowed on the Cool Plate
        p = out / f'{kind}.json'; p.write_text(json.dumps(d, indent=1)); paths.append(str(p))
    return paths


if __name__ == '__main__':
    print(build())
