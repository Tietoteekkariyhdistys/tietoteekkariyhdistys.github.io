import json, math, sys
src = open('gen_ascii.py', encoding='utf-8').read()
exec(src[:src.index('FIG_COLS =')].replace('K = 2 ', 'K = 3 ').replace('SSB = 4 ', 'SSB = 3 ').replace('b_ - a_ <= 6', 'b_ - a_ <= 9'))
FIG_COLS = 31 * K
SIGN_COLS = 30 * K
CX = 86
exec(src[src.index('def sign():'):src.index('poses = {')])

THIGH, SHIN, UARM, FARM = 45, 43, 40, 38
GROUND = 272
FAR, NEAR = 170, 238
HS = 0.8
RH = 58 * HS
CA = math.radians(24)
D = (math.cos(CA), math.sin(CA))          # cigarette direction, 24 degrees below horizontal
N = (-math.sin(CA), math.cos(CA))         # normal, pointing down and back
CW_ = 4                                   # cigarette thickness


def leg(hip, ang, flex):
    a, b = math.radians(ang), math.radians(ang - flex)
    k = (hip[0] + THIGH * math.sin(a), hip[1] + THIGH * math.cos(a))
    f = (k[0] + SHIN * math.sin(b), k[1] + SHIN * math.cos(b))
    return k, f


def two_bone(S, T, l1, l2, side):
    dx, dy = T[0] - S[0], T[1] - S[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 0.5)
    base = math.atan2(dx, dy)
    al = math.acos(max(-1, min(1, (l1 ** 2 + d ** 2 - l2 ** 2) / (2 * l1 * d))))
    a = base + side * al
    e = (S[0] + l1 * math.sin(a), S[1] + l1 * math.cos(a))
    w = (S[0] + d * math.sin(base), S[1] + d * math.cos(base))
    return e, w


def arm_fk(S, ang, flex):
    a, b = math.radians(ang), math.radians(ang + flex)
    e = (S[0] + UARM * math.sin(a), S[1] + UARM * math.cos(a))
    w = (e[0] + FARM * math.sin(b), e[1] + FARM * math.cos(b))
    return e, w


def limb(L, pts, w, lum):
    L.line(pts, w, lum, outline=0, ow=2)


def foot(L, f, lum, cb, twist=0):
    x0, y0, x1, y1 = f[0] - 5 - 4 * cb, f[1] - 2, f[0] + 17 - 8 * cb, f[1] + 7
    if twist:
        cx_, cy_ = (x0 + x1) / 2, (y0 + y1) / 2
        t = math.radians(twist)
        pts = []
        for px, py in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            dx, dy = px - cx_, py - cy_
            pts.append((cx_ + dx * math.cos(t) - dy * math.sin(t), cy_ + dx * math.sin(t) + dy * math.cos(t)))
        L.poly(pts, lum, outline=0, ow=1)
    else:
        L.rect((x0, y0, x1, y1), lum, outline=0, ow=1, radius=3)


def hand(L, w, lum):
    L.ell((w[0] - 7, w[1] - 7, w[0] + 7, w[1] + 7), lum, outline=0, ow=2)


# ---- cigarette ----------------------------------------------------------------
def cig_pts(M, length):
    F = (M[0] + min(8, length * 0.3) * D[0], M[1] + min(8, length * 0.3) * D[1])
    T = (M[0] + length * D[0], M[1] + length * D[1])
    E = (T[0] + 5 * D[0], T[1] + 5 * D[1])
    return F, T, E


def pinch_p(length):
    return min(8, 0.45 * length)


def hold_M(H, length):
    """filter end of a cigarette pinched by a hand at H (the hand sits just below the cigarette)"""
    p = pinch_p(length)
    return (H[0] - 9 * N[0] - p * D[0], H[1] - 9 * N[1] - p * D[1])


def pinch_H(M, length, off=15):
    # at the mouth the hand sits well below the cigarette, joined to it by a visible finger
    p = pinch_p(length)
    return (M[0] + p * D[0] + off * N[0], M[1] + p * D[1] + off * N[1])


def cig_hand(H, length, lit):
    return dict(L=length, lit=lit, M=hold_M(H, length), H=H)


def cig_mouth(length, lit, pinch=False):
    return dict(L=length, lit=lit, M=None, pinch=pinch)


