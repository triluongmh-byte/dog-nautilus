"""Shared dimensions and solids for the Nautilus Dog case (contract frame, mm).

Origin: body footprint centre on the frame underside. +X forward, +Y left, +Z up.
Stage 'simple': plain open box frame (floor + straight walls, servo seats, leg pivot pads,
lid-screw corner bosses, sealed wall openings) and glue-on holders.
"""
import math

import cadquery as cq

# ---- body box -------------------------------------------------------------------------------
BODY_L, BODY_W, FRAME_H = 126.0, 75.0, 28.5
WALL, FLOOR = 2.0, 2.0
CORNER_R = 6.0
XI, YI = BODY_L / 2 - WALL, BODY_W / 2 - WALL          # inner wall faces: x 61, y 35.5
XO, YO = BODY_L / 2, BODY_W / 2                        # outer faces: x 63, y 37.5

# ---- servo seat (SG90/FS90R, GIẢ ĐỊNH nominal) ---------------------------------------------
CRANK_X, CRANK_Z = 27.3, 10.0          # crank axle O (front +, rear mirrored)
GEAR_CD = 18.0                         # nautilus centre distance rmin + rmax
DRIVE_Z = 20.0                         # lowered 1.1 mm from the draft so the wall above the window is >= 2 mm
DRIVE_X = CRANK_X - math.sqrt(GEAR_CD ** 2 - (DRIVE_Z - CRANK_Z) ** 2)   # 12.33
SHAFT_TO_BODY_C = 5.9                  # servo body centre is 5.9 mm outboard of the shaft
SERVO_XC = DRIVE_X + SHAFT_TO_BODY_C   # 18.23
SERVO_L, SERVO_H = 22.8, 12.2          # body along X, along Z
SERVO_FIT = 0.3                        # clearance per side in the wall window
SERVO_DEPTH_IN = 14.5                  # body inside the wall inner face (y 21..35.5)
FLANGE_L, FLANGE_T = 32.2, 2.5
ABOVE_FLANGE = 4.3                     # body above the flange (outside the wall)
SERVO_SCREW_DX = 13.9                  # flange screw holes at body centre +/- 13.9 (27.8 pitch)
SERVO_PILOT_D = 1.8                    # factory self-tap screw
PAD_DEPTH = 2.0                        # inside screw pad thickness (wall + pad = 4 mm of thread)
PAD_GAP = 0.2                          # pad edge beyond the window edge
PAD_W = 5.0

# ---- leg pivot pads (outside the side walls) -------------------------------------------------
JANSEN_SCALE = 0.42
Q_DX, Q_DZ = 38.0 * JANSEN_SCALE, -7.8 * JANSEN_SCALE      # fixed pivot Q from O, outboard
Q_X, Q_Z = CRANK_X + Q_DX, CRANK_Z + Q_DZ                  # 43.26, 6.72
CRANK_PAD_R, Q_PAD_R = 3.2, 4.0
PAD_Y_OUT = 47.0                       # pads reach y 37.5 -> 47 (gear plane starts near y 49.9)
PIN_HOLE_D = 4.2                       # 4 mm pin, through the pad and the wall

# ---- lid screw corner bosses (M3 self-tap) ---------------------------------------------------
LID_BOSS_X0, LID_BOSS_Y0 = 55.5, 30.0  # boss spans |x| 55.5..61, |y| 30..35.5
LID_SCREW = (58.25, 32.75)
LID_PILOT_D, LID_PILOT_DEPTH = 2.5, 10.0

# ---- sealed wall openings --------------------------------------------------------------------
USB_BACK = dict(y=12.5, z=12.0, w=24.0, h=18.0)
SWITCH = dict(y=-10.0, z=11.0, d=7.0)
USB_FRONT = dict(y=0.0, z=11.9, w=14.0, h=9.0)

# ---- glue-on holders -------------------------------------------------------------------------
FLOOR_TOP = FLOOR
BOARD_BOTTOM_Z = 5.0
MOUNTS = [(40.5, -23.5), (57.5, -23.5), (57.5, 23.5), (40.5, 23.5)]
M2_PILOT_D = 1.6
HOLDER_T = 1.2

CELL_Y, CELL_Z, CELL_R = 10.5, 12.75, 9.25
CELL_X0, CELL_X1 = -30.0, 36.0          # cradle end stops (65 mm cells + 1 mm play)
SADDLE_R = 9.5
CRADLE_HALF_W = 22.0
CRADLE_TOP = 12.0
END_T = 1.4
TIE_W, TIE_TOP = 3.6, 9.0              # cable-tie window under the cells in the centre rib (top z 9:
                                        # steep saddle wedge, no thin sliver)

