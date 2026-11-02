import math
from gfx import *

CHARS = {
    "malkin": dict(skin="#cf9269", saree="#8b0f2a", border="#e3b23c", blouse="#d9a22e", hair="#1a1210",
                   bun=True, gajra=True, sindoor=True, jewel=True, specs=False, braid=False, pallu_back=True,
                   bangles="#e3b23c"),
    "sunita": dict(skin="#a86f4c", saree="#4f8094", border="#e8e2d0", blouse="#2f5868", hair="#140e0c",
                   bun=False, gajra=False, sindoor=False, jewel=False, specs=False, braid=True, pallu_back=False,
                   bangles="#d0213a"),
    "samdhan": dict(skin="#c4916c", saree="#2f6b3a", border="#e3b23c", blouse="#8a1f2a", hair="#b9b4ae",
                    bun=True, gajra=False, sindoor=False, jewel=True, specs=True, braid=False, pallu_back=True,
                    bangles="#e3b23c"),
}

POSES = {  # (L elbow, L hand, R elbow, R hand) — local coords (x right, y up negative)
    "idle": ((-100, -650), (-96, -530), (100, -650), (96, -530)),
    "point": ((-100, -650), (-96, -530), (160, -735), (285, -690)),
    "hold": ((-105, -660), (-48, -610), (105, -660), (48, -610)),
    "present": ((-110, -700), (-70, -735), (110, -700), (70, -735)),
    "namaste": ((-92, -665), (-8, -735), (92, -665), (8, -735)),
    "hand_mouth": ((-100, -650), (-96, -530), (90, -720), (24, -845)),
    "cheeks": ((-115, -730), (-62, -860), (115, -730), (62, -860)),
    "hips": ((-150, -660), (-74, -575), (150, -660), (74, -575)),
    "wag": ((-150, -660), (-74, -575), (150, -760), (150, -920)),
    "mop": ((-60, -670), (40, -640), (120, -650), (110, -545)),
    "chest": ((-100, -650), (-96, -530), (80, -660), (10, -720)),
}


