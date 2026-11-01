"""Captions: phrase grouping, SRT, and ASS with karaoke word highlighting."""
from __future__ import annotations

from pathlib import Path


def group_phrases(words: list[dict], max_words: int = 5, max_chars: int = 28, max_gap: float = 0.45,
                  max_dur: float = 2.6) -> list[list[dict]]:
    """Break on punctuation, pauses, length — never mid-idea when avoidable."""
    phrases, cur = [], []
    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            text_len = len(" ".join(x["word"] for x in cur + [w]))
            if (len(cur) >= max_words or text_len > max_chars or gap > max_gap
                    or w["end"] - cur[0]["start"] > max_dur or cur[-1]["word"][-1:] in ".?!,;:"):
                phrases.append(cur); cur = []
        cur.append(w)
    if cur:
        phrases.append(cur)
    return phrases


def _srt_t(t: float) -> str:
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _ass_t(t: float) -> str:
    cs = int(round(t * 100)); h, cs = divmod(cs, 360000); m, cs = divmod(cs, 6000); s, cs = divmod(cs, 100)
    return f"{h}:{m:02}:{s:02}.{cs:02}"


def write_srt(words: list[dict], path: str | Path, **kw) -> Path:
    lines = []
    for n, ph in enumerate(group_phrases(words, **kw), 1):
        end = ph[-1]["end"] + 0.15
        lines += [str(n), f"{_srt_t(ph[0]['start'])} --> {_srt_t(end)}", " ".join(w["word"] for w in ph), ""]
    Path(path).write_text("\n".join(lines))
    return Path(path)


def write_ass(words: list[dict], path: str | Path, width: int = 1920, height: int = 1080,
              font: str = "DejaVu Sans", size: int | None = None, primary: str = "&H00FFFFFF",
              highlight: str = "&H0033C8FF", outline: str = "&H00401A2E", margin_v: int | None = None,
              **kw) -> Path:
    """Karaoke ASS: each word fills with `highlight` exactly while it is spoken (\\kf).

    Colours are ASS BGR: highlight default = warm gold, outline = deep purple.
    """
    size = size or int(height * 0.058)
    margin_v = margin_v if margin_v is not None else int(height * 0.07)
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,{font},{size},{highlight},{primary},{outline},&H80000000,-1,0,0,0,100,100,1,0,1,{max(3, size // 12)},{max(2, size // 24)},2,80,80,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for ph in group_phrases(words, **kw):
        start, end = ph[0]["start"], ph[-1]["end"] + 0.2
        parts, t = [], start
        for w in ph:
            if w["start"] > t:  # silent lead-in before this word
                parts.append(f"{{\\k{int(round((w['start'] - t) * 100))}}}")
            parts.append(f"{{\\kf{max(1, int(round((w['end'] - w['start']) * 100)))}}}{w['word']} ")
            t = w["end"]
        # subtle pop-in: scale from 92% → 100% in 120ms
        ev.append(f"Dialogue: 0,{_ass_t(start)},{_ass_t(end)},Karaoke,,0,0,0,,"
                  f"{{\\fad(80,60)\\fscx92\\fscy92\\t(0,120,\\fscx100\\fscy100)}}{''.join(parts).strip()}")
    Path(path).write_text(head + "\n".join(ev) + "\n")
    return Path(path)


def caption_qc(words: list[dict], min_word: float = 0.06, max_cps: float = 20.0) -> list[str]:
    """Subtitle quality checks: overlaps, impossible durations, reading speed."""
    issues = []
    for a, b in zip(words, words[1:]):
        if b["start"] < a["end"] - 0.02:
            issues.append(f"overlap: '{a['word']}'@{a['start']} / '{b['word']}'@{b['start']}")
    for w in words:
        if w["end"] - w["start"] < min_word:
            issues.append(f"too short to read: '{w['word']}'@{w['start']}")
    for ph in group_phrases(words):
        chars = len(" ".join(w["word"] for w in ph)); dur = ph[-1]["end"] - ph[0]["start"] + 0.2
        if chars / dur > max_cps:
            issues.append(f"reading speed {chars / dur:.1f} cps > {max_cps} at {ph[0]['start']:.2f}s")
    return issues