CHG = dict(x0=-61.0, x1=-37.0, y0=2.0, y1=23.0, z0=6.0)   # CHG1 envelope (PCB bottom z 6)
BUCK = dict(x0=-54.0, x1=-32.0, y0=-33.0, y1=-16.0, z0=3.0)
LIP_CLEAR = 0.3


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_y(x, z, y0, y1, d):
    return cq.Workplane("XY", obj=cq.Solid.makeCylinder(d / 2, y1 - y0, cq.Vector(x, y0, z), cq.Vector(0, 1, 0)))


def cyl_x(y, z, x0, x1, d):
    return cq.Workplane("XY", obj=cq.Solid.makeCylinder(d / 2, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0)))


def cyl_z(x, y, z0, z1, d):
    return cq.Workplane("XY", obj=cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0), cq.Vector(0, 0, 1)))


def stadium_pad(x, z_axis, r, y0, y1):
    """A pad that stands on the bed (z 0) and ends in a round top around a Y axis: no overhang."""
    return box(x - r, x + r, y0, y1, 0, z_axis).union(cyl_y(x, z_axis, y0, y1, 2 * r))


def legs():
    """(name, sx, sy) for FL, FR, RL, RR."""
    return [("FL", 1, 1), ("FR", 1, -1), ("RL", -1, 1), ("RR", -1, -1)]


def servo_window(sx, sy):
    xc = sx * SERVO_XC
    hl, hh = SERVO_L / 2 + SERVO_FIT, SERVO_H / 2 + SERVO_FIT
    y0, y1 = (YI - 1, YO + 1) if sy > 0 else (-YO - 1, -YI + 1)
    return box(xc - hl, xc + hl, y0, y1, DRIVE_Z - hh, DRIVE_Z + hh)


def servo_pads(sx, sy):
    """Inside screw pads either side of the window, floor to frame top (load into the floor)."""
    xc = sx * SERVO_XC
    a, b = SERVO_L / 2 + SERVO_FIT + PAD_GAP, SERVO_L / 2 + SERVO_FIT + PAD_GAP + PAD_W
    y0, y1 = (YI - PAD_DEPTH, YI + 0.5) if sy > 0 else (-YI - 0.5, -YI + PAD_DEPTH)
    outer = box(min(xc + sx * a, xc + sx * b), max(xc + sx * a, xc + sx * b), y0, y1, FLOOR - 0.5, FRAME_H)
    return outer


def central_pad(sy):
    a = SERVO_XC - (SERVO_L / 2 + SERVO_FIT + PAD_GAP)      # 6.33
    y0, y1 = (YI - PAD_DEPTH, YI + 0.5) if sy > 0 else (-YI - 0.5, -YI + PAD_DEPTH)
    return box(-a, a, y0, y1, FLOOR - 0.5, FRAME_H)


def servo_screw_holes(sx, sy):
    xc = sx * SERVO_XC
    y0, y1 = (YI - PAD_DEPTH - 0.5, YO + 0.5) if sy > 0 else (-YO - 0.5, -YI + PAD_DEPTH + 0.5)
    return [cyl_y(xc + d, DRIVE_Z, y0, y1, SERVO_PILOT_D) for d in (-SERVO_SCREW_DX, SERVO_SCREW_DX)]


def leg_pads(sx, sy):
    y0, y1 = (YO - 0.5, PAD_Y_OUT) if sy > 0 else (-PAD_Y_OUT, -YO + 0.5)
    pads = stadium_pad(sx * CRANK_X, CRANK_Z, CRANK_PAD_R, y0, y1)
    return pads.union(stadium_pad(sx * Q_X, Q_Z, Q_PAD_R, y0, y1))


def leg_pin_holes(sx, sy):
    y0, y1 = (YI - 0.5, PAD_Y_OUT + 0.5) if sy > 0 else (-PAD_Y_OUT - 0.5, -YI + 0.5)
    return [cyl_y(sx * CRANK_X, CRANK_Z, y0, y1, PIN_HOLE_D), cyl_y(sx * Q_X, Q_Z, y0, y1, PIN_HOLE_D)]


