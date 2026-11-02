import json, numpy as np, subprocess, wave
from scipy.signal import butter, sosfilt
from script import SEG

SR = 48000
rng = np.random.default_rng(7)
durs = json.load(open("vo/durs.json"))

# ---------------- timeline ----------------
BIG = {"tv", "rotten", "sunita_rise", "c_pan", "present", "puja", "diya_end", "malkin_point", "stunned"}
t = 0.7
tl = []
for i, ((sp, txt, shot, hl), d) in enumerate(zip(SEG, durs)):
    tl.append(dict(i=i, sp=sp, text=txt, shot=shot, hl=hl, start=round(t, 3), end=round(t + d, 3)))
    nxt = SEG[i + 1][2] if i + 1 < len(SEG) else None
    if nxt is None: gap = 0
    elif nxt in BIG: gap = 0.75
    elif nxt.endswith("2"): gap = 0.2
    elif nxt.startswith("c_") and shot.startswith("c_"): gap = 0.28
    else: gap = 0.4
    t += d + gap
TOTAL = round(t + 3.2, 3)
LEAD = 0.18
for k, s in enumerate(tl):
    s["v0"] = 0.0 if k == 0 else round(s["start"] - LEAD, 3)
for k, s in enumerate(tl):
    s["v1"] = tl[k + 1]["v0"] if k + 1 < len(tl) else TOTAL
json.dump(dict(total=TOTAL, shots=tl), open("timeline.json", "w"), ensure_ascii=False, indent=1)
print("total", TOTAL)
N = int(TOTAL * SR)
T = lambda name: next(s for s in tl if s["shot"] == name)

def lp(x, f, order=2):
    return sosfilt(butter(order, f, "low", fs=SR, output="sos"), x)
def hp(x, f, order=2):
    return sosfilt(butter(order, f, "high", fs=SR, output="sos"), x)
def bp(x, f0, f1, order=2):
    return sosfilt(butter(order, [f0, f1], "band", fs=SR, output="sos"), x)
def env(n, a, d):  # attack (s), exp decay tau (s)
    tt = np.arange(n) / SR
    e = np.exp(-tt / d)
    na = max(1, int(a * SR))
    e[:na] *= np.linspace(0, 1, na)
    return e
def add(buf, x, at, g=1.0):
    i = int(at * SR)
    if i >= len(buf): return
    x = x[: len(buf) - i]
    buf[i:i + len(x)] += x * g
def hz(semi, base=146.83):  # D3 = Sa
    return base * 2 ** (semi / 12)

# ---------------- instruments ----------------
def tanpura(freq, dur=3.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = sum((1 / k) * np.sin(2 * np.pi * freq * k * tt * (1 + 0.0004 * k)) for k in range(1, 12))
    x *= env(n, 0.01, 1.4)
    return x * 0.25

def flute(freq, dur):
    n = int(dur * SR); tt = np.arange(n) / SR
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * tt) * np.clip(tt / 0.3, 0, 1)
    ph = 2 * np.pi * np.cumsum(freq * vib) / SR
    x = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    x += 0.05 * bp(rng.standard_normal(n), freq * 0.8, min(freq * 3, 20000))
    a = np.clip(tt / 0.08, 0, 1) * np.clip((dur - tt) / 0.15, 0, 1)
    return x * a * 0.22

def piano(freq, dur=3.0, vel=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.zeros(n)
    for k in range(1, 8):
        fk = freq * k * np.sqrt(1 + 0.0002 * k * k)
        x += (0.7 ** k) * np.sin(2 * np.pi * fk * tt) * np.exp(-tt * (0.9 + 0.5 * k))
    x[: 200] *= np.linspace(0, 1, 200)
    return x * 0.3 * vel

def pad(freqs, dur, bright=1800):
    n = int(dur * SR); tt = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.004, 0, 0.004):
            ph = (f * (1 + det) * tt) % 1.0
            x += (2 * ph - 1)
    x = lp(x, bright, 2) / (len(freqs) * 3)
    a = np.clip(tt / 1.2, 0, 1) * np.clip((dur - tt) / 1.2, 0, 1)
    return x * a * 0.5

