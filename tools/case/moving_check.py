"""Moving-stage checks for the 4 nautilus gear pairs + Jansen legs.

    "$KICAD_CASE_PYTHON" tools/case/moving_check.py print   [--force] -> case/reports/moving-print.json
    "$KICAD_CASE_PYTHON" tools/case/moving_check.py motion  [--force] [--steps N] -> case/reports/moving-motion.json

print : per part (all cores) solid validity, bed fit in its print orientation, walls (kicadpy sampler),
        unsupported downward regions after printRotateDeg.
motion: full revolution sweep (default 72 poses, 5 deg of drive contact angle) of each leg with the
        true linkage kinematics (tools/case/legs.py): every moving part, the M2 screw shanks/heads and
        the frame; overlap between any two (gears mesh: allowed only within the backlash),
        moving-vs-frame clearance, robot envelope 160 x 150 x 70 (ground to deck-post top), the
        foot pad being the lowest point, and front/rear legs on one side never sharing space.
Results are cached in build/case/moving_<kind>_cache.json by input hashes; reports are always
rewritten, then the handwired receipt (tools/case/receipt.py).
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
sys.path.insert(0, str(Path(__file__).resolve().parent))

LEGS = ["FL", "FR", "RL", "RR"]
LEVELS = ["pass", "review", "unverified", "fail"]
ENVELOPE = (160.0, 150.0, 70.0)
DECK_TOP_Z = 37.0              # lid top 31 + 6 mm deck posts (contract)
GROUND_Z = -32.5
OVERLAP_MM3 = 0.05
GEAR_OVERLAP_MM3 = 0.5         # sampled mesh: teeth may graze inside the 0.4 mm backoff
MIN_FRAME_GAP = 0.25          # hubs run 0.4 mm off the pad faces (axial thrust gap)
BRIDGE_MAX_MM = 8.0
GEAR_MAX_GAP = 1.0           # beyond this the teeth could skip


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worst(levels):
    return max(levels, key=LEVELS.index) if levels else "unverified"


def manifest():
    return json.loads((OUT / "parts.json").read_text())


def moving_parts():
    import legs as L
    return [f"{n}_{leg}" for leg in LEGS for n in L.GEARS + L.LINKS]


def coupon_parts():
    return ["coupon_gear_pair_TEST_ONLY"]


def load(name):
    import cadquery as cq
    return cq.importers.importStep(str(OUT / f"{name}.step")).val()


# ------------------------------------------------------------------ print
def rot_matrix(deg):
    import numpy as np
    rx, ry, rz = (math.radians(v) for v in deg)
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


def print_part(name, rot, nozzle, bed, skins=()):
    from kicadpy import case_measure as cm
    import simple_check as sc
    items = []
    shape = load(name)
    valid, vol = shape.isValid(), shape.Volume()
    items.append({"check": f"solid:{name}", "level": "pass" if valid and vol > 0 else "fail",
                  "message": f"{name}: {len(shape.Solids())} solid(s), valid={valid}, volume {vol:.0f} mm3"})
    stl = OUT / f"{name}.stl"
    tris = cm.stl_triangles(stl)
    t = tris @ rot_matrix(rot).T
    span = t.reshape(-1, 3).max(axis=0) - t.reshape(-1, 3).min(axis=0)
    fits = all(span[i] <= bed[i] for i in range(3)) or sorted(span[:2]) <= sorted(bed[:2]) and span[2] <= bed[2]
    items.append({"check": f"bed:{name}", "level": "pass" if fits else "fail",
                  "message": f"{name}: {span[0]:.1f} x {span[1]:.1f} x {span[2]:.1f} mm printed {rot}"})
    items.append(cm.check_walls(name, stl, nozzle, skins))
    regions = sc.overhang_regions(t, float(t[:, :, 2].min()))
    wide = [r for r in regions if r["narrowMm"] > BRIDGE_MAX_MM]
    items.append({"check": f"overhang:{name}", "level": "fail" if wide else "pass",
                  "message": (f"{name}: {len(wide)} unsupported region(s) wider than {BRIDGE_MAX_MM} mm: {wide[:3]}")
                  if wide else f"{name}: prints {rot} without supports ({len(regions)} short bridges/hole tops)"})
    return items


# ------------------------------------------------------------------ motion
def screws(leg, s1):
    """M2 screw shank (d 2.0) + head (d 3.8 x 1.3) at each joint, posed: list of (name, solid)."""
    import cadquery as cq
    import legs as L
    sx, sy = L.leg_sign(leg)
    pts, _, _ = L.kin(s1)
    yl = L.Y_L
    t = L.LINK_T
    # joint: (point, y_from, y_to, head side 'in'/'out')
    spec = {"C": (L.Y_GEAR, yl[3] + t, "in"), "D": (yl[0], yl[3] + t, "out"),
            "E": (yl[0], yl[3] + t, "in"), "F": (yl[1], yl[4] + t, "out"), "G": (yl[3], yl[4] + t, "out")}
    out = []
    for j, (y0, y1, head) in spec.items():
        x, z = L.world(pts[j], leg)
        shank = cq.Solid.makeCylinder(1.0, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0))
        hy = (y0 - 1.3, y0) if head == "in" else (y1, y1 + 1.3)
        hd = cq.Solid.makeCylinder(1.9, 1.3, cq.Vector(x, hy[0], z), cq.Vector(0, 1, 0))
        s = shank.fuse(hd)
        if sy < 0:
            s = s.mirror("XZ")
        out.append((f"screw_{j}_{leg}", s, j))
    return out


# which links each joint screw passes through (no collision check against them)
SCREW_HOSTS = {"C": {"gear_crank", "lower_link", "upper_link"}, "D": {"hip_triangle", "upper_link"},
               "E": {"hip_triangle", "shin_link"}, "F": {"rocker", "lower_link", "foot"},
               "G": {"shin_link", "foot"}}


def sweep_leg(leg, poses):
    import legs as L
    frame = load("frame")
    rest = {n: load(f"{n}_{leg}") for n in L.GEARS + L.LINKS}
    fb = frame.BoundingBox()
    worst_frame_gap, overlaps, gear_max, lowest_non_foot, gear_gap = 1e9, [], 0.0, [], 0.0
    foot_min, mins, maxs = 1e9, [1e9] * 3, [-1e9] * 3
    for s1 in poses:
        shapes = [(f"{n}_{leg}", L.posed(rest[n], n, leg, s1), n) for n in rest]
        scr = screws(leg, s1)
        boxes = {}
        for nm, sh, base in shapes + [(a, b, None) for a, b, _ in scr]:
            bb = sh.BoundingBox()
            boxes[nm] = bb
            mins = [min(mins[0], bb.xmin), min(mins[1], bb.ymin), min(mins[2], bb.zmin)]
            maxs = [max(maxs[0], bb.xmax), max(maxs[1], bb.ymax), max(maxs[2], bb.zmax)]
        fz = boxes[f"foot_{leg}"].zmin
        foot_min = min(foot_min, fz)
        for nm, sh, base in shapes:
            if base != "foot" and boxes[nm].zmin < fz - 0.01:
                lowest_non_foot.append((nm, round(s1, 2), round(boxes[nm].zmin - fz, 2)))
        everything = shapes + [(a, b, j) for a, b, j in scr]
        for i, (an, a, ab) in enumerate(everything):
            for bn, b, bbase in everything[i + 1:]:
                A, B = boxes[an], boxes[bn]
                if A.xmin > B.xmax or B.xmin > A.xmax or A.ymin > B.ymax or B.ymin > A.ymax or A.zmin > B.zmax or B.zmin > A.zmax:
                    continue
                if an.startswith("screw_") and bn.startswith("screw_"):
                    continue
                if an.startswith("screw_") and bbase in SCREW_HOSTS.get(ab, ()):   # (never: a screw first)
                    continue
                if bn.startswith("screw_") and ab in SCREW_HOSTS.get(bbase, ()):
                    continue
                v = a.intersect(b).Volume()
                gears = {ab, bbase} == {"gear_drive", "gear_crank"}
                if gears:
                    gear_max = max(gear_max, v)
                    gap = a.distance(b) if v < 1e-6 else 0.0
                    gear_gap = max(gear_gap, gap)
                    if v > GEAR_OVERLAP_MM3:
                        overlaps.append((an, bn, round(s1, 2), round(v, 3)))
                elif v > OVERLAP_MM3:
                    overlaps.append((an, bn, round(s1, 2), round(v, 3)))
        for nm, sh, base in shapes + [(a, b, None) for a, b, _ in scr]:
            bb = boxes[nm]
            apart = max(bb.xmin - fb.xmax, fb.xmin - bb.xmax, bb.ymin - fb.ymax, fb.ymin - bb.ymax,
                        bb.zmin - fb.zmax, fb.zmin - bb.zmax)
            if apart > 2:
                continue
            d = sh.distance(frame) if frame.intersect(sh).Volume() < 1e-6 else -1.0
            worst_frame_gap = min(worst_frame_gap, d)
    return {"leg": leg, "poses": len(poses), "overlaps": overlaps[:20], "overlapCount": len(overlaps),
            "gearMaxOverlapMm3": round(gear_max, 3), "gearMaxGapMm": round(gear_gap, 3), "frameGapMm": round(worst_frame_gap, 3),
            "footMinZ": round(foot_min, 2), "notFootLowest": lowest_non_foot[:10],
            "sweptBox": [round(v, 2) for v in mins + maxs]}


def motion_items(results):
    items = []
    for r in results:
        leg = r["leg"]
        items.append({"check": f"motion:{leg}:collisions", "level": "fail" if r["overlapCount"] else "pass",
                      "message": f"leg {leg}: {r['overlapCount']} collisions over {r['poses']} poses "
                                 f"(gear mesh max overlap {r['gearMaxOverlapMm3']} mm3) {r['overlaps'][:4]}"})
        gg = r["gearMaxGapMm"]
        items.append({"check": f"motion:{leg}:mesh", "level": "pass" if gg <= GEAR_MAX_GAP else "review",
                      "message": f"leg {leg}: nautilus pair stays in mesh, widest tooth gap {gg} mm "
                                 f"(max {GEAR_MAX_GAP}), overlap max {r['gearMaxOverlapMm3']} mm3"})
        g = r["frameGapMm"]
        lvl = "fail" if g < MIN_FRAME_GAP else ("review" if g < 1.5 * MIN_FRAME_GAP else "pass")
        items.append({"check": f"motion:{leg}:frame", "level": lvl,
                      "message": f"leg {leg}: smallest moving-to-frame gap {g} mm (min {MIN_FRAME_GAP})"})
        items.append({"check": f"motion:{leg}:foot", "level": "review" if r["notFootLowest"] else "pass",
                      "message": f"leg {leg}: foot pad lowest at z {r['footMinZ']}; other parts lower: {r['notFootLowest'][:3]}"})
    box = [min(r["sweptBox"][i] for r in results) for i in range(3)] + \
          [max(r["sweptBox"][i + 3] for r in results) for i in range(3)]
    import legs  # noqa: F401
    import geom as G
    xspan = max(box[3], G.XO) - min(box[0], -G.XO)
    yspan = max(box[4], G.YO) - min(box[1], -G.YO)
    zspan = DECK_TOP_Z - min(box[2], 0.0)
    ok = xspan <= ENVELOPE[0] and yspan <= ENVELOPE[1] and zspan <= ENVELOPE[2]
    items.append({"check": "motion:envelope", "level": "pass" if ok else "fail",
                  "message": f"robot with leg sweep {xspan:.1f} x {yspan:.1f} x {zspan:.1f} mm "
                             f"(sealed {ENVELOPE}); swept box {box}"})
    ground_ok = min(r["footMinZ"] for r in results)
    items.append({"check": "motion:ground", "level": "pass" if abs(ground_ok - GROUND_Z) < 1.0 else "review",
                  "message": f"lowest foot point z {ground_ok} (contract ground about {GROUND_Z})"})
    for side in ("L", "R"):
        f, rr = next(r for r in results if r["leg"] == "F" + side), next(r for r in results if r["leg"] == "R" + side)
        gap = f["sweptBox"][0] - rr["sweptBox"][3]
        items.append({"check": f"motion:front-rear-{side}", "level": "pass" if gap > 0.3 else "fail",
                      "message": f"side {side}: front and rear swept volumes are {gap:.2f} mm apart along X"})
    return items


# ------------------------------------------------------------------ main
def main(argv):
    kind = argv[0] if argv and argv[0] in ("print", "motion") else "print"
    force = "--force" in argv
    steps = int(argv[argv.index("--steps") + 1]) if "--steps" in argv else 72
    started = time.time()
    man = manifest()
    entries = {p["name"]: p for p in man["parts"]}
    names = [n for n in moving_parts() + coupon_parts() if n in entries] if kind == "print" else \
        [n for n in moving_parts() if n in entries] + ["frame"]
    shas = {}
    for n in names:
        for ext in ("step", "stl"):
            shas[f"{n}.{ext}"] = sha(OUT / f"{n}.{ext}")
    here = Path(__file__).parent
    inputs = {"parts": shas, "kind": kind, "steps": steps, "script": sha(__file__), "legs": sha(here / "legs.py"),
              "geom": sha(here / "geom.py"), "intent": sha(ROOT / "case" / "interfaces.json"), "contract": sha(ROOT / "PILOT_CONTRACT.json"),
              "rot": {n: entries[n].get("printRotateDeg") for n in names if n in entries}}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache_file = ROOT / "build" / "case" / f"moving_{kind}_cache.json"
    cache = {}
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text())
        except ValueError:
            cache = {}
    missing = [n for n in moving_parts() if n not in entries]
    if not force and cache.get("key") == key and cache.get("items") is not None:
        items, cached = cache["items"], True
    else:
        cached = False
        items = []
        workers = os.cpu_count() or 1
        if kind == "print":
            intent = json.loads((ROOT / "case" / "interfaces.json").read_text())
            nozzle = float((intent.get("printer") or {}).get("nozzleMm") or 0.4)
            bed = (intent.get("printer") or {}).get("bedMm") or [220, 220, 250]
            with cf.ProcessPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(print_part, n, entries[n].get("printRotateDeg") or [0, 0, 0], nozzle, bed,
                                  intent.get("skins") or ())
                        for n in names]
                for f in futs:
                    items += f.result()
        else:
            poses = [2 * math.pi * i / steps for i in range(steps)]
            chunks = max(1, workers // len(LEGS))
            with cf.ProcessPoolExecutor(max_workers=workers) as ex:
                futs = {leg: [ex.submit(sweep_leg, leg, poses[c::chunks]) for c in range(chunks)] for leg in LEGS}
                results = []
                for leg, fs in futs.items():
                    parts = [f.result() for f in fs]
                    merged = {"leg": leg, "poses": sum(p["poses"] for p in parts),
                              "overlaps": sum((p["overlaps"] for p in parts), []),
                              "overlapCount": sum(p["overlapCount"] for p in parts),
                              "gearMaxOverlapMm3": max(p["gearMaxOverlapMm3"] for p in parts),
                              "gearMaxGapMm": max(p["gearMaxGapMm"] for p in parts),
                              "frameGapMm": min(p["frameGapMm"] for p in parts),
                              "footMinZ": min(p["footMinZ"] for p in parts),
                              "notFootLowest": sum((p["notFootLowest"] for p in parts), []),
                              "sweptBox": [min(p["sweptBox"][i] for p in parts) for i in range(3)] +
                                          [max(p["sweptBox"][i + 3] for p in parts) for i in range(3)]}
                    results.append(merged)
            items = motion_items(results)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"key": key, "items": items}, indent=1))
    if missing:
        items = items + [{"check": "parts", "level": "unverified", "message": f"missing parts: {missing}"}]
    verdict = worst([i["level"] for i in items])
    report = {"schema": 1, "verdict": verdict, "passed": verdict in ("pass", "review"), "stage": "moving",
              "kind": kind, "scope": f"stage moving ({kind}): gears + Jansen legs", "partShas": shas,
              "cached": cached, "seconds": round(time.time() - started, 2), "poses": steps if kind == "motion" else None,
              "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "failures": [i for i in items if i["level"] == "fail"],
              "reviews": [i for i in items if i["level"] in ("review", "unverified")], "checks": items}
    path = ROOT / "case" / "reports" / f"moving-{kind}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1) + "\n")
    import receipt
    receipt.write()
    print(json.dumps({"kind": kind, "verdict": verdict, "fail": len(report["failures"]),
                      "review": len(report["reviews"]), "cached": cached, "seconds": report["seconds"]}))
    for i in report["failures"] + report["reviews"]:
        print(f"  {i['level']:10} {i['check']}: {i['message'][:300]}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
