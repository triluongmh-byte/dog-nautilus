# Case HANDOFF (builder, read first)

All stages built: **simple** (closed), **moving** (4 gear pairs + 4 Jansen legs + gear coupon),
**joints** (8 pins, M2 joints, leg-joint coupon), **lid** (lid, glue-on pigtail_clip, lid coupon).
Hardware for every stage: case/hardware.json (joints + "lid" section).
Contract frame (origin body bottom centre, +X fwd, +Y left, +Z up); handwired -> tile `check-print`.

## Files
- `tools/case/geom.py`: all dimensions and solids.
  - constants: body/servo/pads/lid boss/openings/holders, lines 11-72
  - `frame()` 140-172: plain box + servo windows/pads (`servo_window` 101, `servo_pads` 108,
    `central_pad` 117, `servo_screw_holes` 123), leg pads (`leg_pads` 129, `leg_pin_holes` 135),
    lid corner bosses, back USB 24x18, switch 7 mm, front USB-C 14x9
  - glue-on holders: `carrier_holder` 176, `battery_cradle` 189, `charger_holder` 202, `buck_holder` 217
  - coupons: `coupon_servo_seat`, `coupon_mounts` (openings, lid boss, holder slices), `label` 237
- `case/build.py`: CaseBuild registration; STL tol 0.02; `verification.report = ../reports/verification.json`.
- `tools/case/simple_check.py` (simple-stage parts only) -> case/reports/mechanical.json: `overhang_regions` 56, `envelopes` 128,
  `pair_overlap` 157, `wall_above_servos` 181, `glue_face` 198, `wires` 209. All cores, cached.
- `tools/case/legs.py`: moving stage. Gear consts 19-30, layers `Y_L` 42 (gear 50..54, L1..L5 from 54.4,
  3 mm + 0.4 gap); `kin(s1)` 63 = gear + Jansen kinematics (base = RL, s1 = drive contact angle);
  `gear_drive_base` 130, `gear_crank_base` 142 (hub to the pad), `link_base` 153 / `link_base_by_name`
  179 (layer per link, nut traps), `part(name, leg)` 216 mirrors per leg, `pose_transform`/`posed`
  221-238 for sweeps, `coupon_gear_pair` 242.
- `tools/case/moving_check.py print|motion`: moving-stage checks -> case/reports/moving-{print,motion}.json.
  `print_part` 77 (printRotateDeg applied), `screws` 102 (M2 shanks/heads), `sweep_leg` 132 (72 poses,
  all pairs, frame gap, foot lowest, gear mesh gap), `motion_items` 189 (envelope, ground, front/rear).
- `tools/case/joints.py`: `SCREWS` (C/D/E/F/G head face, direction, length, nut link), `pin_base`
  (crank pin fixed + outer head; Q pin glued in rocker, inner head, D8), `screw_solid`, `hardware()`
  -> case/hardware.json, `coupon_leg_joint` (whole hip/rocker/lower links + both pins, TEST tag).
- `tools/case/joints_check.py` -> case/reports/joints.json: `sweep_leg` (pins + real screws vs every
  non-host part, 72 poses), `nut_items` (thread in nut >= 1.2), `static_pins` (vs holders/modules),
  width envelope; writes case/hardware.json. `--steps 12` ~7 s.
- `tools/case/lid.py`: lid consts 12-33; `lid()` plate, posts, OLED/fan/cable/M3 holes, insert
  pockets; `pigtail_clip()` (snap slot); `hardware()` (lid section); `coupon_lid()` (slices + clip).
- `tools/case/lid_check.py` -> case/reports/lid.json: print, overlaps, keep-outs, `hole_items`
  (probes: M3 vs frame pilots, 12/27 mm, window, pockets, height <= 70), wires; ~20 s; merges hardware.
- `tools/case/receipt.py`: every check calls it -> case/reports/verification.json (handwired receipt).
- `case/interfaces.json`: 16 joints (drive/crank 0..360, hip -1..57, rocker -53..34 per leg; floating
  links are covered by the motion check), 9 wires x 2 routes, 30 fits -> coupons, 5 TEST tag skins.
- `case/checks.json`: stages simple/moving/joints/lid + 5 checks. `case/DEVIATIONS.md`: D1-D10.

## Fastest checks
- `"$KICAD_CASE_PYTHON" case/build.py` (changed parts only, ~10 s for all)
- `"$KICAD_CASE_PYTHON" tools/case/lid_check.py` (~20 s); `... moving_check.py print` (~8 s); `... motion --steps 12` (~15 s coarse)
- `"$KICAD_CASE_PYTHON" -m kicadpy.case check-print .` (~60 s)
- Plates: tools/case/docs/* belong to case-docs; make_plates.py PRODUCTION must gain legs, pins, lid, clip (slice_and_verify .stl names: lead fix).

## Key geometry (for the next stages)
- Crank axle O (±27.3, ±y, 10); fixed pivot Q (±43.26, 6.72); 4.2 mm holes through wall + pad;
  pads end at |y| 47. Drive axis A (±12.33, 20.0) (D1). Gear plane starts near |y| 49.9.
- Servo window 23.4 x 12.8 centred x ±18.23, z 20; flange screw pilots 1.8 at x ±18.23±13.9, z 20.
- Lid screws: M3 self-tap pilots at (±58.25, ±32.75), frame top z 28.5 (D2).

## Open assumptions (GIẢ ĐỊNH)
- SG90/FS90R nominal: body 22.8 x 12.2, flange 32.2 x 2.5, screw pitch 27.8, 4.3 above flange.
- CHG1 21 x 24 PCB bottom at z 6; BUCK1 22 x 17 at z 3; both held with foam tape in their trays.
- 18650 cells 65 mm long, 18.5 mm dia; one cable tie through the centre rib holds them.
- Servo horn top at y 50 (gear inner face); horn radius <= 12 so it clears the crank hub (O at 18 mm).
- Horn screw pilots at r 4.6 / 7.0 on the drive gear: unmeasured horn; gear coupon checks them.