def tabla_dha(v=1.0):
    n = int(0.6 * SR); tt = np.arange(n) / SR
    f = 70 + 60 * np.exp(-tt * 18)
    low = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 6)
    high = (np.sin(2 * np.pi * 520 * tt) + 0.5 * np.sin(2 * np.pi * 1040 * tt)) * np.exp(-tt * 14)
    return (low * 0.9 + high * 0.35) * v * 0.5

def tabla_na(v=1.0):
    n = int(0.3 * SR); tt = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 560 * tt) + 0.4 * np.sin(2 * np.pi * 1500 * tt)) * np.exp(-tt * 22)
    x += 0.2 * hp(rng.standard_normal(n), 3000) * np.exp(-tt * 60)
    return x * v * 0.3

def bell(freq=880, dur=4.0, g=1.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    parts = [(1, 1, 1.2), (2.76, 0.6, 2.0), (5.4, 0.35, 3.0), (8.93, 0.2, 4.5), (0.5, 0.5, 0.9)]
    x = sum(a * np.sin(2 * np.pi * freq * r * tt) * np.exp(-tt * d) for r, a, d in parts)
    return x * 0.25 * g

def noise(dur):
    return rng.standard_normal(int(dur * SR))

# ---------------- music ----------------
mus = np.zeros(N)
A0, A1 = 0.0, T("tv")["v0"]
B0, B1 = A1, T("c_pan")["v0"]
C0, C1 = B1, T("present")["v0"]
D0, D1 = C1, TOTAL
XF = 1.5

def section(t0, t1, fn):
    seg = np.zeros(N)
    fn(seg, t0, t1)
    tt = np.arange(N) / SR
    w = np.clip((tt - (t0 - XF)) / XF, 0, 1) * np.clip(((t1 + XF) - tt) / XF, 0, 1)
    if t0 <= 0: w = np.clip(((t1 + XF) - tt) / XF, 0, 1)
    return seg * w

def festive(buf, t0, t1):
    bpm = 96; beat = 60 / bpm
    t = max(0, t0 - XF)
    while t < t1 + XF:
        add(buf, tanpura(hz(-5)), t, 0.8); add(buf, tanpura(hz(0)), t + beat, 0.7)
        add(buf, tanpura(hz(0)), t + 2 * beat, 0.7); add(buf, tanpura(hz(-12)), t + 3 * beat, 0.9)
        t += 4 * beat
    pat = ["dha", "ge", "na", "ti", "na", "ka", "dhi", "na"]
    t = max(0, t0 - XF) + 4 * beat; k = 0
    while t < t1 + XF:
        p = pat[k % 8]
        add(buf, tabla_dha(0.9) if p in ("dha", "dhi", "ge") else tabla_na(0.9), t)
        t += beat / 2; k += 1
    mel = [0, 2, 4, 7, 9, 7, 4, 2, 4, 7, 12, 9, 7, 4, 2, 0, 2, 4, 2, 0, -3, 0, 2, 0]
    t = max(0, t0 - XF) + 2 * beat; k = 0
    while t < t1:
        d = beat * (2 if k % 4 == 3 else 1)
        add(buf, flute(hz(mel[k % len(mel)] + 12), d * 1.05), t, 0.9)
        t += d; k += 1

def suspense(buf, t0, t1):
    t = t0 - XF
    chords = [[0, 3, 7], [-2, 1, 5], [-4, 0, 3], [-5, -1, 2]]
    k = 0
    while t < t1 + XF:
        add(buf, pad([hz(c - 12) for c in chords[k % 4]], 4.6, 900), t, 1.2)
        t += 4.0; k += 1
    t = t0
    while t < t1 + XF:   # heartbeat
        add(buf, lp(tabla_dha(1.0), 200), t, 1.1); add(buf, lp(tabla_dha(0.7), 200), t + 0.28, 0.9)
        t += 1.1
    tt = np.arange(int((t1 - t0 + 2 * XF) * SR)) / SR  # low drone with tremolo strings
    dr = (np.sin(2 * np.pi * hz(-24) * tt) + 0.5 * np.sin(2 * np.pi * hz(-17) * tt)) * 0.12
    tr = pad([hz(3), hz(7)], len(tt) / SR, 2500) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * tt))
    add(buf, dr + tr * 0.6, t0 - XF)

