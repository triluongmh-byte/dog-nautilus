"""Joints-stage check: pins + real-length M2 screws through a full turn of every leg.

    "$KICAD_CASE_PYTHON" tools/case/joints_check.py [--force] [--steps N]  -> case/reports/joints.json

print : the 8 printed pins and coupon_leg_joint_TEST_ONLY (validity, bed, walls, overhangs after
        printRotateDeg; same rules as the moving stage).
sweep : per leg, 72 poses: moving parts (posed), pins, M2 screws with their real head and tip; any
        overlap between a screw/pin and a part it does not pass through fails; each screw must reach
        through its trapped nut (>= 1.2 mm of thread in the nut); pin fit radial gap in its hubs;
        robot envelope with screw heads and pin heads.
Parallel over all cores; cached in build/case/joints_cache.json; report always rewritten, then the
handwired receipt.
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
OVERLAP_MM3 = 0.05
MIN_NUT_THREAD = 1.2
ENVELOPE_Y = 150.0


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worst(levels):
    return max(levels, key=LEVELS.index) if levels else "unverified"


def stage_parts():
    return [f"{k}_{leg}" for leg in LEGS for k in ("pin_crank", "pin_q")] + ["coupon_leg_joint_TEST_ONLY"]


def load(name):
    import cadquery as cq
    return cq.importers.importStep(str(OUT / f"{name}.step")).val()


def sweep_leg(leg, poses):
    import joints as J
    import legs as L
    rest = {n: load(f"{n}_{leg}") for n in L.GEARS + L.LINKS}
    pins = {k: load(f"{k}_{leg}") for k in ("pin_crank", "pin_q")}
    frame = load("frame")
    hits, ymax = [], 0.0
    for s1 in poses:
        moving = [(n, L.posed(rest[n], n, leg, s1)) for n in rest]
        movers = moving + [("frame", frame)]
        screws = [(j, J.screw_solid(j, leg, s1)) for j in J.SCREWS]
        for j, s in screws:
            sb = s.BoundingBox()
            ymax = max(ymax, abs(sb.ymin), abs(sb.ymax))
            for n, sh in movers:
                if n in J.SCREW_HOSTS[j]:
                    continue
                b = sh.BoundingBox()
                if sb.xmin > b.xmax or b.xmin > sb.xmax or sb.ymin > b.ymax or b.ymin > sb.ymax or sb.zmin > b.zmax or b.zmin > sb.zmax:
                    continue
                v = s.intersect(sh).Volume()
                if v > OVERLAP_MM3:
                    hits.append((f"screw_{j}", n, round(s1, 2), round(v, 3)))
            for k, p in pins.items():
                v = s.intersect(p).Volume()
                if v > OVERLAP_MM3:
                    hits.append((f"screw_{j}", k, round(s1, 2), round(v, 3)))
        for k, p in pins.items():
            pb = p.BoundingBox()
            ymax = max(ymax, abs(pb.ymin), abs(pb.ymax))
            for n, sh in moving:
                if n in J.PIN_HOSTS[k]:
                    continue
                b = sh.BoundingBox()
                if pb.xmin > b.xmax or b.xmin > pb.xmax or pb.ymin > b.ymax or b.ymin > pb.ymax or pb.zmin > b.zmax or b.zmin > pb.zmax:
                    continue
                v = p.intersect(sh).Volume()
                if v > OVERLAP_MM3:
                    hits.append((k, n, round(s1, 2), round(v, 3)))
            for n in J.PIN_HOSTS[k] - {"frame"}:     # pins run free in their hubs
                v = p.intersect(dict(moving)[n]).Volume()
                if v > OVERLAP_MM3:
                    hits.append((k, f"{n} (bearing)", round(s1, 2), round(v, 3)))
        v = pins["pin_crank"].intersect(frame).Volume() + pins["pin_q"].intersect(frame).Volume()
        if v > OVERLAP_MM3:
            hits.append(("pins", "frame", round(s1, 2), round(v, 3)))
    return {"leg": leg, "poses": len(poses), "hits": hits[:20], "hitCount": len(hits), "yMax": round(ymax, 2)}


def nut_items():
    """Thread length in each trapped nut, from the stack (static, all legs identical)."""
    import joints as J
    import legs as L
    items = []
    t, nut_h = L.LINK_T, L.NUT_H
    pockets = {  # nut seat (y0, y1) per joint: pocket face side of the nut link
        "C": (L.Y_L[3] + t - nut_h, L.Y_L[3] + t), "D": (L.Y_L[0], L.Y_L[0] + nut_h),
        "E": (L.Y_L[3] + t - nut_h, L.Y_L[3] + t), "F": (L.Y_L[1], L.Y_L[1] + nut_h),
        "G": (L.Y_L[3], L.Y_L[3] + nut_h)}
    for j, sp in J.SCREWS.items():
        tip = sp["head_y"] + sp["dir"] * sp["length"]
        a, b = pockets[j]
        thread = min(b, max(a, tip)) - a if sp["dir"] > 0 else b - max(a, min(b, tip))
        lvl = "pass" if thread >= MIN_NUT_THREAD - 1e-6 else "fail"
        items.append({"check": f"nut:{j}", "level": lvl,
                      "message": f"joint {j}: M2x{sp['length']} reaches {thread:.2f} mm into its {nut_h} mm nut "
                                 f"(min {MIN_NUT_THREAD}); tip at |y| {tip:.1f}"})
    return items


def static_pins():
    """Pins vs the glued holders (frozen simple stage) and the module keep-outs near the pin heads."""
    import simple_check as sc
    holders = ["carrier_holder", "battery_cradle", "charger_holder", "buck_holder"]
    env = sc.envelopes()
    items = []
    for leg in LEGS:
        for k in ("pin_crank", "pin_q"):
            p = load(f"{k}_{leg}")
            worst_gap, who = 1e9, None
            for n, sh in [(h, load(h)) for h in holders] + list(env.items()):
                d = 0.0 if p.intersect(sh).Volume() > 1e-6 else p.distance(sh)
                if d < worst_gap:
                    worst_gap, who = d, n
            items.append({"check": f"pins:{k}_{leg}", "level": "pass" if worst_gap >= 0.2 else "fail",
                          "message": f"{k}_{leg}: nearest holder/module {who} at {worst_gap:.2f} mm (min 0.2)"})
    return items


def main(argv):
    force = "--force" in argv
    steps = int(argv[argv.index("--steps") + 1]) if "--steps" in argv else 72
    started = time.time()
    man = json.loads((OUT / "parts.json").read_text())
    entries = {p["name"]: p for p in man["parts"]}
    import legs as L
    sweep_names = [f"{n}_{leg}" for leg in LEGS for n in L.GEARS + L.LINKS] + ["frame"]
    names = [n for n in stage_parts() if n in entries]
    missing = [n for n in stage_parts() if n not in entries]
    shas = {f"{n}.{e}": sha(OUT / f"{n}.{e}") for n in names + sweep_names for e in ("step", "stl")}
    here = Path(__file__).parent
    inputs = {"parts": shas, "steps": steps, "script": sha(__file__), "joints": sha(here / "joints.py"),
              "legs": sha(here / "legs.py"), "intent": sha(ROOT / "case" / "interfaces.json"),
              "rot": {n: entries[n].get("printRotateDeg") for n in names}}
    key = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()
    cache_file = ROOT / "build" / "case" / "joints_cache.json"
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
        workers = os.cpu_count() or 1
        poses = [2 * math.pi * i / steps for i in range(steps)]
        chunks = max(1, (workers - 1) // len(LEGS))
        items = []
        with cf.ProcessPoolExecutor(max_workers=workers) as ex:
            fp = [ex.submit(M.print_part, n, entries[n].get("printRotateDeg") or [0, 0, 0], nozzle, bed,
                            intent.get("skins") or ()) for n in names]
            fs = {leg: [ex.submit(sweep_leg, leg, poses[c::chunks]) for c in range(chunks)] for leg in LEGS}
            for f in fp:
                items += f.result()
            ymax = 0.0
            for leg, futs in fs.items():
                res = [f.result() for f in futs]
                hits = sum((r["hits"] for r in res), [])
                count = sum(r["hitCount"] for r in res)
                ymax = max([ymax] + [r["yMax"] for r in res])
                items.append({"check": f"joints:{leg}:sweep", "level": "fail" if count else "pass",
                              "message": f"leg {leg}: pins + M2 screws (real heads/tips) clear every part they do not "
                                         f"pass through over {sum(r['poses'] for r in res)} poses: {count} hits {hits[:4]}"})
        items += nut_items()
        items += static_pins()
        width = 2 * ymax
        items.append({"check": "joints:envelope-width", "level": "pass" if width <= ENVELOPE_Y else "fail",
                      "message": f"width with screw and pin heads {width:.1f} mm (sealed {ENVELOPE_Y})"})
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({"key": key, "items": items}, indent=1))
    if missing:
        items = items + [{"check": "parts", "level": "unverified", "message": f"missing parts: {missing}"}]
    verdict = worst([i["level"] for i in items])
    report = {"schema": 1, "verdict": verdict, "passed": verdict in ("pass", "review"), "stage": "joints",
              "scope": "stage joints: 4 mm pins, M2 screw + trapped-nut joints, leg-joint coupon",
              "partShas": shas, "cached": cached, "poses": steps, "seconds": round(time.time() - started, 2),
              "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "failures": [i for i in items if i["level"] == "fail"],
              "reviews": [i for i in items if i["level"] in ("review", "unverified")], "checks": items}
    path = ROOT / "case" / "reports" / "joints.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=1) + "\n")
    import joints as J
    hw_path = ROOT / "case" / "hardware.json"
    try:
        hw = json.loads(hw_path.read_text())
    except (OSError, ValueError):
        hw = {}
    hw.update(J.hardware())          # keep other stages' sections (lid)
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
