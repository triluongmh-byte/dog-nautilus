"""
Nautilus Dog (compact) - a four-legged walker driven by nautilus (log-spiral) gears.

What it is / does
  A box body with a gear train on each side driving linkage legs, like the
  reference clip. Each leg has its own 360-degree (continuous) servo. The servo
  turns a nautilus DRIVE gear meshing with an identical nautilus CRANK gear.
  Two log spirals r = rmin*e^(k*theta) at centre distance rmin + rmax roll on
  each other exactly, so the pair turns 1:1 on average while the crank speed
  swings between 0.5x and 2x every turn. A crank screw on the crank gear drives
  a Jansen linkage (Theo Jansen's numbers, scaled 0.42), so the foot traces a
  flat-bottomed stride.

Size (user request: 126 x 75 x 31 mm)
  Body (frame + lid) is exactly 126 x 75 x 31 mm. The legs and gear stacks have
  to sit outside that box: SG90-size servos + gear + 4 link layers need ~34 mm per
  side, and the legs need ground clearance, so the whole robot measures about
  127 x 143 x 66 mm. A walking robot with these servos cannot fit inside 75 x 31.

Parts
  frame   open-top box 126 x 75 x 28.5. Side walls carry the servo seats (servo goes in
          from outside, flange on the wall), crank-gear axles and Jansen fixed-pivot axles.
          It also has side windows, a battery cradle (2x 18650 across the body),
          board posts, 4 lid posts, and a USB opening (24 x 18) + switch hole in the back wall
  lid     2.5 mm top (4x M3 self-tap): expansion deck in the centre (8 posts
          7 mm dia x 6 mm high on a 15 mm grid, M3 heat-set inserts, 12 mm cable hole
          in the middle) for later modules (camera, arm...). 1.54" OLED window at the front
          (landscape, module hangs under the lid). 30x30 fan mount at the back
          (27 mm opening, 4x 3.2 holes @ 23 mm)
  Leg layout: cranks and servos sit inboard (crank axles at x = +-27.3, drive gears
  at +-13.1), and each Jansen leg reaches OUTWARD (front legs forward, rear legs back)
  for a wide, planted stance. Inside the box: 2x 18650 lie along X in the middle,
  the fan is behind them, the ESP32-C3 is in front, and the OLED hangs under the front of the lid.
  per leg (front/rear x left/right, front legs mirrored in X):
    gear_drive (on the servo horn), gear_crank (on a frame pin),
    hip_triangle (Q-D-E), rocker (Q-F), lower_link (C-F), upper_link (C-D),
    shin_link (E-G), foot (F-G-H with the pad)
Joints: M2 screws + nuts (nut trapped in a link), printed 4 mm frame pins in
  5 mm holes at the crank-gear axle and the fixed pivot Q (M2 self-tap + washer in the tip).
  Layers out from the gear plane: L1 hip_triangle | L2 rocker | L3 lower_link +
  shin_link | L4 upper_link + foot.

Bought: 4x 360 micro servo (SG90/FS90R size) + horns, 20x M2 screws + nuts,
  2x 18650, ESP32-C3 SuperMini (22.5 x 18, assumed), 1.54" 128x64 OLED
  (44 x 37 module, 36 x 19 view, holes 40 x 32, assumed), 30x30x10 fan.
  These sizes are nominal, so measure yours. Only 4 of the 8 servos are used.
  Front and rear legs reach away from each other, so any gait phase is free
  (trot = diagonal pairs 180 deg apart).

Electrical brief (for the electrical team)
  2S 18650 -> switch (back wall) -> 5-6 V / 3 A buck for servos + fan; ESP32-C3 on 5 V.
  2S BMS/charger behind the back-wall USB opening. 4 servo signals on 4 PWM GPIOs
  (50 Hz, 1.5 ms = stop), 1000 uF on the servo rail. OLED 1.54" SSD1309 on I2C
  (under the lid, front, x = 39). Fan 30x30 5 V under the lid at x = -45.5. Leave a
  spare 5 V / GND / I2C / 2 GPIO header near the deck's 12 mm cable hole for modules. Optional
  battery sense via a 100k/33k divider into an ADC pin.
"""
import math

import cadquery as cq
from cadsmith import Fit
from cadsmith.cadlib.components import (
    servo, servo_horn, servo_cutout, screw, nut, cell_18650,
)


