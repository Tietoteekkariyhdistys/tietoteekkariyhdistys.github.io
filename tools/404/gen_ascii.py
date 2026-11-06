import math, json, html, sys
from PIL import Image, ImageDraw, ImageFont

CW, CH = 6, 10          # cell size in px (matches a monospace cell, ~0.6 wide : 1 high)
K = 2                   # resolution factor over the base design grid
SSB = 4                 # supersampling per cell
SS = K * SSB            # design units -> image px
RAMP = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
ROWS = 28 * K


class Layer:
    def __init__(self, cols):
        self.cols = cols
        self.w, self.h = cols // K * CW, ROWS // K * CH
        self.lum = Image.new("L", (self.w * SS, self.h * SS), 0)
        self.red = Image.new("L", (self.w * SS, self.h * SS), 0)
        self.dl = ImageDraw.Draw(self.lum)
        self.dr = ImageDraw.Draw(self.red)

    def s(self, v):
        return [x * SS for x in v] if isinstance(v, (list, tuple)) else v * SS

    def poly(self, pts, lum=255, red=0, outline=0, ow=0):
        p = [(x * SS, y * SS) for x, y in pts]
        if ow:
            self.dl.line(p + [p[0]], fill=outline, width=ow * SS, joint="curve")
            self.dr.line(p + [p[0]], fill=0, width=ow * SS, joint="curve")
        self.dl.polygon(p, fill=lum)
        self.dr.polygon(p, fill=red)

    def ell(self, box, lum=255, red=0, outline=None, ow=0):
        b = self.s(box)
        if ow:
            e = ow * SS
            ob = (b[0] - e, b[1] - e, b[2] + e, b[3] + e)
            self.dl.ellipse(ob, fill=outline)
            self.dr.ellipse(ob, fill=0)
        self.dl.ellipse(b, fill=lum)
        self.dr.ellipse(b, fill=red)

    def rect(self, box, lum=255, red=0, outline=None, ow=0, radius=0):
        b = self.s(box)
        if ow:
            e = ow * SS
            ob = (b[0] - e, b[1] - e, b[2] + e, b[3] + e)
            if radius:
                self.dl.rounded_rectangle(ob, radius=radius * SS + e, fill=outline)
                self.dr.rounded_rectangle(ob, radius=radius * SS + e, fill=0)
            else:
                self.dl.rectangle(ob, fill=outline)
                self.dr.rectangle(ob, fill=0)
        if radius:
            self.dl.rounded_rectangle(b, radius=radius * SS, fill=lum)
            self.dr.rounded_rectangle(b, radius=radius * SS, fill=red)
        else:
            self.dl.rectangle(b, fill=lum)
            self.dr.rectangle(b, fill=red)

    def line(self, pts, w, lum=255, red=0, outline=None, ow=0):
        p = [(x * SS, y * SS) for x, y in pts]
        if ow:
            self.dl.line(p, fill=outline, width=int(round((w + 2 * ow) * SS)), joint="curve")
            self.dr.line(p, fill=0, width=int(round((w + 2 * ow) * SS)), joint="curve")
        self.dl.line(p, fill=lum, width=int(round(w * SS)), joint="curve")
        self.dr.line(p, fill=red, width=int(round(w * SS)), joint="curve")
        r = w * SS / 2
        for x, y in (p[0], p[-1]):
            self.dl.ellipse((x - r, y - r, x + r, y + r), fill=lum)
            self.dr.ellipse((x - r, y - r, x + r, y + r), fill=red)

    def text(self, xy, s, size, lum=255, font="arialbd.ttf", anchor="mm"):
        f = ImageFont.truetype("C:/Windows/Fonts/" + font, size * SS)
        self.dl.text((xy[0] * SS, xy[1] * SS), s, font=f, fill=lum, anchor=anchor)

    def render(self, gamma=0.85, mask=False):
        lum = self.lum.resize((self.cols, ROWS), Image.BOX)
        red = self.red.resize((self.cols, ROWS), Image.BOX)
        lp, rp = lum.load(), red.load()
        out = []
        for y in range(ROWS):
            chars, isred, ink = [], [], []
            for x in range(self.cols):
                v = (lp[x, y] / 255) ** gamma
                ch = RAMP[min(len(RAMP) - 1, int(v * len(RAMP)))]
                chars.append(ch)
                ink.append(ch != " ")
                isred.append(rp[x, y] > 70 and lp[x, y] > 40 and ch != " ")
            m = [False] * self.cols
            if mask:
                idx = [i for i, v in enumerate(ink) if v]
                for a_, b_ in zip(idx, idx[1:]):
                    if b_ - a_ <= 6:
                        for i in range(a_, b_ + 1):
                            m[i] = True
                for i in idx:
                    m[i] = True
            line, cur, buf = "", None, ""
            for i in range(self.cols):
                key = ("m" if m[i] else "") + (" r" if isred[i] else "")
                key = key.strip()
                if key != cur:
                    if buf:
                        line += ('<span class="%s">%s</span>' % (cur, buf)) if cur else buf
                    cur, buf = key, ""
                buf += html.escape(chars[i], quote=False)
            if buf:
                line += ('<span class="%s">%s</span>' % (cur, buf)) if cur else buf
            out.append(line.rstrip() if "<" not in line else line)
        return out


