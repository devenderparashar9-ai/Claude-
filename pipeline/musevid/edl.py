"""EDL (edit decision list) → rendered timeline, plus editable NLE exports.

EDL JSON is the *contract* for an edit. Shape:

{
  "fps": 30, "width": 1920, "height": 1080,
  "clips": [
    {"src": "raw/a.mp4", "in": 1.2, "out": 4.6, "label": "hook",
     "speed": 1.0,                      # constant speed (0.25–4)
     "ramp": [[0, 1.0], [0.5, 0.35], [1, 1.0]],  # optional speed ramp, [position 0-1, speed]
     "reframe": {"mode": "fill", "focus_x": 0.5, "focus_y": 0.5},   # fill=crop, fit=pad
     "zoom": 1.0,                       # punch-in (1.1 = 10%)
     "stabilize": false}
  ],
  "overlays": [   # B-roll / picture-in-picture, placed on the *output* timeline
    {"src": "broll/city.mp4", "in": 0, "out": 3, "at": 5.0, "mode": "full" | "pip",
     "pip": {"w": 0.35, "x": 0.62, "y": 0.06}, "keep_audio": false}
  ]
}
Clips are concatenated in list order (never by filename glob).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .common import ToolError, ffmpeg, ffprobe_json, log, read_json

CACHE = Path(".musevid_cache")


def _has_audio(src: str) -> bool:
    return any(s["codec_type"] == "audio" for s in ffprobe_json(src)["streams"])


def _atempo_chain(speed: float) -> str:
    """atempo accepts 0.5–2.0 per instance; chain for wider ranges."""
    parts, s = [], speed
    while s > 2.0:
        parts.append("atempo=2.0"); s /= 2.0
    while s < 0.5:
        parts.append("atempo=0.5"); s /= 0.5
    parts.append(f"atempo={s:.5f}")
    return ",".join(parts)


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def expand_ramps(clips: list[dict], steps: int = 12) -> list[dict]:
    """Turn a speed ramp into short constant-speed sub-clips with eased speed changes."""
    out = []
    for c in clips:
        ramp = c.get("ramp")
        if not ramp:
            out.append(c)
            continue
        dur = c["out"] - c["in"]
        for i in range(steps):
            p0, p1 = i / steps, (i + 1) / steps
            mid = (p0 + p1) / 2
            for (a, sa), (b, sb) in zip(ramp, ramp[1:]):
                if a <= mid <= b:
                    speed = sa + (sb - sa) * _smooth((mid - a) / (b - a) if b > a else 0)
                    break
            else:
                speed = ramp[-1][1]
            sub = {k: v for k, v in c.items() if k != "ramp"}
            sub.update({"in": c["in"] + p0 * dur, "out": c["in"] + p1 * dur, "speed": speed,
                        "label": f"{c.get('label', 'clip')}#ramp{i}"})
            out.append(sub)
    return out


def _stabilized(src: str) -> str:
    """Two-pass vid.stab; cached by source hash."""
    CACHE.mkdir(exist_ok=True)
    key = hashlib.sha1(f"{Path(src).resolve()}:{Path(src).stat().st_mtime}".encode()).hexdigest()[:12]
    out = CACHE / f"stab_{key}.mp4"
    if out.exists():
        return str(out)
    trf = CACHE / f"stab_{key}.trf"
    log(f"stabilizing {src} (two-pass vid.stab)")
    ffmpeg(["-i", src, "-vf", f"vidstabdetect=shakiness=6:accuracy=15:result={trf}", "-f", "null", "-"])
    ffmpeg(["-i", src, "-vf", f"vidstabtransform=input={trf}:smoothing=20:zoom=2,unsharp=5:5:0.6",
            "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "copy", str(out)])
    return str(out)


def _frame_chain(c: dict, W: int, H: int, fps: int) -> str:
    rf = c.get("reframe", {"mode": "fill"})
    fx, fy = rf.get("focus_x", 0.5), rf.get("focus_y", 0.5)
    z = float(c.get("zoom", 1.0))
    if rf.get("mode") == "fit":
        geo = (f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
               f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black")
    else:  # fill: cover then crop around the focus point
        geo = (f"scale={int(W * z)}:{int(H * z)}:force_original_aspect_ratio=increase,"
               f"crop={W}:{H}:(iw-{W})*{fx}:(ih-{H})*{fy}")
    return f"{geo},setsar=1,fps={fps},format=yuv420p"


def build_filtergraph(edl: dict) -> tuple[list[str], str, list[str]]:
    W, H, fps = edl["width"], edl["height"], edl["fps"]
    clips = expand_ramps(edl["clips"])
    if not clips:
        raise ToolError("EDL has no clips")
    inputs: list[str] = []
    idx: dict[str, int] = {}

    def inp(src: str) -> int:
        if src not in idx:
            idx[src] = len(inputs) // 2
            inputs.extend(["-i", src])
        return idx[src]

    parts, concat = [], []
    for n, c in enumerate(clips):
        src = _stabilized(c["src"]) if c.get("stabilize") else c["src"]
        i = inp(src)
        sp = float(c.get("speed", 1.0))
        if not 0.25 <= sp <= 4:
            raise ToolError(f"clip {n}: speed {sp} outside 0.25–4")
        a, b = float(c["in"]), float(c["out"])
        if b <= a:
            raise ToolError(f"clip {n} ({c.get('label')}): out <= in")
        parts.append(f"[{i}:v]trim=start={a}:end={b},setpts=(PTS-STARTPTS)/{sp},{_frame_chain(c, W, H, fps)}[v{n}]")
        if _has_audio(src):
            parts.append(f"[{i}:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,{_atempo_chain(sp)},"
                         f"aformat=sample_rates=48000:channel_layouts=stereo[a{n}]")
        else:
            parts.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={(b - a) / sp}[a{n}]")
        concat.append(f"[v{n}][a{n}]")
    parts.append(f"{''.join(concat)}concat=n={len(clips)}:v=1:a=1[vcat][acat]")

    vlast, alast = "vcat", "acat"
    amix = []
    for k, o in enumerate(edl.get("overlays", [])):
        i = inp(o["src"])
        a, b, at = float(o["in"]), float(o["out"]), float(o["at"])
        d = b - a
        if o.get("mode", "full") == "pip":
            pw = int(W * o.get("pip", {}).get("w", 0.35)) // 2 * 2
            geo = f"scale={pw}:-2,setsar=1"
            x = int(W * o.get("pip", {}).get("x", 0.62)); y = int(H * o.get("pip", {}).get("y", 0.06))
        else:
            geo = _frame_chain({"reframe": o.get("reframe", {"mode": "fill"})}, W, H, fps)
            x = y = 0
        parts.append(f"[{i}:v]trim=start={a}:end={b},setpts=PTS-STARTPTS+{at}/TB,{geo},format=yuva420p,"
                     f"fade=t=in:st={at}:d=0.12:alpha=1,fade=t=out:st={at + d - 0.12}:d=0.12:alpha=1[ov{k}]")
        parts.append(f"[{vlast}][ov{k}]overlay=x={x}:y={y}:eof_action=pass:enable='between(t,{at},{at + d})'[vo{k}]")
        vlast = f"vo{k}"
        if o.get("keep_audio") and _has_audio(o["src"]):
            parts.append(f"[{i}:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,adelay={int(at * 1000)}:all=1,"
                         f"aformat=sample_rates=48000:channel_layouts=stereo[oa{k}]")
            amix.append(f"[oa{k}]")
    if amix:
        parts.append(f"[{alast}]{''.join(amix)}amix=inputs={1 + len(amix)}:normalize=0:duration=first[amix]")
        alast = "amix"
    return inputs, ";\n".join(parts), [f"[{vlast}]", f"[{alast}]"]


def render(edl_path: str | Path, out: str | Path, crf: int = 18, preset: str = "medium") -> Path:
    edl = read_json(edl_path)
    inputs, graph, (v, a) = build_filtergraph(edl)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    gfile = out.with_suffix(".filtergraph.txt")
    gfile.write_text(graph)
    log(f"rendering {len(edl['clips'])} clips → {out}")
    ffmpeg([*inputs, "-filter_complex_script", str(gfile), "-map", v, "-map", a,
            "-c:v", "libx264", "-crf", str(crf), "-preset", preset, "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)])
    return out


# ---------------------------------------------------------------- NLE export

def to_otio(edl: dict):
    import opentimelineio as otio

    fps = edl["fps"]
    RT = lambda s: otio.opentime.RationalTime(round(s * fps), fps)  # noqa: E731
    from .common import media_duration

    def ref(src: str):
        return otio.schema.ExternalReference(
            target_url=Path(src).resolve().as_uri(),
            available_range=otio.opentime.TimeRange(RT(0), RT(media_duration(src))))

    tl = otio.schema.Timeline(name=edl.get("name", "musevid edit"))
    tl.global_start_time = RT(0)
    v1 = otio.schema.Track(name="V1", kind=otio.schema.TrackKind.Video)
    a1 = otio.schema.Track(name="A1", kind=otio.schema.TrackKind.Audio)
    for c in expand_ramps(edl["clips"]):
        rng = otio.opentime.TimeRange(RT(c["in"]), RT(c["out"] - c["in"]))
        for trk in (v1, a1):
            clip = otio.schema.Clip(name=c.get("label", Path(c["src"]).stem),
                                    media_reference=ref(c["src"]),
                                    source_range=rng)
            if float(c.get("speed", 1)) != 1:
                clip.effects.append(otio.schema.LinearTimeWarp(time_scalar=float(c["speed"])))
            trk.append(clip)
    tl.tracks.extend([v1, a1])
    if edl.get("overlays"):
        v2 = otio.schema.Track(name="V2 B-roll", kind=otio.schema.TrackKind.Video)
        cursor = 0.0
        for o in sorted(edl["overlays"], key=lambda o: o["at"]):
            if o["at"] > cursor:
                v2.append(otio.schema.Gap(source_range=otio.opentime.TimeRange(RT(0), RT(o["at"] - cursor))))
            v2.append(otio.schema.Clip(name=Path(o["src"]).stem,
                                       media_reference=ref(o["src"]),
                                       source_range=otio.opentime.TimeRange(RT(o["in"]), RT(o["out"] - o["in"]))))
            cursor = o["at"] + o["out"] - o["in"]
        tl.tracks.insert(1, v2)
    return tl


def export_project(edl_path: str | Path, out_dir: str | Path) -> list[Path]:
    """Write .otio (Resolve/OTIO-aware tools), .fcpxml (Final Cut / Resolve), .xml (Premiere FCP7 XML)."""
    import opentimelineio as otio

    edl = read_json(edl_path)
    tl = to_otio(edl)
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(edl_path).stem
    written = []
    for ext, adapter in ((".otio", "otio_json"), (".fcpxml", "fcpx_xml"), (".xml", "fcp_xml")):
        p = out_dir / f"{stem}{ext}"
        try:
            otio.adapters.write_to_file(tl, str(p), adapter_name=adapter)
            written.append(p)
        except Exception as e:  # report adapter limitations honestly instead of failing silently
            log(f"WARNING: {adapter} export failed: {e}")
    return written