class Params:
    # ---- body box (X forward, Y left, Z up) : 126 x 75 x (28.5 + 2.5 lid) ----
    body_len = 126.0
    body_w = 75.0
    wall = 2.0
    floor_t = 2.0
    box_below = 10.0      # box bottom below the crank axis
    box_above = 18.5      # box top above the crank axis
    body_r = 6.0          # one corner radius for body + lid
    lid_t = 2.5
    post_d = 7.0
    post_x = 25.0
    m3_clear = 3.4
    m3_pilot = 2.5
    # ---- servo ----
    servo_kind = "SG90"
    # ---- nautilus gear pair ----
    g_rmin = 6.0
    g_rmax = 12.0
    g_teeth = 8           # teeth along the spiral (plus half a pitch at the step)
    g_tooth_h = 0.9
    g_backoff = 0.4       # pitch curve pulled in on each gear -> backlash
    g_thick = 4.0
    g_pose = 5.6          # drive-gear spiral angle at the contact in this pose
    g_driver_dir = 38.0   # drive gear forward-up; keeps >1 mm wall above the servo window
    g_holes = (2.7, 4.2)
    g_hole_c = 0.6        # hole centre / local radius
    g_hole_d = 0.25       # hole diameter / local radius
    g_drive_bore = 4.0    # access to the horn screw
    pin_theta = 5.9       # crank screw position on the crank gear (rad)
    # ---- Jansen leg ----
    crank_x = -27.3       # module is the REAR leg: crank inboard, leg reaches out to the back
    jansen_scale = 0.42
    link_t = 3.0
    layer_gap = 0.4
    bar_w = 7.0
    boss_r = 4.0
    foot_r = 4.0
    # ---- pins / fasteners (M2 joints) ----
    fast = "M2"
    pin_d = 4.0
    pin_clear = 0.5
    standoff_d = 6.0
    inner_boss_d = 9.0
    m2_clear = 2.4
    m2_pilot = 1.6
    nut_pocket_af = 4.6
    # ---- electronics ----
    cell_y = 10.5         # cells lie along X at y = +-cell_y
    cell_x0 = -29.0       # rear end of the cells (fan sits behind them)
    cradle_dx = 20.0      # cradle ribs at cell centre +- this
    board_x = 49.0
    board_l = 18.0        # along X
    board_w = 22.5        # along Y
    board_lift = 4.0      # above the floor
    # ---- back wall USB opening (enlarged 5 mm per side) ----
    usb_y = 12.5
    usb_w = 24.0
    usb_h = 18.0
    usb_dz = 4.0
    # ---- 1.54" 128x64 OLED under the lid, landscape (long side along Y) ----
    disp_x = 39.0         # front of the lid, clear of the expansion deck
    # ---- expansion deck on the lid (module mounting posts) ----
    deck_x = -5.0
    deck_pitch = 15.0
    deck_post_d = 7.0
    deck_post_h = 6.0
    deck_insert_d = 4.0   # M3 heat-set insert pocket
    deck_insert_depth = 5.5
    deck_cable_d = 12.0
    disp_win_x = 36.0     # landscape, long side along the body
    disp_win_y = 19.0
    disp_mod_x = 44.0
    disp_mod_y = 37.0
    disp_hole_x = 40.0
    disp_hole_y = 32.0
    # ---- 30x30 fan on the lid ----
    fan_x = -45.5
    fan_size = 30.0
    fan_t = 10.0
    fan_hole_pitch = 23.0
    fan_hole_d = 3.2
    fan_open_d = 27.0


# Theo Jansen's link lengths (crank m, fixed pivot offset a, l)
JANSEN = dict(a=38.0, b=41.5, c=39.3, d=40.1, e=55.8, f=39.4, g=36.7,
              h=65.7, i=49.0, j=50.0, k=61.9, l=7.8, m=15.0)

LEGS = [("front_left", -1, 1), ("front_right", -1, -1),
        ("rear_left", 1, 1), ("rear_right", 1, -1)]
LINKS = ["hip_triangle", "rocker", "lower_link", "upper_link", "shin_link", "foot"]
JOINTS = ["c", "d", "e", "f", "g"]


# ------------------------------------------------------------------ helpers
def U(a, b):
    return b if a is None else a.union(b)


def bbox(wp):
    shapes = [v for v in wp.vals() if isinstance(v, cq.Shape)]
    return cq.Compound.makeCompound(shapes).BoundingBox()