def character(cv, who, x, y, s=1.0, expr="neutral", pose="idle", look=0.0, sit=False, prop=None, tear=False, shadow=True):
    c = CHARS[who]
    if s >= 2.5 and not getattr(cv, "_defocused", False):
        cv.defocus()
    dy = 360 if sit else 0
    T = lambda lx, ly: (x + lx * s, y + (ly + (dy if ly < -300 or sit else 0)) * s)

    def TT(lx, ly):
        return (x + lx * s, y + (ly + dy) * s)

    def P(pts, f):
        cv.poly([TT(*p) for p in pts], f)

    if shadow:
        cv.ell(x, y + 6 * s, (230 if sit else 150) * s, 26 * s, "#00000066")

    # hair behind / braid
    if c["braid"]:
        for k in range(9):
            px, py = TT(-48 - k * 3, -840 + k * 26)
            cv.ell(px, py, 17 * s, 15 * s, shade(c["hair"], 1.3))
            cv.ell(px, py, 14 * s, 12 * s, c["hair"])
        px, py = TT(-75, -600)
        cv.ell(px, py, 10 * s, 8 * s, "#d0213a")
    if c["bun"]:
        px, py = TT(0, -955)
        cv.ell(px, py, 44 * s, 30 * s, c["hair"])
        if c["gajra"]:
            for k in range(14):
                a = math.pi + k / 13 * math.pi
                cv.ell(px + math.cos(a) * 46 * s, py + math.sin(a) * 30 * s + 6 * s, 7 * s, 7 * s, "#fffaf0")
    if c["pallu_back"]:
        P([(-88, -800), (-125, -770), (-150, -430), (-100, -440), (-80, -700)], shade(c["saree"], 0.75))

    # skirt
    if sit:
        cx, cy = TT(0, -360)
        cv.chord(x, y - 10 * s, 250 * s, 210 * s, 180, 360, c["saree"])
        cv.arc(x, y - 10 * s, 250 * s, 210 * s, 180, 360, c["border"], 10 * s)
        for k in range(-3, 4):
            cv.line([(x + k * 22 * s, y - 190 * s), (x + k * 60 * s, y - 14 * s)], shade(c["saree"], 0.8), 3 * s)
        cv.rect(x - 250 * s, y - 24 * s, x + 250 * s, y - 6 * s, c["border"])
    else:
        P([(-74, -560), (74, -560), (118, -220), (138, 0), (-138, 0), (-118, -220)], c["saree"])
        for k in range(-2, 4):
            cv.line([TT(10 + k * 8, -520), TT(10 + k * 34, -10)], shade(c["saree"], 0.78), 3 * s)
        cv.line([TT(-8, -520), TT(-34, -10)], c["border"], 7 * s)
        P([(-138, -40), (138, -40), (138, 0), (-138, 0)], c["border"])
        P([(-138, -30), (138, -30), (138, -22), (-138, -22)], shade(c["saree"], 0.6))
        for fx in (-50, 50):
            px, py = TT(fx, 8)
            cv.ell(px, py, 30 * s, 12 * s, shade(c["skin"], 0.85))

    # neck + torso
    P([(-18, -830), (18, -830), (20, -780), (-20, -780)], shade(c["skin"], 0.9))
    P([(-88, -790), (88, -790), (72, -560), (-72, -560)], c["blouse"])
    P([(-30, -790), (30, -790), (0, -755)], c["skin"])
    # midriff
    P([(28, -610), (72, -610), (74, -560), (30, -560)], shade(c["skin"], 0.95))
    # pallu across
    P([(-90, -800), (-30, -800), (88, -600), (86, -525), (-80, -700)], c["saree"])
    cv.line([TT(-30, -800), TT(88, -600)], c["border"], 8 * s)
    cv.line([TT(-80, -700), TT(86, -525)], c["border"], 8 * s)
    for k in range(3):
        cv.line([TT(-60 + k * 20, -770 + k * 10), TT(40 + k * 18, -580 + k * 10)], shade(c["saree"], 0.82), 3 * s)

    # jewellery
    if c["jewel"]:
        nx, ny = TT(0, -772)
        cv.arc(nx, ny - 20 * s, 44 * s, 40 * s, 20, 160, c["border"], 7 * s)
        if who == "malkin":
            for k in range(7):
                a = math.radians(30 + k * 20)
                cv.ell(nx + math.cos(a) * 44 * s, ny - 20 * s + math.sin(a) * 40 * s + 6 * s, 6 * s, 9 * s, "#e3b23c")
            cv.ell(nx, ny + 26 * s, 12 * s, 14 * s, "#c4122f")
    else:
        nx, ny = TT(0, -785)
        cv.arc(nx, ny - 10 * s, 30 * s, 26 * s, 20, 160, "#1a1a1a", 3 * s)

    # arms
    le, lh, re_, rh = POSES[pose]
    for sh, el, hd in [((-86, -780), le, lh), ((86, -780), re_, rh)]:
        cv.line([TT(*sh), TT(*el), TT(*hd)], c["skin"], 30 * s)
        mid = ((sh[0] * 0.55 + el[0] * 0.45), (sh[1] * 0.55 + el[1] * 0.45))
        cv.line([TT(*sh), TT(*mid)], c["blouse"], 36 * s)
        hx, hy = TT(*hd)
        bx, by = TT(el[0] * 0.25 + hd[0] * 0.75, el[1] * 0.25 + hd[1] * 0.75)
        for k in range(3):
            cv.ell(bx, by + (k - 1) * 4 * s, 18 * s, 6 * s, None, c["bangles"], 3 * s)
        cv.ell(hx, hy, 18 * s, 18 * s, c["skin"])
    if pose == "point":
        hx, hy = TT(285, -690)
        cv.line([(hx, hy), (hx + 40 * s, hy + 16 * s)], c["skin"], 10 * s)
    if pose == "wag":
        hx, hy = TT(150, -920)
        cv.line([(hx, hy), (hx, hy - 38 * s)], c["skin"], 10 * s)

    # head
    hx, hy = TT(0, -875)
    cv.ell(hx - 58 * s, hy + 2 * s, 11 * s, 16 * s, shade(c["skin"], 0.9))
    cv.ell(hx + 58 * s, hy + 2 * s, 11 * s, 16 * s, shade(c["skin"], 0.9))
    cv.ell(hx, hy, 58 * s, 70 * s, c["skin"])
    cv.ell(hx, hy + 30 * s, 40 * s, 30 * s, shade(c["skin"], 1.04))
    # hair cap
    cv.chord(hx, hy - 30 * s, 63 * s, 52 * s, 180, 360, c["hair"])
    cv.poly([(hx - 63 * s, hy - 30 * s), (hx - 40 * s, hy - 30 * s), (hx - 56 * s, hy + 10 * s), (hx - 64 * s, hy - 5 * s)], c["hair"])
    cv.poly([(hx + 63 * s, hy - 30 * s), (hx + 40 * s, hy - 30 * s), (hx + 56 * s, hy + 10 * s), (hx + 64 * s, hy - 5 * s)], c["hair"])
    cv.line([(hx, hy - 82 * s), (hx, hy - 42 * s)], "#c4122f" if c["sindoor"] else shade(c["hair"], 1.6), 4 * s)
    if c["jewel"]:
        cv.ell(hx - 60 * s, hy + 26 * s, 8 * s, 10 * s, "#e3b23c")
        cv.ell(hx + 60 * s, hy + 26 * s, 8 * s, 10 * s, "#e3b23c")
    if who == "malkin":
        cv.ell(hx, hy - 38 * s, 7 * s, 9 * s, "#e3b23c")
        cv.ell(hx + 14 * s, hy + 18 * s, 7 * s, 7 * s, None, "#e3b23c", 2 * s)
    # bindi
    cv.ell(hx, hy - 28 * s, (6 if who == "malkin" else 4) * s, (6 if who == "malkin" else 4) * s, "#c4122f")

    face(cv, hx, hy, s, expr, look, c, tear)

    if c["specs"]:
        for sx in (-1, 1):
            cv.ell(hx + sx * 22 * s, hy - 3 * s, 17 * s, 14 * s, None, "#6a4a2a", 3 * s)
        cv.line([(hx - 6 * s, hy - 5 * s), (hx + 6 * s, hy - 5 * s)], "#6a4a2a", 3 * s)
    return TT


