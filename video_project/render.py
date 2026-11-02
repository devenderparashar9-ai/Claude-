import json, math, subprocess, sys, os, numpy as np
from multiprocessing import Pool
from PIL import Image
from scenes import SH

FPS = 30
OW, OH = 1080, 1920
TL = json.load(open("timeline.json"))
TOTAL = TL["total"]
shots = TL["shots"]
os.makedirs("parts", exist_ok=True)

def sprite(r, sharp=2.0):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    d = np.sqrt(x * x + y * y) / r
    return np.clip(1 - d, 0, 1) ** sharp

SPR = {r: sprite(r) for r in (6, 10, 16, 24, 34, 48, 70)}
STAR = {}
for r in (10, 16, 24):
    y, x = np.mgrid[-r:r + 1, -r:r + 1]
    a = np.clip(1 - np.abs(x) / r, 0, 1) * np.exp(-(y / (r * 0.08)) ** 2) + np.clip(1 - np.abs(y) / r, 0, 1) * np.exp(-(x / (r * 0.08)) ** 2)
    a += SPR[min(SPR, key=lambda k: abs(k - r // 2))].copy().__array__()[: 2 * r + 1, : 2 * r + 1] if False else 0
    STAR[r] = np.clip(a, 0, 1)

def blit(frame, spr, cx, cy, col, alpha):
    r = spr.shape[0] // 2
    x0, y0 = int(cx) - r, int(cy) - r
    x1, y1 = x0 + spr.shape[1], y0 + spr.shape[0]
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(OW, x1), min(OH, y1)
    if x0c >= x1c or y0c >= y1c: return
    s = spr[sy0:sy0 + (y1c - y0c), sx0:sx0 + (x1c - x0c)][..., None] * alpha
    reg = frame[y0c:y1c, x0c:x1c]
    reg += (np.array(col, np.float32) - reg * 0) * s * (1 - reg / 300.0)  # soft additive

def ease(t):
    return t * t * (3 - 2 * t)

def camera(move, u, cooking):
    e = ease(u)
    if cooking:
        c0, c1 = (0.74, 0.62) if move != "out" else (0.62, 0.74)
        cx, cy = 0.5, 0.56
        if move == "pan_r": c0 = c1 = 0.66; cx = 0.44 + 0.12 * e
        if move == "down": c0 = c1 = 0.7; cy = 0.48 + 0.12 * e
        c = c0 + (c1 - c0) * e
        return c, cx, cy
    if move == "in": c, cx, cy = 0.95 - 0.13 * e, 0.5, 0.48
    elif move == "out": c, cx, cy = 0.80 + 0.13 * e, 0.5, 0.5
    elif move == "pan_r": c, cx, cy = 0.84, 0.42 + 0.16 * e, 0.52
    elif move == "pan_l": c, cx, cy = 0.84, 0.58 - 0.16 * e, 0.52
    elif move == "up": c, cx, cy = 0.86, 0.5, 0.58 - 0.12 * e
    elif move == "down": c, cx, cy = 0.86, 0.5, 0.44 + 0.12 * e
    else: c, cx, cy = 0.85, 0.5, 0.5
    return c, cx, cy

GRAIN = [np.random.default_rng(i).normal(0, 5.0, (OH // 2, OW // 2, 1)).astype(np.float32) for i in range(6)]

def render_shot(k):
    s = shots[k]
    name = s["shot"]
    f, move, fx = SH[name]
    still = Image.open(f"stills/{name}.png")
    SW, SHh = still.size
    cooking = name.startswith("c_")
    n = max(1, round(s["v1"] * FPS) - round(s["v0"] * FPS))
    rng = np.random.default_rng(100 + k)
    bok = [(rng.uniform(0, OW), rng.uniform(0, OH), rng.choice([16, 24, 34, 48]), rng.uniform(-8, 8), rng.uniform(-22, -6),
            [(255, 190, 90), (255, 140, 60), (255, 220, 150), (255, 120, 160)][rng.integers(4)], rng.uniform(0.15, 0.35), rng.uniform(0, 6)) for _ in range(22)]
    stm = [(rng.uniform(OW * 0.3, OW * 0.7), rng.uniform(0, 1), rng.choice([48, 70]), rng.uniform(0.5, 1.2)) for _ in range(14)]
    spk = [(rng.uniform(OW * 0.1, OW * 0.9), rng.uniform(OH * 0.2, OH * 0.75), rng.choice([10, 16, 24]), rng.uniform(0, 6), rng.uniform(2, 5)) for _ in range(12)]
    dust = [(rng.uniform(OW * 0.25, OW * 0.75), rng.uniform(0, 1), rng.uniform(0.3, 0.8)) for _ in range(60)]
    out = f"parts/{k:02d}.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n):
        u = i / max(1, n - 1)
        tsec = i / FPS
        c, cx, cy = camera(move, u, cooking)
        if "shake" in fx and tsec < 0.7:
            amp = 0.006 * (1 - tsec / 0.7)
            cx += rng.uniform(-amp, amp); cy += rng.uniform(-amp, amp) * 0.6
        cw, ch = SW * c, SHh * c
        x0 = min(max(0, cx * SW - cw / 2), SW - cw); y0 = min(max(0, cy * SHh - ch / 2), SHh - ch)
        img = still.resize((OW, OH), Image.BICUBIC, box=(x0, y0, x0 + cw, y0 + ch))
        fr = np.asarray(img, np.float32).copy()
        if "flicker" in fx or "flame" in fx:
            fr *= 1 + 0.035 * math.sin(tsec * 13.0 + k) * math.sin(tsec * 7.3)
        if "bokeh" in fx:
            for (bx, by, r, vx, vy, col, a, ph) in bok:
                X = (bx + vx * tsec) % OW; Y = (by + vy * tsec) % OH
                blit(fr, SPR[r], X, Y, col, a * (0.6 + 0.4 * math.sin(tsec * 1.5 + ph)))
        if "steam" in fx or "fumes" in fx:
            col = (230, 230, 225) if "steam" in fx else (140, 190, 90)
            for (sx, ph, r, sp) in stm:
                life = (ph + tsec * 0.18 * sp) % 1.0
                Y = OH * (0.62 - 0.45 * life); X = sx + 40 * math.sin(life * 6 + ph * 9)
                blit(fr, SPR[r], X, Y, col, 0.22 * math.sin(life * math.pi))
        if "sparkle" in fx:
            for (sx, sy, r, ph, sp) in spk:
                a = max(0, math.sin(tsec * sp + ph)) ** 3
                blit(fr, STAR[r], sx, sy, (255, 250, 230), 0.9 * a)
        if "dust" in fx:
            for (dx, ph, sp) in dust:
                life = (ph + tsec * sp) % 1.0
                blit(fr, SPR[6], dx + 10 * math.sin(life * 9), OH * (0.45 + 0.35 * life), (250, 240, 220), 0.6)
        if "flash" in fx and tsec < 0.35:
            fr += (255 - fr) * (1 - tsec / 0.35) * 0.85
        # global fade in / out
        gt = s["v0"] + tsec
        if gt < 0.35: fr *= gt / 0.35
        if gt > TOTAL - 1.8: fr *= max(0, (TOTAL - gt) / 1.8)
        g = GRAIN[i % 6]
        fr[::2, ::2] += g; fr[1::2, 1::2] += g
        p.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close(); p.wait()
    return k, n

if __name__ == "__main__":
    ks = [int(a) for a in sys.argv[1:]] or list(range(len(shots)))
    with Pool(4) as pool:
        for k, n in pool.imap_unordered(render_shot, ks):
            print("done", k, n, flush=True)
