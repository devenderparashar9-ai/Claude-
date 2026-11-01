"""Transcription (faster-whisper), script↔ASR alignment, speech-aware cut lists."""
from __future__ import annotations

import difflib
import os
import re
from pathlib import Path

from .common import decode_audio, log, media_duration, model_dir

MODEL_DIR = str(model_dir("whisper"))
_MODELS: dict = {}
_NUM = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
        "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten"}


def transcribe(path: str | Path, model: str = "small.en", language: str | None = "en",
               initial_prompt: str | None = None) -> dict:
    """Word-level transcript. `initial_prompt` should carry names / jargon to bias recognition."""
    from faster_whisper import WhisperModel

    audio = decode_audio(path, 16000)
    if model not in _MODELS:
        _MODELS[model] = WhisperModel(model, device="cpu", compute_type="int8", download_root=MODEL_DIR)
    m = _MODELS[model]
    segs, info = m.transcribe(audio, word_timestamps=True, language=language, vad_filter=True,
                              initial_prompt=initial_prompt, condition_on_previous_text=False)
    words, segments = [], []
    for s in segs:
        segments.append({"start": s.start, "end": s.end, "text": s.text.strip(),
                         "avg_logprob": s.avg_logprob, "no_speech_prob": s.no_speech_prob})
        for w in s.words or []:
            words.append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3),
                          "prob": round(w.probability, 3)})
    flags = []
    if words and words[0]["start"] > 2.0:
        flags.append("first word starts >2s in — check for missed speech")
    for s in segments:
        if s["no_speech_prob"] > 0.6 and len(s["text"]) > 0:
            flags.append(f"possible hallucination over silence at {s['start']:.2f}s: '{s['text']}'")
    low = [w for w in words if w["prob"] < 0.5]
    if low:
        flags.append(f"{len(low)} low-confidence words — proofread: " + ", ".join(f"{w['word']}@{w['start']}" for w in low[:15]))
    return {"source": str(path), "model": model, "language": info.language, "duration": media_duration(path),
            "segments": segments, "words": words, "flags": flags}


def _norm(t: str) -> str:
    t = t.lower().strip()
    t = re.sub(r"[^\w']+", "", t)
    return _NUM.get(t, t)


def align_script(script_words: list[str], asr_words: list[dict]) -> dict:
    """Map the *known* script text onto ASR timestamps.

    Script text wins (it is what was meant); ASR wins on timing (it is what was said).
    Every disagreement is reported so names/numbers/terms get a human check.
    """
    a = [_norm(w) for w in script_words]
    b = [_norm(w["word"]) for w in asr_words]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    out: list[dict | None] = [None] * len(script_words)
    issues = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                w = asr_words[j1 + k]
                out[i1 + k] = {"word": script_words[i1 + k], "start": w["start"], "end": w["end"], "matched": True}
        else:
            heard = " ".join(w["word"] for w in asr_words[j1:j2])
            meant = " ".join(script_words[i1:i2])
            if i2 > i1:
                # spread the script words across the ASR span (or the gap between neighbours)
                if j2 > j1:
                    t0, t1 = asr_words[j1]["start"], asr_words[j2 - 1]["end"]
                else:
                    t0 = asr_words[j1 - 1]["end"] if j1 > 0 else 0.0
                    t1 = asr_words[j1]["start"] if j1 < len(asr_words) else t0 + 0.3 * (i2 - i1)
                step = max(t1 - t0, 0.05 * (i2 - i1)) / (i2 - i1)
                for k in range(i2 - i1):
                    out[i1 + k] = {"word": script_words[i1 + k], "start": round(t0 + k * step, 3),
                                   "end": round(t0 + (k + 1) * step, 3), "matched": False}
            issues.append({"type": tag, "script": meant, "heard": heard,
                           "at": asr_words[j1]["start"] if j1 < len(asr_words) else None})
    ratio = sm.ratio()
    return {"words": out, "match_ratio": round(ratio, 4), "issues": issues}


def keep_ranges_from_silence(silences: list[dict], duration: float, pad: float = 0.12,
                             keep_pause: float = 0.25, protect: list[tuple[float, float]] | None = None) -> list[tuple[float, float]]:
    """Speech-aware jump-cut: remove dead air but leave a natural `keep_pause`.

    Never collapse a pause to zero (sounds like a stutter). `protect` lists
    dramatic pauses (start, end) that must be left untouched.
    """
    protect = protect or []
    cuts = []
    for s in silences:
        a, b = s["start"] + pad, s["end"] - pad
        if b - a <= keep_pause:
            continue
        if any(pa <= s["start"] and s["end"] <= pb for pa, pb in protect):
            continue
        cuts.append((a + keep_pause / 2, b - keep_pause / 2))
    keep, t = [], 0.0
    for a, b in cuts:
        if a > t:
            keep.append((round(t, 3), round(a, 3)))
        t = b
    if t < duration:
        keep.append((round(t, 3), round(duration, 3)))
    return [k for k in keep if k[1] - k[0] > 0.08]


def jumpcut_edl(src: str, silences: list[dict], fps: int, width: int, height: int, **kw) -> dict:
    keep = keep_ranges_from_silence(silences, media_duration(src), **kw)
    zooms = [1.0, 1.08]  # alternate punch-in so cuts read as angle changes, not mistakes
    clips = [{"src": src, "in": a, "out": b, "label": f"seg{n:03d}", "zoom": zooms[n % 2]}
             for n, (a, b) in enumerate(keep)]
    removed = media_duration(src) - sum(b - a for a, b in keep)
    log(f"jumpcut: {len(keep)} segments kept, {removed:.2f}s removed")
    return {"fps": fps, "width": width, "height": height, "clips": clips, "overlays": []}


def retime_words(words: list[dict], keep: list[tuple[float, float]]) -> list[dict]:
    """Map source-time word stamps onto the post-cut timeline (drops words in removed spans)."""
    out, offset_table, acc = [], [], 0.0
    for a, b in keep:
        offset_table.append((a, b, acc)); acc += b - a
    for w in words:
        for a, b, base in offset_table:
            if a <= w["start"] < b:
                out.append({**w, "start": round(base + w["start"] - a, 3), "end": round(base + min(w["end"], b) - a, 3)})
                break
    return out