def draw_cig(L, M, c):
    length = c["L"]
    F, T, E = cig_pts(M, length)
    L.line([M, F], CW_, 170, outline=0, ow=1)
    L.line([F, T], CW_, 255, outline=0, ow=1)
    lit = c["lit"]
    if lit:
        L.line([T, E], CW_ + (1 if lit == 2 else 0), 235, 255, outline=0, ow=1)
    return F, T, E


def draw_bow(L, bx, by, k):
    L.poly([(bx, by), (bx - 19 * k, by - 11), (bx - 20 * k, by + 11)], 190, 255, outline=0, ow=3)
    L.poly([(bx, by), (bx + 19 * k, by - 13), (bx + 20 * k, by + 11)], 190, 255, outline=0, ow=3)
    L.ell((bx - 5 * k, by - 5, bx + 5 * k, by + 5), 230, 255, outline=0, ow=3)


PSI = 62   # ears sit +-62 degrees around the head: wide, and close together when seen from the front


def head(L, hx, hy, yaw):
    th = math.radians(yaw)
    cth, sth = math.cos(th), math.sin(th)
    X = lambda psi, r: hx + r * RH * math.sin(th + math.radians(psi))
    vis = lambda psi: math.cos(th + math.radians(psi))
    for psi in sorted((PSI, -PSI), key=vis):
        c = vis(psi)
        ex = X(psi, 0.72)
        wb = 24 * HS * (0.6 + 0.4 * cth)
        lum = 245 if c > 0 else 215
        tipx = ex + 7 * math.sin(th + math.radians(psi))
        L.poly([(ex - wb, hy - 14 * HS), (tipx, hy - 64 * HS), (ex + wb, hy - 14 * HS)], lum)
    # the bow sits on the character's left ear: the viewer's right ear when she faces the viewer
    bc = vis(PSI)
    bex = X(PSI, 0.72)
    bx = bex + 12 * cth - 12 * sth
    by = hy - (40 - 8 * sth) * HS
    bk = 1 - 0.3 * sth
    if bc <= 0:
        draw_bow(L, bx, by, bk)
    L.ell((hx - RH, hy - 42 * HS, hx + RH, hy + 40 * HS), 245)
    for psi in (PSI, -PSI):
        c = vis(psi)
        if c > 0.15:
            ex = X(psi, 0.72)
            wi = 10 * HS * (0.6 + 0.4 * cth)
            L.poly([(ex - wi, hy - 24 * HS), (ex + 2, hy - 52 * HS), (ex + wi, hy - 24 * HS)], 120)
    if bc > 0:
        draw_bow(L, bx, by, bk)
    for psi in (-34, 34):
        c = vis(psi)
        if c > 0.12:
            ex = X(psi, 0.85)
            hw = 7 * max(0.45, c)
            L.ell((ex - hw, hy - 10 * HS, ex + hw, hy + 12 * HS), 0)
    nx = hx + 0.96 * RH * sth
    nw = 7.5 * max(0.55, cth)
    L.ell((nx - nw, hy + 6 * HS, nx + nw, hy + 16 * HS), 110)
    for psi in (62, -62):
        c = vis(psi)
        if c > 0.1:
            bxw = X(psi, 0.97)
            txw = hx + (0.97 * RH + 36) * math.sin(th + math.radians(psi))
            for dy, ey in ((-8, -20), (4, 4), (16, 28)):
                L.line([(bxw, hy + dy * HS), (txw, hy + ey * HS)], 4, 245)


def mouth(g):
    return (g["hx"] + 12 + 29 * g["sb"], g["hy"] + 19)


def geometry(pose):
    yaw = pose.get("yaw", 90)
    th = math.radians(yaw)
    cb, sb = math.cos(th), math.sin(th)
    legs = pose["legs"]
    if "py" in pose:
        py = pose["py"]
    else:
        py = GROUND - max(leg((0, 0), *l)[1][1] for l in legs if l[0] != "ik")
    top = py - 72
    lean = pose.get("lean", 0) * sb
    nx = CX + lean
    return dict(yaw=yaw, cb=cb, sb=sb, py=py, top=top, nx=nx, hx=nx + 4 * sb, hy=top - 38,
                S_f=(nx + 25 * cb, top + 22), S_n=(nx - 25 * cb, top + 22),
                hip_f=(CX + 14 * cb, py), hip_n=(CX - 14 * cb, py), wT=14 + 11 * cb)


