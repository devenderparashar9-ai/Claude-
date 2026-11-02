import math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops, ImageFont, ImageEnhance

W, H = 1300, 2310      # still size (frame is 1080x1920, extra room for camera moves)
SS = 2                 # supersampling
FONT_B = "fonts/DevaBold.ttf"

def hexc(h, a=255):
    h = h.lstrip('#')
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

def mix(c1, c2, t):
    c1, c2 = hexc(c1) if isinstance(c1, str) else c1, hexc(c2) if isinstance(c2, str) else c2
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(4))

def shade(c, f):
    c = hexc(c) if isinstance(c, str) else c
    return tuple(max(0, min(255, int(v * f))) for v in c[:3]) + (c[3],)

def C(c):
    return hexc(c) if isinstance(c, str) else c


class Canvas:
    def __init__(self, bg="#000000"):
        self.img = Image.new("RGBA", (W * SS, H * SS), C(bg))
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.glows = []

    # ---- primitives (logical coords) ----
    def p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def ell(self, cx, cy, rx, ry, fill=None, outline=None, w=0):
        self.d.ellipse([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS],
                       fill=C(fill) if fill else None, outline=C(outline) if outline else None, width=int(w * SS))

    def poly(self, pts, fill=None, outline=None, w=0):
        self.d.polygon(self.p(pts), fill=C(fill) if fill else None)
        if outline:
            self.line(pts + [pts[0]], outline, w)

    def line(self, pts, fill, w=2, joint=True):
        self.d.line(self.p(pts), fill=C(fill), width=max(1, int(w * SS)), joint="curve" if joint else None)
        if joint and w > 4:
            for x, y in pts:
                self.ell(x, y, w / 2, w / 2, fill)

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, w=0, r=0):
        if r:
            self.d.rounded_rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], radius=r * SS,
                                     fill=C(fill) if fill else None, outline=C(outline) if outline else None, width=int(w * SS))
        else:
            self.d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], fill=C(fill) if fill else None,
                             outline=C(outline) if outline else None, width=int(w * SS))

    def arc(self, cx, cy, rx, ry, a0, a1, fill, w):
        self.d.arc([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], a0, a1, fill=C(fill), width=max(1, int(w * SS)))

    def chord(self, cx, cy, rx, ry, a0, a1, fill):
        self.d.chord([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], a0, a1, fill=C(fill))

    def pieslice(self, cx, cy, rx, ry, a0, a1, fill):
        self.d.pieslice([(cx - rx) * SS, (cy - ry) * SS, (cx + rx) * SS, (cy + ry) * SS], a0, a1, fill=C(fill))

    def vgrad(self, x0, y0, x1, y1, c0, c1):
        c0, c1 = C(c0), C(c1)
        n = int((y1 - y0) * SS)
        for i in range(n):
            t = i / max(1, n - 1)
            col = tuple(int(c0[k] + (c1[k] - c0[k]) * t) for k in range(4))
            self.d.line([(x0 * SS, y0 * SS + i), (x1 * SS, y0 * SS + i)], fill=col)

    def rgrad(self, cx, cy, r, c0, c1, steps=40):
        for i in range(steps, 0, -1):
            t = i / steps
            self.ell(cx, cy, r * t, r * t, mix(c0, c1, t))

    def glow(self, cx, cy, r, color, k=1.0):
        self.glows.append((cx, cy, r, C(color), k))

    def glow_layer(self):
        import numpy as np
        f = 4
        gw, gh = W // f, H // f
        buf = np.zeros((gh, gw, 3), np.float32)
        yy, xx = np.mgrid[0:gh, 0:gw]
        for cx, cy, r, col, k in self.glows:
            sig = max(1.0, r / f / 2.0)
            x0, x1 = int(max(0, cx / f - 3 * sig)), int(min(gw, cx / f + 3 * sig + 1))
            y0, y1 = int(max(0, cy / f - 3 * sig)), int(min(gh, cy / f + 3 * sig + 1))
            if x0 >= x1 or y0 >= y1: continue
            d2 = (xx[y0:y1, x0:x1] - cx / f) ** 2 + (yy[y0:y1, x0:x1] - cy / f) ** 2
            g = np.exp(-d2 / (2 * sig * sig))[..., None] * k
            buf[y0:y1, x0:x1] += g * np.array(col[:3], np.float32)
        buf = np.clip(buf, 0, 255).astype(np.uint8)
        return Image.fromarray(buf).resize((W, H), Image.BILINEAR)

    def defocus(self, radius=16):
        g = self.glow_layer().resize((W * SS, H * SS), Image.BILINEAR)
        base = ImageChops.screen(self.img.convert("RGB"), g)
        base = base.resize((W // 2, H // 2), Image.BILINEAR).filter(ImageFilter.GaussianBlur(radius / 2))
        base = ImageEnhance.Brightness(base).enhance(0.8)
        self.img = base.resize((W * SS, H * SS), Image.BILINEAR).convert("RGBA")
        self.d = ImageDraw.Draw(self.img, "RGBA")
        self.glows = []
        self._defocused = True

    def text(self, x, y, s, size, fill, anchor="mm", stroke=0, stroke_fill="#000000"):
        f = ImageFont.truetype(FONT_B, int(size * SS), layout_engine=ImageFont.Layout.RAQM)
        self.d.text((x * SS, y * SS), s, font=f, fill=C(fill), anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=C(stroke_fill))

    def finish(self, vignette=0.55, warm=True, glow_blur=18):
        img = self.img.convert("RGB").resize((W, H), Image.LANCZOS)
        img = ImageChops.screen(img, self.glow_layer())
        if vignette:
            v = Image.new("L", (W // 10, H // 10), 0)
            vd = ImageDraw.Draw(v)
            for i in range(30, 0, -1):
                t = i / 30
                vd.ellipse([W / 20 - W / 10 * t * 0.95, H / 20 - H / 10 * t * 0.75, W / 20 + W / 10 * t * 0.95, H / 20 + H / 10 * t * 0.75],
                           fill=int(255 * (1 - t) ** 0.6))
            v = v.resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(40))
            dark = Image.new("RGB", (W, H), (10, 4, 2))
            mask = Image.eval(v, lambda a: int(255 - (255 - a) * 1) if False else int((255 - a) * vignette))
            img = Image.composite(dark, img, Image.eval(v, lambda a: int(min(255, (255 - a)) * vignette)))
        if warm:
            r, g2, b = img.split()
            r = r.point(lambda v: min(255, int(v * 1.04 + 4)))
            b = b.point(lambda v: int(v * 0.92))
            img = Image.merge("RGB", (r, g2, b))
        return img


# ---------------- elements ----------------
def diya(cv, x, y, s=1.0, glow=True):
    cv.ell(x, y + 6 * s, 30 * s, 6 * s, "#00000060")
    cv.chord(x, y - 4 * s, 28 * s, 18 * s, 0, 180, "#a8501e")
    cv.ell(x, y - 4 * s, 28 * s, 6 * s, "#d9762e")
    cv.ell(x, y - 4 * s, 20 * s, 4 * s, "#5a2a0c")
    # flame
    cv.poly([(x + 10 * s, y - 8 * s), (x + 6 * s, y - 44 * s), (x + 18 * s, y - 14 * s)], "#ffb02e")
    cv.ell(x + 12 * s, y - 14 * s, 6 * s, 7 * s, "#ffb02e")
    cv.poly([(x + 11 * s, y - 10 * s), (x + 9 * s, y - 32 * s), (x + 15 * s, y - 14 * s)], "#fff3b0")
    if glow:
        cv.glow(x + 10 * s, y - 22 * s, 70 * s, "#ff9a2a", 0.9)
        cv.glow(x + 10 * s, y - 22 * s, 26 * s, "#ffe3a0", 1.0)


def marigold_string(cv, x0, y0, x1, y1, sag=40, n=24, r=13):
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + math.sin(t * math.pi) * sag
        col = "#ff8c00" if i % 2 else "#ffc20e"
        cv.ell(x, y, r, r, shade(col, 0.75))
        cv.ell(x - 2, y - 2, r * 0.8, r * 0.8, col)


def toran(cv, x0, x1, y, n=9):
    marigold_string(cv, x0, y, x1, y, sag=10, n=30, r=11)
    for i in range(n):
        x = x0 + (x1 - x0) * (i + 0.5) / n
        L = 70 if i % 2 else 110
        for k in range(int(L / 20)):
            col = "#ff8c00" if k % 2 else "#ffc20e"
            cv.ell(x, y + 18 + k * 20, 10, 10, col)
        cv.poly([(x - 10, y + 18 + L), (x + 10, y + 18 + L), (x, y + 50 + L)], "#3f8f2a")


def fairy_lights(cv, x0, y0, x1, y1, sag=60, n=26, cols=("#ffe08a", "#ff9ad5", "#9ae0ff", "#ffd04a")):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t + math.sin(t * math.pi) * sag))
    cv.line(pts, "#2a1a10", 2, joint=False)
    for i, (x, y) in enumerate(pts):
        c = cols[i % len(cols)]
        cv.ell(x, y + 6, 5, 7, c)
        cv.glow(x, y + 6, 22, c, 0.9)


def rangoli(cv, x, y, R=230, sy=0.42):
    cols = ["#e8114f", "#ff8c00", "#ffd400", "#21a366", "#1e6fd9", "#8e2bd6", "#ffffff"]
    rings = [(1.0, 16, 0), (0.82, 12, 1), (0.64, 16, 2), (0.47, 10, 3), (0.3, 8, 4), (0.15, 6, 5)]
    cv.ell(x, y, R * 1.05, R * 1.05 * sy, "#ffffffcc")
    for rr, n, ci in rings:
        for i in range(n):
            a = 2 * math.pi * i / n
            px, py = x + math.cos(a) * R * rr * 0.86, y + math.sin(a) * R * rr * 0.86 * sy
            pr = R * rr * 0.22
            cv.ell(px, py, pr, pr * sy * 1.2, cols[(ci + i % 2) % len(cols)])
        cv.ell(x, y, R * rr * 0.7, R * rr * 0.7 * sy, cols[(ci + 3) % len(cols)])
    cv.ell(x, y, R * 0.08, R * 0.08 * sy, "#ffffff")


def peanut(cv, x, y, s=1.0, col="#b5653a", ang=0):
    dx, dy = math.cos(ang) * 7 * s, math.sin(ang) * 7 * s
    cv.ell(x - dx, y - dy, 9 * s, 8 * s, shade(col, 0.8))
    cv.ell(x + dx, y + dy, 9 * s, 8 * s, shade(col, 0.8))
    cv.ell(x - dx - 1, y - dy - 2, 7 * s, 6 * s, col)
    cv.ell(x + dx - 1, y + dy - 2, 7 * s, 6 * s, col)


def peanut_pile(cv, x, y, rx, ry, n=60, s=1.0, col="#a9542e", seed=1):
    rnd = random.Random(seed)
    for i in range(n):
        a = rnd.random() * 2 * math.pi
        r = rnd.random() ** 0.5
        px, py = x + math.cos(a) * rx * r, y + math.sin(a) * ry * r - (1 - r) * ry * 0.6
        c = shade(col, 0.85 + rnd.random() * 0.3)
        peanut(cv, px, py, s, c, rnd.random() * 3)


def steel_bowl(cv, x, y, rx, ry, depth):
    cv.ell(x, y + depth + 6, rx * 0.9, ry * 0.4, "#00000055")
    cv.chord(x, y, rx, depth, 0, 180, "#9aa3ab")
    cv.chord(x, y, rx * 0.9, depth * 0.85, 0, 180, "#c7cfd6")
    cv.ell(x, y, rx, ry, "#dfe5ea")
    cv.ell(x, y, rx * 0.9, ry * 0.85, "#7c858d")


def katli(cv, x, y, s=1.0, col="#ead7ae", vark=True, rot=False):
    pts = [(x, y - 26 * s), (x + 40 * s, y), (x, y + 26 * s), (x - 40 * s, y)]
    cv.poly([(px, py + 7 * s) for px, py in pts], shade(col, 0.72))
    cv.poly(pts, col)
    if vark:
        cv.poly([(x, y - 21 * s), (x + 32 * s, y), (x, y + 21 * s), (x - 32 * s, y)], mix(col, "#ffffff", 0.45))
        cv.line([(x - 18 * s, y - 4 * s), (x + 4 * s, y - 14 * s)], "#ffffffcc", 2 * s)
    if rot:
        cv.ell(x - 10 * s, y + 3 * s, 9 * s, 5 * s, "#4f6b2acc")
        cv.ell(x + 14 * s, y - 4 * s, 7 * s, 4 * s, "#3a3a1acc")


def katli_tray(cv, x, y, cols, rows, s=1.0, col="#ead7ae", vark=True, rot=False):
    for r in range(rows):
        for c in range(cols):
            off = 40 * s if r % 2 else 0
            katli(cv, x + c * 80 * s + off - cols * 40 * s, y + r * 28 * s, s, col, vark, rot)


def sweet_box(cv, x, y, s=1.0, rotten=False, open_=True):
    w, h = 300 * s, 70 * s
    cv.ell(x, y + h + 30 * s, w * 1.05, 40 * s, "#00000050")
    # box body
    cv.poly([(x - w, y), (x + w, y), (x + w * 0.92, y + h), (x - w * 0.92, y + h)], "#7a0d1e")
    cv.line([(x - w * 0.96, y + h * 0.5), (x + w * 0.96, y + h * 0.5)], "#e3b23c", 6 * s)
    if open_:
        # lid behind
        cv.poly([(x - w, y), (x + w, y), (x + w * 1.02, y - 230 * s), (x - w * 1.02, y - 230 * s)], "#8f1226")
        cv.poly([(x - w * 0.9, y - 12 * s), (x + w * 0.9, y - 12 * s), (x + w * 0.92, y - 215 * s), (x - w * 0.92, y - 215 * s)], "#b3162f")
        cv.rect(x - w * 0.92, y - 215 * s, x + w * 0.92, y - 12 * s, None, "#e3b23c", 5 * s)
        cv.text(x, y - 120 * s, "स्वर्ण मिष्ठान", 46 * s, "#f3cf6a")
        # inside top surface
        cv.poly([(x - w, y), (x + w, y), (x + w * 0.95, y + 40 * s), (x - w * 0.95, y + 40 * s)], "#d9c08a" if not rotten else "#6b5a2c")
        katli_tray(cv, x, y + 6 * s, 7, 2, s * 0.85, "#ead7ae" if not rotten else "#8e8a52", vark=not rotten, rot=rotten)
    else:
        cv.poly([(x - w, y), (x + w, y), (x + w, y - 40 * s), (x - w, y - 40 * s)], "#8f1226")
        cv.text(x, y - 18 * s, "स्वर्ण मिष्ठान", 40 * s, "#f3cf6a")


def fumes(cv, x, y, s=1.0, seed=3):
    rnd = random.Random(seed)
    for k in range(6):
        px = x + (k - 2.5) * 70 * s
        pts = []
        for i in range(12):
            pts.append((px + math.sin(i * 0.9 + k) * 22 * s, y - i * 28 * s))
        cv.line(pts, (120, 170, 60, 150), 10 * s, joint=False)
    for i in range(10):
        fx, fy = x + rnd.uniform(-260, 260) * s, y - rnd.uniform(40, 300) * s
        cv.ell(fx, fy, 5 * s, 4 * s, "#111111")
        cv.ell(fx - 5 * s, fy - 4 * s, 5 * s, 3 * s, "#ffffff80")
        cv.ell(fx + 5 * s, fy - 4 * s, 5 * s, 3 * s, "#ffffff80")


def brass_set(cv, x, y, s=1.0):
    cv.ell(x, y + 10 * s, 170 * s, 40 * s, "#00000050")
    cv.ell(x, y, 160 * s, 42 * s, "#b07a1a")
    cv.ell(x, y - 4 * s, 150 * s, 36 * s, "#e6b23a")
    cv.ell(x, y - 4 * s, 110 * s, 24 * s, "#f6d27a")
    # lota
    cv.ell(x + 70 * s, y - 60 * s, 48 * s, 52 * s, "#d39a2a")
    cv.rect(x + 50 * s, y - 135 * s, x + 90 * s, y - 100 * s, "#d39a2a")
    cv.ell(x + 70 * s, y - 135 * s, 30 * s, 9 * s, "#f0c862")
    cv.ell(x + 55 * s, y - 75 * s, 12 * s, 20 * s, "#fff2c0aa")
    diya(cv, x - 60 * s, y - 8 * s, 1.2 * s)
    for k in range(5):
        a = k * 1.3
        sx, sy = x + math.cos(a) * 150 * s, y - 60 * s + math.sin(a) * 60 * s
        star(cv, sx, sy, 14 * s, "#fff6c8")


def star(cv, x, y, r, col):
    cv.poly([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22),
             (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)], col)
    cv.glow(x, y, r * 2.2, col, 0.7)