def cooking(buf, t0, t1):
    bpm = 108; beat = 60 / bpm
    t = t0 - XF; k = 0
    prog = [[0, 4, 7], [-3, 0, 4], [5, 9, 12], [7, 11, 14]]
    while t < t1 + XF:
        ch = prog[(k // 8) % 4]
        add(buf, piano(hz(ch[k % 3] + 12), 1.2, 0.8), t)
        if k % 2 == 0: add(buf, tabla_na(0.8), t)
        if k % 8 == 0: add(buf, tabla_dha(1.0), t); add(buf, pad([hz(c) for c in ch], 4.6, 1500), t, 0.7)
        if k % 8 == 5: add(buf, tabla_dha(0.7), t)
        t += beat / 2; k += 1
    mel = [7, 9, 12, 9, 7, 4, 7, 9, 4, 2, 0, 2, 4, 7, 4, 2]
    t = t0 + 2 * beat; k = 0
    while t < t1:
        add(buf, flute(hz(mel[k % 16] + 12), beat * 0.95), t, 0.7)
        t += beat; k += 1

def emotional(buf, t0, t1):
    prog = [[0, 4, 7], [-3, 0, 4], [-7, -3, 0], [-5, -1, 2]]
    t = t0 - XF; k = 0
    while t < t1 + XF:
        ch = prog[k % 4]
        add(buf, pad([hz(c) for c in ch] + [hz(ch[0] - 12)], 4.8, 1600), t, 1.0)
        for j, c in enumerate([ch[0], ch[1], ch[2], ch[1] + 12, ch[2], ch[1]]):
            add(buf, piano(hz(c + 12), 3.0, 0.7), t + j * 0.66)
        t += 4.0; k += 1
    mel = [(4, 2), (7, 1), (9, 1), (7, 2), (4, 2), (2, 2), (4, 1), (0, 3), (-3, 2), (0, 2), (2, 2), (4, 4)]
    t = t0 + 2.0; k = 0
    while t < t1 - 2:
        n, d = mel[k % len(mel)]
        add(buf, flute(hz(n + 12), d * 0.66 * 1.05), t, 0.8)
        t += d * 0.66; k += 1

mus += section(A0, A1, festive)
mus += section(B0, B1, suspense)
mus += section(C0, C1, cooking)
mus += section(D0, D1, emotional)
mus /= np.max(np.abs(mus)) + 1e-9
tt = np.arange(N) / SR
mus *= np.clip(tt / 0.6, 0, 1) * np.clip((TOTAL - tt) / 2.5, 0, 1)

# ---------------- voice ----------------
vo = np.zeros(N)
def readwav(p):
    with wave.open(p) as w:
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float64) / 32768
for s in tl:
    x = readwav(f"vo/{s['i']:02d}.wav")
    if s["sp"] == "T":  # TV speaker colour
        x = bp(x, 300, 3400) * 1.6
    add(vo, x, s["start"])
vo /= np.max(np.abs(vo)) + 1e-9
vo *= 0.89

# ducking envelope from voice activity
act = np.zeros(N)
for s in tl:
    a, b = int((s["start"] - 0.15) * SR), int((s["end"] + 0.25) * SR)
    act[max(0, a):b] = 1
k = int(0.25 * SR)
act = np.convolve(act, np.ones(k) / k, mode="same")
duck = 1 - 0.62 * act
music_gain = 0.20

# ---------------- SFX ----------------
sfx = np.zeros(N)
def at(name, off=0.0, which="v0"):
    return T(name)[which] + off

def crackers(t0, t1, n):
    for _ in range(n):
        tt0 = rng.uniform(t0, t1)
        x = lp(noise(0.5), 900) * env(int(0.5 * SR), 0.002, 0.08)
        add(sfx, x, tt0, rng.uniform(0.1, 0.25))

# opening: big temple bell + crackers
add(sfx, bell(660, 5, 1.4), 0.05); add(sfx, bell(990, 4, 0.6), 0.1)
crackers(0.2, at("mop_wide"), 8)
# mop swishes
for k in range(5):
    tt0 = at("mop_wide", 0.4 + k * 0.85)
    n = int(0.6 * SR)
    sw = bp(noise(0.6), 800, 4000) * np.sin(np.linspace(0, np.pi, n)) ** 2
    add(sfx, sw, tt0, 0.18)
    add(sfx, bp(noise(0.3), 2000, 7000) * env(int(0.3 * SR), 0.01, 0.06), tt0 + 0.2, 0.06)
# insult tension hit
def hit(t0, g=1.0, f=55):
    n = int(2.5 * SR); tt = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * tt * (1 + 0.5 * np.exp(-tt * 8))) * np.exp(-tt * 1.6)
    x += lp(noise(2.5), 400) * np.exp(-tt * 4) * 0.5
    add(sfx, x, t0, 0.7 * g)
