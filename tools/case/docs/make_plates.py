"""Build native Bambu 3MF plate projects from case/out/parts.json (no geometry change).

Usage: make_plates.py  (run from the workspace root) -> case/print/production.3mf, case/print/test-only.3mf (unsliced
inputs in build/case/docs/); slice_and_verify.py slices them and writes the check reports.
Plate layout: assumed Bambu A1 256x256 bed, one filament (GIẢ ĐỊNH: PETG), Z rotation only so the
longest footprint runs along X, 8 mm gaps, 10 mm edge margin.
"""
import json, math, struct, sys, zipfile
from pathlib import Path
from array import array

ROOT = Path.cwd()
OUT = ROOT / 'case' / 'out'
BED = 256.0
GAP, MARGIN = 10.0, 12.0
STRIDE = BED * 1.2          # Bambu lays plates out in a row, 1.2 x bed apart
REV = 'r2'
Y_SIGN = -1


def read_stl(path):
    data = path.read_bytes()
    n = struct.unpack_from('<I', data, 80)[0]
    if 84 + 50 * n != len(data):
        raise SystemExit(f'not a binary STL: {path}')
    return [struct.unpack_from('<9f', data, 84 + 50 * i + 12) for i in range(n)]


def mesh(tris):
    idx, verts, faces = {}, [], []
    for t in tris:
        f = []
        for k in range(3):
            v = tuple(round(x, 5) for x in t[3 * k:3 * k + 3])
            if v not in idx:
                idx[v] = len(verts); verts.append(v)
            f.append(idx[v])
        faces.append(f)
    return verts, faces


