"""Lid stage: flat 2.5 mm lid (z 28.5..31) with the contract's openings and deck posts, a glue-on
pigtail stow clip, and a TEST ONLY lid coupon. Contract frame (mm).

DISP1 (OLED) and FAN1 hang from the lid on screws through its own holes (no printed holder):
OLED on 4x M2 at the 40 x 32 holes, fan on 4x M3 at the 23 mm square. Nothing printed goes below
z 28.5 inside the OLED, fan or pigtail envelopes.
"""
import cadquery as cq

import geom as g

LID_T = 2.5
LID_Z0, LID_Z1 = g.FRAME_H, g.FRAME_H + LID_T          # 28.5 .. 31.0
M3_CLEAR = 3.4

OLED_C = (39.0, 0.0)
OLED_WIN = (36.0, 19.0)
OLED_HOLES = (40.0, 32.0)
OLED_HOLE_D = 2.4                    # M2 clearance (GIẢ ĐỊNH: module holes ~2.5-3 mm)

FAN_C = (-45.5, 0.0)
FAN_OPEN_D = 27.0
FAN_PITCH = 23.0
FAN_HOLE_D = 3.2

DECK_C = (-5.0, 0.0)
DECK_PITCH = 15.0
DECK_POST_D = 7.0
DECK_POST_TOP = 37.0
INSERT_POCKET_D, INSERT_POCKET_DEPTH = 4.0, 5.0    # M3 x 4 mm heat-set insert, OD ~4.6
CABLE_HOLE_D = 12.0

PIGTAIL_BOX = dict(x0=-15.0, x1=5.0, y0=-8.0, y1=8.0, z0=23.0, z1=28.5)   # contract envelope
CLIP = dict(x0=5.3, x1=11.3, y0=-5.0, y1=5.0, z0=23.5, slot_w=4.5, slot_top=26.5, lip=0.5, lip_h=0.8)


def deck_posts():
    cx, cy = DECK_C
    return [(cx + i * DECK_PITCH, cy + j * DECK_PITCH) for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)]


def oled_holes():
    hx, hy = OLED_HOLES[0] / 2, OLED_HOLES[1] / 2
    return [(OLED_C[0] + sx * hx, OLED_C[1] + sy * hy) for sx in (1, -1) for sy in (1, -1)]


def fan_holes():
    h = FAN_PITCH / 2
    return [(FAN_C[0] + sx * h, FAN_C[1] + sy * h) for sx in (1, -1) for sy in (1, -1)]


def screw_points():
    x, y = g.LID_SCREW
    return [(sx * x, sy * y) for sx in (1, -1) for sy in (1, -1)]


def lid():
    plate = g.box(-g.XO, g.XO, -g.YO, g.YO, LID_Z0, LID_Z1).edges("|Z").fillet(g.CORNER_R)
    for x, y in deck_posts():
        plate = plate.union(g.cyl_z(x, y, LID_Z1 - 0.5, DECK_POST_TOP, DECK_POST_D))
    cuts = [g.box(OLED_C[0] - OLED_WIN[0] / 2, OLED_C[0] + OLED_WIN[0] / 2,
                  OLED_C[1] - OLED_WIN[1] / 2, OLED_C[1] + OLED_WIN[1] / 2, LID_Z0 - 1, LID_Z1 + 1),
            g.cyl_z(FAN_C[0], FAN_C[1], LID_Z0 - 1, LID_Z1 + 1, FAN_OPEN_D),
            g.cyl_z(DECK_C[0], DECK_C[1], LID_Z0 - 1, LID_Z1 + 1, CABLE_HOLE_D)]
    cuts += [g.cyl_z(x, y, LID_Z0 - 1, LID_Z1 + 1, M3_CLEAR) for x, y in screw_points()]
    cuts += [g.cyl_z(x, y, LID_Z0 - 1, LID_Z1 + 1, OLED_HOLE_D) for x, y in oled_holes()]
    cuts += [g.cyl_z(x, y, LID_Z0 - 1, LID_Z1 + 1, FAN_HOLE_D) for x, y in fan_holes()]
    cuts += [g.cyl_z(x, y, DECK_POST_TOP - INSERT_POCKET_DEPTH, DECK_POST_TOP + 1, INSERT_POCKET_D)
             for x, y in deck_posts()]
    for c in cuts:
        plate = plate.cut(c)
    return plate