def kadhai(cv, x, y, rx=300, ry=95, depth=170, inner="#1d1a18"):
    cv.chord(x, y, rx, depth, 0, 180, "#1a1716")
    cv.arc(x, y, rx, depth, 20, 160, "#3a3532", 6)
    cv.ell(x, y, rx, ry, "#2b2724")
    cv.ell(x, y, rx * 0.93, ry * 0.88, inner)
    for sx in (-1, 1):
        cv.arc(x + sx * (rx + 25), y, 34, 22, 0, 360, "#2b2724", 12)


def burner(cv, x, y, rx=260, ry=70, flame=True):
    cv.ell(x, y, rx + 60, ry + 20, "#2a2a2c")
    cv.ell(x, y, rx, ry, "#3c3c40")
    for i in range(4):
        a = i * math.pi / 2 + 0.6
        cv.line([(x + math.cos(a) * rx * 0.4, y + math.sin(a) * ry * 0.4), (x + math.cos(a) * rx * 1.05, y + math.sin(a) * ry * 1.05)], "#18181a", 16)
    if flame:
        for i in range(16):
            a = i / 16 * 2 * math.pi
            fx, fy = x + math.cos(a) * rx * 0.42, y + math.sin(a) * ry * 0.42
            cv.poly([(fx - 9, fy), (fx + 9, fy), (fx, fy - 34)], "#3d7bff")
            cv.poly([(fx - 5, fy), (fx + 5, fy), (fx, fy - 18)], "#b9d4ff")
        cv.glow(x, y - 10, rx * 0.8, "#2c5cff", 0.8)