def whoosh(t0, dur=0.7, g=0.3):
    n = int(dur * SR)
    x = bp(noise(dur), 300, 3000) * np.sin(np.linspace(0, np.pi, n)) ** 3
    add(sfx, x, t0 - dur * 0.6, g)
hit(at("malkin_point"), 0.7)
add(sfx, piano(hz(1 - 12), 3, 1.0), at("katli_box"))
for k in range(6):
    add(sfx, bell(2600 + k * 300, 1.2, 0.25), at("katli_box", 0.2 + k * 0.18))
hit(at("malkin_warn"), 0.4, 70)
# breaking news sting
tv0 = at("tv")
whoosh(tv0, 0.9, 0.35)
for k in range(3):
    n = int(0.16 * SR); tt = np.arange(n) / SR
    add(sfx, np.sign(np.sin(2 * np.pi * 880 * tt)) * 0.15 * env(n, 0.005, 0.1), tv0 + k * 0.2)
hit(tv0 + 0.6, 0.6, 50)
add(sfx, np.sin(2 * np.pi * 70 * np.arange(int(1.5 * SR)) / SR) * env(int(1.5 * SR), 0.01, 0.5), at("tv2"), 0.6)
hit(at("malkin_shock"), 0.6, 60)
# door knock + creak
for k in range(3):
    add(sfx, lp(noise(0.12), 600) * env(int(0.12 * SR), 0.001, 0.03), at("door", 1.2 + k * 0.2), 0.5)
n = int(1.0 * SR); tt = np.arange(n) / SR
add(sfx, np.sin(2 * np.pi * np.cumsum(300 + 200 * np.sin(2 * np.pi * 1.3 * tt)) / SR) * 0.08 * np.sin(np.linspace(0, np.pi, n)), at("door", 1.9))
# rotten reveal: suspense hit + flies
hit(at("rotten"), 1.0, 45); whoosh(at("rotten"), 0.8, 0.3)
n = int(4 * SR); tt = np.arange(n) / SR
fly = np.sin(2 * np.pi * np.cumsum(190 + 30 * np.sin(2 * np.pi * 3 * tt)) / SR) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.7 * tt))
add(sfx, bp(fly, 150, 2000) * np.clip(tt / 0.5, 0, 1) * np.clip((4 - tt), 0, 1), at("rotten", 0.5), 0.08)
# clock ticking during despair
for k in range(int((at("stunned") - at("malkin_despair")) / 0.5)):
    add(sfx, hp(noise(0.03), 2500) * env(int(0.03 * SR), 0.001, 0.008), at("malkin_despair", k * 0.5), 0.25)
hit(at("stunned"), 0.5, 40)
whoosh(at("sunita_rise"), 0.8, 0.25)
add(sfx, bell(1320, 3, 0.4), at("sunita_confident", 0.1))
# cooking SFX
def sizzle(t0, dur, g):
    x = hp(noise(dur), 2500) * (0.6 + 0.4 * rng.random(int(dur * SR)) ** 8)
    x *= np.clip(np.arange(len(x)) / SR / 0.3, 0, 1) * np.clip((dur - np.arange(len(x)) / SR) / 0.4, 0, 1)
    add(sfx, x, t0, g)
