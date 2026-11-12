"""Nautilus Dog case: per-part cached build into case/out/ (assembled, contract frame).

Stage 'simple': frame + glue-on holders + TEST ONLY coupons.
    "$KICAD_CASE_PYTHON" case/build.py            # changed parts only
    "$KICAD_CASE_PYTHON" case/build.py --plan
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools" / "case"))

from kicadpy.case_build import CaseBuild  # noqa: E402

import geom  # noqa: E402
import legs  # noqa: E402
import joints  # noqa: E402
import lid  # noqa: E402

build = CaseBuild(
    __file__, stl_tolerance=0.02, angular_tolerance=0.1,
    manifest={"stage": "lid",
              "verification": {"nativePCBCheckerApplies": False, "report": "../reports/verification.json"}})

GLUE = "glue-on with 502 (CA) on its flat bottom face to the frame floor"
PARTS = {
    "frame": {"fn": geom.frame, "role": "shell",
              "note": "plain open box; prints floor-down, no supports (pads stand on the bed, round tops)"},
    "carrier_holder": {"fn": geom.carrier_holder, "role": "bracket",
                       "note": "carrier PCB holder, 4x M2 self-tap posts; " + GLUE},
    "battery_cradle": {"fn": geom.battery_cradle, "role": "bracket",
                       "note": "2x 18650 cradle + one cable tie through the centre rib; " + GLUE},
    "charger_holder": {"fn": geom.charger_holder, "role": "bracket",
                       "note": "CHG1 rails + lips, USB-C at the back-wall opening; foam tape on rails; " + GLUE},
    "buck_holder": {"fn": geom.buck_holder, "role": "bracket",
                    "note": "BUCK1 tray, foam tape; " + GLUE},
    "coupon_servo_seat_TEST_ONLY": {"fn": geom.coupon_servo_seat, "role": "coupon",
                                    "note": "TEST ONLY: servo window, flange screws, crank + Q pin holes"},
    "coupon_mounts_TEST_ONLY": {"fn": geom.coupon_mounts, "role": "coupon",
                                "note": "TEST ONLY: wall openings, lid boss, slices of every glue-on holder"},
}


def _leg_part(name, leg):
    def make():
        return legs.part(name, leg)
    make.__name__ = f"{name}_{leg}"
    return make


LEG_NOTES = {
    "gear_drive": "nautilus drive gear on the servo horn (horn screws + CA)",
    "gear_crank": "nautilus crank gear with spacer hub, turns on the 4 mm crank pin; crank screw at C",
    "hip_triangle": "Jansen hip triangle Q-D-E with spacer hub on the 4 mm Q pin",
    "rocker": "Jansen rocker Q-F", "lower_link": "Jansen lower link C-F", "shin_link": "Jansen shin E-G",
    "upper_link": "Jansen upper link C-D", "foot": "Jansen foot F-G-H with the pad",
}
for _leg in ("FL", "FR", "RL", "RR"):
    _rot = [-90, 0, 0] if legs.leg_sign(_leg)[1] > 0 else [90, 0, 0]
    for _name in legs.GEARS + legs.LINKS:
        PARTS[f"{_name}_{_leg}"] = {"fn": _leg_part(_name, _leg), "role": "other", "printRotateDeg": _rot,
                                    "note": LEG_NOTES[_name] + "; prints flat, outer face down, no supports"}
PARTS["coupon_gear_pair_TEST_ONLY"] = {
    "fn": legs.coupon_gear_pair, "role": "coupon",
    "note": "TEST ONLY: one nautilus gear pair on two 3.9 mm posts at the 18 mm centre distance"}


def _pin_part(kind, leg):
    def make():
        return joints.pin(kind, leg)
    make.__name__ = f"{kind}_{leg}"
    return make


for _leg in ("FL", "FR", "RL", "RR"):
    for _kind, _how in (
            ("pin_crank", "4 mm printed crank pin: push in from outside through the crank gear hub, "
                          "CA (502) in the frame hole only; gear turns on it"),
            ("pin_q", "4 mm printed Q pin (D8): push in from inside the box before the electronics, through the "
                      "frame Q bore and the hip_triangle hub into the rocker; CA in the rocker only; the pin turns "
                      "in the frame bore, the hip hub turns on the pin")):
        PARTS[f"{_kind}_{_leg}"] = {
            "fn": _pin_part(_kind, _leg), "role": "other", "printRotateDeg": [0, 180, 0],
            "note": _how + "; prints lying on its flat, no supports"}
PARTS["coupon_leg_joint_TEST_ONLY"] = {
    "fn": joints.coupon_leg_joint, "role": "coupon",
    "note": "TEST ONLY: rocker+foot ends at F (M2 screw + trapped nut), hip hub at Q, one Q pin and one crank pin"}
PARTS["lid"] = {"fn": lid.lid, "role": "lid",
                "note": "2.5 mm lid, 4x M3 self-tap into the frame corners; OLED and fan screw to it; "
                        "prints underside down, deck posts up, no supports"}
PARTS["pigtail_clip"] = {"fn": lid.pigtail_clip, "role": "bracket", "printRotateDeg": [180, 0, 0],
                         "note": "expansion pigtail cable clip, glued (502) to the lid underside beside the stow box; "
                                 "prints glue face down"}
PARTS["coupon_lid_TEST_ONLY"] = {
    "fn": lid.coupon_lid, "role": "coupon",
    "note": "TEST ONLY: OLED window+holes, fan opening+holes, cable hole + deck posts, M3 corner hole, spare clip"}
build.add_parts(PARTS)

if __name__ == "__main__":
    build.main()
