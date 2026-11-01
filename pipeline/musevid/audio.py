"""Audio post: license-clean procedural SFX/music/ambience, dialogue chain, ducking, loudness.

Everything here is generated from a fixed seed, so renders are reproducible and
there is no third-party music/SFX licensing to track.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .common import ToolError, ffmpeg, log, write_wav

SR = 48000

# Integrated loudness targets (LUFS) and true-peak ceilings (dBTP) per platform.
TARGETS = {
    "youtube": {"I": -14.0, "TP": -1.0, "LRA": 11},
    "tiktok": {"I": -14.0, "TP": -1.0, "LRA": 9},
    "instagram": {"I": -14.0, "TP": -1.0, "LRA": 9},
    "podcast": {"I": -16.0, "TP": -1.0, "LRA": 11},
    "broadcast": {"I": -23.0, "TP": -1.0, "LRA": 15},  # EBU R128
}


# ----------------------------------------------------------------- synthesis

def _env(n: int, a: float, r: float, curve: float = 3.0) -> np.ndarray:
    t = np.linspace(0, 1, n)
    att = max(1, int(n * a))
    e = np.ones(n)
    e[:att] = np.linspace(0, 1, att) ** 0.5
    rel = np.linspace(1, 0, n - att) ** curve
    e[att:] = rel
    return e * (1 - 0 * t)


def _noise(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.standard_normal(n).astype(np.float32)


def _lowpass(x: np.ndarray, cutoff: np.ndarray | float) -> np.ndarray:
    """One-pole low-pass with optionally time-varying cutoff (Hz)."""
    if np.isscalar(cutoff):
        try:
            from scipy.signal import lfilter
            k = 1 - np.exp(-2 * np.pi * cutoff / SR)
            return lfilter([k], [1, -(1 - k)], x).astype(np.float32)
        except ImportError:
            pass
    c = np.broadcast_to(np.asarray(cutoff, np.float32), x.shape)
    k = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += k[i] * (x[i] - acc); y[i] = acc
    return y


def sfx(kind: str, seed: int = 1, dur: float | None = None) -> np.ndarray:
    rng = np.random.default_rng(seed)
    if kind == "whoosh":  # filtered noise sweep for camera moves / transitions
        n = int((dur or 0.7) * SR); t = np.linspace(0, 1, n)
        cut = 300 + 5000 * np.sin(np.pi * t) ** 2
        x = _lowpass(_noise(n, rng), cut) * np.sin(np.pi * t) ** 1.5 * 2.2
    elif kind == "pop":  # UI/element appear
        n = int(0.14 * SR); t = np.arange(n) / SR
        f = 900 * np.exp(-t * 18) + 380
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 32)
    elif kind == "chime":  # idea / reveal sparkle
        n = int((dur or 1.4) * SR); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) * g
                for f, d, g in ((1318.5, 3.5, .5), (1975.5, 4.5, .35), (2637, 6, .2), (3951, 9, .1)))
    elif kind == "impact":  # soft cartoon thud for landings
        n = int(0.5 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * (55 + 90 * np.exp(-t * 25)) * t) * np.exp(-t * 9) + _lowpass(_noise(n, rng), 900) * np.exp(-t * 30) * 1.5
    elif kind == "riser":  # build into a reveal
        n = int((dur or 1.2) * SR); t = np.linspace(0, 1, n)
        x = _lowpass(_noise(n, rng), 400 + 6000 * t ** 2) * t ** 2 * 1.4 + np.sin(2 * np.pi * np.cumsum(200 + 600 * t ** 2) / SR) * t ** 3 * 0.3
    elif kind == "click":
        n = int(0.05 * SR); t = np.arange(n) / SR
        x = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 120)
    elif kind == "boing":  # cartoon spring
        n = int(0.6 * SR); t = np.arange(n) / SR
        f = 220 + 140 * np.sin(2 * np.pi * 9 * t) * np.exp(-t * 4)
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    else:
        raise ToolError(f"unknown sfx kind {kind}")
    x = np.asarray(x, np.float32)
    return x / (np.max(np.abs(x)) + 1e-9) * 0.7


def ambience(duration: float, seed: int = 7, kind: str = "outdoor") -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(duration * SR)
    base = _lowpass(_noise(n, rng), 700 if kind == "outdoor" else 300) * 0.25
    out = np.stack([base, np.roll(base, 1200)], 1)
    if kind == "outdoor":  # sparse soft bird chirps
        for _ in range(int(duration / 3)):
            at = rng.integers(0, max(1, n - SR)); m = int(0.12 * SR); t = np.arange(m) / SR
            ch = np.sin(2 * np.pi * np.cumsum(3200 + 900 * np.sin(2 * np.pi * 22 * t)) / SR) * np.exp(-t * 30) * 0.05
            pan = rng.uniform(0.2, 0.8)
            out[at:at + m, 0] += ch * (1 - pan); out[at:at + m, 1] += ch * pan
    return out.astype(np.float32)


def music_bed(duration: float, bpm: float = 92, seed: int = 3, mood: str = "warm") -> np.ndarray:
    """Gentle explainer bed: pad chords + soft plucked arpeggio + light pulse. Stereo."""
    rng = np.random.default_rng(seed)
    n = int(duration * SR); t = np.arange(n) / SR
    beat = 60 / bpm; bar = beat * 4
    prog = [[60, 64, 67, 71], [57, 60, 64, 67], [65, 69, 72, 76], [67, 71, 74, 77]]  # Cmaj7 Am7 Fmaj7 G7sus-ish
    if mood == "curious":
        prog = [[62, 65, 69, 72], [58, 62, 65, 69], [60, 64, 67, 70], [57, 60, 64, 67]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)  # noqa: E731
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    nbars = int(np.ceil(duration / bar)) + 1
    for b in range(nbars):
        ch = prog[b % len(prog)]
        s0 = int(b * bar * SR); s1 = min(n, int((b + 1) * bar * SR + 0.5 * SR))
        if s0 >= n:
            break
        tt = np.arange(s1 - s0) / SR
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (s1 - s0) / SR - tt + 0.05) ** 0.5
        for k, m in enumerate(ch):
            det = 1 + (k - 1.5) * 0.0015
            w = (np.sin(2 * np.pi * hz(m - 12) * det * tt) + 0.3 * np.sin(2 * np.pi * hz(m) * tt)) * 0.06 * env
            L[s0:s1] += w * (0.6 + 0.1 * k); R[s0:s1] += w * (1.0 - 0.1 * k)
        for i in range(8):  # arpeggio eighth notes
            a0 = s0 + int(i * beat / 2 * SR)
            m = ch[[0, 1, 2, 3, 2, 1, 2, 3][i]] + 12
            ln = int(0.45 * SR)
            if a0 + ln > n:
                continue
            tt2 = np.arange(ln) / SR
            p = (np.sin(2 * np.pi * hz(m) * tt2) + 0.25 * np.sin(4 * np.pi * hz(m) * tt2)) * np.exp(-tt2 * 7) * 0.05
            pan = 0.5 + 0.35 * np.sin(i)
            L[a0:a0 + ln] += p * (1 - pan); R[a0:a0 + ln] += p * pan
        for i in range(4):  # soft pulse on beats
            a0 = s0 + int(i * beat * SR); ln = int(0.18 * SR)
            if a0 + ln > n:
                continue
            tt3 = np.arange(ln) / SR
            k = np.sin(2 * np.pi * (50 + 70 * np.exp(-tt3 * 30)) * tt3) * np.exp(-tt3 * 18) * 0.12
            L[a0:a0 + ln] += k; R[a0:a0 + ln] += k
    fade = np.minimum(1, np.minimum(t / 1.5, (duration - t) / 2.0)).clip(0, 1)
    out = np.stack([L * fade, R * fade], 1)
    return (out / (np.max(np.abs(out)) + 1e-9) * 0.5).astype(np.float32)


def place(events: list[dict], duration: float, seed: int = 11) -> np.ndarray:
    """events: [{"t": sec, "kind": "pop", "gain_db": -6, "pan": 0.5, "dur": opt}] → stereo track.

    Repeated identical sounds get small pitch/level variation (avoids the
    machine-gun effect)."""
    n = int(duration * SR)
    out = np.zeros((n, 2), np.float32)
    for k, e in enumerate(sorted(events, key=lambda e: e["t"])):
        x = sfx(e["kind"], seed=seed + k, dur=e.get("dur"))
        var = 1 + ((k * 7919) % 13 - 6) / 200  # ±3% deterministic pitch variation
        idx = np.arange(0, len(x) - 1, var)
        x = np.interp(idx, np.arange(len(x)), x).astype(np.float32)
        g = 10 ** (e.get("gain_db", -6) / 20)
        pan = e.get("pan", 0.5)
        s = int(e["t"] * SR)
        if s >= n:
            continue
        m = min(len(x), n - s)
        out[s:s + m, 0] += x[:m] * g * np.cos(pan * np.pi / 2) * 1.414
        out[s:s + m, 1] += x[:m] * g * np.sin(pan * np.pi / 2) * 1.414
    return out


def write_stem(path: str | Path, audio: np.ndarray) -> Path:
    return write_wav(path, audio, SR)


# ----------------------------------------------------------------- mixing

DIALOGUE_CHAIN = {
    # Real recorded dialogue: rumble cut, broadband denoise, mud cut, presence, de-ess, leveling.
    "recorded": "highpass=f=80,afftdn=nr=12:nf=-40:tn=1,equalizer=f=250:t=q:w=1.2:g=-2.5,"
                "equalizer=f=3200:t=q:w=1.0:g=2.5,deesser=i=0.35:m=0.5:f=0.5,"
                "acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=3dB,"
                "alimiter=limit=0.89:level=false",
    # Clean TTS: skip denoise (it adds artifacts), keep tone shaping and gentle leveling.
    "tts": "highpass=f=70,equalizer=f=220:t=q:w=1.2:g=-1.5,equalizer=f=3000:t=q:w=1.0:g=2,"
           "deesser=i=0.25:m=0.5:f=0.5,acompressor=threshold=-18dB:ratio=2.5:attack=10:release=150:makeup=2dB",
}


def measure(path: str | Path) -> dict:
    """EBU R128 integrated loudness, LRA, true peak and sample peak of a rendered file."""
    p = ffmpeg(["-i", str(path), "-vn", "-af", "ebur128=peak=true+sample:framelog=quiet", "-f", "null", "-"])
    s = p.stderr[p.stderr.rfind("Summary:"):]
    g = lambda pat: float(re.search(pat, s).group(1))  # noqa: E731
    return {"integrated_lufs": g(r"I:\s*(-?[\d.]+) LUFS"), "lra_lu": g(r"LRA:\s*(-?[\d.]+) LU"),
            "true_peak_dbtp": g(r"True peak:\s*Peak:\s*(-?[\d.inf]+) dBFS"),
            "sample_peak_dbfs": g(r"Sample peak:\s*Peak:\s*(-?[\d.inf]+) dBFS")}


def master_loudness(src: str | Path, out: str | Path, platform: str = "youtube", tol: float = 0.3, max_iter: int = 4) -> dict:
    """Hit the integrated target precisely: static gain + 4x-oversampled peak limiter, re-measured each pass.

    loudnorm alone backs off when the gain would violate the true-peak ceiling (we measured −14.7 for a −14
    target); limiting the few peaks instead keeps the programme at target without audible pumping."""
    tg = TARGETS[platform]
    ceiling = 10 ** ((tg["TP"] - 0.4) / 20)
    gain = tg["I"] - measure(src)["integrated_lufs"]
    m = {}
    for _ in range(max_iter):
        ffmpeg(["-i", str(src), "-af",
                f"volume={gain:.3f}dB,aresample=192000,alimiter=limit={ceiling:.4f}:level=false:attack=0.5:release=40,"
                f"aresample=48000", "-ar", "48000", "-c:a", "pcm_s24le", str(out)])
        m = measure(out)
        err = tg["I"] - m["integrated_lufs"]
        if abs(err) <= tol and m["true_peak_dbtp"] <= tg["TP"]:
            break
        gain += err
    m["gain_db"] = round(gain, 2)
    return m


def loudnorm_2pass(src: str | Path, out: str | Path, platform: str = "youtube") -> dict:
    tg = TARGETS[platform]
    spec = f"loudnorm=I={tg['I']}:TP={tg['TP'] - 0.5}:LRA={tg['LRA']}"
    p = ffmpeg(["-i", str(src), "-af", f"{spec}:print_format=json", "-f", "null", "-"])
    j = json.loads(p.stderr[p.stderr.rfind("{"):p.stderr.rfind("}") + 1])
    ffmpeg(["-i", str(src), "-af",
            f"{spec}:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:"
            f"measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true,"
            f"aresample=48000,alimiter=limit={10 ** ((tg['TP'] - 0.3) / 20):.4f}:level=false:attack=1:release=50",
            "-ar", "48000", "-c:a", "pcm_s16le", str(out)])
    return measure(out)


def mix(narration: str | Path, out: str | Path, music: str | Path | None = None, sfx_track: str | Path | None = None,
        amb: str | Path | None = None, dialogue: str = "tts", music_db: float = -14, amb_db: float = -24,
        sfx_db: float = -4, duck_db: float = 10, platform: str = "youtube") -> dict:
    """Narration-first mix: music is sidechain-ducked under speech, then loudness-normalized and measured."""
    ins, chains, labels = ["-i", str(narration)], [], []
    chains.append(f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo,{DIALOGUE_CHAIN[dialogue]},asplit=2[vo][key]")
    labels.append("[vo]")
    k = 1
    if music:
        ins += ["-i", str(music)]
        ratio = max(2, duck_db / 2)
        chains.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={music_db}dB[m]")
        chains.append(f"[m][key]sidechaincompress=threshold=0.03:ratio={ratio}:attack=40:release=450:knee=4[mduck]")
        labels.append("[mduck]"); k += 1
    else:
        chains.append("[key]anullsink")
    if sfx_track:
        ins += ["-i", str(sfx_track)]
        chains.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={sfx_db}dB[fx]")
        labels.append("[fx]"); k += 1
    if amb:
        ins += ["-i", str(amb)]
        chains.append(f"[{k}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={amb_db}dB[amb]")
        labels.append("[amb]"); k += 1
    chains.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=first[mix]")
    pre = Path(out).with_suffix(".premaster.wav")
    ffmpeg([*ins, "-filter_complex", ";".join(chains), "-map", "[mix]", "-ar", "48000", "-c:a", "pcm_s24le", str(pre)])
    m = master_loudness(pre, out, platform)
    tg = TARGETS[platform]
    m["target"] = tg
    m["pass"] = abs(m["integrated_lufs"] - tg["I"]) <= 1.0 and m["true_peak_dbtp"] <= tg["TP"]
    log(f"mix {out}: {m['integrated_lufs']} LUFS, TP {m['true_peak_dbtp']} dBTP → {'PASS' if m['pass'] else 'FAIL'}")
    return m


def speech_to_music_ratio(narration: str | Path, mixfile: str | Path, timing: dict) -> float:
    """dB difference between speech-active and speech-free regions in the final mix (higher = clearer)."""
    from .common import decode_audio
    a = decode_audio(mixfile, 16000)
    speech = np.zeros(len(a), bool)
    for ln in timing["lines"]:
        speech[int(ln["start"] * 16000):int(ln["end"] * 16000)] = True
    rms = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)  # noqa: E731
    if speech.all() or not speech.any():
        return float("nan")
    return round(float(rms(a[speech]) - rms(a[~speech])), 2)