def rot_matrix(deg):
    rx, ry, rz = (math.radians(v) for v in deg)
    X = [[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]]
    Y = [[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]]
    Z = [[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]]
    mm = lambda A, B: [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return mm(Z, mm(Y, X))          # same convention as tools/case/moving_check.py


def apply(R, v):
    return tuple(sum(R[i][k] * v[k] for k in range(3)) for i in range(3))


def bbox(vs):
    return tuple(f(v[i] for v in vs) for i in range(3) for f in (min, max))


def footprint(verts, R):
    """(xmin,xmax,ymin,ymax,zmin,zmax) after the rotation R."""
    return bbox([apply(R, v) for v in verts])


def plate_origin(index0, count):
    cols = max(1, math.ceil(math.sqrt(count) - 1e-9))
    return ((index0 % cols) * STRIDE, (index0 // cols) * STRIDE * Y_SIGN)


def plan(manifest, groups):
    """groups: list of (title, [part names]); a group that overflows the bed gets numbered plates."""
    rotd = {p['name']: p.get('printRotateDeg') or [0, 0, 0] for p in manifest['parts']}
    plates = []            # [title, [items]]
    for title, names in groups:
        items = []
        for n in names:
            v, f = mesh(read_stl(OUT / f'{n}.stl'))
            Rp = rot_matrix(rotd[n])
            best = None
            for zr in (0, 90):          # Z rotation only: the longest footprint runs along X when possible
                Rz = rot_matrix([0, 0, zr])
                R = [[sum(Rz[i][k] * Rp[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
                fp = footprint(v, R)
                cand = (fp[1] - fp[0], fp[3] - fp[2], zr, R, fp)
                if best is None or (cand[0] >= cand[1] and best[0] < best[1]):
                    best = cand
            w, h, zr, R, fp = best
            items.append(dict(name=n, verts=v, faces=f, R=R, zrot=zr, printRotateDeg=rotd[n], fp=fp, w=w, h=h))
        items.sort(key=lambda i: (-i['h'], -i['w']))
        pages = []
        for it in items:
            for pg in pages:
                if try_place(pg, it):
                    break
            else:
                pg = dict(items=[], x=MARGIN, y=MARGIN, rowh=0.0)
                pages.append(pg)
                if not try_place(pg, it):
                    raise SystemExit(f'{it["name"]} does not fit a plate')
        for k, pg in enumerate(pages, 1):
            plates.append([title if len(pages) == 1 else f'{title} {k}', pg['items']])
    return plates


def try_place(pg, it):
    x, y, rowh = pg['x'], pg['y'], pg['rowh']
    if x + it['w'] > BED - MARGIN:
        x, y, rowh = MARGIN, y + rowh + GAP, 0.0
    if x + it['w'] > BED - MARGIN or y + it['h'] > BED - MARGIN:
        return False
    it['box'] = (x, y, x + it['w'], y + it['h'])
    pg['items'].append(it)
    pg['x'], pg['y'], pg['rowh'] = x + it['w'] + GAP, y, max(rowh, it['h'])
    return True


def write_3mf(path, plates, title):
    res, build, cfg, plate_cfg = [], [], [], []
    oid = 0
    for pi, (pname, items) in enumerate(plates):
        ox0, oy0 = plate_origin(pi, len(plates))
        inst = ''
        for it in items:
            oid += 1; it['id'] = oid; it['plate'] = pi
            xs, ys, zs = ([v[i] for v in it['verts']] for i in range(3))
            c0 = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
            verts = [(a - c0[0], b - c0[1], c - c0[2]) for a, b, c in it['verts']]   # re-based on the bbox centre
            vx = ''.join(f'<vertex x="{a:.5f}" y="{b:.5f}" z="{c:.5f}"/>' for a, b, c in verts)
            tr = ''.join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in it['faces'])
            res.append(f'<object id="{oid}" name="{it["name"]}" type="model"><mesh><vertices>{vx}</vertices><triangles>{tr}</triangles></mesh></object>')
            R = it['R']
            rb = bbox([apply(R, v) for v in verts])
            rc = ((rb[0] + rb[1]) / 2, (rb[2] + rb[3]) / 2)
            tx = ox0 + (it['box'][0] + it['box'][2]) / 2 - rc[0]
            ty = oy0 + (it['box'][1] + it['box'][3]) / 2 - rc[1]
            tz = -rb[4]
            it['expect'] = dict(x=it['box'][0], y=it['box'][1], w=it['w'], d=it['h'], h=rb[5] - rb[4])
            # 3MF: row vectors, v' = v * M  ->  the 3x3 part is R transposed, row by row
            m = ' '.join(f'{R[j][i]:.9f}' for i in range(3) for j in range(3))
            build.append(f'<item objectid="{oid}" transform="{m} {tx:.5f} {ty:.5f} {tz:.5f}" printable="1"/>')
            cfg.append(f'<object id="{oid}"><metadata key="name" value="{it["name"]}"/><metadata key="extruder" value="1"/>'
                       f'<part id="1" subtype="normal_part"><metadata key="name" value="{it["name"]}"/></part></object>')
            inst += (f'<model_instance><metadata key="object_id" value="{oid}"/><metadata key="instance_id" value="0"/>'
                     f'<metadata key="identify_id" value="{100 + oid}"/></model_instance>')
        plate_cfg.append(f'<plate><metadata key="plater_id" value="{pi + 1}"/><metadata key="plater_name" value="{pname}"/>'
                         f'<metadata key="locked" value="false"/>{inst}</plate>')
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
             'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">'
             f'<metadata name="Title">{title}</metadata><metadata name="Application">BambuStudio-02.07.01.62</metadata>'
             '<metadata name="BambuStudio:3mfVersion">1</metadata>'
             f'<resources>{"".join(res)}</resources><build>{"".join(build)}</build></model>')
    ct = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
          '<Default Extension="config" ContentType="text/xml"/></Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', ct); z.writestr('_rels/.rels', rels)
        z.writestr('3D/3dmodel.model', model)
        z.writestr('Metadata/project_settings.config', (ROOT / 'build/case/docs/project_settings.config').read_text())
        z.writestr('Metadata/model_settings.config', '<?xml version="1.0" encoding="UTF-8"?>\n<config>' + ''.join(cfg) + ''.join(plate_cfg) + '</config>')


def groups(manifest):
    names = [p['name'] for p in manifest['parts'] if p.get('role') != 'coupon' and not p['name'].startswith('ref')]
    pick = lambda f: [n for n in names if f(n)]
    leg = lambda n: n.split('_')[0] in ('hip', 'rocker', 'lower', 'shin', 'upper', 'foot')
    prod = [('Khung hộp', pick(lambda n: n == 'frame')),
            ('Nắp hộp', pick(lambda n: n == 'lid')),
            ('Bánh răng', pick(lambda n: n.startswith('gear_'))),
            ('Khớp chân', pick(leg)),
            ('Chốt và giá nhỏ', pick(lambda n: n.startswith('pin_') or n.endswith('_holder') or n.endswith('_cradle') or n == 'pigtail_clip'))]
    rest = set(names) - {n for _, ns in prod for n in ns}
    if rest:
        raise SystemExit(f'unassigned production parts: {sorted(rest)}')
    prod = [(f'MỚI-SỬA — CẦN IN — {t} {REV}', ns) for t, ns in prod if ns]
    test = [n for n in (p['name'] for p in manifest['parts']) if n.endswith('TEST_ONLY')]
    return prod, [(f'THỬ — TEST ONLY — Mẫu thử {REV}', test)]


if __name__ == '__main__':
    manifest = json.loads((OUT / 'parts.json').read_text())
    prod, test = groups(manifest)
    for (g, name) in ((prod, 'production'), (test, 'test-only')):
        plates = plan(manifest, g)
        write_3mf(ROOT / 'build' / 'case' / 'docs' / f'{name}.raw.3mf', plates, name)
        lay = [dict(plate=pi + 1, plateName=t, name=i['name'], zRotationDeg=i['zrot'], printRotateDeg=i['printRotateDeg'],
                    expect=i['expect']) for pi, (t, its) in enumerate(plates) for i in its]
        json.dump(lay, open(ROOT / 'build' / 'case' / 'docs' / f'{name}.layout.json', 'w'), indent=1, ensure_ascii=False)
        for pi, (t, its) in enumerate(plates, 1):
            print(name, pi, t, len(its))
