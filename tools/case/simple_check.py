"""Simple-stage check: printability, defects, clearances and glue faces of the frame + glue-on holders.

    "$KICAD_CASE_PYTHON" tools/case/simple_check.py [--force]

Reads case/out/*.step|stl (never the build code). Per part (parallel, every CPU core):
  solid validity, bed fit, wall thickness (kicadpy sampler), unsupported downward faces.
Assembly: pairwise overlaps between printed parts, clearance to every module envelope
(cells as cylinders, servo body/flange/above-flange as boxes), wall above each servo window,
glue face of each glue-on holder, declared wire routes (kicadpy sampler).
Writes case/reports/mechanical.json (verdict + passed + scope + partShas, handwired receipt input).
Results are cached in build/case/simple_check_cache.json by input hashes; the report is
rewritten on every run.
"""
import concurrent.futures as cf
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "case" / "out"
REPORT = ROOT / "case" / "reports" / "mechanical.json"
CACHE = ROOT / "build" / "case" / "simple_check_cache.json"
sys.path.insert(0, str(Path(__file__).resolve().parent))

STAGE_PARTS = ["frame", "carrier_holder", "battery_cradle", "charger_holder", "buck_holder",
               "coupon_servo_seat_TEST_ONLY", "coupon_mounts_TEST_ONLY"]
GLUE_ON = ["carrier_holder", "battery_cradle", "charger_holder", "buck_holder"]
MIN_GAP = 0.2              # holder/frame to module envelope
OVERLAP_MM3 = 0.5
BRIDGE_MAX_MM = 8.0        # a downward face narrower than this is a printable bridge / hole top
MIN_WALL_ABOVE_SERVO = 2.0
LEVELS = ["pass", "review", "unverified", "fail"]
# designed seating contacts: touching is the mount, overlap is still a failure
SEATS = {("carrier_holder", "carrier_pcb"), ("charger_holder", "charger_bms_2s_usbc"),
         ("buck_holder", "buck_5v_3a"), ("frame", "power_switch"), ("frame", "oled_154_128x64")}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worst(levels):
    return max(levels, key=LEVELS.index) if levels else "unverified"


def load_step(name):
    import cadquery as cq
    return cq.importers.importStep(str(OUT / f"{name}.step")).val()


