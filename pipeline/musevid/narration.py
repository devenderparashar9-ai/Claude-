"""Narration: local Piper TTS per script line, assembly, word timing, lip-sync envelope.

Script JSON:
{"voice": "en_US-joe-medium", "speaker": null, "pace": 1.0,
 "lines": [{"id": "l1", "text": "Meet Pip.", "pause_after": 0.5, "pace": 0.95}]}

Output timing JSON (the timeline every visual syncs to):
{"duration": .., "lines": [{"id", "text", "start", "end", "words": [{"word","start","end","matched"}]}],
 "issues": [...], "mouth": {"fps": 30, "values": [...]}}
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from .common import ToolError, decode_audio, log, model_dir, read_json, write_json, write_wav
from .speech import align_script, transcribe

VOICE_DIR = model_dir("piper")
SR = 48000

# Commercial-safety of Piper voices depends on the *training dataset* license.
VOICE_LICENSES = {
    "en_US-joe-medium": "CC0 (commercial OK)",
    "en_US-libritts_r-medium": "CC BY 4.0 (commercial OK with attribution)",
    "en_US-lessac-high": "Blizzard 2013 research license — NOT for commercial use",
    "en_US-ryan-high": "CC BY-NC-SA 4.0 — NOT for commercial use",
}


def _piper_bin() -> str:
    for c in (shutil.which("piper"), str(Path.home() / "venv-video" / "bin" / "piper"), "/home/user/venv-video/bin/piper"):
        if c and Path(c).exists():
            return c
    raise ToolError("piper not installed (pip install piper-tts)")


def tts_line(text: str, out: Path, voice: str, pace: float = 1.0, speaker: int | None = None) -> Path:
    model = VOICE_DIR / f"{voice}.onnx"
    if not model.exists():
        raise ToolError(f"voice model missing: {model}")
    cmd = [_piper_bin(), "-m", str(model), "-f", str(out), "--length_scale", f"{1 / pace:.3f}",
           "--sentence_silence", "0.18"]
    if speaker is not None:
        cmd += ["--speaker", str(speaker)]
    p = subprocess.run(cmd, input=text, text=True, capture_output=True)
    if p.returncode != 0 or not out.exists():
        raise ToolError(f"piper failed: {p.stderr[-800:]}")
    return out


def _trim_silence(a: np.ndarray, th: float = 0.008, pad: int = int(0.03 * SR)) -> np.ndarray:
    idx = np.where(np.abs(a) > th)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - pad): idx[-1] + pad]


def mouth_envelope(audio: np.ndarray, sr: int, fps: int) -> list[float]:
    """Per-frame mouth openness 0..1 from speech energy (attack fast, release slower)."""
    hop = sr // fps
    n = len(audio) // hop + 1
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(n)])
    db = 20 * np.log10(rms + 1e-9)
    v = np.clip((db + 45) / 30, 0, 1)
    out, prev = [], 0.0
    for x in v:
        prev = x if x > prev else prev * 0.55 + x * 0.45
        out.append(round(float(prev), 3))
    return out


def _tts_text(text: str, pron: dict) -> str:
    for k, v in pron.items():
        text = re.sub(rf"\b{re.escape(k)}\b", v, text, flags=re.I)
    return text


def _best_take(ln: dict, voice: str, script: dict, pron: dict, out_dir: Path, td: Path, verify: bool,
               max_takes: int) -> tuple[np.ndarray, list[dict]]:
    """Synthesize up to `max_takes` takes of a line, ASR-check each, keep the best.

    The chosen take is cached by content hash so later runs are reproducible
    (Piper sampling is stochastic: the same text can mispronounce on one take)."""
    import hashlib

    pace = ln.get("pace", script.get("pace", 1.0))
    key = hashlib.sha1(json.dumps([voice, ln["text"], pace, script.get("speaker"), pron], sort_keys=True).encode()).hexdigest()[:16]
    cache = out_dir / "lines" / f"{ln['id']}.{key}.wav"
    final = out_dir / "lines" / f"{ln['id']}.wav"
    if cache.exists():
        a = decode_audio(cache, SR)
        write_wav(final, a, SR)
        return a, [{"take": "cached", "file": cache.name}]
    words = ln["text"].split()
    best, takes = None, []
    for k in range(max_takes if verify else 1):
        wav = tts_line(_tts_text(ln["text"], pron), td / f"{ln['id']}_{k}.wav", voice, pace, script.get("speaker"))
        a = _trim_silence(decode_audio(wav, SR))
        score, heard = 1.0, None
        if verify:
            pad = np.zeros(int(0.5 * SR), np.float32)  # ASR/VAD drops a first word that starts at 0 s
            write_wav(td / f"{ln['id']}_{k}_t.wav", np.concatenate([pad, a, pad]), SR)
            tr = transcribe(td / f"{ln['id']}_{k}_t.wav", initial_prompt=" ".join(re.findall(r"[A-Z][a-z]+", ln["text"])) or None)
            al = align_script(words, tr["words"])
            score, heard = al["match_ratio"], " ".join(w["word"] for w in tr["words"])
        takes.append({"take": k, "score": score, "heard": heard})
        if best is None or score > best[0]:
            best = (score, a)
        if score >= 0.999:
            break
    log(f"{ln['id']}: {len(takes)} take(s), best match {best[0]:.3f}")
    if best[0] < 0.9:
        log(f"WARNING {ln['id']}: no clean take — add a 'pronounce' respelling or reword: {takes[-1]['heard']}")
    write_wav(cache, best[1], SR)
    write_wav(final, best[1], SR)
    return best[1], takes


def build(script_path: str | Path, out_dir: str | Path, fps: int = 30, lead_in: float = 0.6,
          verify: bool = True, max_takes: int = 4) -> dict:
    script = read_json(script_path)
    voice = script.get("voice", "en_US-joe-medium")
    lic = VOICE_LICENSES.get(voice, "unknown — check MODEL_CARD")
    if "NOT" in lic:
        log(f"WARNING: voice {voice}: {lic}")
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    pron = script.get("pronounce", {})  # {"word": "respelling"} — affects TTS input only, never captions
    takes_log = {}
    pieces, lines, t = [np.zeros(int(lead_in * SR), np.float32)], [], lead_in
    with tempfile.TemporaryDirectory() as td:
        for ln in script["lines"]:
            a, takes = _best_take(ln, voice, script, pron, out_dir, Path(td), verify, max_takes)
            takes_log[ln["id"]] = takes
            lines.append({"id": ln["id"], "text": ln["text"], "start": round(t, 3), "end": round(t + len(a) / SR, 3)})
            pause = float(ln.get("pause_after", 0.45))
            pieces += [a, np.zeros(int(pause * SR), np.float32)]
            t += len(a) / SR + pause
    full = np.concatenate(pieces + [np.zeros(int(0.8 * SR), np.float32)])
    wav_path = write_wav(out_dir / "narration.wav", full, SR)
    timing = {"voice": voice, "voice_license": lic, "duration": round(len(full) / SR, 3), "lines": lines,
              "issues": [], "takes": takes_log, "mouth": {"fps": fps, "values": mouth_envelope(full, SR, fps)}}

    if verify:
        # Listen back with ASR: script text + ASR timestamps; report anything misheard.
        terms = " ".join(sorted({w for ln in script["lines"] for w in re.findall(r"[A-Z][a-z]+|\d+", ln["text"])}))
        tr = transcribe(wav_path, initial_prompt=terms or None)
        script_words = [w for ln in script["lines"] for w in ln["text"].split()]
        al = align_script(script_words, tr["words"])
        k = 0
        for ln in lines:
            n = len(ln["text"].split())
            ws = al["words"][k:k + n]; k += n
            # Synthesis gives exact line bounds: clamp ASR word times inside them, keep order monotonic.
            prev = ln["start"]
            for w in ws:
                w["start"] = round(min(max(w["start"], prev), ln["end"] - 0.05), 3)
                w["end"] = round(min(max(w["end"], w["start"] + 0.06), ln["end"]), 3)
                prev = w["start"]
            ln["words"] = ws
        timing["match_ratio"] = al["match_ratio"]
        for iss in al["issues"]:
            phantom = re.search(r"thank(s| you) for watching|subscribe|subtitles? by|see you next time", iss["heard"], re.I)
            if iss["type"] == "insert" and iss["at"] is not None and (phantom or not any(
                    ln["start"] - 0.1 <= iss["at"] <= ln["end"] + 0.05 for ln in lines)):
                iss["note"] = "ASR hallucination over silence (no audio was synthesized here) — ignored"
        timing["issues"] = al["issues"] + tr["flags"]
        if al["match_ratio"] < 0.85:
            log(f"WARNING: narration intelligibility low (match {al['match_ratio']:.2f}) — rewrite or change pace/voice")
    write_json(out_dir / "timing.json", timing)
    log(f"narration {timing['duration']:.2f}s, {len(lines)} lines, match={timing.get('match_ratio')}")
    return timing
