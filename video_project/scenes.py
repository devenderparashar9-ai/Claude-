from chars import *

SH = {}
def shot(name, move="in", fx=()):
    def deco(f):
        SH[name] = (f, move, fx)
        return f
    return deco

FY = 1500  # living-room floor line

def table_with(cv, x, y, w=330):
    cv.rect(x - w, y, x + w, y + 30, "#5a2a12")
    cv.rect(x - w + 20, y + 30, x - w + 50, y + 260, "#4a200c")
    cv.rect(x + w - 50, y + 30, x + w - 20, y + 260, "#4a200c")
    cv.rect(x - w, y - 8, x + w, y + 4, "#8a4a22")

def peanut_bowl(cv, x, y, s=1.0):
    steel_bowl(cv, x, y, 90 * s, 26 * s, 50 * s)
    peanut_pile(cv, x, y - 4 * s, 70 * s, 16 * s, n=28, s=s * 0.9, seed=11)

# ---------- story shots ----------
@shot("house", "in", ("bokeh", "flicker"))
def _(cv):
    night_ext(cv)

@shot("mop_wide", "pan_r", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    table_with(cv, 1000, 1330, 200)
    brass_set(cv, 1000, 1300, 0.8)
    character(cv, "sunita", 520, 2020, 1.25, "tired", "mop", look=0.6)
    cv.line([(520 + 20 * 1.25, 2020 - 760 * 1.25), (520 + 230 * 1.25, 2020 + 10)], "#8a6a3a", 10)
    cv.ell(520 + 250 * 1.25, 2040, 90, 22, "#d8d0c0")
    for k in range(9):
        cv.line([(520 + 200 * 1.25 + k * 12, 2030), (520 + 190 * 1.25 + k * 14, 2058)], "#bdb3a0", 5)
    for k in range(10):   # wet sheen streaks
        cv.ell(250 + k * 90, 2120 + (k % 3) * 30, 60, 6, "#ffffff70")

@shot("sunita_tired", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "sunita", 650, 3300, 2.9, "tired", "idle", look=-0.3, shadow=False)

@shot("malkin_point", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "sunita", 1050, 2050, 1.05, "lowered", "idle", look=-0.6)
    character(cv, "malkin", 420, 2150, 1.45, "angry", "point", look=0.8)

@shot("malkin_point2", "out", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 560, 3150, 2.7, "angry", "point", look=0.7, shadow=False)

@shot("malkin_box", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "malkin", 560, 2200, 1.55, "arrogant", "hold", look=0.4)
    sweet_box(cv, 560, 2200 - 560 * 1.55, 0.6)
    character(cv, "sunita", 1120, 2060, 1.0, "lowered", "idle", look=-0.7)

@shot("katli_box", "in", ("sparkle",))
def _(cv):
    cv.vgrad(0, 0, W, H, "#2a0c06", "#5a1e0c")
    cv.glow(650, 1100, 700, "#ffb050", 0.6)
    cv.rect(0, 1450, W, H, "#3a1608")
    sweet_box(cv, 650, 1350, 1.9)
    for k in range(8):
        star(cv, 250 + k * 110, 1150 + (k % 3) * 70, 12, "#fff6d0")

@shot("malkin_peanuts", "pan_l", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "malkin", 450, 2180, 1.45, "arrogant", "point", look=0.8)
    hx, hy = T(285, -690)
    peanut_bowl(cv, hx + 60, hy + 10, 0.9)
    character(cv, "sunita", 1060, 2080, 1.05, "sad", "idle", look=-0.6)

@shot("malkin_warn", "in", ("bokeh", "sparkle"))
def _(cv):
    living_bg(cv, FY)
    table_with(cv, 950, 1700, 260)
    brass_set(cv, 950, 1670, 1.1)
    character(cv, "malkin", 430, 2300, 1.7, "angry", "wag", look=0.6)

@shot("sunita_corner", "out", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    cv.rect(0, 0, 260, H, "#2a1208aa")
    character(cv, "sunita", 330, 2000, 1.05, "sad", "hold", look=0.3, sit=True)
    peanut_bowl(cv, 330, 2000 - 250 * 1.05, 0.7)
    cv.text(950, 1250, "", 10, "#000000")
    # malkin far, back to us, busy (small figure)
    character(cv, "malkin", 1030, 1720, 0.7, "neutral", "hips", look=0.0)

@shot("sunita_smile", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "sunita", 650, 3200, 2.8, "smile", "chest", look=0.0, shadow=False)
    hx, hy = T(10, -720)
    peanut(cv, hx, hy - 30, 2.6, "#b5653a", 0.5)

@shot("tv", "in", ("flash",))
def _(cv):
    living_bg(cv, FY)
    tv_set(cv, 650, 980, 1.0)

def tv_set(cv, x, y, s, big=False):
    w, h = 520 * s, 300 * s
    cv.rect(x - w - 20 * s, y - h - 20 * s, x + w + 20 * s, y + h + 20 * s, "#0c0c0e", r=14 * s)
    cv.vgrad(x - w, y - h, x + w, y + h, "#1d2c5a", "#0c1430")
    # anchor silhouette (generic)
    cv.ell(x - 200 * s, y - 70 * s, 70 * s, 82 * s, "#d0a080")
    cv.chord(x - 200 * s, y - 100 * s, 76 * s, 60 * s, 180, 360, "#1a1010")
    cv.poly([(x - 330 * s, y + h), (x - 70 * s, y + h), (x - 110 * s, y + 20 * s), (x - 290 * s, y + 20 * s)], "#2a2a40")
    # inset: sweets with red X
    cv.rect(x + 60 * s, y - 230 * s, x + 470 * s, y + 60 * s, "#3a1a10")
    katli_tray(cv, x + 265 * s, y - 120 * s, 4, 3, 0.9 * s, "#8e8a52", vark=False, rot=True)
    cv.line([(x + 90 * s, y - 210 * s), (x + 440 * s, y + 40 * s)], "#ff2020", 14 * s)
    cv.line([(x + 440 * s, y - 210 * s), (x + 90 * s, y + 40 * s)], "#ff2020", 14 * s)
    cv.rect(x - w, y + 110 * s, x + w, y + 210 * s, "#d40f1a")
    cv.rect(x - w, y + 210 * s, x + w, y + h, "#f2f2f2")
    cv.text(x - w + 30 * s, y + 160 * s, "ब्रेकिंग न्यूज़", 58 * s, "#ffffff", anchor="lm")
    cv.text(x - w + 30 * s, y + 255 * s, "बाज़ार में ज़हरीली मिठाइयाँ!", 44 * s, "#c40f1a", anchor="lm")
    cv.rect(x + w - 150 * s, y - h + 30 * s, x + w - 30 * s, y - h + 90 * s, "#d40f1a", r=8 * s)
    cv.text(x + w - 90 * s, y - h + 60 * s, "LIVE", 34 * s, "#ffffff")
    cv.glow(x, y, 600 * s, "#5070ff", 0.35)

@shot("tv2", "in", ("flash", "shake"))
def _(cv):
    cv.vgrad(0, 0, W, H, "#0a0a12", "#1a1020")
    tv_set(cv, 650, 1150, 1.22)

@shot("malkin_shock", "in", ("shake", "bokeh"))
def _(cv):
    living_bg(cv, FY)
    cv.glow(650, 900, 600, "#4060ff", 0.35)
    character(cv, "malkin", 650, 3150, 2.75, "shocked", "cheeks", look=0.0, shadow=False)

@shot("door", "pan_r", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    # door opening at right
    cv.rect(760, 520, 1200, FY + 8, "#1a1030")
    cv.vgrad(780, 540, 1180, FY, "#20183a", "#3a2a50")
    toran(cv, 740, 1220, 520, 6)
    cv.poly([(1180, 540), (1290, 500), (1290, FY + 60), (1180, FY)], "#7a3414")
    character(cv, "samdhan", 980, 1980, 1.2, "shocked", "idle", look=-0.6)
    character(cv, "malkin", 330, 2120, 1.35, "shocked", "cheeks", look=0.7)

@shot("samdhan_talk", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "samdhan", 650, 3150, 2.7, "shocked", "point", look=-0.3, shadow=False)

@shot("rotten", "in", ("fumes", "shake"))
def _(cv):
    cv.vgrad(0, 0, W, H, "#1a160c", "#3a2a12")
    cv.glow(650, 1100, 600, "#90c050", 0.25)
    cv.rect(0, 1450, W, H, "#2a1a0a")
    sweet_box(cv, 650, 1350, 1.9, rotten=True)
    fumes(cv, 650, 1250, 1.6)

@shot("malkin_despair", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    # wall clock
    cx, cy = 1040, 380
    cv.ell(cx, cy, 120, 120, "#e3b23c"); cv.ell(cx, cy, 104, 104, "#fffaf0")
    for k in range(12):
        a = k / 12 * 2 * math.pi
        cv.line([(cx + math.cos(a) * 88, cy + math.sin(a) * 88), (cx + math.cos(a) * 98, cy + math.sin(a) * 98)], "#2a1a10", 5)
    cv.line([(cx, cy), (cx + 55, cy - 20)], "#2a1a10", 9)                       # hour ~ near 7? (approx)
    cv.line([(cx, cy), (cx + math.cos(math.radians(-150)) * 85, cy + math.sin(math.radians(-150)) * 85)], "#c4122f", 6)  # minute at :50
    character(cv, "malkin", 600, 3150, 2.7, "sad", "cheeks", look=0.0, tear=True, shadow=False)

@shot("stunned", "out", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "samdhan", 1060, 1980, 1.0, "shocked", "cheeks")
    character(cv, "malkin", 650, 2050, 1.1, "shocked", "hand_mouth")
    character(cv, "sunita", 230, 1940, 0.9, "neutral", "hold", look=0.6, sit=True)
    peanut_bag(cv, 230, 1940 - 245 * 0.9, 0.7)

def peanut_bag(cv, x, y, s=1.0):
    cv.poly([(x - 70 * s, y - 60 * s), (x + 70 * s, y - 60 * s), (x + 90 * s, y + 80 * s), (x - 90 * s, y + 80 * s)], "#e8dcc0")
    cv.line([(x - 70 * s, y - 60 * s), (x + 70 * s, y - 60 * s)], "#b8a880", 6 * s)
    peanut_pile(cv, x, y - 64 * s, 60 * s, 12 * s, n=14, s=s, seed=7)
    for k in range(3):
        cv.line([(x - 60 * s + k * 50 * s, y - 20 * s), (x - 50 * s + k * 50 * s, y + 60 * s)], "#d0c4a4", 3 * s)

@shot("sunita_rise", "up", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "sunita", 650, 2200, 1.6, "neutral", "hold", look=0.0)
    peanut_bag(cv, 650, 2200 - 600 * 1.6, 0.9)

@shot("sunita_confident", "in", ("bokeh", "sparkle"))
def _(cv):
    living_bg(cv, FY)
    cv.glow(650, 700, 500, "#ffd070", 0.4)
    T = character(cv, "sunita", 650, 3150, 2.7, "confident", "chest", look=0.0, shadow=False)
    hx, hy = T(10, -720)
    peanut_pile(cv, hx, hy - 10, 40, 14, n=8, s=2.0, seed=3)

@shot("malkin_brow", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 600, 3150, 2.7, "arrogant", "hips", look=0.5, shadow=False)

@shot("malkin_brow2", "out", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "sunita", 950, 2060, 1.15, "confident", "hold", look=-0.6)
    peanut_bag(cv, 950, 2060 - 600 * 1.15, 0.7)
    character(cv, "malkin", 380, 2150, 1.35, "neutral", "point", look=0.7)

# ---------- cooking montage ----------
def stove_scene(cv, contents=None, flame=True, y=1450):
    counter_top(cv)
    burner(cv, 650, y + 120, 300, 80, flame)
    kadhai(cv, 650, y, 330, 105, 190)
    if contents:
        contents(cv, 650, y)

@shot("c_pan", "in", ("flame", "steam"))
def _(cv):
    def c(cv, x, y):
        peanut_pile(cv, x, y + 10, 260, 70, n=150, s=1.6, col="#c9855a", seed=21)
    stove_scene(cv, c)
    # hand pouring from bowl
    cv.line([(1300, 640), (1010, 930)], "#a86f4c", 70)
    steel_bowl(cv, 860, 960, 150, 40, 90)
    cv.ell(1000, 935, 50, 40, "#a86f4c")
    for k in range(3): cv.ell(1040 + k * 20, 900 - k * 18, 30, 10, None, "#d0213a", 6)
    for k in range(10):
        peanut(cv, 820 + (k % 3) * 20, 1050 + k * 30, 1.6, "#c9855a", k)

@shot("c_roast", "in", ("flame", "steam"))
def _(cv):
    def c(cv, x, y):
        peanut_pile(cv, x, y + 10, 270, 75, n=170, s=1.6, col="#9a4a26", seed=22)
        cv.line([(x + 40, y - 300), (x - 40, y + 20)], "#6a4020", 22)
        cv.ell(x - 50, y + 30, 70, 26, "#8a8f94")
    stove_scene(cv, c)

@shot("c_rub", "in", ())
def _(cv):
    counter_top(cv)
    cv.ell(650, 1350, 480, 230, "#f4f0e6")
    for k in range(8):
        cv.line([(220 + k * 120, 1180), (260 + k * 110, 1520)], "#e2dccd", 4)
    rnd = random.Random(4)
    for i in range(70):  # loose red skins
        x, y = 650 + rnd.uniform(-420, 420), 1350 + rnd.uniform(-180, 180)
        cv.ell(x, y, rnd.uniform(5, 12), rnd.uniform(3, 6), "#8a3a1e")
    peanut_pile(cv, 650, 1330, 220, 70, n=50, s=1.7, col="#f0dcb4", seed=5)
    for sx in (-1, 1):  # hands rubbing (cloth over)
        cv.ell(650 + sx * 150, 1250, 150, 90, "#ece6d8")
        cv.line([(650 + sx * 150, 1250), (650 + sx * 420, 700)], "#a86f4c", 80)
        cv.ell(650 + sx * 150, 1250, 120, 70, "#f6f2e8")
        for k in range(3):
            cv.ell(650 + sx * 330, 920 - k * 14, 46, 14, None, "#d0213a", 6)

@shot("c_white", "in", ("sparkle",))
def _(cv):
    counter_top(cv)
    steel_bowl(cv, 650, 1300, 380, 110, 200)
    peanut_pile(cv, 650, 1290, 320, 85, n=200, s=2.0, col="#f2e0b8", seed=8)
    cv.glow(650, 1250, 400, "#fff0c0", 0.3)

@shot("c_mixer", "in", ("shake",))
def _(cv):
    kitchen_bg(cv)
    x, y = 650, 1450
    cv.rect(x - 230, y, x + 230, y + 300, "#f2f2f2", r=40)
    cv.rect(x - 230, y + 230, x + 230, y + 300, "#d0d0d0", r=20)
    cv.ell(x, y + 150, 40, 40, "#c0c0c0"); cv.ell(x, y + 150, 30, 30, "#e03030")
    cv.text(x - 130, y + 150, "PULSE", 26, "#555555")
    # jar
    cv.poly([(x - 170, y), (x + 170, y), (x + 210, y - 560), (x - 210, y - 560)], (220, 235, 245, 170))
    cv.poly([(x - 165, y - 10), (x + 165, y - 10), (x + 185, y - 260), (x - 185, y - 260)], "#e8d4a8")
    rnd = random.Random(6)
    for i in range(160):
        px, py = x + rnd.uniform(-200, 200), y - rnd.uniform(270, 540)
        cv.ell(px, py, 9, 6, "#efd9ad")
    cv.rect(x - 230, y - 620, x + 230, y - 560, "#2a2a2a", r=20)
    cv.line([(x + 210, y - 500), (x + 300, y - 450), (x + 300, y - 150), (x + 190, y - 120)], "#2a2a2a", 26, joint=False)

@shot("c_sieve", "down", ("dust",))
def _(cv):
    counter_top(cv)
    steel_bowl(cv, 650, 1650, 360, 100, 190)
    cv.ell(650, 1650, 300, 80, "#e9d6ac")
    # sieve
    cv.ell(650, 1050, 330, 95, "#8a8f94")
    cv.ell(650, 1050, 305, 85, "#b9bec4")
    for k in range(-14, 15):
        cv.line([(650 + k * 20, 980), (650 + k * 20, 1120)], "#9aa0a6", 2)
    for k in range(-4, 5):
        cv.line([(360, 1050 + k * 18), (940, 1050 + k * 18)], "#9aa0a6", 2)
    cv.ell(650, 1045, 210, 50, "#ead8b0")
    cv.line([(980, 1050), (1250, 960)], "#5a3a1a", 30)
    rnd = random.Random(3)
    for i in range(160):
        cv.ell(650 + rnd.uniform(-260, 260), rnd.uniform(1130, 1600), 3, 3, (240, 220, 180, 200))

@shot("c_milk", "in", ("dust",))
def _(cv):
    counter_top(cv)
    steel_bowl(cv, 650, 1550, 400, 110, 210)
    cv.ell(650, 1550, 340, 92, "#e9d6ac")
    cv.ell(650, 1540, 160, 45, "#fbf8f2")
    # spoon / measuring cup pouring
    cv.poly([(780, 860), (980, 820), (1010, 960), (810, 1010)], "#c7cfd6")
    cv.ell(895, 915, 110, 40, "#dfe5ea")
    cv.line([(1000, 880), (1280, 760)], "#a86f4c", 60)
    rnd = random.Random(8)
    for i in range(120):
        t = rnd.random()
        cv.ell(800 - t * 140 + rnd.uniform(-30, 30), 1000 + t * 520, 4, 4, (255, 255, 255, 220))
    cv.text(650, 1830, "", 10, "#000000")

@shot("c_syrup", "in", ("flame", "steam"))
def _(cv):
    def c(cv, x, y):
        cv.ell(x, y + 6, 290, 88, "#e9b65a")
        cv.ell(x, y + 6, 240, 70, "#f6cf7a")
        rnd = random.Random(2)
        for i in range(60):
            cv.ell(x + rnd.uniform(-250, 250), y + rnd.uniform(-60, 70), rnd.uniform(5, 14), rnd.uniform(4, 9), None, "#fff0c0", 2)
    stove_scene(cv, c)
    # one-string test between thumb and finger (inset)
    cv.ell(650, 640, 300, 300, "#2a1a10")
    cv.ell(650, 640, 285, 285, "#f0d8b0")
    cv.ell(560, 560, 70, 110, "#a86f4c")
    cv.ell(740, 720, 70, 110, "#a86f4c")
    cv.line([(590, 600), (650, 640), (710, 680)], "#e6a640", 6)
    cv.glow(650, 640, 60, "#ffd080", 0.6)
    cv.text(650, 1000, "एक-तार की चाशनी", 64, "#ffe9a8", stroke=4, stroke_fill="#3a1a08")

@shot("c_ghee", "in", ("flame", "steam"))
def _(cv):
    def c(cv, x, y):
        cv.ell(x, y + 6, 290, 88, "#e9b65a")
        cv.ell(x - 40, y + 10, 180, 50, "#e9d6ac")
        cv.ell(x + 120, y, 60, 20, "#ffd84a")
        cv.glow(x + 120, y, 70, "#ffe080", 0.6)
    stove_scene(cv, c)
    steel_bowl(cv, 930, 900, 110, 30, 60)
    cv.ell(930, 900, 95, 25, "#f6cf4a")
    cv.line([(900, 930), (800, 1300)], "#c7cfd6", 16)
    cv.ell(790, 1320, 40, 22, "#c7cfd6"); cv.ell(790, 1316, 30, 14, "#ffd84a")

@shot("c_dough", "in", ("flame", "steam"))
def _(cv):
    def c(cv, x, y):
        cv.ell(x, y + 10, 210, 70, "#d9bd86")
        cv.ell(x - 10, y, 190, 60, "#e8d09c")
        cv.line([(x + 200, y - 360), (x + 40, y + 10)], "#6a4020", 26)
        cv.ell(x + 30, y + 16, 80, 30, "#5a3418")
    stove_scene(cv, c)

@shot("c_roll", "pan_r", ())
def _(cv):
    counter_top(cv)
    cv.rect(180, 900, 1120, 1800, "#f3ecda")
    cv.rect(180, 900, 1120, 1800, None, "#d8ceb4", 4)
    cv.rect(260, 1000, 1040, 1700, "#e9d3a8", r=30)
    cv.rect(270, 1010, 1030, 1060, "#f2e0ba", r=20)
    cv.line([(140, 1330), (1160, 1250)], "#b07a3a", 70)
    cv.line([(60, 1336), (160, 1328)], "#8a5a26", 40)
    cv.line([(1140, 1252), (1240, 1244)], "#8a5a26", 40)
    cv.line([(140, 1310), (1160, 1230)], "#d09a5a", 14)

@shot("c_vark", "in", ("sparkle",))
def _(cv):
    counter_top(cv)
    cv.rect(180, 900, 1120, 1800, "#f3ecda")
    cv.rect(260, 1000, 1040, 1700, "#e9d3a8", r=30)
    rnd = random.Random(12)
    for i in range(14):  # silver leaf patches
        x, y = rnd.uniform(320, 980), rnd.uniform(1060, 1640)
        cv.poly([(x, y), (x + 120, y + 10), (x + 110, y + 100), (x - 10, y + 90)], (232, 236, 240, 230))
        cv.line([(x + 10, y + 20), (x + 80, y + 40)], "#ffffff", 3)
    # floating vark sheet + fingers
    cv.poly([(560, 700), (800, 720), (790, 900), (550, 880)], (235, 240, 245, 240))
    cv.line([(560, 700), (800, 720)], "#ffffff", 3)
    cv.line([(820, 600), (1250, 300)], "#a86f4c", 60)
    cv.ell(800, 650, 40, 34, "#a86f4c")

@shot("c_cut", "in", ("sparkle",))
def _(cv):
    counter_top(cv)
    cv.rect(180, 900, 1120, 1800, "#f3ecda")
    katli_tray(cv, 650, 1050, 10, 22, 1.25, "#e9d3a8", vark=True)
    cv.poly([(840, 600), (880, 600), (720, 1250), (700, 1240)], "#cfd6dc")
    cv.line([(860, 600), (1100, 250)], "#2a2a2a", 40)

@shot("present", "in", ("sparkle", "bokeh"))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 1080, 2150, 1.2, "amazed", "idle", look=-0.7)
    T = character(cv, "sunita", 430, 2200, 1.4, "smile", "present", look=0.5)
    hx, hy = T(0, -735)
    silver_plate(cv, hx + 40, hy - 10, 0.9)

def silver_plate(cv, x, y, s=1.0):
    cv.ell(x, y + 12 * s, 230 * s, 70 * s, "#00000050")
    cv.ell(x, y, 230 * s, 66 * s, "#a9b1b8")
    cv.ell(x, y - 4 * s, 215 * s, 60 * s, "#e3e8ec")
    cv.ell(x, y - 4 * s, 170 * s, 46 * s, "#cfd6dc")
    for r, n in [(0, 1), (1, 4)]:
        pass
    pos = [(-90, -10), (0, -20), (90, -10), (-45, 12), (45, 12), (0, -46), (-130, 8), (130, 8)]
    for px, py in pos:
        katli(cv, x + px * s, y - 6 * s + py * s, 0.95 * s, "#e9d3a8", vark=True)
    for k in range(4):
        star(cv, x + (-150 + k * 100) * s, y - 80 * s - (k % 2) * 30 * s, 10 * s, "#ffffff")

@shot("taste", "in", ("sparkle", "bokeh"))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "malkin", 650, 3150, 2.7, "taste", "hand_mouth", look=0.0, shadow=False)
    hx, hy = T(24, -845)
    katli(cv, hx + 10, hy - 30, 1.1, "#e9d3a8")

@shot("taste2", "in", ("sparkle", "bokeh"))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 650, 3150, 2.7, "amazed", "cheeks", look=0.0, shadow=False)

@shot("samdhan_praise", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    T = character(cv, "samdhan", 650, 3150, 2.7, "taste", "hand_mouth", look=0.0, shadow=False)
    hx, hy = T(24, -845)
    katli(cv, hx + 10, hy - 30, 1.1, "#e9d3a8")

@shot("samdhan_praise2", "out", ("bokeh", "sparkle"))
def _(cv):
    living_bg(cv, FY)
    character(cv, "sunita", 330, 2050, 1.15, "smile", "namaste", look=0.6)
    character(cv, "samdhan", 900, 2120, 1.3, "happy", "point", look=-0.8)

@shot("regret", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "sunita", 1100, 2020, 1.0, "neutral", "idle", look=-0.6)
    character(cv, "malkin", 520, 2250, 1.6, "regret", "chest", look=0.8)

@shot("apology", "in", ("bokeh",))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 650, 3150, 2.7, "regret", "namaste", look=0.0, tear=True, shadow=False)

@shot("namaste", "in", ("bokeh", "sparkle"))
def _(cv):
    living_bg(cv, FY)
    cv.glow(650, 800, 500, "#ffd070", 0.35)
    character(cv, "sunita", 650, 3150, 2.7, "smile", "namaste", look=0.0, tear=True, shadow=False)

@shot("namaste2", "out", ("bokeh", "sparkle"))
def _(cv):
    living_bg(cv, FY)
    character(cv, "malkin", 880, 2120, 1.3, "regret", "namaste", look=-0.7, tear=True)
    character(cv, "sunita", 380, 2080, 1.25, "smile", "namaste", look=0.7)

@shot("puja", "out", ("bokeh", "flicker", "sparkle"))
def _(cv):
    puja_bg(cv, 1600)
    # bhog
    cv.rect(380, 1200, 920, 1250, "#8a4a1a")
    silver_plate(cv, 650, 1190, 0.85)
    for x in (300, 420, 880, 1000):
        diya(cv, x, 1260, 1.3)
    brass_set(cv, 650, 1330, 0.0001) if False else None
    character(cv, "samdhan", 1080, 2250, 1.05, "smile", "namaste", look=-0.4)
    character(cv, "malkin", 700, 2290, 1.15, "smile", "namaste", look=0.0)
    character(cv, "sunita", 300, 2270, 1.12, "smile", "namaste", look=0.3)
    for x in range(120, 1250, 150):
        diya(cv, x, 2290, 1.1)

@shot("diya_end", "in", ("bokeh", "flicker"))
def _(cv):
    cv.vgrad(0, 0, W, H, "#1a0604", "#3a1208")
    # blurred lakshmi silhouette glow in background
    cv.glow(650, 700, 420, "#ff9a2a", 0.5)
    cv.ell(650, 640, 150, 150, "#5a2a10")
    cv.ell(650, 640, 120, 120, "#7a3a14")
    cv.ell(650, 960, 260, 220, "#5a1a0c")
    cv.rect(0, 1600, W, H, "#2a0e06")
    diya(cv, 600, 1560, 6.0)