FIG_COLS = 31 * K
SIGN_COLS = 30 * K
CX = 86


def figure(pose):
    L = Layer(FIG_COLS)
    cx = CX
    arm = lambda pts, w=8: L.line(pts, w, 235, outline=0, ow=2)
    hy = 94          # head centre y
    hip = (cx, 204)
    L.line([(cx, 130), hip], 9, 235)
    lf, rf = pose["feet"]
    L.line([hip, (cx + lf[0], lf[1])], 9, 235)
    L.line([hip, (cx + rf[0], rf[1])], 9, 235)
    for foot in (lf, rf):
        L.ell((cx + foot[0] - 11, foot[1] - 3, cx + foot[0] + 11, foot[1] + 3), 235)
    for pts in pose["arms"]:
        arm([(cx + a, b) for a, b in pts])
    for hx, hy2 in pose.get("hands", []):
        L.ell((cx + hx - 7, hy2 - 7, cx + hx + 7, hy2 + 7), 235, outline=0, ow=2)
    # head: ears, face, bow
    L.poly([(cx - 56, 80), (cx - 50, 30), (cx - 14, 58)], 245)
    L.poly([(cx + 56, 80), (cx + 50, 30), (cx + 14, 58)], 245)
    L.poly([(cx - 46, 66), (cx - 43, 42), (cx - 26, 58)], 120)
    L.ell((cx - 58, hy - 42, cx + 58, hy + 40), 245)
    L.poly([(cx - 46, 66), (cx - 43, 42), (cx - 26, 58)], 120)
    L.poly([(cx + 46, 66), (cx + 43, 42), (cx + 26, 58)], 120)
    bx, by = cx + 40, 38
    L.poly([(bx, by), (bx - 24, by - 16), (bx - 26, by + 16)], 190, 255, outline=0, ow=3)
    L.poly([(bx, by), (bx + 24, by - 18), (bx + 26, by + 16)], 190, 255, outline=0, ow=3)
    L.ell((bx - 7, by - 7, bx + 7, by + 7), 230, 255, outline=0, ow=3)
    # eyes, nose, whiskers
    L.ell((cx - 32, hy - 8, cx - 19, hy + 10), 0)
    L.ell((cx + 19, hy - 8, cx + 32, hy + 10), 0)
    L.ell((cx - 9, hy + 6, cx + 9, hy + 16), 110)
    for dy, ey in ((hy - 8, hy - 16), (hy + 4, hy + 4), (hy + 16, hy + 22)):
        L.line([(cx - 54, dy), (cx - 80, ey)], 3, 240)
        L.line([(cx + 54, dy), (cx + 80, ey)], 3, 240)
    # cigarette from the mouth
    if pose.get("cig"):
        cy = hy + 24
        L.rect((cx + 14, cy, cx + 24, cy + 7), 150, outline=0, ow=2)
        L.rect((cx + 24, cy, cx + 66, cy + 7), 240, outline=0, ow=2)
        if pose.get("ember"):
            L.rect((cx + 66, cy, cx + 76, cy + 7), 215, 255, outline=0, ow=2)
    if pose.get("flame"):
        fx, fy = cx + 84, hy + 20
        L.poly([(fx, fy - 22), (fx - 9, fy + 2), (fx, fy + 12), (fx + 9, fy + 2)], 235, 255, outline=0, ow=2)
        L.poly([(fx, fy - 9), (fx - 3, fy + 3), (fx + 3, fy + 3)], 255, 0)
    return L.render(mask=True)


