import json, re
TL = json.load(open("timeline.json"))
shots = TL["shots"]

GOLD = r"{\c&H33D2FF&}"   # #FFD233 in BGR
WHITE = r"{\c&HFFFFFF&}"
KEY = ["लक्ष्मी पूजा", "लक्ष्मी पूजन", "करोड़पति", "काजू कतली", "कतली", "मूँगफली", "ज़हरीली", "सड़ी", "बदबू", "भोग",
       "शुभ मुहूर्त", "दस मिनट", "दो कप", "चाँदी का वर्क", "मिल्क पाउडर", "एक-तार", "घी", "अमृत", "कमाल", "माफ़",
       "इज़्ज़त", "इंसान", "मेहनत", "सात्विक", "शुद्ध", "थकान", "सबसे महँगी", "सस्ती", "ब्रेकिंग न्यूज़", "मुस्कुराई", "दीये"]
SPK = {"M": ("मालकिन", "&H2A0F8B&"), "S": ("सुनीता", "&H94804F&"), "D": ("समधन जी", "&H3A6B2F&"), "T": ("टीवी समाचार", "&H1A0FD4&")}

def ts(t):
    t = max(0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def hilite(txt):
    for k in sorted(KEY, key=len, reverse=True):
        txt = txt.replace(k, "\x01" + k + "\x02")
    # collapse nested markers
    out, depth = "", 0
    for ch in txt:
        if ch == "\x01":
            if depth == 0: out += GOLD
            depth += 1
        elif ch == "\x02":
            depth -= 1
            if depth == 0: out += WHITE
        else: out += ch
    return out

def chunks(text, maxc=38):
    words = text.split()
    out, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > maxc:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
        if re.search(r"[।!?]$", w) and len(cur) > 14:
            out.append(cur); cur = ""
    if cur: out.append(cur)
    # merge tiny tail
    if len(out) > 1 and len(out[-1]) < 8:
        tail = out.pop(); out[-1] += " " + tail
    return out

def wrap2(c, lim=20):
    if len(c) <= lim: return c
    words = c.split(); best, bd = c, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        d = abs(len(a) - len(b))
        if d < bd: bd, best = d, a + r"\N" + b
    return best

head = r"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Noto Sans Devanagari,112,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,6,4,2,70,70,300,1
Style: Spk,Noto Sans Devanagari,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,10,0,2,90,90,640,1
Style: Ban,Noto Sans Devanagari,82,&H00101A6A,&H00FFFFFF,&H0033C8F5,&H00000000,-1,0,0,0,100,100,0,0,3,22,0,8,60,60,150,1
Style: Title,Noto Sans Devanagari,136,&H0033D2FF,&H00FFFFFF,&H00081040,&HA0000000,-1,0,0,0,100,100,0,0,1,7,6,8,50,50,150,1
Style: Sub,Noto Sans Devanagari,66,&H00FFFFFF,&H00FFFFFF,&H00081040,&H96000000,-1,0,0,0,100,100,0,0,1,4,3,8,50,50,370,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
ev = []
POP = r"{\fad(90,70)\fscx88\fscy88\t(0,140,\fscx100\fscy100)}"
for s in shots:
    cs = chunks(s["text"])
    total = sum(len(c) for c in cs)
    t = s["start"] - 0.05
    dur = s["end"] - s["start"]
    for i, c in enumerate(cs):
        d = dur * len(c) / total
        end = t + d + (0.12 if i == len(cs) - 1 else 0)
        ev.append(f"Dialogue: 1,{ts(t)},{ts(end)},Cap,,0,0,0,,{POP}{hilite(wrap2(c))}")
        t += d
    if s["sp"] in SPK:
        nm, col = SPK[s["sp"]]
        ev.append(f"Dialogue: 2,{ts(s['start'] - 0.05)},{ts(s['end'] + 0.1)},Spk,,0,0,0,,{{\\fad(80,80)\\3c{col}}}{nm}")

# opening title + banners
ev.append(r"Dialogue: 3,0:00:00.15,0:00:03.10,Title,,0,0,0,,{\fad(150,250)\fscx70\fscy70\t(0,260,\fscx104\fscy104)\t(260,420,\fscx100\fscy100)}लक्ष्मी पूजा की मिठाई")
ev.append(r"Dialogue: 3,0:00:00.55,0:00:03.10,Sub,,0,0,0,,{\fad(200,250)}एक गरीब नौकरानी ने बचाई पूजा की इज़्ज़त")
for s in shots:
    if not s["hl"]: continue
    t0 = s["start"]; t1 = max(s["end"] + 0.4, t0 + 2.6)
    if s["i"] == 0:
        t0, t1 = 3.15, 5.6
    ev.append(f"Dialogue: 4,{ts(t0)},{ts(t1)},Ban,,0,0,0,,{{\\fad(60,200)\\fscx0\\fscy0\\t(0,170,\\fscx112\\fscy112)\\t(170,280,\\fscx100\\fscy100)}}{s['hl']}")
open("captions.ass", "w").write(head + "\n".join(ev) + "\n")
print(len(ev))
