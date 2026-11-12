"""Slice build/case/docs/*.raw.3mf with the Bambu Studio CLI, save the native projects to print/, verify them by
re-opening the saved 3MF + the slicer's per-plate result, write print/*-check.json, and bind printProject.
Run from the workspace root after make_plates.py. Assumption (GIẢ ĐỊNH): Bambu Lab A1 0.4, Generic PETG, 0.20 mm Standard.
The slicer needs a temp-dir output path (it cannot write its .tmp file inside the worktree)."""
import hashlib, json, os, re, shutil, subprocess, tempfile, zipfile, struct
from pathlib import Path

ROOT = Path.cwd(); OUT = ROOT / 'case/out'; DOCS = ROOT / 'build/case/docs'; PRINT = ROOT / 'case/print'
BIN = '/Applications/BambuStudio.app/Contents/MacOS/BambuStudio'
R = '/Applications/BambuStudio.app/Contents/Resources/profiles/BBL'
PROF = DOCS / 'profiles'      # flattened by profiles.py (the CLI does not resolve 'inherits' fully)
SETTINGS = f'{PROF}/machine.json;{PROF}/process.json'
FILAMENT = f'{PROF}/filament.json'
BED = 256.0
Y_SIGN = -1
FORBIDDEN = set('/\\:*?"<>|')
sha = lambda b: hashlib.sha256(b).hexdigest()


def tri_count(stl):
    return struct.unpack_from('<I', stl.read_bytes(), 80)[0]


