"""Moving stage: nautilus gear pair + Jansen leg per corner, in the contract frame (mm).

Base module = rear-left (RL): crank O at (-27.3, z 10), leg reaches -X, parts on +Y.
Other legs are mirror images (FL: x -> -x, RR: y -> -y, FR: both); every printed link is the same
flat shape, so mirrored copies are the same print turned over.

Y stack (left side, outward): wall 37.5 | servo flange/body | horn | gear plane 50..54 |
L1 hip_triangle 54.4..57.4 | L2 rocker 57.8..60.8 | L3 lower_link 61.2..64.2 |
L4 upper_link + shin_link 64.6..67.6 | L5 foot 68.0..71.0 (shin left L3: it crossed lower_link).
Kinematics are parameterised by s1, the drive spiral's polar angle at the contact (0..2*pi = one
revolution of both gears; nautilus pair turns 1:1 on average, speed ratio r1/r2 varies).
"""
import math

import cadquery as cq

import geom as g

# ---- nautilus gear pair (draft numbers, radii trimmed so front/rear drive gears never touch) ----
G_RMIN, G_RMAX = 6.5, 11.5          # rmin + rmax = 18 = centre distance (frame is frozen)
G_TEETH = 8
G_TOOTH_H = 0.9
G_BACKOFF = 0.4
G_THICK = 4.0
G_OUTER = G_RMAX - G_BACKOFF + G_TOOTH_H          # 12.0
PIN_THETA = 5.9                     # crank pin angle on the crank gear (rad)
DRIVE_BORE = 4.0                    # horn screw access
HORN_PILOT_D, HORN_PILOT_R = 1.5, (4.6, 7.0)   # GIẢ ĐỊNH: SG90 horn arm holes ~2 mm pitch
HORN_PILOT_ANG = 5.0              # local spiral angle (rad): the wide side, >= 1 mm wall to the tooth roots
REST_S1 = 5.6                       # draft pose

# ---- Jansen linkage (Theo Jansen's numbers, scaled 0.42) --------------------------------------
JANSEN = dict(a=38.0, b=41.5, c=39.3, d=40.1, e=55.8, f=39.4, g=36.7,
              h=65.7, i=49.0, j=50.0, k=61.9, l=7.8, m=15.0)
S = g.JANSEN_SCALE
LINK_T, LAYER_GAP, BAR_W, BOSS_R, FOOT_R = 3.0, 0.4, 7.0, 4.0, 4.0
M2_CLEAR, PIN_HOLE = 2.4, g.PIN_HOLE_D
NUT_AF, NUT_H = 4.6, 1.6
HUB_R = 3.5                         # spacer hubs on the 4 mm pins (O on the crank gear, Q on the hip)

Y_GEAR = 50.0
Y_L = [Y_GEAR + G_THICK + LAYER_GAP + i * (LINK_T + LAYER_GAP) for i in range(5)]   # inner faces
Y_HUB0 = g.PAD_Y_OUT + 0.4          # hubs stop 0.4 mm off the frame pads

BASE_O = (-g.CRANK_X, g.CRANK_Z)
BASE_A = (-g.DRIVE_X, g.DRIVE_Z)
PHI = math.atan2(BASE_A[1] - BASE_O[1], BASE_A[0] - BASE_O[0])   # O -> A direction
K = math.log(G_RMAX / G_RMIN) / (2 * math.pi)

LINKS = ["hip_triangle", "rocker", "lower_link", "shin_link", "upper_link", "foot"]
GEARS = ["gear_drive", "gear_crank"]


def circ_int(c0, r0, c1, r1):
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    d = math.hypot(dx, dy)
    a = (r0 * r0 - r1 * r1 + d * d) / (2 * d)
    h = math.sqrt(max(r0 * r0 - a * a, 0.0))
    mx, my = c0[0] + a * dx / d, c0[1] + a * dy / d
    return [(mx - h * dy / d, my + h * dx / d), (mx + h * dy / d, my - h * dx / d)]


def kin(s1):
    """Base (RL) pose for drive contact angle s1: points (x, z) and gear angles (rad)."""
    s1 = s1 % (2 * math.pi)
    r1 = G_RMIN * math.exp(K * s1)
    r2 = G_RMIN + G_RMAX - r1
    s2 = math.log(r2 / G_RMIN) / K
    beta_a = PHI + math.pi - s1
    beta_b = PHI - s2
    crank = beta_b + PIN_THETA
    J = JANSEN
    Q = (-J["a"], -J["l"])
    C = (J["m"] * math.cos(crank), J["m"] * math.sin(crank))
    D = max(circ_int(C, J["j"], Q, J["b"]), key=lambda p: p[1])
    E = min(circ_int(Q, J["d"], D, J["e"]), key=lambda p: p[0])
    F = min(circ_int(C, J["k"], Q, J["c"]), key=lambda p: p[1])
    G = min(circ_int(E, J["f"], F, J["g"]), key=lambda p: p[0])
    H = min(circ_int(F, J["i"], G, J["h"]), key=lambda p: p[1])
    ab = lambda p: (BASE_O[0] + S * p[0], BASE_O[1] + S * p[1])
    pts = {n: ab(p) for n, p in zip("QCDEFGH", (Q, C, D, E, F, G, H))}
    pts["O"], pts["A"] = BASE_O, BASE_A
    # gear markers: a point on each gear at local angle 0
    pts["Ma"] = (BASE_A[0] + 5 * math.cos(beta_a), BASE_A[1] + 5 * math.sin(beta_a))
    pts["Mb"] = (BASE_O[0] + 5 * math.cos(beta_b), BASE_O[1] + 5 * math.sin(beta_b))
    return pts, beta_a, beta_b


