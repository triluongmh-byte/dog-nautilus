# HANDOFF — board team (carrier "nautilus-dog-carrier", dummy ERC/DRC board, never ordered)

State: native ERC/DRC/parity 0 findings; netlist parity 70 pins = 70 pads, 0 hollow; gate: fab.ready=True (prototypeReady), 1 warning `power_entry_narrow` (3 short +5V segments 0.3-0.4 mm; see power.md). Nothing powered/ordered.
Frame: KiCad (x, y) = contract (x, -y), offset 0. Outline x 38..60, y -26..26, mounts MH1-4 as sealed. Pin orders/nets sealed, unchanged.

## Files I own
- `design/main.kicad_sch|pcb|pro`, `design/nautilus.kicad_sym`, `design/nautilus.pretty/` (stock footprints + custom `ESP32C3_SuperMini_2x8_P2.54`), `fp/sym-lib-table`: THE SOURCE. Do not hand-edit the schematic; regenerate.
- `product.json` (railLimitsUF +5V 1200), `parts.json` (manual-assembly identities, assumptions), `manufacturing.json` (generated; hashes must be refreshed after ANY source edit).
- `boards/` + `.harness/`: derived by the publisher, never edit.
- `engineering/`: power.md protection.md pinout.md thermal.md assembly.md fabricator.md bringup.md sources.md harness.md (off-board harness table + coordinate offset), DEVIATIONS.md.
- `tools/board/`:
  - `gen_spec.py` (host): net table -> build/board/spec.json + local footprints. Net table: `U1MAP` ln ~28, connectors `conns` ~38, passives after; U1 footprint fn `u1_fp`.
  - `build_pcb.py` (KiCad python): outline, placement dict `P` (search "P = {"), nets, footprint paths = schematic uuids, silk 0.15, stackup text injection.
  - `set_rules.py`: netclasses Default/Power/Power_mid + design rules into design/main.kicad_pro.
  - `fix_labels.py` (KiCad python, in place): MH label positions + C1 value without re-routing. build_pcb.py already has the same MH order.
  - `route.py` (dsn|ses via pcbnew), `freeroute.py` (Freerouting retry until 0 unrouted), `widen.py` (parallel per-track widening of power nets, DRC-gated), `drc_summary.py`.
  - `build_all.sh`: full rebuild spec -> sch -> pcb -> route -> widen -> installs design/main.kicad_pcb. ~3-6 min (router is non-deterministic; may fail to give 0 unrouted with wider classes). REBUILD OVERWRITES design/main.kicad_pcb, so rerun the publish steps after.
  - `publish.sh`: SANDBOX WORKAROUND — kicadpy writes its store to the parent of the project root (outside the worktree), so publish runs from a copy in build/board/pub and rsyncs boards/ + .harness/ back; prints the gate.
  - `make_manufacturing.py`: rewrites manufacturing.json (hashes, ignored-check list, 7 areas). Order after any edit: `publish.sh` -> `make_manufacturing.py` -> `publish.sh`.

## Fastest checks
- Parity: `$KICAD_HARNESS_PYTHON -m kicadpy.verify netlist design/main.kicad_pro`
- DRC all severities (5 s): `$KICAD_HARNESS_PYTHON tools/board/drc_summary.py design/main.kicad_pcb`
- Full: `tools/board/publish.sh` (gate output last).
- Placement tweak only: edit `P` in build_pcb.py then build_all.sh (no schematic change needed; keep gen_spec.py's uuids via keep_uuids_from).

## Key geometry (KiCad mm)
U1 centre (49.25, 0), pad rows y -7.62 (pads 1-8, USB end = +X) and +7.62 (pads 9-16). Servo headers J3/J4/J5/J6 at y -11.5/-15.3 (pin 1 at x 52.9 or 41.4), J7 at -19.1; J9 11.5, J1/J2/J8 15.3, C1 (origin = pad 1) at (46.25, 21.7), D1 (56.2, 19.2). Passives between the pin rows (courtyard of U1 is a C-shape, interior y ±5.9).

## Open assumptions
- GIA DINH: SuperMini row spacing 15.24 mm, pin order per module card, module overhangs the board 0.75 mm at +X (DEVIATIONS.md #1).
- GIA DINH: C1 1000 uF 10 V 8 x 11.5 mm (Rubycon 10PX1000MEFC8X11.5, LCSC listing only); CHG1 not chosen (needs >= 5 A discharge); BUCK1 = Pololu S13V30F5.
- Plug height <= 14 mm unverified (DEVIATIONS.md #3); U1 on MALE headers (#4).
- Servo power is wired to a splice at the buck (power.md, harness.md); board trunk carries <= 1.0 A.
- No part identities were live-checked (no web); no LCSC codes; all assembly manual.