def run(name, layout, manifest, production):
    tmp = Path(tempfile.mkdtemp(prefix='slice-'))
    p = subprocess.run([BIN, '--load-settings', SETTINGS, '--load-filaments', FILAMENT, '--slice', '0',
                        '--outputdir', str(tmp), '--export-3mf', f'{name}.3mf', str(DOCS / f'{name}.raw.3mf')],
                       capture_output=True, text=True)
    (DOCS / f'{name}.slicer.log').write_text(p.stdout + p.stderr)
    result = json.loads((tmp / 'result.json').read_text())
    PRINT.mkdir(exist_ok=True)
    dst = PRINT / f'{name}.3mf'
    shutil.copyfile(tmp / f'{name}.3mf', dst)
    # re-open the saved project
    with zipfile.ZipFile(dst) as z:
        cfg = z.read('Metadata/model_settings.config').decode('utf-8')
        ps = z.read('Metadata/project_settings.config').decode('utf-8')
    objs = dict(re.findall(r'<object id="(\d+)">\s*<metadata key="name" value="([^"]+)"', cfg))
    plates = []
    for m in re.finditer(r'<plate>(.*?)</plate>', cfg, re.S):
        b = m.group(1)
        pname = re.search(r'plater_name" value="([^"]*)"', b).group(1)
        pid = int(re.search(r'plater_id" value="(\d+)"', b).group(1))
        ids = re.findall(r'key="object_id" value="(\d+)"', b)
        plates.append({'index': pid, 'name': pname, 'objects': [objs[i] for i in ids]})
    settings = json.loads(ps)
    problems, warnings = [], []
    bys = {s['id']: s for s in result['sliced_plates']}
    meshes, outp = [], []
    rot = {l['name']: l for l in layout}
    nplates = len(plates)
    import math
    cols = max(1, math.ceil(math.sqrt(nplates) - 1e-9))
    for pl in plates:
        if not pl['name'] or len(pl['name']) > 40 or set(pl['name']) & FORBIDDEN:
            problems.append(f"plate name not allowed: {pl['name']!r}")
        s = bys.get(pl['index'])
        if not s:
            problems.append(f"plate {pl['index']} not sliced"); continue
        if s.get('warning_message'):
            warnings.append(f"plate {pl['index']}: {s['warning_message']}")
        boxes = []
        for o in s['objects']:
            b = dict(o['bbox']); i0 = pl['index'] - 1   # plates sit 1.2 bed widths apart in the slicer's world (grid, ceil(sqrt(n)) columns)
            b['x'] -= (i0 % cols) * BED * 1.2; b['y'] -= (i0 // cols) * BED * 1.2 * Y_SIGN
            e = rot[o['name']]['expect']
            if max(abs(b['x'] - e['x']), abs(b['y'] - e['y']), abs(b['width'] - e['w']), abs(b['depth'] - e['d']), abs(b['height'] - e['h'])) > 0.3:
                problems.append(f"{o['name']}: slicer box {[round(b[k], 1) for k in ('x', 'y', 'width', 'depth', 'height')]} differs from the planned {[round(e[k], 1) for k in ('x', 'y', 'w', 'd', 'h')]}")
            boxes.append((o['name'], b['x'], b['y'], b['x'] + b['width'], b['y'] + b['depth'], b['height']))
            if b['x'] < 0 or b['y'] < 0 or b['x'] + b['width'] > BED or b['y'] + b['depth'] > BED:
                problems.append(f"{o['name']} outside the {BED:g} mm bed")
            if abs(b['z']) > 0.01:
                problems.append(f"{o['name']} floating at z={b['z']}")
            if o['triangle_count'] != tri_count(OUT / f"{o['name']}.stl"):
                warnings.append(f"{o['name']}: slicer triangle count {o['triangle_count']} differs from STL (repaired/merged)")
        for i, a in enumerate(boxes):
            for c in boxes[i + 1:]:
                if a[1] < c[3] and c[1] < a[3] and a[2] < c[4] and c[2] < a[4]:
                    problems.append(f"{a[0]} and {c[0]} overlap on plate {pl['index']}")
        outp.append({'index': pl['index'], 'name': pl['name'], 'parts': [f'{n}.stl' for n in pl['objects']],
                     'filament': 'Generic PETG (GIẢ ĐỊNH)', 'supports': 'none',
                     'estimatedMinutes': round(s.get('total_predication', 0) / 60),
                     'footprints': [{'part': n, 'xMm': round(x1 - x0, 2), 'yMm': round(y1 - y0, 2), 'zMm': round(h, 2),
                                     'zRotationDeg': rot[n]['zRotationDeg'], 'yLongerReason': ('' if (x1 - x0) >= (y1 - y0) else 'needs a reason')}
                                    for n, x0, y0, x1, y1, h in boxes]})
    seen = [n for pl in plates for n in pl['objects']]
    names = [l['name'] for l in layout]
    if sorted(seen) != sorted(names):
        problems.append(f'plate coverage {sorted(seen)} != {sorted(names)}')
    if not production and any('TEST_ONLY' not in n for n in seen):
        problems.append('non-test part in test project')
    if production and any('TEST_ONLY' in n for n in seen):
        problems.append('coupon in the production project')
    for n in names:
        mp = next(p for p in manifest['parts'] if p['name'] == n)
        meshes.append({'name': f'{n}.stl', 'canonicalSTLSha256': sha((OUT / f'{n}.stl').read_bytes()),
                       'printRotateDeg': mp.get('printRotateDeg') or [0, 0, 0], 'zRotationDeg': rot[n]['zRotationDeg']})
    report = {'passed': not problems, 'file': f'case/print/{name}.3mf', 'sha256': sha(dst.read_bytes()),
              'slicer': 'BambuStudio 02.07.01.62 CLI', 'profile': {'machine': 'Bambu Lab A1 0.4 nozzle',
              'process': '0.20mm Standard @BBL A1', 'filament': 'Generic PETG @BBL A1 (GIẢ ĐỊNH)',
              'bedMm': [BED, BED], 'layerHeightMm': result.get('layer_height')},
              'meshes': meshes, 'plates': outp, 'problems': problems, 'warnings': warnings,
              'note': 'CAD/slicer check only; no physical print. Generated by tools/case/docs/slice_and_verify.py.'}
    (PRINT / f'{name}-check.json').write_text(json.dumps(report, indent=1, ensure_ascii=False))
    print(name, 'passed' if report['passed'] else problems, warnings)
    return report


if __name__ == '__main__':
    manifest = json.loads((OUT / 'parts.json').read_text())
    for name, prod in (('production', True), ('test-only', False)):
        run(name, json.loads((DOCS / f'{name}.layout.json').read_text()), manifest, prod)
