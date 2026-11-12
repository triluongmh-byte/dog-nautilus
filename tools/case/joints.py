"""Joints stage: printed 4 mm pins (crank O and fixed pivot Q) and the M2 screw + trapped-nut joints.

Pins (see pin_base): crank pin fixed in the frame, head outside the gear; Q pin glued in the rocker,
turning in the frame hole, low head inside the box on the inner wall face. A 0.25 mm flat on the TOP of the shank (the
unloaded side: the leg pushes the pin up into the hubs) is the print face; prints lying flat-down.

M2 link joints (C, D, E, F, G): screw through the stack into a nut trapped in one link; snug the nut,
back off 1/4 turn so the stack has ~0.2 mm play, then lock the nut to the screw with a drop of CA
(the screw turns with the nut link; the other links turn on the shank). Lengths below are checked
in the full-turn sweep (tools/case/joints_check.py) with the real head and tip.
"""
import math

import cadquery as cq

import geom as g
import legs as L

PIN_D = 4.0
PIN_FLAT = 0.25                 # flat depth on the top of the shank (print face)
HEAD_D, HEAD_T = 7.0, 2.0
AXIAL_PLAY = 0.3
PIN_Y0 = g.YI + 0.1             # shank inner end, 0.1 mm proud of the inner wall face (35.6)

# M2 screw per joint: (head side y, length, which face the head sits on, nut link)
T = L.LINK_T
YL = L.Y_L
SCREWS = {
    #      head face y, direction (+1 = shank runs +Y from the head), length, nut link, nut pocket
    "C": dict(head_y=L.Y_GEAR, dir=+1, length=18, nut="upper_link", note="head on the crank gear inner face"),
    "D": dict(head_y=YL[3] + T, dir=-1, length=14, nut="hip_triangle", note="head on upper_link outer face"),
    "E": dict(head_y=YL[0], dir=+1, length=14, nut="shin_link", note="head on hip_triangle inner face"),
    "F": dict(head_y=YL[4] + T, dir=-1, length=14, nut="rocker", note="head on foot outer face"),
    "G": dict(head_y=YL[4] + T, dir=-1, length=8, nut="shin_link", note="head on foot outer face"),
}
SCREW_HOSTS = {"C": {"gear_crank", "lower_link", "upper_link"}, "D": {"hip_triangle", "upper_link"},
               "E": {"hip_triangle", "shin_link"}, "F": {"rocker", "lower_link", "foot"},
               "G": {"shin_link", "foot"}}
M2_HEAD_D, M2_HEAD_T, M2_D = 3.8, 1.3, 2.0
PIN_HOSTS = {"pin_crank": {"gear_crank", "frame"}, "pin_q": {"hip_triangle", "rocker", "frame"}}


def pin_end_y(kind):
    """Outer end of the pin shank."""
    if kind == "pin_crank":
        return L.Y_GEAR + L.G_THICK + AXIAL_PLAY            # 54.3, head beyond
    return L.Y_L[1] + T - 0.1                                # flush with the rocker's outer face (60.7)


Q_HEAD = dict(w=6.0, h=3.0, t=1.9)   # low head inside the box: 6 (X) x 3 (Z) tab, 1.9 thick


def pin_base(kind):
    """Base (RL, +Y) pin at O or Q, assembled.

    pin_crank: fixed. Pushed from OUTSIDE through the crank-gear hub into the frame hole, CA in the
      frame hole; the 7 x 2 head outside the gear retains it with 0.3 mm end play.
    pin_q: turns with the rocker. Pushed from INSIDE the box (before the electronics) through the
      frame hole and the hip hub, CA-glued in the rocker only; the low head bears on the inner wall
      face, so nothing sits on the outer layers where lower_link sweeps over Q.
    """
    y1 = pin_end_y(kind)
    if kind == "pin_crank":
        x, z = L.BASE_O
        body = g.cyl_y(x, z, PIN_Y0, y1 + 0.01, PIN_D).union(g.cyl_y(x, z, y1, y1 + HEAD_T, HEAD_D))
        y_lo, y_hi = PIN_Y0, y1 + HEAD_T
    else:
        x, z = -g.Q_X, g.Q_Z
        yh = g.YI - 0.1
        body = g.cyl_y(x, z, yh - 0.01, y1, PIN_D).union(
            g.box(x - Q_HEAD["w"] / 2, x + Q_HEAD["w"] / 2, yh - Q_HEAD["t"], yh,
                  z - Q_HEAD["h"] / 2, z + PIN_D / 2))   # head top meets the print flat: prints on the bed
        y_lo, y_hi = yh - Q_HEAD["t"], y1
    flat_z = z + PIN_D / 2 - PIN_FLAT
    return body.cut(g.box(x - HEAD_D, x + HEAD_D, y_lo - 1, y_hi + 1, flat_z, z + HEAD_D))


