"""Full production driver for a narration-driven animated explainer.

productions/<name>/{script.json, beats.json}  →  productions/<name>/build/...

Stages (each writes files the next one reads; re-run any stage alone):
  narrate  → build/narration/{narration.wav, timing.json}
  cues     → build/cues.json  + animation/src/generated/<name>.json
  animate  → build/video_silent.mp4   (Remotion)
  audio    → build/stems/*.wav, build/mix.wav (ducked, loudness-normalized, measured)
  master   → build/<name>.mp4 (+ .srt/.ass sidecars)
  qa       → build/qa/qa_report.json, contact_sheet.png, frames/
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from . import audio, captions, narration, qa
from .common import ToolError, ffmpeg, log, read_json, write_json

REPO = Path(__file__).resolve().parents[2]
ANIM = REPO / "animation"
CHROME = os.environ.get("MUSEVID_CHROME", "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell")


def _norm(w: str) -> str:
    return re.sub(r"[^\w']", "", w.lower())


def resolve_cues(beats: dict, timing: dict) -> dict:
    lines = {ln["id"]: ln for ln in timing["lines"]}
    out = {}
    for name, c in beats["cues"].items():
        ln = lines.get(c["line"])
        if ln is None:
            raise ToolError(f"cue {name}: unknown line {c['line']}")
        word, _, nth = c["word"].partition("#")
        hits = [w for w in ln["words"] if _norm(w["word"]) == _norm(word)]
        if not hits:
            raise ToolError(f"cue {name}: word '{word}' not in line {c['line']}: {ln['text']}")
        w = hits[int(nth) - 1 if nth else 0]
        t = max(0.0, w["start"] + c.get("offset", 0.0))
        out[name] = {"t": round(t, 3), "frame": round(t * beats["fps"]), "word": w["word"], "line": c["line"]}
    return out


def stage_cues(prod: Path) -> dict:
    beats = read_json(prod / "script.json"), read_json(prod / "beats.json")
    script, beats = beats
    timing = read_json(prod / "build" / "narration" / "timing.json")
    cues = resolve_cues(beats, timing)
    dur = timing["duration"] + beats.get("tail", 2.0)
    fps = beats["fps"]
    gen = {"name": prod.name, "title": script["title"], "fps": fps, "width": beats["width"], "height": beats["height"],
           "durationInFrames": int(round(dur * fps)), "cues": cues,
           "lines": [{"id": ln["id"], "start": ln["start"], "end": ln["end"],
                      "words": [{"word": w["word"], "start": w["start"], "end": w["end"]} for w in ln["words"]]}
                     for ln in timing["lines"]],
           "mouth": timing["mouth"]["values"]}
    write_json(prod / "build" / "cues.json", gen)
    write_json(ANIM / "src" / "generated" / f"{prod.name}.json", gen)
    log(f"cues: {len(cues)} resolved; video {dur:.2f}s = {gen['durationInFrames']} frames")
    return gen


def stage_animate(prod: Path, comp: str, extra: list[str] | None = None) -> Path:
    out = prod / "build" / "video_silent.mp4"
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out), f"--browser-executable={CHROME}",
           "--concurrency=4", "--crf=16", "--muted", "--pixel-format=yuv420p", "--color-space=bt709", "--log=warn", *(extra or [])]
    log("remotion: " + " ".join(cmd[2:5]))
    p = subprocess.run(cmd, cwd=ANIM, capture_output=True, text=True)
    if p.returncode != 0:
        raise ToolError("remotion render failed:\n" + (p.stderr or p.stdout)[-3000:])
    return out


def stage_audio(prod: Path, platform: str = "youtube") -> dict:
    beats = read_json(prod / "beats.json")
    gen = read_json(prod / "build" / "cues.json")
    dur = gen["durationInFrames"] / gen["fps"]
    st = prod / "build" / "stems"
    nar = prod / "build" / "narration" / "narration.wav"
    # pad narration to full video length so amix duration=first covers the tail
    nar_pad = st / "narration_padded.wav"; st.mkdir(parents=True, exist_ok=True)
    ffmpeg(["-i", str(nar), "-af", f"apad=whole_dur={dur}", "-ar", "48000", "-ac", "1", str(nar_pad)])
    mus = beats.get("music", {})
    audio.write_stem(st / "music.wav", audio.music_bed(dur, mus.get("bpm", 92), mood=mus.get("mood", "warm")))
    events = [{**e, "t": gen["cues"][e["cue"]]["t"] + e.get("offset", 0.0)} for e in beats["sfx"]]
    write_json(st / "sfx_events.json", events)
    audio.write_stem(st / "sfx.wav", audio.place(events, dur))
    amb = beats.get("ambience", {})
    audio.write_stem(st / "ambience.wav", audio.ambience(dur, kind=amb.get("kind", "outdoor")))
    m = audio.mix(nar_pad, prod / "build" / "mix.wav", st / "music.wav", st / "sfx.wav", st / "ambience.wav",
                  music_db=mus.get("gain_db", -15), amb_db=amb.get("gain_db", -26), platform=platform)
    write_json(prod / "build" / "mix_loudness.json", m)
    return m


def stage_master(prod: Path) -> Path:
    gen = read_json(prod / "build" / "cues.json")
    b = prod / "build"
    words = [w for ln in gen["lines"] for w in ln["words"]]
    captions.write_srt(words, b / f"{prod.name}.srt")
    captions.write_ass(words, b / f"{prod.name}.ass", gen["width"], gen["height"])
    out = b / f"{prod.name}.mp4"
    ffmpeg(["-i", str(b / "video_silent.mp4"), "-i", str(b / "mix.wav"), "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", str(out)])
    return out


def stage_qa(prod: Path, platform: str = "youtube") -> dict:
    gen = read_json(prod / "build" / "cues.json")
    timing = read_json(prod / "build" / "narration" / "timing.json")
    exp = {"width": gen["width"], "height": gen["height"], "fps": gen["fps"],
           "min_duration": gen["durationInFrames"] / gen["fps"] - 0.2, "max_duration": gen["durationInFrames"] / gen["fps"] + 0.2}
    rep = qa.check(prod / "build" / f"{prod.name}.mp4", prod / "build" / "qa", exp, platform, timing)
    rep["caption_qc"] = captions.caption_qc([w for ln in gen["lines"] for w in ln["words"]])
    rep["narration_issues"] = timing["issues"]
    # "Listen" by proxy: can the narration still be understood through music + SFX in the final file?
    from .speech import align_script, transcribe
    script = read_json(prod / "script.json")
    tr = transcribe(prod / "build" / f"{prod.name}.mp4")
    al = align_script([w for ln in script["lines"] for w in ln["text"].split()], tr["words"])
    ok = al["match_ratio"] >= timing.get("match_ratio", 0.9) - 0.05
    rep["checks"].append({"check": "final-mix intelligibility (ASR match vs clean narration)", "pass": ok,
                          "detail": {"final": al["match_ratio"], "clean": timing.get("match_ratio"),
                                     "issues": [i for i in al["issues"] if i["heard"] or i["script"]][:12]}})
    rep["pass"] = rep["pass"] and ok
    # frames at every cue, so each narration-synced action can be inspected
    rep["cue_frames"] = [str(p) for p in qa.extract_frames(prod / "build" / f"{prod.name}.mp4",
                                                             sorted({c["t"] + 0.35 for c in gen["cues"].values()}),
                                                             prod / "build" / "qa" / "cue_frames")]
    write_json(prod / "build" / "qa" / "qa_report.json", rep)
    return rep


def run(prod: str | Path, comp: str, stages: list[str], platform: str = "youtube") -> None:
    prod = Path(prod).resolve()
    for s in stages:
        log(f"=== stage {s}")
        if s == "narrate":
            narration.build(prod / "script.json", prod / "build" / "narration", read_json(prod / "beats.json")["fps"])
        elif s == "cues":
            stage_cues(prod)
        elif s == "animate":
            stage_animate(prod, comp)
        elif s == "audio":
            stage_audio(prod, platform)
        elif s == "master":
            stage_master(prod)
        elif s == "qa":
            rep = stage_qa(prod, platform)
            for c in rep["checks"]:
                log(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['check']}: {c['detail']}")
        else:
            raise ToolError(f"unknown stage {s}")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("production"); ap.add_argument("--comp", required=True)
    ap.add_argument("--stages", default="narrate,cues,animate,audio,master,qa")
    ap.add_argument("--platform", default="youtube")
    a = ap.parse_args()
    run(a.production, a.comp, a.stages.split(","), a.platform)