def pigtail_clip():
    """Glue-on cable clip under the lid, just +X of the stow box: glue face up on the lid underside.

    The 6-wire bundle is pressed up into a 4.5 mm slot (0.5 mm snap lips); the 1x6 housing then hangs
    in the stow box under the 12 mm hole and is pulled out through it.
    """
    c = CLIP
    body = g.box(c["x0"], c["x1"], c["y0"], c["y1"], c["z0"], LID_Z0)
    w = c["slot_w"] / 2
    body = body.cut(g.box(c["x0"] - 1, c["x1"] + 1, -w, w, c["z0"] - 1, c["slot_top"]))
    for s in (1, -1):   # snap lips at the slot mouth
        y0, y1 = sorted((s * w, s * (w - c["lip"])))
        body = body.union(g.box(c["x0"], c["x1"], y0, y1, c["z0"], c["z0"] + c["lip_h"]))
    return body


def hardware():
    return {
        "lidScrews": {"qty": 4, "item": "M3 x 10 self-tapping (pan head)", "where": "lid holes 3.4 at (±58.25, ±32.75) into the "
                      "frame corner pilots 2.5 x 10 deep (7.5 mm of thread)"},
        "deckInserts": {"qty": 8, "item": "M3 x 4 mm heat-set insert, OD about 4.6", "where": "deck post pockets 4.0 x 5.0 deep"},
        "oled": {"qty": 4, "item": "M2 x 10 screw + 2 M2 nuts each (one nut under the lid as a spacer)",
                 "where": "OLED 40 x 32 holes; glass faces the 36 x 19 window (GIẢ ĐỊNH module layout)"},
        "fan": {"qty": 4, "item": "M3 x 16 screw + M3 nut", "where": "fan 23 mm square, fan hangs under the 27 mm opening, exhausting up"},
        "pigtailClip": "printed pigtail_clip glued (502) to the lid underside; the 6-wire bundle snaps into its slot",
    }


# ------------------------------------------------------------------ TEST ONLY coupon
def coupon_lid():
    """Slices of the real lid, laid flat (lid underside on the bed): OLED window + its 4 holes, fan
    opening + 4 holes, deck cable hole + 3 posts with insert pockets, one M3 corner hole; plus a spare
    pigtail clip. Parked at y 130.. (never assembled)."""
    L = lid()
    pieces = [
        L.intersect(g.box(16.0, 62.0, -19.5, 19.5, 20, 40)),          # OLED window + holes
        L.intersect(g.box(-61.0, -29.5, -16.5, 16.5, 20, 40)),        # fan opening + holes
        L.intersect(g.box(-25.0, 2.0, -8.0, 21.0, 20, 40)),           # cable hole + posts
        L.intersect(g.box(52.0, 63.0, 27.0, 37.5, 20, 40)),           # M3 corner hole
        pigtail_clip().rotate((0, 0, 0), (1, 0, 0), 180),             # glue face down
    ]
    out, x = None, -60.0
    for p in pieces:
        bb = p.val().BoundingBox()
        moved = p.translate((x - bb.xmin, 130.0 - bb.ymin, -bb.zmin))
        out = moved if out is None else out.union(moved)
        x += bb.xlen + 4.0
    tag = cq.Workplane("XY").workplane(offset=LID_T - 0.6).center(-56.0 + 23.0, 130.0 + 37.0).text(
        "TEST", 3.0, 1.0, combine=False, halign="center", valign="center")
    return out.cut(tag)