def arm_pts(g, S, spec, idx=0):
    if spec[0] == "fk":
        return arm_fk(S, spec[1], spec[2])
    # pick the elbow that bends away from the body: sideways when facing the viewer, downwards in profile
    sign = 1 if idx == 0 else -1
    best = None
    for side in (-1, 1):
        e, w = two_bone(S, spec[1], UARM, FARM, side)
        score = g["cb"] * sign * (e[0] - S[0]) + g["sb"] * (e[1] - S[1])
        if best is None or score > best[0]:
            best = (score, e, w)
    return best[1], best[2]


def torso_poly(nx, top, cx_bot, py, w, rt=15, rb=5):
    rt = min(rt, w)
    pts = []
    def arc(cx, cy, r, a0, a1):
        for i in range(8):
            a = a0 + (a1 - a0) * i / 7
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    arc(-w + rt, top + rt, rt, math.pi, 1.5 * math.pi)
    arc(w - rt, top + rt, rt, 1.5 * math.pi, 2 * math.pi)
    arc(w - rb, py - rb, rb, 0, 0.5 * math.pi)
    arc(-w + rb, py - rb, rb, 0.5 * math.pi, math.pi)
    out = []
    for x, y in pts:
        out.append((x + cx_bot + (nx - cx_bot) * (py - y) / (py - top), y))
    return out


def leg_pts(g, hip, spec, side):
    if spec[0] == "ik":
        return two_bone(hip, spec[1], THIGH, SHIN, side)
    return leg(hip, *spec)


def draw_pack(L, g, stubs):
    px, py = CX + 9 * g["sb"], g["py"]
    for i in range(stubs):
        x = px - 3 + 3.2 * i
        L.line([(x, py - 14), (x, py - 22)], 2.6, 255, outline=0, ow=1)
    L.rect((px - 6, py - 16, px + 6, py + 2), 110, outline=0, ow=1, radius=1)
    L.rect((px - 6, py - 10, px + 6, py - 7), 215)


def draw_fig(pose):
    L = Layer(FIG_COLS)
    g = geometry(pose)
    cb, sb = g["cb"], g["sb"]
    FAR = int(NEAR - (NEAR - 170) * sb)   # far side is darker in profile, identical to the near side when facing the viewer
    front = pose.get("front")
    far_leg, near_leg = pose["legs"]
    k, f = leg_pts(g, g["hip_f"], far_leg, 1)
    limb(L, [g["hip_f"], k, f], 15, FAR); foot(L, f, FAR, cb, pose.get("twist", 0))
    arms = []
    for idx, (S, lum, w_) in enumerate(((g["S_f"], FAR, 12), (g["S_n"], NEAR, 12))):
        e, w = arm_pts(g, S, pose["arms"][idx], idx)
        arms.append((S, e, w, lum, w_))
    if front != 0:
        S, e, w, lum, w_ = arms[0]
        limb(L, [S, e, w], w_, lum); hand(L, w, lum)
    wT = g["wT"]
    L.poly(torso_poly(g["nx"], g["top"], CX, g["py"], wT), 235, outline=0, ow=2)
    k, f = leg_pts(g, g["hip_n"], near_leg, -1)
    limb(L, [g["hip_n"], k, f], 15, NEAR); foot(L, f, NEAR, cb)
    if pose.get("pack") and sb > 0.8:
        draw_pack(L, g, pose["pack"])
    if front != 1:
        S, e, w, lum, w_ = arms[1]
        limb(L, [S, e, w], w_, lum); hand(L, w, lum)
    head(L, g["hx"], g["hy"], g["yaw"])
    if front is not None:
        S, e, w, lum, w_ = arms[front]
        limb(L, [S, e, w], w_, lum); hand(L, w, lum)
    # lighter and flame
    fl = pose.get("flame")
    if fl:
        fx, fy, size = fl
        L.rect((fx - 5, fy + 9, fx + 5, fy + 30), 130, outline=0, ow=1, radius=2)
        s = 1.0 if size == 1 else 0.72
        L.poly([(fx, fy - 22 * s), (fx - 8 * s, fy + 2), (fx, fy + 11), (fx + 8 * s, fy + 2)], 235, 255, outline=0, ow=2)
        L.poly([(fx, fy - 9 * s), (fx - 3, fy + 3), (fx + 3, fy + 3)], 255, 0)
    # the cigarette is always drawn last, so no hand or arm can ever cover it
    c = pose.get("cig")
    if c:
        M = c["M"] or mouth(g)
        F, T, E = cig_pts(M, c["L"])
        hh = c.get("H") or (pinch_H(M, c["L"]) if c.get("pinch") else None)
        if hh:
            p = pinch_p(c["L"])
            P = (M[0] + p * D[0], M[1] + p * D[1])
            L.line([hh, (P[0] + 1.0 * N[0], P[1] + 1.0 * N[1])], 5, FAR if pose.get("hold") == 0 else NEAR, outline=0, ow=1)
        tap = pose.get("tap")
        if tap:
            q = (M[0] + 0.7 * c["L"] * D[0] - tap[0] * N[0], M[1] + 0.7 * c["L"] * D[1] - tap[0] * N[1])
            L.line([hh, q], 4, FAR, outline=0, ow=1)
        draw_cig(L, M, c)
        if tap and tap[1]:
            for dx, dy, r in tap[1]:
                L.ell((T[0] + dx - r, T[1] + dy - r, T[0] + dx + r, T[1] + dy + r), 150)
    return L.render(mask=True)


