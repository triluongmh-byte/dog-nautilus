# Case — assembly and overview (revision r2, all stages)

Dog-nautilus robot case: **frame, lid, 4 legs (nautilus gear pair + Jansen links each), pins, glue-on holders**,
plus 5 **TEST ONLY** coupons. Nothing has been physically printed or fitted (CAD and slicer checks only).

- **Interactive 3D overview, step by step:** [overview.html](overview.html) (Đủ bộ, then steps 1–8; the drawings are in its details)
- Notes for the person, written by the harness: [NOTES.md](NOTES.md)
- Builder handoff and deviations: [HANDOFF.md](HANDOFF.md), [DEVIATIONS.md](DEVIATIONS.md); hardware list: [hardware.json](hardware.json)
- Printed-part inventory: [PRINTED-INVENTORY.md](PRINTED-INVENTORY.md)
- Step data for the overview: [assembly_steps.json](assembly_steps.json)
- Wiring guide: `firmware/WIRING.md` (firmware team)

## Engineering drawings (from the STEP files; 48 sheets)
[assembly](out/drawings/assembly.svg) · [battery_cradle](out/drawings/battery_cradle.svg) · [buck_holder](out/drawings/buck_holder.svg) · [carrier_holder](out/drawings/carrier_holder.svg) · [charger_holder](out/drawings/charger_holder.svg) · [foot_FL](out/drawings/foot_FL.svg) · [foot_FR](out/drawings/foot_FR.svg) · [foot_RL](out/drawings/foot_RL.svg) · [foot_RR](out/drawings/foot_RR.svg) · [frame](out/drawings/frame.svg) · [gear_crank_FL](out/drawings/gear_crank_FL.svg) · [gear_crank_FR](out/drawings/gear_crank_FR.svg) · [gear_crank_RL](out/drawings/gear_crank_RL.svg) · [gear_crank_RR](out/drawings/gear_crank_RR.svg) · [gear_drive_FL](out/drawings/gear_drive_FL.svg) · [gear_drive_FR](out/drawings/gear_drive_FR.svg) · [gear_drive_RL](out/drawings/gear_drive_RL.svg) · [gear_drive_RR](out/drawings/gear_drive_RR.svg) · [hip_triangle_FL](out/drawings/hip_triangle_FL.svg) · [hip_triangle_FR](out/drawings/hip_triangle_FR.svg) · [hip_triangle_RL](out/drawings/hip_triangle_RL.svg) · [hip_triangle_RR](out/drawings/hip_triangle_RR.svg) · [lid](out/drawings/lid.svg) · [lower_link_FL](out/drawings/lower_link_FL.svg) · [lower_link_FR](out/drawings/lower_link_FR.svg) · [lower_link_RL](out/drawings/lower_link_RL.svg) · [lower_link_RR](out/drawings/lower_link_RR.svg) · [pigtail_clip](out/drawings/pigtail_clip.svg) · [pin_crank_FL](out/drawings/pin_crank_FL.svg) · [pin_crank_FR](out/drawings/pin_crank_FR.svg) · [pin_crank_RL](out/drawings/pin_crank_RL.svg) · [pin_crank_RR](out/drawings/pin_crank_RR.svg) · [pin_q_FL](out/drawings/pin_q_FL.svg) · [pin_q_FR](out/drawings/pin_q_FR.svg) · [pin_q_RL](out/drawings/pin_q_RL.svg) · [pin_q_RR](out/drawings/pin_q_RR.svg) · [rocker_FL](out/drawings/rocker_FL.svg) · [rocker_FR](out/drawings/rocker_FR.svg) · [rocker_RL](out/drawings/rocker_RL.svg) · [rocker_RR](out/drawings/rocker_RR.svg) · [shin_link_FL](out/drawings/shin_link_FL.svg) · [shin_link_FR](out/drawings/shin_link_FR.svg) · [shin_link_RL](out/drawings/shin_link_RL.svg) · [shin_link_RR](out/drawings/shin_link_RR.svg) · [upper_link_FL](out/drawings/upper_link_FL.svg) · [upper_link_FR](out/drawings/upper_link_FR.svg) · [upper_link_RL](out/drawings/upper_link_RL.svg) · [upper_link_RR](out/drawings/upper_link_RR.svg)

## What to print
Native Bambu Studio projects sliced with the Bambu Studio 2.7 CLI. **Assumed (GIẢ ĐỊNH):** Bambu Lab A1, 0.4 mm nozzle,
0.20 mm Standard, Generic PETG (one colour), Textured PEI, 256 x 256 mm bed, no supports. Parts are laid in their
manifest print orientation; each part is turned about Z only, longest side along X.

**Production: [print/production.3mf](print/production.3mf)** (check: [report](print/production-check.json)) — select all
5 plates; every part is on exactly one plate (47 parts).

| Plate (name in the slicer) | Parts | Contents | Est. time |
|---|---|---|---|
| 1 — MỚI-SỬA — CẦN IN — Khung hộp r2 | 1 | frame | ~1 h 55 |
| 2 — MỚI-SỬA — CẦN IN — Nắp hộp r2 | 1 | lid | ~48 min |
| 3 — MỚI-SỬA — CẦN IN — Bánh răng r2 | 8 | gear_drive_FL, gear_drive_RR, gear_drive_FR, gear_drive_RL, gear_crank_FL, gear_crank_FR, gear_crank_RL, gear_crank_RR | ~24 min |
| 4 — MỚI-SỬA — CẦN IN — Khớp chân r2 | 24 | hip_triangle_FL, hip_triangle_FR, hip_triangle_RL, hip_triangle_RR, lower_link_FL, lower_link_FR, lower_link_RL, lower_link_RR, foot_FL, foot_FR, foot_RL, foot_RR, upper_link_FL, upper_link_FR, upper_link_RL, upper_link_RR, rocker_FL, rocker_FR, rocker_RL, rocker_RR, shin_link_FL, shin_link_FR, shin_link_RL, shin_link_RR | ~1 h 04 |
| 5 — MỚI-SỬA — CẦN IN — Chốt và giá nhỏ r2 | 13 | battery_cradle, charger_holder, carrier_holder, buck_holder, pin_crank_FL, pin_crank_FR, pin_crank_RL, pin_crank_RR, pigtail_clip, pin_q_FL, pin_q_FR, pin_q_RL, pin_q_RR | ~35 min |

No print is confirmed in print/events.jsonl, so there is no ĐÃ IN — GIỮ LẠI plate: every plate is new.

**TEST ONLY: [print/test-only.3mf](print/test-only.3mf)** (check: [report](print/test-only-check.json)) — print these first.

| Plate | Parts | Contents | Est. time |
|---|---|---|---|
| 1 — THỬ — TEST ONLY — Mẫu thử r2 | 5 | coupon_gear_pair_TEST_ONLY, coupon_mounts_TEST_ONLY, coupon_lid_TEST_ONLY, coupon_leg_joint_TEST_ONLY, coupon_servo_seat_TEST_ONLY | ~1 h 28 |

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
