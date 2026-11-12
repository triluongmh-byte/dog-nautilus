"""Write case/README.md and case/PRINTED-INVENTORY.md from the manifest, the check reports and print/events.jsonl.
Run from the workspace root after slice_and_verify.py."""
import json
from pathlib import Path
ROOT = Path.cwd(); C = ROOT / 'case'
man = json.loads((C / 'out/parts.json').read_text())
prod = json.loads((C / 'print/production-check.json').read_text())
test = json.loads((C / 'print/test-only-check.json').read_text())
sheets = json.loads((C / 'out/drawings/index.json').read_text())['sheets']
events = ROOT / 'print/events.jsonl'
ev = [json.loads(l) for l in events.read_text().splitlines() if l.strip()] if events.exists() else []
fmt = lambda m: f'{m // 60} h {m % 60:02d}' if m >= 60 else f'{m} min'


def plate_rows(rep):
    out = []
    for p in rep['plates']:
        parts = [x[:-4] for x in p['parts']]
        out.append(f"| {p['index']} — {p['name']} | {len(parts)} | {', '.join(parts)} | ~{fmt(p['estimatedMinutes'])} |")
    return '\n'.join(out)


draw = ' · '.join(f"[{s['name']}](out/drawings/{s['svg']})" for s in sheets)
(C / 'README.md').write_text(f'''# Case — assembly and overview (revision r2, all stages)

Dog-nautilus robot case: **frame, lid, 4 legs (nautilus gear pair + Jansen links each), pins, glue-on holders**,
plus 5 **TEST ONLY** coupons. Nothing has been physically printed or fitted (CAD and slicer checks only).

- **Interactive 3D overview, step by step:** [overview.html](overview.html) (Đủ bộ, then steps 1–8; the drawings are in its details)
- Notes for the person, written by the harness: [NOTES.md](NOTES.md)
- Builder handoff and deviations: [HANDOFF.md](HANDOFF.md), [DEVIATIONS.md](DEVIATIONS.md); hardware list: [hardware.json](hardware.json)
- Printed-part inventory: [PRINTED-INVENTORY.md](PRINTED-INVENTORY.md)
- Step data for the overview: [assembly_steps.json](assembly_steps.json)
- Wiring guide: `firmware/WIRING.md` (firmware team)

## Engineering drawings (from the STEP files; {len(sheets)} sheets)
{draw}

## What to print
Native Bambu Studio projects sliced with the Bambu Studio 2.7 CLI. **Assumed (GIẢ ĐỊNH):** Bambu Lab A1, 0.4 mm nozzle,
0.20 mm Standard, Generic PETG (one colour), Textured PEI, 256 x 256 mm bed, no supports. Parts are laid in their
manifest print orientation; each part is turned about Z only, longest side along X.

**Production: [print/production.3mf](print/production.3mf)** (check: [report](print/production-check.json)) — select all
{len(prod['plates'])} plates; every part is on exactly one plate ({len(prod['meshes'])} parts).

| Plate (name in the slicer) | Parts | Contents | Est. time |
|---|---|---|---|
{plate_rows(prod)}

{"No print is confirmed in print/events.jsonl, so there is no ĐÃ IN — GIỮ LẠI plate: every plate is new." if not ev else "Printed status comes from print/events.jsonl; see PRINTED-INVENTORY.md."}

**TEST ONLY: [print/test-only.3mf](print/test-only.3mf)** (check: [report](print/test-only-check.json)) — print these first.

| Plate | Parts | Contents | Est. time |
|---|---|---|---|
{plate_rows(test)}

Coupon procedure (set them aside afterwards; **do not assemble or glue a coupon into the product**):
- `coupon_servo_seat_TEST_ONLY`: push a real SG90/FS90R in from outside; it should seat without force, flange screw pilots aligned.
- `coupon_mounts_TEST_ONLY`: try the real USB-C plug, the 7 mm switch, charger and buck boards on the opening/holder slices.
- `coupon_gear_pair_TEST_ONLY`: two gears on their 3.9 mm posts at 18 mm centres; they should turn by hand without binding.
- `coupon_leg_joint_TEST_ONLY`: rocker/foot ends with a real M2 screw + trapped nut, hip hub on one Q pin and one crank pin; the joint should swing freely with about 0.2 mm play.
- `coupon_lid_TEST_ONLY`: OLED window/holes, fan opening/holes, cable hole, deck posts (heat-set insert), M3 corner hole and a spare pigtail clip.
If a coupon fails, report what did not fit and by how much to the case builder.

Regenerate: `"$KICAD_CASE_PYTHON" tools/case/docs/profiles.py && "$KICAD_CASE_PYTHON" tools/case/docs/make_plates.py && "$KICAD_CASE_PYTHON" tools/case/docs/slice_and_verify.py && "$KICAD_CASE_PYTHON" tools/case/docs/write_docs.py && "$KICAD_CASE_PYTHON" -m kicadpy.case_overview .`

## Assembly (same 8 steps as the overview)
Total hardware (4 legs): 4 x M2x18, 12 x M2x14, 4 x M2x8, 20 M2 hex nuts; lid 4 x M3x10 self-tap, 8 M3x4 heat-set inserts,
OLED 4 x M2x10 (+8 nuts), fan 4 x M3x16 (+4 nuts). Servo screws are the servos' own (size unmeasured).
1. **Frame** — lay it flat (origin: body bottom centre, +X forward, +Y left).
2. **Holders** — glue carrier_holder, battery_cradle, charger_holder, buck_holder with 502 (CA) on the floor.
3. **Servos and drive gears** — fit the 4 servos; drive gear on each horn (factory screw + CA).
4. **Q pins, hip triangles, rockers** — push each Q pin in from inside the box, before the electronics; CA only in the rocker.
5. **Crank pins and gears, joint C** — crank pin from outside, CA only in the frame hole; M2x18 into the nut in upper_link.
6. **Joints D and E** — M2x14 each, nut in hip_triangle / shin_link.
7. **Foot, joints F and G** — M2x14 (F) and M2x8 (G); turn the drive gear once to check the motion.
8. **Lid** — glue pigtail_clip, press in inserts, mount OLED and fan, close with 4 x M3x10.
Every joint: set about 0.2 mm play, then one drop of 502 on the nut.

## Open points
- All bought-part sizes (servos, 18650, charger, buck, switch, OLED, fan, screws) are nominal and unmeasured; the coupons check them.
- Slicer filament weight reads 0 g (generic profile has no density); times are slicer estimates.
- Not physically tested: fit, gear mesh, joint play, strength, glue joints.
''')
rows = []
for p in man['parts']:
    if p['name'].startswith('ref'):
        continue
    kind = 'TEST ONLY' if p.get('role') == 'coupon' else 'production'
    rows.append(f"| {p['name']} | {kind} | 1 | 0 | unknown | none recorded |")
(C / 'PRINTED-INVENTORY.md').write_text(f'''# Printed inventory (actual physical prints)

Source of truth: `print/events.jsonl` (append-only; written only from the person's explicit confirmation).
{"**That file does not exist, so no part is confirmed printed.**" if not ev else f"{len(ev)} event(s) read from it; see below."}
Slicing, exporting or opening a 3MF is not a print, and a printer job marked complete is not a confirmation.
Revision of all parts: **r2** (all stages). Nothing is recorded as printed, fitted, failed or modified.

| Part ID | Kind | Qty needed | Confirmed printed | Fits / works | Failed / modified |
|---|---|---|---|---|---|
{chr(10).join(rows)}

Reconciliation: required production parts ({len(prod['meshes'])}) = compatible printed (0) + new to print ({len(prod['meshes'])}).
No ĐÃ IN — GIỮ LẠI plate exists. Coupons ({len(test['meshes'])}) are TEST ONLY and not counted in the product.
Mesh hashes: `case/print/production-check.json`, `case/print/test-only-check.json`.
Update this file and the plate groups when `print/events.jsonl` gains entries.
''')
print('ok', len(ev))