# ------------------------------------------------------------------ per part
def overhang_regions(tris, bed_z):
    """Connected downward-facing (>45 deg) regions off the bed, with their narrow span."""
    import numpy as np
    e1, e2 = tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]
    n = np.cross(e1, e2)
    area = np.linalg.norm(n, axis=1)
    ok = area > 1e-12
    nz = np.zeros(len(tris))
    nz[ok] = n[ok, 2] / area[ok]
    down = np.nonzero((nz < -math.cos(math.radians(45)) + 1e-6) & (tris[:, :, 2].min(axis=1) > bed_z + 0.05))[0]
    if not len(down):
        return []
    # union-find over shared (rounded) vertices
    parent = list(range(len(down)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    seen = {}
    for k, t in enumerate(down):
        for v in tris[t]:
            key = tuple(np.round(v, 3))
            if key in seen:
                a, b = find(k), find(seen[key])
                if a != b:
                    parent[a] = b
            else:
                seen[key] = k
    groups = {}
    for k in range(len(down)):
        groups.setdefault(find(k), []).append(down[k])
    regions = []
    for idx in groups.values():
        pts = tris[idx].reshape(-1, 3)
        span = pts.max(axis=0) - pts.min(axis=0)
        regions.append({"narrowMm": round(float(min(span[0], span[1])), 2),
                        "areaMm2": round(float(area[idx].sum() / 2), 2),
                        "at": [round(float(v), 1) for v in pts.mean(axis=0)]})
    return regions


def check_part(name, nozzle, bed, skins=()):
    from kicadpy import case_measure as cm
    items = []
    shape = load_step(name)
    solids = shape.Solids()
    valid = shape.isValid()
    vol = shape.Volume()
    items.append({"check": f"solid:{name}", "level": "pass" if valid and vol > 0 else "fail",
                  "message": f"{name}: {len(solids)} solid(s), valid={valid}, volume {vol:.0f} mm3"})
    bb = shape.BoundingBox()
    dims = sorted([bb.xlen, bb.ylen, bb.zlen])
    fits = dims[0] <= sorted(bed)[0] and dims[1] <= sorted(bed)[1] and dims[2] <= sorted(bed)[2]
    items.append({"check": f"bed:{name}", "level": "pass" if fits else "fail",
                  "message": f"{name}: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm on a {bed} bed"})
    stl = OUT / f"{name}.stl"
    items.append(cm.check_walls(name, stl, nozzle, skins))
    tris = cm.stl_triangles(stl)
    regions = overhang_regions(tris, float(tris[:, :, 2].min()))
    wide = [r for r in regions if r["narrowMm"] > BRIDGE_MAX_MM]
    items.append({"check": f"overhang:{name}", "level": "fail" if wide else "pass",
                  "message": (f"{name}: {len(wide)} unsupported downward region(s) wider than {BRIDGE_MAX_MM} mm: "
                              f"{wide[:4]}") if wide else
                  f"{name}: prints floor/glue-face down without supports ({len(regions)} short bridges/hole tops, "
                  f"widest {max([r['narrowMm'] for r in regions], default=0)} mm)",
                  "regions": len(regions)})
    return items


# ------------------------------------------------------------------ assembly
def envelopes():
    """Module keep-outs from the contract, plus the servos at the case's chosen seat."""
    import cadquery as cq
    import geom as g
    c = json.loads((ROOT / "PILOT_CONTRACT.json").read_text())
    env = {}
    for m in c["interfaces"]["modules"]:
        mid = m["id"]
        if mid.startswith("servo_") or mid in ("battery_2s_18650", "carrier_component_zone"):
            continue
        (x, y, z), (dx, dy, dz) = m["positionMm"], m["sizeMm"]
        env[mid] = cq.Solid.makeBox(dx, dy, dz, cq.Vector(x - dx / 2, y - dy / 2, z - dz / 2))
    for i, y in enumerate((g.CELL_Y, -g.CELL_Y)):
        env[f"cell_{i + 1}"] = cq.Solid.makeCylinder(g.CELL_R, 65.0, cq.Vector(3.5 - 32.5, y, g.CELL_Z),
                                                     cq.Vector(1, 0, 0))
    for leg, sx, sy in g.legs():
        xc = sx * g.SERVO_XC
        hl, hh = g.SERVO_L / 2, g.SERVO_H / 2
        y_in = g.YI - g.SERVO_DEPTH_IN
        y0, y1 = (y_in, g.YO + g.FLANGE_T + g.ABOVE_FLANGE) if sy > 0 else (-(g.YO + g.FLANGE_T + g.ABOVE_FLANGE), -y_in)
        body = cq.Solid.makeBox(2 * hl, y1 - y0, 2 * hh, cq.Vector(xc - hl, y0, g.DRIVE_Z - hh))
        fy0, fy1 = (g.YO, g.YO + g.FLANGE_T) if sy > 0 else (-g.YO - g.FLANGE_T, -g.YO)
        flange = cq.Solid.makeBox(g.FLANGE_L, fy1 - fy0, 2 * hh,
                                  cq.Vector(xc - g.FLANGE_L / 2, fy0, g.DRIVE_Z - hh))
        env[f"servo_{leg}"] = body
        env[f"servo_{leg}_flange"] = flange          # bears on the outer wall face: contact allowed
    return env


def pair_overlap(a_name, b_name):
    a, b = load_step(a_name), load_step(b_name)
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if ba.xmin > bb.xmax or bb.xmin > ba.xmax or ba.ymin > bb.ymax or bb.ymin > ba.ymax or ba.zmin > bb.zmax or bb.zmin > ba.zmax:
        return a_name, b_name, 0.0
    return a_name, b_name, float(a.intersect(b).Volume())


def part_vs_envelopes(name):
    shape = load_step(name)
    sb = shape.BoundingBox()
    res = []
    for mid, e in envelopes().items():
        eb = e.BoundingBox()
        apart = max(sb.xmin - eb.xmax, eb.xmin - sb.xmax, sb.ymin - eb.ymax, eb.ymin - sb.ymax,
                    sb.zmin - eb.zmax, eb.zmin - sb.zmax)
        if apart > 3:
            continue
        inter = float(shape.intersect(e).Volume())
        gap = 0.0 if inter > 1e-6 else float(shape.distance(e))
        res.append((name, mid, inter, gap))
    return res


def wall_above_servos():
    import cadquery as cq
    import geom as g
    fr = load_step("frame")
    out = []
    top = g.DRIVE_Z + g.SERVO_H / 2 + g.SERVO_FIT
    for leg, sx, sy in g.legs():
        xs = [sx * g.SERVO_XC + d for d in (-8, 0, 8)]
        ymid = sy * (g.YI + g.WALL / 2)
        mins = []
        for x in xs:
            probe = cq.Solid.makeBox(0.2, 0.2, g.FRAME_H - top + 1, cq.Vector(x - 0.1, ymid - 0.1, top - 0.5))
            mins.append(fr.intersect(probe).Volume() / 0.04 - 0.0)
        out.append((leg, min(mins)))
    return out


def glue_face(name):
    """The holder's lowest face: planar, at the floor top, and its area."""
    import geom as g
    shape = load_step(name)
    faces = [f for f in shape.Faces() if f.geomType() == "PLANE" and abs(f.normalAt().z + 1) < 1e-6]
    zmin = shape.BoundingBox().zmin
    bottom = [f for f in faces if abs(f.Center().z - zmin) < 1e-4]
    area = sum(f.Area() for f in bottom)
    return name, abs(zmin - g.FLOOR_TOP) < 1e-3, area


def wires(names):
    import cadquery as cq
    from kicadpy import case_measure as cm
    intent = json.loads((ROOT / "case" / "interfaces.json").read_text())
    printed = [(n, load_step(n)) for n in names]
    return cm.check_wires(cq, intent.get("wires") or [], printed)


# ------------------------------------------------------------------ main
def main(argv):
    force = "--force" in argv
    started = time.time()
    manifest = json.loads((OUT / "parts.json").read_text())
    # scoped to the simple stage's own parts: later stages (moving, joints, lid) have their own checks
    # (the lid deliberately seats on the OLED/fan/stow envelope tops at z 28.5: tools/case/lid_check.py)
    stage = [p for p in manifest["parts"] if p["name"] in STAGE_PARTS]
    parts = [p["name"] for p in stage]
    roles = {p["name"]: p.get("role") for p in stage}
    part_shas = {}
    for p in stage:
        for k in ("step", "stl"):
            part_shas[p[k]] = sha(OUT / p[k])
    intent = json.loads((ROOT / "case" / "interfaces.json").read_text())
    inputs = {"parts": part_shas, "contract": sha(ROOT / "PILOT_CONTRACT.json"),
              "intent": sha(ROOT / "case" / "interfaces.json"), "geom": sha(Path(__file__).parent / "geom.py"),
              "script": sha(__file__)}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache = {}
    if CACHE.exists():
        try:
            cache = json.loads(CACHE.read_text())
        except ValueError:
            cache = {}
    if not force and cache.get("key") == key and cache.get("items"):
        items, cached = cache["items"], True
    else:
        cached = False
        nozzle = float((intent.get("printer") or {}).get("nozzleMm") or 0.4)
        bed = (intent.get("printer") or {}).get("bedMm") or [220, 220, 250]
        assembled = [n for n in parts if roles.get(n) != "coupon"]
        items = []
        with cf.ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
            f_parts = [ex.submit(check_part, n, nozzle, bed, intent.get("skins") or ()) for n in parts]
            f_pairs = [ex.submit(pair_overlap, a, b) for i, a in enumerate(assembled) for b in assembled[i + 1:]]
            f_env = [ex.submit(part_vs_envelopes, n) for n in assembled]
            f_glue = [ex.submit(glue_face, n) for n in GLUE_ON if n in parts]
            f_wall = ex.submit(wall_above_servos)
            f_wires = ex.submit(wires, parts)
            for f in f_parts:
                items += f.result()
            for f in f_pairs:
                a, b, v = f.result()
                items.append({"check": f"overlap:{a}+{b}", "level": "fail" if v > OVERLAP_MM3 else "pass",
                              "message": f"{a} and {b} share {v:.2f} mm3"})
            for f in f_env:
                for n, mid, inter, gap in f.result():
                    need = 0.0 if mid.endswith("_flange") or (n, mid) in SEATS else MIN_GAP
                    lvl = "fail" if inter > 1e-3 or gap < need - 1e-6 else "pass"
                    items.append({"check": f"keepout:{n}+{mid}", "level": lvl,
                                  "message": f"{n} vs {mid}: overlap {inter:.2f} mm3, gap {gap:.2f} mm (min {MIN_GAP})"})
            for f in f_glue:
                n, at_floor, area = f.result()
                lvl = "pass" if at_floor and area >= 50 else "fail"
                items.append({"check": f"glue:{n}", "level": lvl,
                              "message": f"{n}: flat glue face {area:.0f} mm2, on the floor top: {at_floor}"})
            for leg, h in f_wall.result():
                items.append({"check": f"servo-wall:{leg}",
                              "level": "pass" if h >= MIN_WALL_ABOVE_SERVO - 0.01 else "fail",
                              "message": f"servo_{leg}: {h:.2f} mm of wall above the window (min {MIN_WALL_ABOVE_SERVO})"})
            items += f_wires.result()
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"key": key, "items": items}, indent=1))
    verdict = worst([i["level"] for i in items])
    report = {"schema": 1, "verdict": verdict, "passed": verdict in ("pass", "review"),
              "scope": "stage simple: frame + glue-on holders + TEST ONLY coupons (printability, defects, "
                       "keep-outs, glue faces, servo wall, wire routes)",
              "stage": "simple", "parts": parts,
              "partShas": part_shas, "cached": cached, "seconds": round(time.time() - started, 2),
              "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "failures": [i for i in items if i["level"] == "fail"],
              "reviews": [i for i in items if i["level"] in ("review", "unverified")],
              "checks": items}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=1) + "\n")
    import receipt
    receipt.write()
    print(json.dumps({"verdict": verdict, "fail": len(report["failures"]), "review": len(report["reviews"]),
                      "cached": cached, "seconds": report["seconds"]}))
    for i in report["failures"] + report["reviews"]:
        print(f"  {i['level']:10} {i['check']}: {i['message'][:220]}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