def kitchen_bg(cv, top_view=False):
    cv.vgrad(0, 0, W, H * 0.55, "#efe3cf", "#d8c4a3")
    # tiles
    for yy in range(0, int(H * 0.55), 90):
        cv.line([(0, yy), (W, yy)], "#c9b28c", 2)
    for xx in range(0, W, 90):
        cv.line([(xx, 0), (xx, H * 0.55)], "#c9b28c", 2)
    # window glow
    cv.rect(820, 160, 1180, 640, "#ffd889")
    cv.glow(1000, 400, 380, "#ffcf7a", 0.6)
    cv.rect(820, 160, 1180, 640, None, "#7a4a22", 18)
    cv.line([(1000, 160), (1000, 640)], "#7a4a22", 12)
    # counter
    cv.vgrad(0, H * 0.55, W, H, "#3b3230", "#1f1a19")
    rnd = random.Random(5)
    for i in range(500):
        cv.ell(rnd.uniform(0, W), rnd.uniform(H * 0.56, H), 2, 2, (200, 190, 170, rnd.randint(30, 90)))
    cv.rect(0, H * 0.55 - 14, W, H * 0.55 + 6, "#5a4a44")


def counter_top(cv):
    # close-up top-down-ish granite surface with warm light
    cv.vgrad(0, 0, W, H, "#3a302d", "#1c1716")
    rnd = random.Random(9)
    for i in range(1400):
        cv.ell(rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(1, 3), rnd.uniform(1, 3), (210, 195, 170, rnd.randint(20, 80)))
    cv.glow(W * 0.5, H * 0.35, 700, "#ffb060", 0.35)