def kflex(q):
    q = q % (2 * math.pi)
    if q < math.pi:
        return 6 + 16 * max(0.0, math.sin(2 * q)) if q < math.pi / 2 else 6
    u = (q - math.pi) / math.pi
    return 6 + 58 * math.sin(math.pi * u ** 0.8)


def walk_pose(i, n):
    q = 2 * math.pi * i / n
    def lg(p):
        return (12 + 24 * math.cos(p), kflex(p))
    def am(p):
        return (-22 * math.cos(p) + 2, 12 + 24 * max(0.0, -math.cos(p)))
    near, far = q, q + math.pi
    return dict(legs=[lg(far), lg(near)], arms=[("fk",) + am(far), ("fk",) + am(near)], lean=6, pack=3)


def lerp(a, b, t):
    t = t * t * (3 - 2 * t)
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


_orig_render = Layer.render
LAST = [None]
def _render(self, *a, **k):
    LAST[0] = self
    return _orig_render(self, *a, **k)
Layer.render = _render
IMGS = {}
class FD(dict):
    def __setitem__(self, k, v):
        super().__setitem__(k, v)
        IMGS[k] = LAST[0]
NW = 12
frames = FD()
for i in range(NW):
    frames["w%d" % i] = draw_fig(walk_pose(i, NW))

STAND = [(-7, 5), (7, 5)]
REST_ARMS = [("fk", -4, 14), ("fk", 5, 16)]
FRONT_LEGS = [(4, 3), (-4, 3)]
FRONT_ARMS = [("fk", 5, 4), ("fk", -5, 4)]
frames["settle"] = draw_fig(dict(legs=[(-8, 10), (14, 22)], arms=[("fk", -8, 14), ("fk", 8, 16)], lean=3, pack=3))
frames["rest"] = draw_fig(dict(legs=STAND, arms=REST_ARMS, pack=3))

g0 = geometry(dict(legs=STAND, yaw=90))
REST_F = arm_fk(g0["S_f"], -4, 14)[1]
REST_N = arm_fk(g0["S_n"], 5, 16)[1]
PACK_H = (CX + 9 * 1.0 + 2, g0["py"] - 6)          # hand over the pack in the pocket
M0 = mouth(g0)


def prof(arm_n=REST_ARMS[1], arm_f=REST_ARMS[0], **kw):
    return dict(legs=STAND, arms=[arm_f, arm_n], pack=kw.pop("pack", 3), **kw)


# --- beat 3: take a cigarette from the pack and put it in the mouth
frames["pk1"] = draw_fig(prof(("ik", lerp(REST_N, PACK_H, 0.6))))
frames["pk2"] = draw_fig(prof(("ik", PACK_H), cig=cig_hand((PACK_H[0] + 6, PACK_H[1] - 8), 24, 0), hold=1))
Hm = pinch_H(M0, 24)
H_pk3 = lerp((PACK_H[0] + 6, PACK_H[1] - 8), Hm, 0.5)
frames["pk3"] = draw_fig(prof(("ik", H_pk3), cig=cig_hand(H_pk3, 24, 0), hold=1))
frames["pk4"] = draw_fig(prof(("ik", Hm), cig=cig_mouth(24, 0, True), hold=1))
frames["pk5"] = draw_fig(prof(("ik", lerp(Hm, REST_N, 0.5)), cig=cig_mouth(24, 0), pack=2))
frames["restc"] = draw_fig(prof(cig=cig_mouth(24, 0), pack=2))