def gasclick(t0):
    add(sfx, hp(noise(0.02), 3000) * env(int(0.02 * SR), 0.0005, 0.004), t0, 0.5)
    add(sfx, lp(noise(0.8), 1500) * np.sin(np.linspace(0, np.pi, int(0.8 * SR))) ** 0.5, t0 + 0.1, 0.12)
gasclick(at("c_pan", 0.1))
for k in range(14):  # peanuts dropping
    add(sfx, bp(noise(0.05), 1500, 6000) * env(int(0.05 * SR), 0.001, 0.012), at("c_pan", 0.6 + k * 0.09 + rng.uniform(0, 0.05)), 0.25)
sizzle(at("c_pan"), at("c_rub") - at("c_pan"), 0.05)
for k in range(8):
    add(sfx, bp(noise(0.25), 400, 2500) * np.sin(np.linspace(0, np.pi, int(0.25 * SR))), at("c_rub", 0.2 + k * 0.3), 0.15)
for k in range(5):  # mixer pulses
    d = 0.45; n = int(d * SR); tt = np.arange(n) / SR
    m = (np.sign(np.sin(2 * np.pi * 95 * tt)) * 0.5 + lp(noise(d), 3000)) * np.clip(tt / 0.03, 0, 1) * np.clip((d - tt) / 0.05, 0, 1)
    add(sfx, m, at("c_mixer", 0.4 + k * 0.85), 0.12)
for k in range(8):
    add(sfx, hp(noise(0.2), 4000) * np.sin(np.linspace(0, np.pi, int(0.2 * SR))), at("c_sieve", 0.1 + k * 0.18), 0.06)
sizzle(at("c_syrup"), at("c_roll") - at("c_syrup"), 0.04)
for k in range(10):  # bubbles
    n = int(0.08 * SR); tt = np.arange(n) / SR
    f = rng.uniform(300, 700)
    add(sfx, np.sin(2 * np.pi * np.cumsum(f + 900 * tt / 0.08) / SR) * env(n, 0.002, 0.03), at("c_syrup", 0.5 + k * 0.5 + rng.uniform(0, 0.3)), 0.1)
for k in range(6):  # stirring
    add(sfx, bp(noise(0.4), 200, 1500) * np.sin(np.linspace(0, np.pi, int(0.4 * SR))), at("c_dough", 0.2 + k * 0.5), 0.15)
for k in range(3):  # rolling pin
    add(sfx, lp(noise(0.6), 500) * np.sin(np.linspace(0, np.pi, int(0.6 * SR))), at("c_roll", 0.1 + k * 0.65), 0.25)
for k in range(5):  # vark sparkles
    add(sfx, bell(3000 + k * 450, 1.0, 0.12), at("c_vark", 0.1 + k * 0.12))
for k in range(8):  # knife cuts
    add(sfx, hp(noise(0.04), 1500) * env(int(0.04 * SR), 0.001, 0.01), at("c_cut", 0.2 + k * 0.25), 0.35)
    add(sfx, lp(noise(0.05), 300) * env(int(0.05 * SR), 0.001, 0.015), at("c_cut", 0.22 + k * 0.25), 0.4)
# magic reveal
for k in range(9):
    add(sfx, bell(1800 + k * 260, 1.5, 0.2), at("present", 0.0 + k * 0.07))
add(sfx, bell(1320, 2.5, 0.3), at("taste"))
# puja bells & ambience
for k in range(4):
    add(sfx, bell(700, 5, 0.8), at("puja", 0.0 + k * 1.6))
    add(sfx, bell(1400, 3, 0.3), at("puja", 0.8 + k * 1.6))
crackers(at("puja"), TOTAL - 2, 6)
add(sfx, bell(660, 6, 1.0), at("diya_end", 0.2))

# ---------------- mix ----------------
mix_ = vo + mus * music_gain * duck + sfx * 0.55 * (1 - 0.35 * act)
mix_ = np.tanh(mix_ * 1.1) / np.tanh(1.1)
mix_ /= np.max(np.abs(mix_)) / 0.95
st = np.stack([mix_, mix_], 1)
with wave.open("mix_raw.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "mix_raw.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-ar", "48000", "mix.wav"], check=True)
print("ok")
