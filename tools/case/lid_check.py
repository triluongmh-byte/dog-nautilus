"""Lid-stage check -> case/reports/lid.json (+ case/hardware.json "lid" section, handwired receipt).

    "$KICAD_CASE_PYTHON" tools/case/lid_check.py [--force]

print : lid, pigtail_clip, coupon_lid_TEST_ONLY (validity, bed fit, walls, overhangs after printRotateDeg).
fit   : lid vs frame and every other assembled part: no overlap; lid M3 holes concentric with the
        frame pilots (a 2.8 mm probe through the lid hole meets no lid, and the frame pilot is open);
        zero intersection with every module envelope (OLED, fan and pigtail boxes included; the lid
        underside may touch their tops at z 28.5); the clip outside the pigtail box; opening sizes
        measured (12 mm cable hole, 27 mm fan opening, 36 x 19 OLED window, 3.4 / 3.2 / 2.4 holes);
        deck post tops <= 37 so ground to post top stays inside 70 mm; declared wire routes against
        every assembled printed part including the lid and clip.
All cores; cached in build/case/lid_cache.json by input hashes; report always rewritten.
"""
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "case" / "out"
sys.path.insert(0, str(Path(__file__).resolve().parent))

LEVELS = ["pass", "review", "unverified", "fail"]
PARTS = ["lid", "pigtail_clip", "coupon_lid_TEST_ONLY"]
GROUND_Z = -32.5
HEIGHT_LIMIT = 70.0
OVERLAP_MM3 = 0.5


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worst(levels):
    return max(levels, key=LEVELS.index) if levels else "unverified"


def load(name):
    import cadquery as cq
    return cq.importers.importStep(str(OUT / f"{name}.step")).val()


def item(check, ok, message, review=False):
    return {"check": check, "level": "pass" if ok else ("review" if review else "fail"), "message": message}


def overlap(a_name, b_name):
    a, b = load(a_name), load(b_name)
    A, B = a.BoundingBox(), b.BoundingBox()
    if A.xmin > B.xmax or B.xmin > A.xmax or A.ymin > B.ymax or B.ymin > A.ymax or A.zmin > B.zmax or B.zmin > A.zmax:
        return a_name, b_name, 0.0
    return a_name, b_name, float(a.intersect(b).Volume())


def keepouts(name):
    import simple_check as sc
    shape = load(name)
    out = []
    for mid, e in sc.envelopes().items():
        v = float(shape.intersect(e).Volume())
        out.append((name, mid, v))
    return out


def hole_items():
    """Measured openings and screw-hole alignment, by probing the lid and frame solids."""
    import cadquery as cq
    import geom as g
    import lid as L
    lid, frame = load("lid"), load("frame")
    z0, z1 = L.LID_Z0 - 0.5, L.LID_Z1 + 0.5
    items = []

    def solid_in(shape, x, y, d, za=z0, zb=z1):
        probe = cq.Solid.makeCylinder(d / 2, zb - za, cq.Vector(x, y, za), cq.Vector(0, 0, 1))
        return float(shape.intersect(probe).Volume())

    for x, y in L.screw_points():
        lid_hit = solid_in(lid, x, y, 2.8)
        pilot = solid_in(frame, x, y, 2.0, g.FRAME_H - 9.5, g.FRAME_H)
        items.append(item(f"lid:screw@{x:+.2f},{y:+.2f}", lid_hit < 1e-3 and pilot < 1e-3,
                          f"M3 at ({x}, {y}): lid hole clear for a 2.8 mm probe ({lid_hit:.3f} mm3), frame pilot open "
                          f"9.5 mm deep ({pilot:.3f} mm3)"))
    for label, (x, y), d_ok, d_wall in (("cable hole 12", L.DECK_C, 11.9, 12.4),
                                        ("fan opening 27", L.FAN_C, 26.9, 27.4)):
        clear, wall = solid_in(lid, x, y, d_ok), solid_in(lid, x, y, d_wall)
        items.append(item(f"lid:{label}", clear < 1e-3 and wall > 1e-3,
                          f"{label} mm at ({x}, {y}): {d_ok} mm probe clear ({clear:.3f}), {d_wall} mm probe hits ({wall:.3f})"))
    wx, wy = L.OLED_WIN
    probe = cq.Solid.makeBox(wx - 0.2, wy - 0.2, z1 - z0, cq.Vector(L.OLED_C[0] - wx / 2 + 0.1, L.OLED_C[1] - wy / 2 + 0.1, z0))
    v = float(lid.intersect(probe).Volume())
    items.append(item("lid:oled window", v < 1e-3, f"OLED window {wx} x {wy} at {L.OLED_C}: open ({v:.3f} mm3)"))
    for label, pts, d in (("oled holes", L.oled_holes(), L.OLED_HOLE_D), ("fan holes", L.fan_holes(), L.FAN_HOLE_D)):
        hits = [solid_in(lid, x, y, d - 0.2) for x, y in pts]
        items.append(item(f"lid:{label}", max(hits) < 1e-3, f"{label} {d} mm at {pts}: open ({max(hits):.3f})"))
    posts = L.deck_posts()
    pocket = [solid_in(lid, x, y, L.INSERT_POCKET_D - 0.2, L.DECK_POST_TOP - L.INSERT_POCKET_DEPTH + 0.1,
                       L.DECK_POST_TOP + 0.5) for x, y in posts]
    items.append(item("lid:insert pockets", max(pocket) < 1e-3,
                      f"8 deck posts {posts}: {L.INSERT_POCKET_D} x {L.INSERT_POCKET_DEPTH} heat-set pockets open"))
    top = lid.BoundingBox().zmax
    items.append(item("lid:height", top <= L.DECK_POST_TOP + 1e-6 and top - GROUND_Z <= HEIGHT_LIMIT,
                      f"deck post top z {top:.2f}; ground {GROUND_Z} to post top {top - GROUND_Z:.2f} mm (limit {HEIGHT_LIMIT})"))
    return items