def cyl_y(u, v, y0, y1, d):
    return cq.Workplane("XY", obj=cq.Solid.makeCylinder(
        d / 2, y1 - y0, cq.Vector(u, y0, v), cq.Vector(0, 1, 0)))


def cyl_x(x0, x1, y, z, d):
    return cq.Workplane("XY", obj=cq.Solid.makeCylinder(
        d / 2, x1 - x0, cq.Vector(x0, y, z), cq.Vector(1, 0, 0)))


def side(wp, y0, t):
    """Slab drawn in XY (x->X, y->Z), thickness t along +z -> world slab y0..y0+t.
    Local top face (z=t) becomes the INNER face (y0)."""
    return wp.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, y0 + t, 0))


def mirror_to(wp, sx, sy):
    if sx < 0:
        wp = wp.mirror("YZ")
    if sy < 0:
        wp = wp.mirror("XZ")
    return wp


def circ_int(c0, r0, c1, r1):
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    d = math.hypot(dx, dy)
    a = (r0 * r0 - r1 * r1 + d * d) / (2 * d)
    h = math.sqrt(max(r0 * r0 - a * a, 0.0))
    mx, my = c0[0] + a * dx / d, c0[1] + a * dy / d
    return [(mx - h * dy / d, my + h * dx / d), (mx + h * dy / d, my - h * dx / d)]


# ------------------------------------------------------------------ layout
def layout(P):
    Lo = {}
    kk = math.log(P.g_rmax / P.g_rmin) / (2 * math.pi)
    Lo["k"] = kk
    r1 = P.g_rmin * math.exp(kk * P.g_pose)
    r2 = P.g_rmin + P.g_rmax - r1
    th2 = math.log(r2 / P.g_rmin) / kk
    phi = math.radians(P.g_driver_dir)
    Lo["beta_b"] = phi - th2
    Lo["beta_a"] = phi + math.pi - P.g_pose
    crank = Lo["beta_b"] + P.pin_theta

    J = JANSEN
    s = P.jansen_scale
    Q = (-J["a"], -J["l"])
    C = (J["m"] * math.cos(crank), J["m"] * math.sin(crank))
    D = max(circ_int(C, J["j"], Q, J["b"]), key=lambda p: p[1])
    E = min(circ_int(Q, J["d"], D, J["e"]), key=lambda p: p[0])
    F = min(circ_int(C, J["k"], Q, J["c"]), key=lambda p: p[1])
    G = min(circ_int(E, J["f"], F, J["g"]), key=lambda p: p[0])
    H = min(circ_int(F, J["i"], G, J["h"]), key=lambda p: p[1])
    zO = P.foot_r - s * H[1]
    Lo["zO"] = zO
    ab = lambda p: (P.crank_x + s * p[0], zO + s * p[1])
    Lo["O"] = (P.crank_x, zO)
    for n, p in zip("QCDEFGH", (Q, C, D, E, F, G, H)):
        Lo[n] = ab(p)
    dab = P.g_rmin + P.g_rmax
    Lo["A"] = (P.crank_x + dab * math.cos(phi), zO + dab * math.sin(phi))

    # Y layers (left side, +Y)
    sb = bbox(servo(P.servo_kind))
    hb = bbox(servo_horn(P.servo_kind))
    Lo["servo_top"] = sb.zmax
    Lo["servo_flip"] = (sb.xmin + sb.xmax) / 2 > 0   # body must point to -X (body centre)
    Lo["y_w"] = P.body_w / 2
    Lo["y_g0"] = Lo["y_w"] + sb.zmax + hb.zmax + 0.05
    Lo["yL"] = [Lo["y_g0"] + P.g_thick + P.layer_gap + i * (P.link_t + P.layer_gap)
                for i in range(4)]   # inner faces of L1..L4
    Lo["nut_h"] = bbox(nut(P.fast)).zlen
    Lo["zb"] = zO - P.box_below
    Lo["zt"] = zO + P.box_above
    return Lo