def living_bg(cv, floor_y=1500):
    cv.vgrad(0, 0, W, floor_y, "#4a1f10", "#a35a2a")
    # wall panel / arch
    cv.rect(140, 260, 1160, floor_y - 120, "#b8693499")
    cv.pieslice(650, 560, 420, 300, 180, 360, "#5c2512")
    cv.rect(230, 560, 1070, floor_y - 160, "#5c2512")
    cv.pieslice(650, 580, 390, 280, 180, 360, "#2a120b")
    cv.rect(260, 580, 1040, floor_y - 180, "#2a120b")
    fairy_lights(cv, 230, 560, 1070, 560, sag=160, n=30)
    fairy_lights(cv, 230, 760, 1070, 760, sag=120, n=30)
    toran(cv, 60, 1240, 120, 12)
    # floor marble
    cv.vgrad(0, floor_y, W, H, "#f3ece0", "#c9bca6")
    rnd = random.Random(2)
    for i in range(14):
        x = rnd.uniform(0, W); y = rnd.uniform(floor_y, H)
        pts = [(x + k * 40, y + math.sin(k * 0.8 + i) * 30 + k * 8) for k in range(12)]
        cv.line(pts, (150, 140, 130, 90), 2, joint=False)
    for k in range(1, 6):
        yy = floor_y + (H - floor_y) * (k / 6) ** 1.5
        cv.line([(0, yy), (W, yy)], (170, 155, 135, 120), 2)
    cv.rect(0, floor_y - 10, W, floor_y + 4, "#5a2a14")
    # reflection glow of lights on floor
    cv.glow(650, floor_y + 140, 420, "#ffcf7a", 0.35)