def wire_items(names):
    import cadquery as cq
    from kicadpy import case_measure as cm
    intent = json.loads((ROOT / "case" / "interfaces.json").read_text())
    return cm.check_wires(cq, intent.get("wires") or [], [(n, load(n)) for n in names])


def main(argv):
    force = "--force" in argv
    started = time.time()
    man = json.loads((OUT / "parts.json").read_text())
    entries = {p["name"]: p for p in man["parts"]}
    assembled = [n for n, p in entries.items() if p.get("role") != "coupon"]
    names = [n for n in PARTS if n in entries]
    missing = [n for n in PARTS if n not in entries]
    shas = {f"{n}.{e}": sha(OUT / f"{n}.{e}") for n in assembled + names for e in ("step", "stl")}
    here = Path(__file__).parent
    inputs = {"parts": shas, "script": sha(__file__), "lid": sha(here / "lid.py"), "geom": sha(here / "geom.py"),
              "intent": sha(ROOT / "case" / "interfaces.json"), "contract": sha(ROOT / "PILOT_CONTRACT.json"),
              "rot": {n: entries[n].get("printRotateDeg") for n in names}}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache_file = ROOT / "build" / "case" / "lid_cache.json"
    try:
        cache = json.loads(cache_file.read_text())
    except (OSError, ValueError):
        cache = {}
    if not force and cache.get("key") == key and cache.get("items") is not None:
        items, cached = cache["items"], True
    else:
        cached = False
        import moving_check as M
        intent = json.loads((ROOT / "case" / "interfaces.json").read_text())
        nozzle = float((intent.get("printer") or {}).get("nozzleMm") or 0.4)
        bed = (intent.get("printer") or {}).get("bedMm") or [220, 220, 250]
        items = []
        with cf.ProcessPoolExecutor(max_workers=os.cpu_count() or 1) as ex:
            fp = [ex.submit(M.print_part, n, entries[n].get("printRotateDeg") or [0, 0, 0], nozzle, bed,
                            intent.get("skins") or ()) for n in names]
            fo = [ex.submit(overlap, a, b) for a in ("lid", "pigtail_clip") if a in entries
                  for b in assembled if b != a and not (a == "pigtail_clip" and b == "lid")]
            fk = [ex.submit(keepouts, n) for n in ("lid", "pigtail_clip") if n in entries]
            fh = ex.submit(hole_items)
            fw = ex.submit(wire_items, assembled)
            for f in fp:
                items += f.result()
            for f in fo:
                a, b, v = f.result()
                if v > 0 or b == "frame":
                    items.append(item(f"overlap:{a}+{b}", v <= OVERLAP_MM3, f"{a} and {b} share {v:.2f} mm3"))
            for f in fk:
                for n, mid, v in f.result():
                    if v > 0 or mid in ("oled_154_128x64", "fan_30x30x10", "expansion_pigtail_stow"):
                        items.append(item(f"keepout:{n}+{mid}", v <= 1e-3, f"{n} vs {mid}: overlap {v:.3f} mm3"))
            items += fh.result()
            items += fw.result()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"key": key, "items": items}, indent=1))
    if missing:
        items = items + [{"check": "parts", "level": "unverified", "message": f"missing parts: {missing}"}]
    verdict = worst([i["level"] for i in items])
    report = {"schema": 1, "verdict": verdict, "passed": verdict in ("pass", "review"), "stage": "lid",
              "scope": "stage lid: lid, pigtail clip, lid coupon (print, fit to frame, keep-outs, openings, wires)",
              "partShas": shas, "cached": cached, "seconds": round(time.time() - started, 2),
              "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "failures": [i for i in items if i["level"] == "fail"],
              "reviews": [i for i in items if i["level"] in ("review", "unverified")], "checks": items}
    path = ROOT / "case" / "reports" / "lid.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1) + "\n")
    import lid as L
    hw_path = ROOT / "case" / "hardware.json"
    try:
        hw = json.loads(hw_path.read_text())
    except (OSError, ValueError):
        hw = {}
    hw["lid"] = L.hardware()
    hw_path.write_text(json.dumps(hw, indent=1) + "\n")
    import receipt
    receipt.write()
    print(json.dumps({"verdict": verdict, "fail": len(report["failures"]), "review": len(report["reviews"]),
                      "cached": cached, "seconds": report["seconds"]}))
    for i in report["failures"] + report["reviews"]:
        print(f"  {i['level']:10} {i['check']}: {i['message'][:300]}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