# ------------------------------------------------------------------ gears
def gear_points(P, Lo):
    kk = Lo["k"]
    cs = math.sqrt(1 + kk * kk) / kk
    L = cs * (P.g_rmax - P.g_rmin)
    pitch = L / (P.g_teeth + 0.5)          # makes f(L - s) = -f(s): pair interleaves
    pts = []
    M = 200
    for i in range(M + 1):
        th = 2 * math.pi * i / M
        r = P.g_rmin * math.exp(kk * th)
        s = cs * (r - P.g_rmin)
        R = r - P.g_backoff + P.g_tooth_h * math.cos(2 * math.pi * s / pitch)
        pts.append((R * math.cos(th), R * math.sin(th)))
    return pts


def nautilus_gear(P, Lo, bore, crank=False):
    T = P.g_thick
    # one smooth spline face for the toothed spiral + a straight radial step
    g = cq.Workplane("XY").spline(gear_points(P, Lo), includeCurrent=False).close().extrude(T)
    cut = cq.Workplane("XY").workplane(offset=-0.5).circle(bore / 2).extrude(T + 1)
    for th in P.g_holes:
        r = P.g_rmin * math.exp(Lo["k"] * th)
        c, d = P.g_hole_c * r, P.g_hole_d * r
        cut = cut.union(cq.Workplane("XY").workplane(offset=-0.5)
                        .center(c * math.cos(th), c * math.sin(th)).circle(d / 2).extrude(T + 1))
    if crank:
        rc = JANSEN["m"] * P.jansen_scale
        x, y = rc * math.cos(P.pin_theta), rc * math.sin(P.pin_theta)
        cut = cut.union(cq.Workplane("XY").workplane(offset=-0.5)
                        .center(x, y).circle(P.m2_clear / 2).extrude(T + 1))
    return g.cut(cut)


