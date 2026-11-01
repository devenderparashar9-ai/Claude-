"""Source-footage inventory and metadata inspection."""
from __future__ import annotations

from pathlib import Path

from .common import ffprobe_json, parse_rate

MEDIA_EXT = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mxf", ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".png", ".jpg", ".jpeg"}


def describe(path: str | Path) -> dict:
    info = ffprobe_json(path)
    fmt = info["format"]
    out: dict = {
        "path": str(path),
        "container": fmt.get("format_name"),
        "duration": float(fmt.get("duration", 0) or 0),
        "size_bytes": int(fmt.get("size", 0) or 0),
        "bit_rate": int(fmt.get("bit_rate", 0) or 0),
        "video": None,
        "audio": [],
        "warnings": [],
    }
    for s in info["streams"]:
        if s["codec_type"] == "video" and out["video"] is None and s.get("disposition", {}).get("attached_pic", 0) == 0:
            afr = parse_rate(s.get("avg_frame_rate"))
            rfr = parse_rate(s.get("r_frame_rate"))
            rot = 0
            for sd in s.get("side_data_list", []) or []:
                if "rotation" in sd:
                    rot = int(sd["rotation"])
            w, h = int(s.get("width", 0)), int(s.get("height", 0))
            if abs(rot) in (90, 270):
                w, h = h, w
            out["video"] = {
                "codec": s.get("codec_name"),
                "width": w,
                "height": h,
                "display_aspect": s.get("display_aspect_ratio"),
                "sample_aspect": s.get("sample_aspect_ratio"),
                "fps": round(afr, 3),
                "pix_fmt": s.get("pix_fmt"),
                "color_transfer": s.get("color_transfer"),
                "rotation": rot,
                "frames": int(s["nb_frames"]) if s.get("nb_frames", "").isdigit() else None,
            }
            if afr and rfr and abs(afr - rfr) > 0.01:
                out["warnings"].append(f"variable frame rate suspected (avg {afr:.3f} vs r {rfr:.3f}) — conform to CFR before editing")
            if s.get("color_transfer") in ("smpte2084", "arib-std-b67"):
                out["warnings"].append("HDR transfer — tone-map before mixing with SDR")
            if rot:
                out["warnings"].append(f"rotation metadata {rot}° — dimensions reported post-rotation")
        elif s["codec_type"] == "audio":
            out["audio"].append({
                "codec": s.get("codec_name"),
                "sample_rate": int(s.get("sample_rate", 0)),
                "channels": s.get("channels"),
                "layout": s.get("channel_layout"),
            })
    if out["video"] is None and not out["audio"]:
        out["warnings"].append("no audio or video streams")
    return out


def inventory(root: str | Path) -> list[dict]:
    root = Path(root)
    files = [root] if root.is_file() else sorted(p for p in root.rglob("*") if p.suffix.lower() in MEDIA_EXT)
    return [describe(p) for p in files]