def face(cv, hx, hy, s, expr, look, c, tear):
    ey = hy - 3 * s
    dark = "#1a0f0a"
    # cheeks
    cv.ell(hx - 32 * s, hy + 18 * s, 12 * s, 7 * s, (230, 110, 110, 60))
    cv.ell(hx + 32 * s, hy + 18 * s, 12 * s, 7 * s, (230, 110, 110, 60))
    wide = expr in ("shocked", "amazed", "taste")
    half = expr in ("tired", "sad", "regret", "lowered")
    for sx in (-1, 1):
        ex = hx + sx * 22 * s
        ry = (10 if wide else 6.5) * s
        rx = (12 if wide else 12) * s
        if expr == "smile" or expr == "happy":
            cv.arc(ex, ey + 4 * s, 11 * s, 7 * s, 200, 340, dark, 3.5 * s)
        else:
            cv.ell(ex, ey, rx, ry, "#fbf6ef")
            py = ey + (3 * s if half else 0)
            cv.ell(ex + look * 5 * s, py, (4 if wide else 5.5) * s, (4 if wide else 5.5) * s, dark)
            cv.ell(ex + look * 5 * s + 2 * s, py - 2 * s, 1.5 * s, 1.5 * s, "#ffffff")
            if half:
                cv.chord(ex, ey, rx + 1 * s, ry + 1 * s, 180, 360, c["skin"])
                cv.line([(ex - rx, ey), (ex + rx, ey)], dark, 2.5 * s)
            else:
                cv.arc(ex, ey, rx, ry, 190, 350, dark, 2.5 * s)
            if expr == "angry":
                cv.chord(ex, ey - 2 * s, rx + 1 * s, ry, 180, 360, c["skin"])
                cv.line([(ex - rx, ey - 1 * s), (ex + rx, ey - 1 * s)], dark, 2.5 * s)
        if expr == "tired":
            cv.arc(ex, ey + 9 * s, 10 * s, 5 * s, 20, 160, (90, 50, 40, 140), 3 * s)
        # brows
        by = hy - 18 * s
        if expr == "angry":
            p = [(ex - sx * 14 * s, by - 6 * s), (ex + sx * 12 * s, by + 4 * s)] if sx < 0 else [(ex + sx * 14 * s, by - 6 * s), (ex - sx * 12 * s, by + 4 * s)]
            cv.line([(hx + sx * 36 * s, by - 6 * s), (hx + sx * 9 * s, by + 4 * s)], dark, 5 * s)
        elif expr in ("shocked", "amazed", "taste"):
            cv.arc(ex, by - 6 * s, 14 * s, 6 * s, 200, 340, dark, 4 * s)
        elif expr in ("sad", "regret", "tired", "lowered"):
            cv.line([(hx + sx * 36 * s, by + 3 * s), (hx + sx * 10 * s, by - 5 * s)], dark, 4 * s)
        elif expr == "arrogant" and sx > 0:
            cv.arc(ex, by - 6 * s, 14 * s, 6 * s, 200, 340, dark, 4 * s)
        elif expr == "confident":
            cv.line([(hx + sx * 36 * s, by - 4 * s), (hx + sx * 10 * s, by + 1 * s)], dark, 4.5 * s)
        else:
            cv.arc(ex, by, 14 * s, 4 * s, 200, 340, dark, 4 * s)
    # nose
    cv.line([(hx - 2 * s, hy + 2 * s), (hx - 5 * s, hy + 18 * s), (hx + 3 * s, hy + 20 * s)], shade(c["skin"], 0.7), 2.5 * s, joint=False)
    # mouth
    my = hy + 36 * s
    lip = "#8a2a2a"
    if expr in ("angry",):
        cv.chord(hx, my + 6 * s, 16 * s, 10 * s, 180, 360, "#4a1010")
        cv.line([(hx - 16 * s, my + 6 * s), (hx + 16 * s, my + 6 * s)], lip, 3 * s)
    elif expr in ("shocked",):
        cv.ell(hx, my + 2 * s, 9 * s, 12 * s, "#4a1010")
    elif expr in ("amazed", "happy"):
        cv.chord(hx, my - 2 * s, 18 * s, 13 * s, 0, 180, "#4a1010")
        cv.chord(hx, my - 2 * s, 15 * s, 5 * s, 0, 180, "#ffffff")
    elif expr in ("smile", "confident", "taste"):
        cv.arc(hx, my - 6 * s, 16 * s, 10 * s, 20, 160, lip, 4 * s)
    elif expr in ("arrogant",):
        cv.line([(hx - 14 * s, my + 2 * s), (hx + 6 * s, my + 1 * s), (hx + 16 * s, my - 5 * s)], lip, 4 * s, joint=False)
    elif expr in ("sad", "regret", "lowered", "tired"):
        cv.arc(hx, my + 8 * s, 12 * s, 7 * s, 200, 340, lip, 3.5 * s)
    else:
        cv.line([(hx - 12 * s, my), (hx + 12 * s, my)], lip, 3.5 * s)
    if tear:
        for sx in (-1, 1):
            cv.ell(hx + sx * 26 * s, ey + 16 * s, 3 * s, 5 * s, "#cfe8ff")
            cv.glow(hx + sx * 26 * s, ey + 16 * s, 8 * s, "#ffffff", 0.6)
