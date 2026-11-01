"""Deterministic analysis: scene cuts, silence, black frames, frozen frames."""
from __future__ import annotations

import re
from pathlib import Path

from .common import ffmpeg, media_duration

_F = r"(-?\d+(?:\.\d+)?)"


def scenes(path: str | Path, threshold: float = 0.3) -> list[dict]:
    """Scene changes via the scdet filter. Returns [{time, score}]."""
    p = ffmpeg(["-i", str(path), "-an", "-vf", f"scdet=threshold={threshold * 100:.1f}", "-f", "null", "-"])
    hits = re.findall(rf"lavfi\.scd\.score:\s*{_F},\s*lavfi\.scd\.time:\s*{_F}", p.stderr)
    return [{"time": float(t), "score": float(s)} for s, t in hits]


def shots(path: str | Path, threshold: float = 0.3, min_len: float = 0.5) -> list[dict]:
    """Shot list (start/end) derived from scene cuts, with a rough size classification hook."""
    dur = media_duration(path)
    cuts = [0.0] + [c["time"] for c in scenes(path, threshold)] + [dur]
    out = []
    for a, b in zip(cuts, cuts[1:]):
        if b - a >= min_len:
            out.append({"start": round(a, 3), "end": round(b, 3), "duration": round(b - a, 3)})
    return out


def silences(path: str | Path, noise_db: float = -35, min_dur: float = 0.4) -> list[dict]:
    p = ffmpeg(["-i", str(path), "-vn", "-af", f"silencedetect=noise={noise_db}dB:d={min_dur}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(rf"silence_start:\s*{_F}", p.stderr)]
    ends = [float(x) for x in re.findall(rf"silence_end:\s*{_F}", p.stderr)]
    dur = media_duration(path)
    if len(ends) < len(starts):
        ends.append(dur)
    return [{"start": max(0.0, s), "end": e, "duration": round(e - s, 3)} for s, e in zip(starts, ends)]


def black_frames(path: str | Path, min_dur: float = 0.1, pix_th: float = 0.10) -> list[dict]:
    p = ffmpeg(["-i", str(path), "-an", "-vf", f"blackdetect=d={min_dur}:pix_th={pix_th}", "-f", "null", "-"])
    return [{"start": float(a), "end": float(b), "duration": float(c)}
            for a, b, c in re.findall(rf"black_start:{_F} black_end:{_F} black_duration:{_F}", p.stderr)]


def frozen_frames(path: str | Path, min_dur: float = 2.0, noise_db: float = -60) -> list[dict]:
    p = ffmpeg(["-i", str(path), "-an", "-vf", f"freezedetect=n={noise_db}dB:d={min_dur}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(rf"freeze_start:\s*{_F}", p.stderr)]
    durs = [float(x) for x in re.findall(rf"freeze_duration:\s*{_F}", p.stderr)]
    return [{"start": s, "duration": d} for s, d in zip(starts, durs)] + (
        [{"start": starts[-1], "duration": None, "note": "frozen until end"}] if len(starts) > len(durs) else [])