# --- beat 4: lighter and first puff
F0, T0, E0 = cig_pts(M0, 24)
FL = (T0[0] + 3, T0[1] - 4)
HL = (FL[0], FL[1] + 29)
for j in range(1, 4):
    frames["lt%d" % j] = draw_fig(prof(arm_f=("ik", lerp(REST_F, HL, j / 3)), cig=cig_mouth(24, 0), pack=2))
for n, lit, size in (("fA", 0, 1), ("fB", 0, 2), ("fC", 1, 1), ("fD", 1, 2)):
    frames[n] = draw_fig(prof(arm_f=("ik", HL), cig=cig_mouth(24, lit), flame=(FL[0], FL[1], size), pack=2))
for j in range(1, 3):
    frames["ld%d" % j] = draw_fig(prof(arm_f=("ik", lerp(HL, REST_F, j / 2)), cig=cig_mouth(24, 1), pack=2))
frames["litrest"] = draw_fig(prof(cig=cig_mouth(24, 1), pack=2))

# --- beat 5: turn to the viewer (side, three-quarter, front)
frames["t1"] = draw_fig(dict(legs=[(-4, 5), (4, 5)], arms=REST_ARMS, cig=cig_mouth(24, 1), yaw=58, pack=2))
frames["t2"] = draw_fig(dict(legs=[(0, 4), (0, 4)], arms=FRONT_ARMS, cig=cig_mouth(24, 1), yaw=28))

# --- beat 6: frontal smoking
gf = geometry(dict(legs=FRONT_LEGS, yaw=0))
MF = mouth(gf)
S_f = gf["S_f"]
REST_FA = arm_fk(S_f, 5, 4)[1]
H_LOW = (S_f[0] + 14, S_f[1] + 72)
FR = dict(legs=FRONT_LEGS, yaw=0)


def fr(arm=None, **kw):
    arms = [FRONT_ARMS[0] if arm is None else arm, FRONT_ARMS[1]]
    return draw_fig(dict(FR, arms=arms, front=0 if arm is not None else None, **kw))


L0 = 24
frames["idle"] = fr(cig=cig_mouth(L0, 1))
frames["pm"] = fr(("ik", lerp(REST_FA, pinch_H(MF, L0), 0.6)), cig=cig_mouth(L0, 1), hold=0)
for L_ in (24, 21, 18, 15, 12, 9, 6):
    H = pinch_H(MF, L_)
    frames["mB%d" % L_] = fr(("ik", H), cig=cig_mouth(L_, 2, True), hold=0)
# carrying the cigarette down: mid height, then low
for L_ in (18, 12, 6):
    Hmid = lerp(H_LOW, pinch_H(MF, L_, 9), 0.55)
    frames["cm%d" % L_] = fr(("ik", Hmid), cig=cig_hand(Hmid, L_, 1), hold=0)
    frames["cl%d" % L_] = fr(("ik", H_LOW), cig=cig_hand(H_LOW, L_, 1), hold=0)
# the tap, once, at low height with length 18
ASH = [[(4, 8, 1.8), (-2, 14, 1.4)], [(5, 17, 1.8), (-3, 26, 1.4), (7, 28, 1.2)]]
frames["tapA"] = fr(("ik", H_LOW), cig=cig_hand(H_LOW, 18, 1), hold=0, tap=(14, None))
frames["tapB"] = fr(("ik", H_LOW), cig=cig_hand(H_LOW, 18, 1), hold=0, tap=(4, ASH[0]))
frames["tapC"] = fr(("ik", H_LOW), cig=cig_hand(H_LOW, 18, 1), hold=0, tap=(12, ASH[1]))

# --- beat 7: throw the butt (to the viewer's right, from the cigarette hand)
H_T1 = (S_f[0] + 8, S_f[1] + 70)
H_T2 = (S_f[0] + 12, S_f[1] + 14)
H_T3 = (S_f[0] + 54, S_f[1] + 30)
frames["thr1"] = fr(("ik", H_T1), cig=cig_hand(H_T1, 6, 1), hold=0)
frames["thr2"] = fr(("ik", H_T2))
frames["thr3"] = fr(("ik", H_T3))

