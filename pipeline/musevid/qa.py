"""Post-render quality assurance. A render is not delivered until this passes
*and* a human/agent has looked at the contact sheet and frames.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from .audio import TARGETS, measure
from .common import decode_audio, ffmpeg, ffprobe_json, log, parse_rate, write_json
from .detect import black_frames, frozen_frames, silences


def contact_sheet(video: str | Path, out: str | Path, cols: int = 4, rows: int = 4, width: int = 480) -> Path:
    info = ffprobe_json(video)
    dur = float(info["format"]["duration"])
    n = cols * rows
    step = dur / (n + 1)
    ffmpeg(["-i", str(video), "-vf",
            f"fps=1/{step:.4f},scale={width}:-2,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"text='%{{pts\\:hms}}':x=6:y=6:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.55,tile={cols}x{rows}:padding=4",
            "-frames:v", "1", str(out)])
    return Path(out)


def extract_frames(video: str | Path, times: list[float], out_dir: str | Path) -> list[Path]:
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for t in times:
        p = out_dir / f"frame_{t:07.2f}.png"
        ffmpeg(["-ss", f"{t:.3f}", "-i", str(video), "-frames:v", "1", str(p)])
        paths.append(p)
    return paths


def check(video: str | Path, out_dir: str | Path, expect: dict | None = None, platform: str = "youtube",
          timing: dict | None = None, allow_black: list[tuple[float, float]] | None = None) -> dict:
    """expect: {"width", "height", "fps", "min_duration", "max_duration"}."""
    expect = expect or {}
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    video = Path(video)
    rep: dict = {"file": str(video), "checks": [], "pass": True}

    def chk(name: str, ok: bool, detail) -> None:
        rep["checks"].append({"check": name, "pass": bool(ok), "detail": detail})
        rep["pass"] &= bool(ok)

    chk("file exists and non-empty", video.exists() and video.stat().st_size > 10_000,
        video.stat().st_size if video.exists() else "missing")
    if not video.exists():
        return rep
    info = ffprobe_json(video)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
    dur = float(info["format"]["duration"])
    chk("has video stream", v is not None, v and v["codec_name"])
    chk("has audio stream", a is not None, a and f"{a['codec_name']} {a.get('sample_rate')}Hz {a.get('channels')}ch")
    if v:
        W, H, fps = v["width"], v["height"], parse_rate(v["avg_frame_rate"])
        rep["video"] = {"width": W, "height": H, "fps": fps, "pix_fmt": v.get("pix_fmt"), "codec": v["codec_name"],
                        "aspect": f"{W / H:.4f}"}
        if "width" in expect:
            chk("resolution", (W, H) == (expect["width"], expect["height"]), f"{W}x{H}")
        if "fps" in expect:
            chk("frame rate", abs(fps - expect["fps"]) < 0.01, fps)
        chk("pixel format yuv420p (max player compatibility)", v.get("pix_fmt") == "yuv420p", v.get("pix_fmt"))
        vdur = float(v.get("duration", dur)); adur = float(a.get("duration", dur)) if a else vdur
        chk("audio/video duration drift < 100ms", abs(vdur - adur) < 0.1, f"v={vdur:.3f}s a={adur:.3f}s")
    rep["duration"] = dur
    if "min_duration" in expect:
        chk("duration in range", expect["min_duration"] <= dur <= expect.get("max_duration", 1e9), round(dur, 2))

    blacks = black_frames(video)
    allow_black = allow_black or [(0, 0.5), (dur - 1.0, dur + 1)]
    bad_black = [b for b in blacks if not any(x <= b["start"] and b["end"] <= y for x, y in allow_black)]
    chk("no unintended black frames", not bad_black, bad_black or "none")
    frozen = frozen_frames(video, min_dur=2.5)
    chk("no frozen picture ≥2.5s (everything on screen should keep moving)", not frozen, frozen or "none")

    if a:
        m = measure(video)
        tg = TARGETS[platform]
        rep["loudness"] = m
        chk(f"integrated loudness {tg['I']}±1 LUFS ({platform})", abs(m["integrated_lufs"] - tg["I"]) <= 1.0, m["integrated_lufs"])
        chk(f"true peak ≤ {tg['TP']} dBTP", m["true_peak_dbtp"] <= tg["TP"], m["true_peak_dbtp"])
        pcm = decode_audio(video, 48000, mono=False)
        clipped = int(np.sum(np.abs(pcm) >= 0.999))
        chk("no clipped samples", clipped == 0, clipped)
        gaps = [s for s in silences(video, -50, 1.5) if s["start"] > 0.5 and s["end"] < dur - 0.5]
        chk("no dead-air gaps ≥1.5s", not gaps, gaps or "none")
        if timing:
            from .audio import speech_to_music_ratio
            r = speech_to_music_ratio(None, video, timing)
            rep["speech_over_bed_db"] = r
            chk("narration ≥ 6 dB above bed (intelligibility)", r >= 6, r)

    sheet = contact_sheet(video, out_dir / "contact_sheet.png")
    rep["contact_sheet"] = str(sheet)
    times = [round(dur * f, 2) for f in (0.05, 0.25, 0.5, 0.75, 0.95)]
    rep["frames"] = [str(p) for p in extract_frames(video, times, out_dir / "frames")]
    rep["manual_review_required"] = [
        "Open contact_sheet.png and every frame: character on-model (face, outline, proportions), lighting (purple shadows, gold rim)",
        "Captions readable, not covering faces, spelled correctly (names/numbers/terms)",
        "Each narration cue lands with its visual action (check timing.json against frames)",
    ]
    write_json(out_dir / "qa_report.json", rep)
    log(f"QA {'PASS' if rep['pass'] else 'FAIL'}: {sum(c['pass'] for c in rep['checks'])}/{len(rep['checks'])} checks")
    return rep