def frame():
    outer = box(-XO, XO, -YO, YO, 0, FRAME_H).edges("|Z").fillet(CORNER_R)
    inner = box(-XI, XI, -YI, YI, FLOOR, FRAME_H + 1).edges("|Z").fillet(CORNER_R - WALL)
    body = outer.cut(inner)
    for sy in (1, -1):
        body = body.union(central_pad(sy))
    for name, sx, sy in legs():
        body = body.union(servo_pads(sx, sy)).union(leg_pads(sx, sy))
    # lid-screw corner bosses
    for sx in (1, -1):
        for sy in (1, -1):
            x0, x1 = sorted((sx * LID_BOSS_X0, sx * (XI + 0.5)))
            y0, y1 = sorted((sy * LID_BOSS_Y0, sy * (YI + 0.5)))
            body = body.union(box(x0, x1, y0, y1, FLOOR - 0.5, FRAME_H))
    cuts = []
    for name, sx, sy in legs():
        cuts.append(servo_window(sx, sy))
        cuts += servo_screw_holes(sx, sy)
        cuts += leg_pin_holes(sx, sy)
    for sx in (1, -1):
        for sy in (1, -1):
            cuts.append(cyl_z(sx * LID_SCREW[0], sy * LID_SCREW[1], FRAME_H - LID_PILOT_DEPTH, FRAME_H + 1,
                              LID_PILOT_D))
    u = USB_BACK
    cuts.append(box(-XO - 1, -XI + 0.5, u["y"] - u["w"] / 2, u["y"] + u["w"] / 2,
                    u["z"] - u["h"] / 2, u["z"] + u["h"] / 2))
    cuts.append(cyl_x(SWITCH["y"], SWITCH["z"], -XO - 1, -XI + 0.5, SWITCH["d"]))
    f = USB_FRONT
    cuts.append(box(XI - 0.5, XO + 1, f["y"] - f["w"] / 2, f["y"] + f["w"] / 2,
                    f["z"] - f["h"] / 2, f["z"] + f["h"] / 2))
    for c in cuts:
        body = body.cut(c)
    return body


# ---- glue-on holders (flat glue face on the floor top, z 2.0) --------------------------------
def carrier_holder():
    """U-shaped plate: two strips under the board's long edges + a front bar, 4 short M2 posts."""
    z0, z1 = FLOOR_TOP, FLOOR_TOP + HOLDER_T
    x0, x1 = 38.0, XI - 0.2
    part = box(x0, x1, 19.5, 27.5, z0, z1).union(box(x0, x1, -27.5, -19.5, z0, z1))
    part = part.union(box(59.0, x1, -27.5, 27.5, z0, z1))
    for x, y in MOUNTS:
        part = part.union(cyl_z(x, y, z1 - 0.3, BOARD_BOTTOM_Z, 5.0))
    for x, y in MOUNTS:
        part = part.cut(cyl_z(x, y, z0 - 0.5, BOARD_BOTTOM_Z + 0.5, M2_PILOT_D))
    return part


def battery_cradle():
    """Base plate + 2 end stops + a centre saddle rib with a cable-tie window under the cells."""
    z0, zb = FLOOR_TOP, FLOOR_TOP + HOLDER_T
    w = CRADLE_HALF_W
    part = box(CELL_X0 - END_T, CELL_X1 + END_T, -w, w, z0, zb)
    for xa, xb in ((CELL_X0 - END_T, CELL_X0), (CELL_X1, CELL_X1 + END_T), (-3.0, 3.0)):
        part = part.union(box(xa, xb, -w, w, zb - 0.2, CRADLE_TOP))
    for y in (CELL_Y, -CELL_Y):
        part = part.cut(cyl_x(y, CELL_Z, CELL_X0 - END_T - 1, CELL_X1 + END_T + 1, 2 * SADDLE_R))
    part = part.cut(box(-TIE_W / 2, TIE_W / 2, -w - 1, w + 1, zb, TIE_TOP))
    return part


def charger_holder():
    """Two rails under CHG1's long edges, side lips and a front stop; USB-C stays at the wall."""
    c = CHG
    z0, zb = FLOOR_TOP, FLOOR_TOP + HOLDER_T
    x0, x1 = -XI + 0.2, c["x1"]
    ya, yb = c["y0"] - LIP_CLEAR - 1.2, c["y1"] + LIP_CLEAR + 1.2
    part = box(x0, x1 + 1.2, ya, yb, z0, zb)
    part = part.union(box(x0, x1, c["y0"], c["y0"] + 3, zb - 0.2, c["z0"]))
    part = part.union(box(x0, x1, c["y1"] - 3, c["y1"], zb - 0.2, c["z0"]))
    part = part.union(box(x0 + 2, x1, ya, c["y0"] - LIP_CLEAR, zb - 0.2, c["z0"] + 2.5))
    part = part.union(box(x0 + 2, x1, c["y1"] + LIP_CLEAR, yb, zb - 0.2, c["z0"] + 2.5))
    part = part.union(box(x1 + LIP_CLEAR, x1 + 1.5, ya, yb, zb - 0.2, c["z0"] + 3))
    return part