def puja_bg(cv, floor_y=1600):
    cv.vgrad(0, 0, W, floor_y, "#3b0f0a", "#7a2a12")
    # mandap
    cx = 650
    cv.rect(220, 380, 1080, 1260, "#5a2a10")
    cv.pieslice(cx, 520, 430, 280, 180, 360, "#c88a2a")
    cv.pieslice(cx, 540, 400, 260, 180, 360, "#5a2a10")
    for x in (250, 1050):
        cv.rect(x - 30, 520, x + 30, 1260, "#c88a2a")
        cv.rect(x - 40, 1230, x + 40, 1270, "#e3b23c")
    marigold_string(cv, 230, 400, 1070, 400, sag=160, n=34, r=14)
    fairy_lights(cv, 230, 470, 1070, 470, sag=130, n=30)
    # halo + Lakshmi (stylized idol)
    lx, ly = 520, 940
    cv.ell(lx, ly - 150, 125, 125, "#ffd76a")
    cv.glow(lx, ly - 140, 230, "#ffc04a", 0.9)
    for i in range(10):  # lotus
        a = math.pi + i / 9 * math.pi
        cv.ell(lx + math.cos(a) * 120, ly + 170 + math.sin(a) * 30, 46, 22, "#f27aa6")
    cv.ell(lx, ly + 175, 140, 34, "#d94f86")
    cv.poly([(lx - 90, ly + 160), (lx + 90, ly + 160), (lx + 55, ly - 40), (lx - 55, ly - 40)], "#c4122f")
    cv.rect(lx - 70, ly + 120, lx + 70, ly + 160, "#e3b23c")
    cv.ell(lx, ly - 130, 46, 54, "#e8b46a")
    cv.poly([(lx - 42, ly - 170), (lx - 30, ly - 225), (lx, ly - 200), (lx + 30, ly - 225), (lx + 42, ly - 170)], "#f2c230")
    cv.line([(lx - 55, ly - 30), (lx - 110, ly + 40)], "#e8b46a", 20)
    cv.line([(lx + 55, ly - 30), (lx + 110, ly + 40)], "#e8b46a", 20)
    cv.ell(lx + 112, ly + 44, 18, 18, "#f6d27a")
    for k in range(6):
        cv.ell(lx + 112 + k * 6, ly + 70 + k * 18, 6, 6, "#ffd23a")
    # Ganesh (stylized idol)
    gx, gy = 800, 1000
    cv.ell(gx, gy - 160, 105, 105, "#ffd76a")
    cv.glow(gx, gy - 150, 200, "#ffc04a", 0.8)
    cv.ell(gx, gy + 40, 100, 110, "#ff8a1f")
    cv.ell(gx - 70, gy - 150, 50, 60, "#f2a04a")
    cv.ell(gx + 70, gy - 150, 50, 60, "#f2a04a")
    cv.ell(gx, gy - 140, 55, 60, "#f6b25a")
    cv.line([(gx, gy - 120), (gx + 10, gy - 60), (gx + 40, gy - 40), (gx + 50, gy - 60)], "#f6b25a", 24)
    cv.poly([(gx - 40, gy - 190), (gx, gy - 260), (gx + 40, gy - 190)], "#f2c230")
    cv.ell(gx, gy + 150, 120, 30, "#c4122f")
    # floor
    cv.vgrad(0, floor_y, W, H, "#e9d8bd", "#a8916d")
    cv.rect(0, floor_y - 10, W, floor_y + 4, "#4a1a0c")