# ------------------------------------------------------------------ links
def link_part(P, Lo, segs, joints, holes, traps, foot=None):
    t = P.link_t
    body = None
    for a, b in segs:
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx))
        body = U(body, cq.Workplane("XY").center((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                 .slot2D(d + P.bar_w, P.bar_w, ang).extrude(t))
    body = body.union(cq.Workplane("XY").pushPoints(joints).circle(P.boss_r).extrude(t))
    if foot is not None:
        body = body.union(cq.Workplane("XY").center(*foot).circle(P.foot_r).extrude(t))
    for pt, d in holes:
        body = body.cut(cq.Workplane("XY").workplane(offset=-0.5)
                        .center(*pt).circle(d / 2).extrude(t + 1))
    depth = Lo["nut_h"] + 0.2
    circ = P.nut_pocket_af / math.cos(math.pi / 6)
    for pt, where in traps:
        z0 = t - depth if where == "in" else -0.5
        body = body.cut(cq.Workplane("XY").workplane(offset=z0)
                        .center(*pt).polygon(6, circ).extrude(depth + 0.5))
    return body


def screw_at(P, length, u, v, y, head_out=True):
    s = screw(P.fast, length)
    s = s.rotate((0, 0, 0), (1, 0, 0), -90 if head_out else 90)
    return s.translate((u, y, v))


def nut_at(P, u, v, y, grow_out=True):
    n = nut(P.fast).rotate((0, 0, 0), (1, 0, 0), -90 if grow_out else 90)
    return n.translate((u, y, v))


def servo_xform(P, Lo, obj):
    if Lo["servo_flip"]:
        obj = obj.rotate((0, 0, 0), (0, 0, 1), 180)
    A = Lo["A"]
    return obj.rotate((0, 0, 0), (1, 0, 0), -90).translate((A[0], Lo["y_w"], A[1]))


# ------------------------------------------------------------------ one leg module (front-left frame)
def leg_module(P, Lo):
    t, T = P.link_t, P.g_thick
    yg, yL = Lo["y_g0"], Lo["yL"]
    O, A = Lo["O"], Lo["A"]
    Q, C, D, E, F, G, H = (Lo[n] for n in "QCDEFGH")
    pin_hole = P.pin_d + 2 * P.pin_clear
    mc = P.m2_clear
    out = {}

    out["servo"] = servo_xform(P, Lo, servo(P.servo_kind))
    # horn arm points back toward the body centre so it stays inside the 126 mm length
    out["horn"] = (servo_horn(P.servo_kind).rotate((0, 0, 0), (0, 0, 1), 180)
                   .rotate((0, 0, 0), (1, 0, 0), -90)
                   .translate((A[0], Lo["y_w"] + Lo["servo_top"], A[1])))

    ga = (nautilus_gear(P, Lo, P.g_drive_bore)
          .rotate((0, 0, 0), (0, 0, 1), math.degrees(Lo["beta_a"])).translate((A[0], A[1], 0)))
    out["gear_drive"] = side(ga, yg, T)
    gb = (nautilus_gear(P, Lo, pin_hole, crank=True)
          .rotate((0, 0, 0), (0, 0, 1), math.degrees(Lo["beta_b"])).translate((O[0], O[1], 0)))
    out["gear_crank"] = side(gb, yg, T)

    out["hip_triangle"] = side(link_part(
        P, Lo, [(Q, D), (D, E), (E, Q)], [Q, D, E],
        [(Q, pin_hole), (D, mc), (E, mc)], [(D, "in")]), yL[0], t)
    out["rocker"] = side(link_part(
        P, Lo, [(Q, F)], [Q, F], [(Q, pin_hole), (F, mc)], [(F, "in")]), yL[1], t)
    out["lower_link"] = side(link_part(
        P, Lo, [(C, F)], [C, F], [(C, mc), (F, mc)], []), yL[2], t)
    out["shin_link"] = side(link_part(
        P, Lo, [(E, G)], [E, G], [(E, mc), (G, mc)], [(E, "out"), (G, "in")]), yL[2], t)
    out["upper_link"] = side(link_part(
        P, Lo, [(C, D)], [C, D], [(C, mc), (D, mc)], [(C, "out")]), yL[3], t)
    out["foot"] = side(link_part(
        P, Lo, [(F, G), (G, H), (H, F)], [F, G], [(F, mc), (G, mc)], [], foot=H), yL[3], t)

    y4o = yL[3] + t
    # crank screw: head under the crank gear, nut trapped in upper_link's outer face
    out["screw_c"] = screw_at(P, y4o - yg, C[0], C[1], yg, head_out=False)
    out["nut_c"] = nut_at(P, C[0], C[1], y4o, grow_out=False)
    out["screw_d"] = screw_at(P, y4o - yL[0], D[0], D[1], y4o)
    out["nut_d"] = nut_at(P, D[0], D[1], yL[0])
    out["screw_e"] = screw_at(P, yL[2] + t - yL[0], E[0], E[1], yL[0], head_out=False)
    out["nut_e"] = nut_at(P, E[0], E[1], yL[2] + t, grow_out=False)
    out["screw_f"] = screw_at(P, y4o - yL[1], F[0], F[1], y4o)
    out["nut_f"] = nut_at(P, F[0], F[1], yL[1])
    out["screw_g"] = screw_at(P, y4o - yL[2], G[0], G[1], y4o)
    out["nut_g"] = nut_at(P, G[0], G[1], yL[2])

    # frame features for this leg
    yw, w = Lo["y_w"], P.wall
    add = None
    for (u, v), y_end, pin_end in ((O, yg, yg + T), (Q, yL[0], yL[1] + t)):
        add = U(add, cyl_y(u, v, yw - w - 1.5, yw - w + 0.5, P.inner_boss_d))
        add = add.union(cyl_y(u, v, yw - 0.5, y_end, P.standoff_d))
        add = add.union(cyl_y(u, v, y_end - 0.5, pin_end, P.pin_d))
    # servo seat: closed window, servo goes in from outside (body first)
    cut = servo_xform(P, Lo, servo_cutout(P.servo_kind))
    cut = cut.union(cyl_y(O[0], O[1], yg + T - 6, yg + T + 1, P.m2_pilot))
    cut = cut.union(cyl_y(Q[0], Q[1], yL[1] + t - 6, yL[1] + t + 1, P.m2_pilot))
    return out, add, cut


# ------------------------------------------------------------------ body parts
def post_points(P):
    py = P.body_w / 2 - P.wall - 3.2
    return [(sx * P.post_x, sy * py) for sx in (1, -1) for sy in (1, -1)]


def frame_part(P, Lo, add, cut):
    zb, zt, zO = Lo["zb"], Lo["zt"], Lo["zO"]
    H = zt - zb
    Lb, W, w = P.body_len, P.body_w, P.wall
    outer = (cq.Workplane("XY").box(Lb, W, H).edges("|Z").fillet(P.body_r)
             .edges("<Z").chamfer(1.0).translate((0, 0, (zb + zt) / 2)))
    ih = H - P.floor_t + 1
    inner = (cq.Workplane("XY").box(Lb - 2 * w, W - 2 * w, ih).edges("|Z").fillet(P.body_r - w)
             .translate((0, 0, zb + P.floor_t + ih / 2)))
    body = outer.cut(inner)
    fz = zb + P.floor_t

    # lid screw posts (mid-length, clear of the servos)
    posts = post_points(P)
    ph = zt - fz + 0.5
    body = body.union(cq.Workplane("XY").pushPoints(posts).circle(P.post_d / 2).extrude(ph)
                      .translate((0, 0, fz - 0.5)))
    body = body.cut(cq.Workplane("XY").pushPoints(posts).circle(P.m3_pilot / 2).extrude(11)
                    .translate((0, 0, zt - 10)))

    # leg modules
    for _, sx, sy in LEGS:
        body = body.union(mirror_to(add, sx, sy))
    for _, sx, sy in LEGS:
        body = body.cut(mirror_to(cut, sx, sy))

    # side windows
    body = body.cut(cq.Workplane("XZ").center(0, zO - 1).slot2D(30, 8, 0)
                    .extrude(W, both=True))
    # USB + switch openings in the back wall
    body = body.cut(cq.Workplane("YZ").center(P.usb_y, zO + P.usb_dz).rect(P.usb_w, P.usb_h)
                    .extrude(3, both=True).translate((-Lb / 2, 0, 0)))
    body = body.cut(cyl_x(-Lb / 2 - 1, -Lb / 2 + 4, -14, zO + P.usb_dz, 7))

    # board posts
    bpts = [(P.board_x + dx, dy) for dx in (-6.5, 6.5) for dy in (-9, 9)]
    body = body.union(cq.Workplane("XY").pushPoints(bpts).circle(1.5)
                      .extrude(P.board_lift + 0.5).translate((0, 0, fz - 0.5)))

    # battery cradle: two ribs across Y, cells lie along X
    zc = Lo["cell_zc"]
    cx = Lo["cell_cx"]
    rc = Lo["cell_r"] + 0.3
    ch = zc - fz + 0.5
    for x in (cx - P.cradle_dx, cx + P.cradle_dx):
        rib = cq.Workplane("XY").box(4, 46, ch).translate((x, 0, fz - 0.5 + ch / 2))
        for y in (-P.cell_y, P.cell_y):
            rib = rib.cut(cyl_x(x - 3, x + 3, y, zc, 2 * rc))
        body = body.union(rib)
    return body


def lid_part(P, Lo):
    zt = Lo["zt"]
    Lb, W = P.body_len, P.body_w
    lid = (cq.Workplane("XY").box(Lb, W, P.lid_t).edges("|Z").fillet(P.body_r)
           .edges(">Z").fillet(1.0).translate((0, 0, zt + P.lid_t / 2)))
    lid = lid.cut(cq.Workplane("XY").pushPoints(post_points(P)).circle(P.m3_clear / 2)
                  .extrude(10).translate((0, 0, zt - 2)))
    # OLED window + M2 holes
    lid = lid.cut(cq.Workplane("XY").box(P.disp_win_x, P.disp_win_y, 10).edges("|Z").fillet(1.5)
                  .translate((P.disp_x, 0, zt)))
    dh = [(P.disp_x + sx * P.disp_hole_x / 2, sy * P.disp_hole_y / 2)
          for sx in (1, -1) for sy in (1, -1)]
    lid = lid.cut(cq.Workplane("XY").pushPoints(dh).circle(P.m2_clear / 2).extrude(10)
                  .translate((0, 0, zt - 2)))
    # expansion deck: 8 posts on a 15 mm grid (3x3 minus centre) with M3 heat-set
    # pockets for future modules (camera, arm, ...), plus a central cable hole
    top = zt + P.lid_t
    pts = [(P.deck_x + i * P.deck_pitch, j * P.deck_pitch)
           for i in (-1, 0, 1) for j in (-1, 0, 1) if (i, j) != (0, 0)]
    lid = lid.union(cq.Workplane("XY").pushPoints(pts).circle(P.deck_post_d / 2)
                    .extrude(P.deck_post_h + 0.5).translate((0, 0, top - 0.5)))
    lid = lid.cut(cq.Workplane("XY").pushPoints(pts).circle(P.deck_insert_d / 2)
                  .extrude(P.deck_insert_depth + 1)
                  .translate((0, 0, top + P.deck_post_h - P.deck_insert_depth)))
    lid = lid.cut(cq.Workplane("XY").center(P.deck_x, 0).circle(P.deck_cable_d / 2)
                  .extrude(10).translate((0, 0, zt - 2)))
    # 30x30 fan: air opening + 4 holes on a 23 mm square
    lid = lid.cut(cq.Workplane("XY").center(P.fan_x, 0).circle(P.fan_open_d / 2).extrude(10)
                  .translate((0, 0, zt - 2)))
    hp = P.fan_hole_pitch / 2
    lid = lid.cut(cq.Workplane("XY")
                  .pushPoints([(P.fan_x + sx * hp, sy * hp) for sx in (1, -1) for sy in (1, -1)])
                  .circle(P.fan_hole_d / 2).extrude(10).translate((0, 0, zt - 2)))
    return lid


def fan_part(P, Lo):
    """30x30x10 fan envelope hanging under the lid."""
    f = cq.Workplane("XY").box(P.fan_size, P.fan_size, P.fan_t).edges("|Z").fillet(2)
    return f.translate((P.fan_x, 0, Lo["zt"] - P.fan_t / 2))


def display_part(P, Lo):
    """1.54 in 128x64 OLED module under the lid window (envelope)."""
    zt = Lo["zt"]
    panel = (cq.Workplane("XY").box(P.disp_win_x + 4, P.disp_win_y + 4, 1.5)
             .translate((P.disp_x, 0, zt - 0.75)))
    pcb = (cq.Workplane("XY").box(P.disp_mod_x, P.disp_mod_y, 1.6)
           .translate((P.disp_x, 0, zt - 1.5 - 0.8 + 0.05)))
    return panel.union(pcb)


def board_part(P, Lo):
    z = Lo["zb"] + P.floor_t + P.board_lift
    b = cq.Workplane("XY").box(P.board_l, P.board_w, 1.2).translate((P.board_x, 0, z + 0.6))
    b = b.union(cq.Workplane("XY").box(16, 12, 3).translate((P.board_x, 0, z + 1.2 + 1.5 - 0.1)))
    return b


# ------------------------------------------------------------------ assembly
def parts():
    P = Params
    Lo = layout(P)
    cb = bbox(cell_18650())
    Lo["cell_r"] = cb.zlen / 2
    Lo["cell_zc"] = Lo["zb"] + P.floor_t + Lo["cell_r"] + 1.5
    Lo["cell_cx"] = P.cell_x0 + cb.xlen / 2

    mod, add, cut = leg_module(P, Lo)
    out = {
        "frame": frame_part(P, Lo, add, cut),
        "lid": lid_part(P, Lo),
        "controller_board": board_part(P, Lo),
        "fan": fan_part(P, Lo),
        "display": display_part(P, Lo),
    }
    for i, y in enumerate((-P.cell_y, P.cell_y)):
        out[f"battery_{i + 1}"] = cell_18650().translate((Lo["cell_cx"], y, Lo["cell_zc"]))
    for leg, sx, sy in LEGS:
        for name, wp in mod.items():
            out[f"{name}_{leg}"] = mirror_to(wp, sx, sy)
    return out


_BOUGHT_BASE = ["servo", "horn"] + [f"screw_{j}" for j in JOINTS] + [f"nut_{j}" for j in JOINTS]
BOUGHT = {f"{b}_{leg}" for b in _BOUGHT_BASE for leg, _, _ in LEGS} | {
    "battery_1", "battery_2", "controller_board", "fan", "display"}

FITS = [Fit("frame", "lid", seat="z")]
for _leg, _, _ in LEGS:
    FITS += [
        Fit("frame", f"gear_crank_{_leg}", seat="y"),
        Fit("frame", f"hip_triangle_{_leg}", seat="y"),
        Fit(f"gear_drive_{_leg}", f"gear_crank_{_leg}", min_clearance=0.2),
    ]

ORIENT = {"frame": "-Z", "lid": "-Z"}
for _leg, _, _sy in LEGS:
    for _p in LINKS + ["gear_drive", "gear_crank"]:
        ORIENT[f"{_p}_{_leg}"] = "+Y" if _sy > 0 else "-Y"
    # upper_link's only nut pocket is on its outer face: print inner face down, pocket up
    ORIENT[f"upper_link_{_leg}"] = "-Y" if _sy > 0 else "+Y"
