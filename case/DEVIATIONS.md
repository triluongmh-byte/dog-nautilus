# Case deviations from the contract / cadsmith draft

Each entry: contract or draft text, the change, evidence, and the cross-team impact.

## D1: servo seat lowered 1.1 mm (wall above the servo window)
- Contract: servo drive axis at (x ±13.1, z 21.1); assumption "wall above the servo window is
  only about 1.3 mm (needs >= 2 mm)". Servos may move up to 5 mm in X/Z.
- Change: drive axis at z 20.0 and x ±12.33 (keeps the 18 mm nautilus centre distance to the
  crank at (±27.3, 10)). Servo body centre is x ±18.23 (contract envelope x ±19). Window is 23.4 x 12.8
  (0.3 mm a side), so the wall above it is 2.1 mm (measured: `servo-wall:*` in
  case/reports/mechanical.json).
- Impact: none for board/firmware (servo position is case-owned). Servo envelopes still clear
  every electronic module envelope (`keepout:*` checks).

## D2: lid screws moved to the four inner corners
- Draft/contract assumption: lid posts at (±25, ±32.3); the draft cut them with the servo windows.
- Change: 4 corner bosses (|x| 55.5..61, |y| 30..35.5, full height) with M3 self-tap pilots
  (2.5 mm, 10 deep) at (±58.25, ±32.75). They clear the servos, the carrier, CHG1 and BUCK1.
- Impact: the lid stage must put its 4 screw holes at (±58.25, ±32.75).

## D3: draft's frame-printed horizontal pins replaced by pads with 4.2 mm holes
- Draft: printed 4 mm pins standing out of the side wall on 6 mm standoffs (needed support).
- Change: crank pad (r 3.2) and Q pad (r 4.0) stand on the bed (flat sides, round top around the
  axis, no overhang) and reach y ±37.5..47; a 4.2 mm hole runs through pad and wall for a separate
  4 mm pin (moving/joint stage). Crank pad top z 13.2 clears the servo flange bottom (z 13.9).
- Impact: none outside case. The moving stage supplies the pins and the 47 -> gear-plane spacer.

## D4: devices on glue-on holders instead of frame-printed posts/ribs
- Contract task: carrier posts, CHG1 standoffs, BUCK1 clip, battery cradle ribs on the frame.
- Change (team rule: plain box frame, devices on small 502-glued holders): `carrier_holder`
  (4 M2 posts, board bottom z 5.0 kept), `battery_cradle` (end stops x -30/36, centre saddle,
  cable tie), `charger_holder` (rails to z 6.0, lips, front stop), `buck_holder` (tray).
- Impact: positions and heights match the contract envelopes; no pin/outline change.

## D5: battery cradle length assumes 65 mm unprotected cells
- Cradle stops at x -30..36 (66 mm). Protected cells (up to 69 mm) do not fit; the contract
  already lists this. The front stop stays 0.35 mm clear of the SuperMini envelope.

## D6: nautilus gear radii 6.5/11.5 instead of the draft's 6/12
- Draft: g_rmin 6, g_rmax 12 (outer radius 12.5 with teeth).
- Change: rmin 6.5, rmax 11.5 (same 18 mm centre distance, outer radius 12.0). With D1 the front
  and rear drive axes are 24.66 mm apart on one side and share the gear plane; 2 x 12.5 would
  touch. Now the gap is >= 0.66 mm at any phase, and the crank gear clears the Q hub by 0.8 mm.
  Crank speed now swings about 0.57x..1.77x per turn (draft 0.5x..2x): still a nautilus pair.
- Evidence: case/reports/moving-motion.json (motion:front-rear-*, motion:*:mesh).
- Impact: none for board/firmware (open-loop phase timing is calibrated per servo anyway).

## D7: shin link moved out of the lower-link layer; foot on a 5th layer
- Draft layers: L3 lower_link + shin_link, L4 upper_link + foot.
- Change: L3 lower_link, L4 upper_link + shin_link, L5 foot (y 68.0..71.0). The sweep found
  lower_link and shin_link crossing (7 mm3 at one crank angle). The outermost screw head now sits
  at |y| 72.3, inside the sealed 150 mm width (robot 152.1 x 144.6 x 69.6 with leg sweep).
- Impact: case only; M2 screw lengths grow (D, E, F screws) and are listed in the joints stage.

## D8: Q pin turns with the rocker, inserted from inside the box
- Draft: printed 4 mm pins on the frame (both O and Q), M2 self-tap + washer in the tip.
- Change: crank pin (O) is fixed: pushed from outside through the gear hub, CA in the frame hole,
  7 x 2 head outside the gear (0.3 mm end play). The Q pin cannot have an outer head: the sweep
  showed it hitting lower_link (43 mm3), which passes over Q. So the Q pin goes in from inside the
  box with a 6 x 3 x 1.9 head on the inner wall face, is CA-glued in the rocker only, and turns in the
  11.5 mm frame wall+pad bore; the hip hub turns on it. Insert both Q pins before the electronics.
- Evidence: case/reports/joints.json (joints:*:sweep, pins:*).

## D9: M2 link joints locked with CA on a trapped nut, lengths fixed
- Draft: trapped nuts with no locking method, so the nut would unscrew as its link turns.
- Change: snug the nut, back off 1/4 turn (about 0.2 mm play), then a drop of CA on the nut. Lengths
  per leg are C M2x18, D/E/F M2x14, G M2x8 (4 legs: 4x M2x18, 12x M2x14, 4x M2x8, 20 nuts),
  written to case/hardware.json. Every screw reaches the full 1.6 mm nut, and tips and heads clear
  all links over the full turn.

## D10: lid details vs the draft
- Same as the draft: 2.5 mm flat lid at z 28.5..31, OLED window 36 x 19 at (39,0) with 4 holes on
  40 x 32, fan opening 27 at (-45.5,0) with 4x 3.2 on 23 mm, 8 deck posts d7 on a 15 mm grid around
  (-5,0) up to z 37, 12 mm cable hole at (-5,0). OLED and fan hang from the lid on screws (no
  printed holder), as in the draft.
- Changed: the M3 lid holes (3.4) moved to the frame corner pilots (±58.25, ±32.75) (D2). The
  heat-set pocket is 4.0 x 5.0 for an M3 x 4 insert (draft 5.5 deep), so 1 mm of post stays
  below the pocket. Added a glue-on `pigtail_clip` (draft had none) beside the contract stow box,
  outside it, glue face on the lid underside. Wire routes were lowered to stay under the lid with
  their plug diameter, and the fan route goes around the clip.
- Evidence: case/reports/lid.json (hole probes, keep-outs, height 37 - (-32.5) = 69.5 mm, wires).
- Impact: none for board/firmware.
- Seat contact (not a change): the contract envelopes end exactly at the lid underside, z 28.5:
  oled_154_128x64 25.45 ± 3.05, fan_30x30x10 23.5 ± 5, expansion_pigtail_stow 25.75 ± 2.75. The lid
  touches their tops as the mounting face and never enters them (lid_check keepout: 0.000 mm3).
  tools/case/simple_check.py is scoped to the simple-stage parts only. Every later stage has its
  own check: moving_check, joints_check and lid_check.