def night_ext(cv):
    cv.vgrad(0, 0, W, H * 0.6, "#070a24", "#2a1846")
    rnd = random.Random(4)
    for i in range(80):
        cv.ell(rnd.uniform(0, W), rnd.uniform(0, 700), 1.6, 1.6, "#ffffffaa")
    # firework bursts (distant)
    for (fx, fy, col) in [(250, 320, "#ffcf4a"), (1050, 230, "#ff5aa8"), (820, 520, "#7ae0ff")]:
        for k in range(20):
            a = k / 20 * 2 * math.pi
            cv.line([(fx + math.cos(a) * 30, fy + math.sin(a) * 30), (fx + math.cos(a) * 90, fy + math.sin(a) * 90)], col, 3)
        cv.glow(fx, fy, 120, col, 0.6)
    # house
    cv.poly([(80, 860), (650, 520), (1220, 860)], "#7a2416")
    cv.rect(140, 840, 1160, 1900, "#e8c89a")
    cv.rect(140, 840, 1160, 880, "#b8875a")
    for (x0, y0) in [(220, 960), (860, 960)]:
        cv.rect(x0, y0, x0 + 220, y0 + 300, "#ffcf6e")
        cv.glow(x0 + 110, y0 + 150, 220, "#ffb84a", 0.7)
        cv.rect(x0, y0, x0 + 220, y0 + 300, None, "#6a3a1a", 14)
        cv.line([(x0 + 110, y0), (x0 + 110, y0 + 300)], "#6a3a1a", 10)
        diya(cv, x0 + 60, y0 + 330, 1.1)
        diya(cv, x0 + 160, y0 + 330, 1.1)
    # door
    cv.rect(520, 1320, 780, 1900, "#6a2a10")
    cv.rect(540, 1340, 760, 1900, "#8a3a18")
    cv.line([(650, 1340), (650, 1900)], "#5a200c", 8)
    cv.ell(630, 1620, 8, 8, "#e3b23c"); cv.ell(670, 1620, 8, 8, "#e3b23c")
    toran(cv, 500, 800, 1300, 7)
    fairy_lights(cv, 140, 880, 1160, 880, sag=50, n=40)
    fairy_lights(cv, 140, 1290, 1160, 1290, sag=40, n=40)
    # ground
    cv.vgrad(0, 1900, W, H, "#5a4a3a", "#2a2018")
    rangoli(cv, 650, 2080, 300, 0.4)
    for x in range(110, 1250, 120):
        diya(cv, x, 1930, 1.0)