# two tracked points per moving part (pivot, marker) for rigid pose transforms
TRACK = {"gear_drive": ("A", "Ma"), "gear_crank": ("O", "Mb"), "hip_triangle": ("Q", "D"),
         "rocker": ("Q", "F"), "lower_link": ("C", "F"), "shin_link": ("E", "G"),
         "upper_link": ("C", "D"), "foot": ("F", "G")}


def leg_sign(leg):
    return {"FL": (1, 1), "FR": (1, -1), "RL": (-1, 1), "RR": (-1, -1)}[leg]


def world(pt, leg):
    """Base (RL) point -> this leg's (x, z): front legs mirror x."""
    sx, _ = leg_sign(leg)
    return (-pt[0], pt[1]) if sx > 0 else pt


# ------------------------------------------------------------------ solids (base frame, +Y)
def xz(y_in, y_out):
    """Workplane in the XZ plane whose extrude(y_out - y_in) spans y_in..y_out."""
    return cq.Workplane("XZ", origin=(0, y_out, 0))


def gear_points():
    cs = math.sqrt(1 + K * K) / K
    L = cs * (G_RMAX - G_RMIN)
    pitch = L / (G_TEETH + 0.5)
    pts = []
    for i in range(201):
        th = 2 * math.pi * i / 200
        r = G_RMIN * math.exp(K * th)
        s = cs * (r - G_RMIN)
        R = r - G_BACKOFF + G_TOOTH_H * math.cos(2 * math.pi * s / pitch)
        pts.append((R * math.cos(th), R * math.sin(th)))
    return pts


def gear_profile(centre, beta):
    c, s = math.cos(beta), math.sin(beta)
    return [(centre[0] + x * c - y * s, centre[1] + x * s + y * c) for x, y in gear_points()]


def gear_drive_base():
    pts, beta_a, _ = kin(REST_S1)
    A = pts["A"]
    y0, y1 = Y_GEAR, Y_GEAR + G_THICK
    body = xz(y0, y1).polyline(gear_profile(A, beta_a)).close().extrude(y1 - y0)
    body = body.cut(g.cyl_y(A[0], A[1], y0 - 1, y1 + 1, DRIVE_BORE))
    for r in HORN_PILOT_R:   # one row of horn-arm screw pilots + CA glue
        ang = beta_a + HORN_PILOT_ANG
        body = body.cut(g.cyl_y(A[0] + r * math.cos(ang), A[1] + r * math.sin(ang), y0 - 1, y1 + 1, HORN_PILOT_D))
    return body


def gear_crank_base():
    pts, _, beta_b = kin(REST_S1)
    O, C = pts["O"], pts["C"]
    y0, y1 = Y_GEAR, Y_GEAR + G_THICK
    body = xz(y0, y1).polyline(gear_profile(O, beta_b)).close().extrude(y1 - y0)
    body = body.union(g.cyl_y(O[0], O[1], Y_HUB0, y0 + 0.5, 2 * HUB_R))        # spacer hub to the pad
    body = body.cut(g.cyl_y(O[0], O[1], Y_HUB0 - 1, y1 + 1, PIN_HOLE))
    body = body.cut(g.cyl_y(C[0], C[1], y0 - 1, y1 + 1, M2_CLEAR))
    return body


def link_base(segs, joints, holes, traps, layer, foot=None, hub=None):
    y0 = Y_L[layer]
    y1 = y0 + LINK_T
    body = None
    for a, b in segs:
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        s = xz(y0, y1).center((a[0] + b[0]) / 2, (a[1] + b[1]) / 2).slot2D(d + BAR_W, BAR_W, ang).extrude(LINK_T)
        body = s if body is None else body.union(s)
    for p in joints:
        body = body.union(g.cyl_y(p[0], p[1], y0, y1, 2 * BOSS_R))
    if foot is not None:
        body = body.union(g.cyl_y(foot[0], foot[1], y0, y1, 2 * FOOT_R))
    if hub is not None:
        body = body.union(g.cyl_y(hub[0], hub[1], Y_HUB0, y0 + 0.5, 2 * HUB_R))
    for p, dia in holes:
        body = body.cut(g.cyl_y(p[0], p[1], Y_HUB0 - 1, y1 + 1, dia))
    circ = NUT_AF / math.cos(math.pi / 6)
    depth = NUT_H + 0.2
    for p, where in traps:          # "out": pocket on the outer face, "in": on the inner face
        ya, yb = (y1 - depth, y1 + 0.5) if where == "out" else (y0 - 0.5, y0 + depth)
        nut = xz(ya, yb).center(*p).polygon(6, circ).extrude(yb - ya)
        body = body.cut(nut)
    return body