# --- beat 8: stomp it out, three times, with a small twist
BUTT_X = CX + 66
py_f = GROUND - 76      # she bends her knees a little to reach the butt, out to the side


def stomp(y, twist=0):
    return draw_fig(dict(yaw=0, legs=[("ik", (BUTT_X, y)), ("ik", (CX - 16, GROUND - 1))], arms=FRONT_ARMS, py=py_f, twist=twist))


frames["stU"] = stomp(GROUND - 26)
frames["stM"] = stomp(GROUND - 12)
frames["stD"] = stomp(GROUND)
frames["stT1"] = stomp(GROUND, 24)
frames["stT2"] = stomp(GROUND, -24)
frames["end"] = draw_fig(dict(yaw=0, legs=FRONT_LEGS, arms=FRONT_ARMS))


def puff(M):
    Lr = Layer(FIG_COLS)
    for dx, dy, r, lum in ((2, -8, 4, 200), (7, -20, 6, 170), (4, -34, 8, 130), (9, -50, 9, 90)):
        Lr.ell((M[0] + dx - r, M[1] + dy - r, M[0] + dx + r, M[1] + dy + r), lum)
    return Lr.render(gamma=1.0)


def butt(cx, cy, ang, lit):
    Lr = Layer(FIG_COLS)
    t = math.radians(ang)
    d = (math.cos(t), math.sin(t))
    P = lambda q: (cx + q * d[0], cy + q * d[1])
    Lr.line([P(-9), P(-4)], 6, 190, outline=0, ow=1)
    Lr.line([P(-4), P(5)], 6, 255, outline=0, ow=1)
    Lr.line([P(5), P(9)], 6, 235, 255 if lit else 0, outline=0, ow=1)
    return Lr.render()


# the thrown butt: ASCII tumbling frames along an outward arc, then lying on the ground
BX0, BY0 = H_T2[0] + 6, H_T2[1] - 6
BY_G = GROUND - 4
NB = 8
for i in range(NB):
    t_ = (i + 0.5) / NB
    x_ = BX0 + (BUTT_X - BX0) * t_
    y_ = BY0 + (BY_G - BY0) * t_ - 4 * 70 * t_ * (1 - t_)
    frames["bf%d" % i] = butt(x_, y_, 60 * i, True)
frames["bl"] = butt(BUTT_X, BY_G, 14, True)
frames["bg"] = butt(BUTT_X, BY_G, 14, False)
frames["puffP"] = puff(M0)
frames["puffF"] = puff(MF)
frames["sign"] = sign()
Hb = H_T2
meta = dict(butt_start=(Hb[0], Hb[1]), butt_end=(BUTT_X, GROUND + 4))
json.dump(dict(frames=frames, meta=meta), open('frames5.json', 'w'))
print(len(frames), "frames", sum(len("".join(v)) for v in frames.values()) // 1000, "KB", meta)

if len(sys.argv) > 1:
    from PIL import Image
    ims = []
    for spec in sys.argv[1:]:
        name, _, crop = spec.partition('@')
        Ly = IMGS[name]
        lum = Ly.lum.resize((Ly.lum.width // SS * 3, Ly.lum.height // SS * 3), Image.BOX)
        red = Ly.red.resize(lum.size, Image.BOX)
        im = Image.merge("RGB", (Image.eval(lum, lambda v: v), Image.eval(lum, lambda v: v), Image.eval(lum, lambda v: v)))
        px, rp, lp = im.load(), red.load(), lum.load()
        for y in range(im.height):
            for x in range(im.width):
                if rp[x, y] > 60 and lp[x, y] > 30:
                    px[x, y] = (255, 60, 50)
        if crop:
            x0, y0, x1, y1 = [int(v) * 3 for v in crop.split(':')]
            im = im.crop((x0, y0, x1, y1))
        ims.append(im)
    W = sum(i.width for i in ims) + 10 * len(ims); H = max(i.height for i in ims)
    sheet = Image.new("RGB", (W, H), (60, 60, 90))
    x = 0
    for i in ims:
        sheet.paste(i, (x, 0)); x += i.width + 10
    sheet.save('dbg.png')
