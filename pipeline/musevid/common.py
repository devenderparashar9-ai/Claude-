"""Shared helpers: subprocess wrappers, ffprobe, JSON IO, audio decode."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np


class ToolError(RuntimeError):
    pass


def log(msg: str) -> None:
    print(f"[musevid] {msg}", file=sys.stderr, flush=True)


def require(*tools: str) -> None:
    missing = [t for t in tools if shutil.which(t) is None]
    if missing:
        raise ToolError(f"missing required tools: {', '.join(missing)}")


def run(cmd: list[str], *, capture: bool = True, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command; on failure raise with the tail of stderr (never swallow errors)."""
    p = subprocess.run([str(c) for c in cmd], capture_output=capture, text=True)
    if check and p.returncode != 0:
        tail = (p.stderr or "")[-2500:]
        raise ToolError(f"command failed ({p.returncode}): {' '.join(map(str, cmd[:8]))} ...\n{tail}")
    return p


def ffmpeg(args: list[str], **kw) -> subprocess.CompletedProcess:
    return run(["ffmpeg", "-hide_banner", "-nostdin", "-y", *args], **kw)


def ffprobe_json(path: str | Path) -> dict[str, Any]:
    p = run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", str(path)])
    return json.loads(p.stdout)


def parse_rate(r: str | None) -> float:
    if not r or r in ("0/0", "N/A"):
        return 0.0
    return float(Fraction(r))


def media_duration(path: str | Path) -> float:
    return float(ffprobe_json(path)["format"].get("duration", 0.0))


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text())


def write_json(path: str | Path, data: Any) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=_np_default))
    return path


def _np_default(o: Any) -> Any:
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    raise TypeError(type(o))


def decode_audio(path: str | Path, sr: int = 16000, mono: bool = True) -> np.ndarray:
    """Decode any media to float32 PCM via FFmpeg (avoids PyAV version issues)."""
    ch = "1" if mono else "2"
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", ch, "-ar", str(sr), "-"],
        capture_output=True, check=True,
    )
    a = np.frombuffer(p.stdout, np.int16).astype(np.float32) / 32768.0
    return a if mono else a.reshape(-1, 2)


def write_wav(path: str | Path, audio: np.ndarray, sr: int) -> Path:
    """Write float audio (mono or Nx2) as 16-bit WAV, with a hard clip guard."""
    import wave

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.clip(np.asarray(audio, np.float32), -1.0, 1.0)
    ch = 1 if a.ndim == 1 else a.shape[1]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((a * 32767).astype("<i2").tobytes())
    return path


def model_dir(kind: str) -> Path:
    """Locate a model directory: $MUSEVID_<KIND>_DIR, ~/models/<kind>, /home/user/models/<kind>."""
    import os
    env = os.environ.get(f"MUSEVID_{kind.upper()}_DIR")
    cands = [Path(env)] if env else []
    cands += [Path.home() / "models" / kind, Path("/home/user/models") / kind]
    for c in cands:
        if c.exists():
            return c
    return cands[0]