def link_base_by_name(name):
    P, _, _ = kin(REST_S1)
    Q, C, D, E, F, G, H = (P[n] for n in "QCDEFGH")
    mc = M2_CLEAR
    if name == "hip_triangle":
        return link_base([(Q, D), (D, E), (E, Q)], [Q, D, E], [(Q, PIN_HOLE), (D, mc), (E, mc)],
                         [(D, "in")], 0, hub=Q)
    if name == "rocker":
        return link_base([(Q, F)], [Q, F], [(Q, PIN_HOLE), (F, mc)], [(F, "in")], 1)
    if name == "lower_link":
        return link_base([(C, F)], [C, F], [(C, mc), (F, mc)], [], 2)
    if name == "shin_link":
        return link_base([(E, G)], [E, G], [(E, mc), (G, mc)], [(E, "out"), (G, "in")], 3)
    if name == "upper_link":
        return link_base([(C, D)], [C, D], [(C, mc), (D, mc)], [(C, "out")], 3)
    if name == "foot":
        return link_base([(F, G), (G, H), (H, F)], [F, G], [(F, mc), (G, mc)], [], 4, foot=H)
    raise KeyError(name)


def base_part(name):
    if name == "gear_drive":
        return gear_drive_base()
    if name == "gear_crank":
        return gear_crank_base()
    return link_base_by_name(name)


def mirror_leg(wp, leg):
    sx, sy = leg_sign(leg)
    if sx > 0:
        wp = wp.mirror("YZ")
    if sy < 0:
        wp = wp.mirror("XZ")
    return wp


def part(name, leg):
    return mirror_leg(base_part(name), leg)


# ------------------------------------------------------------------ posing (checks)
def pose_transform(name, leg, s1):
    """(pivot_rest_xz, angle_deg_about_+Y, translation_xz) moving the rest part to pose s1."""
    a, b = TRACK[name]
    rest, _, _ = kin(REST_S1)
    now, _, _ = kin(s1)
    p0, p1 = world(rest[a], leg), world(rest[b], leg)
    q0, q1 = world(now[a], leg), world(now[b], leg)
    th = math.atan2(q1[1] - q0[1], q1[0] - q0[0]) - math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    return p0, -math.degrees(th), (q0[0] - p0[0], q0[1] - p0[1])


def posed(shape, name, leg, s1):
    p0, ang, (dx, dz) = pose_transform(name, leg, s1)
    out = shape.rotate(cq.Vector(p0[0], 0, p0[1]), cq.Vector(p0[0], 1, p0[1]), ang)
    return out.translate(cq.Vector(dx, 0, dz))


# ------------------------------------------------------------------ gear-pair coupon (TEST ONLY)
COUPON_GEAR_SHIFT = (0.0, 0.0, 0.0)


def coupon_gear_pair():
    """Flat base with two 3.9 mm posts at the 18 mm centre distance + both gears laid flat beside it.

    Placed at x 90..150 (away from the robot). Gears print flat; the base prints flat, posts up.
    """
    base_x, base_y = 100.0, -60.0
    plate = g.box(base_x - 12, base_x + 30, base_y - 12, base_y + 12, 0, 2.0)
    posts = g.cyl_z(base_x, base_y, 1.5, 2.0 + G_THICK + 1.5, 3.9).union(
        g.cyl_z(base_x + 18.0, base_y, 1.5, 2.0 + G_THICK + 1.5, 3.9))
    tag = cq.Workplane("XY").workplane(offset=1.4).center(base_x + 9, base_y - 8.5).text(
        "TEST", 3.0, 1.0, combine=False, halign="center", valign="center")
    plate = plate.union(posts).cut(tag)

    def flat(wp, cx, cy):
        # lay a gear (axis along Y) flat on the bed, axis vertical, hub up
        sh = wp.rotate((0, 0, 0), (1, 0, 0), -90)      # inner face (hub side) up
        bb = sh.val().BoundingBox()
        return sh.translate((cx - (bb.xmin + bb.xmax) / 2, cy - (bb.ymin + bb.ymax) / 2, -bb.zmin))
    gd = gear_drive_base()
    gc = gear_crank_base()
    return plate.union(flat(gd, base_x - 5, base_y + 32)).union(flat(gc, base_x + 25, base_y + 32))