def smoke(phase):
    L = Layer(FIG_COLS)
    pts = []
    for i in range(0, 41):
        t = i / 40
        y = 108 - t * 100
        x = CX + 84 + 12 * math.sin(t * 6.5 + phase) + t * 10
        pts.append((x, y))
    for i in range(len(pts) - 1):
        t = i / len(pts)
        lum = int(190 * (1 - t) ** 1.2) + 20
        L.line([pts[i], pts[i + 1]], 3 + int(4 * t), lum)
    return L.render(gamma=1.0)


def sign():
    L = Layer(SIGN_COLS)
    # pole and base
    L.rect((84, 150, 96, 276), 215)
    L.rect((64, 270, 116, 280), 235)
    # timetable plate
    L.rect((58, 164, 122, 210), 235, outline=0, ow=2)
    L.rect((63, 169, 117, 205), 0)
    for yy in (177, 187, 197):
        L.rect((68, yy, 112, yy + 3), 200)
    # board
    L.rect((10, 6, 170, 158), 250, outline=0, ow=0, radius=10)
    L.rect((18, 14, 162, 150), 0, radius=6)
    # bus pictogram
    L.rect((28, 26, 152, 86), 240, radius=12)
    for x0 in (36, 58, 80, 102):
        L.rect((x0, 34, x0 + 17, 54), 0, radius=2)
    L.rect((124, 34, 146, 66), 0, radius=3)
    L.rect((28, 70, 152, 74), 0)
    L.ell((44, 78, 68, 102), 240, outline=0, ow=3)
    L.ell((52, 86, 60, 94), 0)
    L.ell((112, 78, 136, 102), 240, outline=0, ow=3)
    L.ell((120, 86, 128, 94), 0)
    L.text((90, 126), "404", 40, 255, "ariblk.ttf")
    return L.render()


poses = {
    "fa": dict(feet=[(-34, 278), (30, 278)], arms=[[(0, 150), (-14, 174), (-26, 200)], [(0, 150), (14, 172), (26, 196)]], hands=[(-26, 200), (26, 196)]),
    "fb": dict(feet=[(-14, 278), (14, 278)], arms=[[(0, 150), (-6, 176), (-12, 204)], [(0, 150), (6, 176), (12, 204)]], hands=[(-12, 204), (12, 204)]),
    "stand": dict(feet=[(-18, 278), (18, 278)], arms=[[(0, 150), (-12, 176), (-20, 206)], [(0, 150), (14, 176), (22, 206)]], hands=[(-20, 206), (22, 206)]),
    "light": dict(feet=[(-18, 278), (18, 278)], arms=[[(0, 150), (-12, 176), (-20, 206)], [(0, 150), (40, 170), (88, 140)]], hands=[(-20, 206), (88, 140)], cig=True, flame=True),
    "smoke": dict(feet=[(-18, 278), (18, 278)], arms=[[(0, 150), (-12, 176), (-20, 206)], [(0, 150), (36, 172), (16, 188)]], hands=[(-20, 206), (16, 188)], cig=True, ember=True),
}

frames = {k: figure(v) for k, v in poses.items()}
frames["sign"] = sign()
frames["smoke1"] = smoke(0.0)
frames["smoke2"] = smoke(2.1)
frames["smoke3"] = smoke(4.2)
json.dump(frames, open(sys.argv[1], "w"))
if len(sys.argv) > 2:
    import re
    for name in sys.argv[2:]:
        print("=====", name)
        for ln in frames[name]:
            print(re.sub(r"<[^>]+>", "", ln).replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&"))