def pin(kind, leg):
    return L.mirror_leg(pin_base(kind), leg)


def screw_solid(j, leg, s1):
    """The real M2 screw (shank + head) at joint j for pose s1, world frame."""
    sp = SCREWS[j]
    pts, _, _ = L.kin(s1)
    x, z = L.world(pts[j], leg)
    h, d, n = sp["head_y"], sp["dir"], sp["length"]
    shank = cq.Solid.makeCylinder(M2_D / 2, n, cq.Vector(x, h, z), cq.Vector(0, d, 0))
    head = cq.Solid.makeCylinder(M2_HEAD_D / 2, M2_HEAD_T, cq.Vector(x, h, z), cq.Vector(0, -d, 0))
    s = shank.fuse(head)
    if L.leg_sign(leg)[1] < 0:
        s = s.mirror("XZ")
    return s


def hardware():
    """Bought hardware per leg and in total (for the docs member and the tester)."""
    per_leg = [{"id": f"M2x{sp['length']}-{j}", "joint": j, "thread": "M2", "lengthMm": sp["length"],
                "head": "pan/cap, Phillips or 1.5 hex (GIẢ ĐỊNH)", "nut": f"M2 hex nut trapped in {sp['nut']}",
                "lock": "drop of CA (502) on the nut after setting 0.2 mm play", "note": sp["note"]}
               for j, sp in SCREWS.items()]
    counts = {}
    for sp in SCREWS.values():
        counts[f"M2x{sp['length']}"] = counts.get(f"M2x{sp['length']}", 0) + 4
    return {"perLeg": per_leg, "totals": {**{k: v for k, v in sorted(counts.items())}, "M2 hex nut": 20},
            "printedPins": {"pin_crank": f"4 mm x {pin_end_y('pin_crank') - PIN_Y0:.1f} shank + 7x2 head outside; "
                                         "push from outside, CA in the frame hole",
                            "pin_q": f"4 mm x {pin_end_y('pin_q') - g.YI + 0.1:.1f} shank + 6x3x1.9 head inside; "
                                     "push from inside before the electronics, CA in the rocker only"}}


# ------------------------------------------------------------------ leg-joint coupon (TEST ONLY)
def coupon_leg_joint():
    """One spare set of real links laid flat: hip_triangle (Q hub + D nut trap), rocker (F nut trap),
    lower_link (C/F), plus one Q pin and one crank pin. Tests the M2 screw + trapped-nut joint at F,
    the hub on the 4 mm pin and the pin print. Parked at x 90.., y 20.. (never assembled)."""
    pieces = [L.base_part("hip_triangle"), L.base_part("rocker"), L.base_part("lower_link")]
    flat = []
    for p in pieces:            # links: outer face down, hubs/inner pockets up
        flat.append(p.rotate((0, 0, 0), (1, 0, 0), -90))
    for kind in ("pin_q", "pin_crank"):   # pins lie on their flat
        flat.append(pin_base(kind).rotate((0, 0, 0), (0, 1, 0), 180))
    out, x = None, 90.0
    for p in flat:
        bb = p.val().BoundingBox()
        moved = p.translate((x - bb.xmin, 20.0 - bb.ymin, -bb.zmin))
        out = moved if out is None else out.union(moved)
        x += bb.xlen + 4.0
    tag = cq.Workplane("XY").workplane(offset=-0.5).center(96.0, 16.0).text(
        "TEST", 3.0, 1.0, combine=False, halign="center", valign="center")
    plate = g.box(90.0, 104.0, 13.0, 19.5, 0, 1.6).cut(tag.translate((0, 0, 1.0)))
    return out.union(plate)