def buck_holder():
    """Flat tray with low lips on the rear and both long sides; front left open for the wires."""
    b = BUCK
    z0, zb = FLOOR_TOP, b["z0"]
    xa = b["x0"] - LIP_CLEAR - 0.9
    ya, yb = b["y0"] - LIP_CLEAR - 1.2, b["y1"] + LIP_CLEAR + 1.2
    top = 4.8
    # base stops at the lip line so it clears the RR servo screw pad (x -35.1..-30.1, y -35.5..-33.5)
    part = box(xa, b["x1"], b["y0"] - LIP_CLEAR, yb, z0, zb)
    part = part.union(box(xa, b["x0"] - LIP_CLEAR, b["y0"] - LIP_CLEAR, yb, zb - 0.2, top))
    part = part.union(box(xa, -35.8, ya, b["y0"] - LIP_CLEAR + 0.2, z0, top))
    part = part.union(box(xa, b["x1"], b["y1"] + LIP_CLEAR, yb, zb - 0.2, top))
    return part


# ---- TEST ONLY coupons (cut from the final mating geometry, parked away from the assembly) ----
COUPON_SERVO_SHIFT = (0.0, 75.0, 0.0)
COUPON_MOUNTS_SHIFT = (0.0, -150.0, 0.0)


def label(text, x, y, z, size=4.0, depth=0.6):
    """Engraving tool for a TEST ONLY tag: cut it from a top face at height z."""
    try:
        return cq.Workplane("XY").workplane(offset=z - depth).center(x, y).text(
            text, size, depth + 0.5, combine=False, halign="center", valign="center")
    except Exception:  # no font on this machine: the TEST ONLY tag is in the part name and guide
        return None


def coupon_servo_seat():
    """FL wall section: servo window, flange screw pilots, crank + Q pivot pads/holes, on its floor strip."""
    part = frame().intersect(box(0.0, 48.0, 30.0, PAD_Y_OUT + 1, 0, FRAME_H))
    tag = label("TEST", 14.0, 32.6, FLOOR, size=3.0)
    if tag is not None:
        part = part.cut(tag)
    return part.translate(COUPON_SERVO_SHIFT)


def coupon_mounts():
    """Back-wall openings, front USB-C slot, lid-screw corner, and slices of every glue-on holder."""
    fr = frame()
    pieces = [
        fr.intersect(box(-XO, -XO + 6, -16.0, 27.0, 0, 23.0)),            # back wall: USB 24x18 + switch 7
        fr.intersect(box(XO - 6, XO, -10.0, 10.0, 0, 19.0)),              # front USB-C service slot
        fr.intersect(box(50.0, XO, 26.0, YO, 0, FRAME_H)),                # lid-screw corner boss
        carrier_holder().intersect(box(50.0, 62.0, 15.0, 30.0, 0, 10)),   # carrier post + strip + bar
        battery_cradle().intersect(box(-4.0, 4.0, -25.0, 25.0, 0, 20)),   # centre saddle + tie window
        charger_holder().intersect(box(-62.0, -30.0, 0.0, 12.0, 0, 20)),  # rail, lip, front stop
        buck_holder().intersect(box(-57.0, -40.0, -36.0, -12.0, 0, 20)),  # rear lip, side lips
    ]
    # lay the slices in a row on a common bed line
    out, x = None, -60.0
    for p in pieces:
        bb = p.val().BoundingBox()
        moved = p.translate((x - bb.xmin, -bb.ymin, -bb.zmin))
        out = moved if out is None else out.union(moved)
        x += bb.xlen + 4.0
    tag = label("TEST", -56.0, 21.0, FLOOR, size=2.6)    # on the back-wall slice's floor strip
    if tag is not None:
        out = out.cut(tag.rotate((-56.0, 21.0, 0), (-56.0, 21.0, 1), 90))
    return out.translate(COUPON_MOUNTS_SHIFT)
