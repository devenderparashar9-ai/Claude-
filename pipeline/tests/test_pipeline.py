"""End-to-end tests on real (synthesized) media. Run: cd pipeline && ~/venv-video/bin/pytest -q"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest

from musevid import audio, captions, detect, edl, narration, probe, qa, speech
from musevid.common import decode_audio, ffmpeg, media_duration, write_json, write_wav

VOICE_OK = (narration.VOICE_DIR / "en_US-joe-medium.onnx").exists()


@pytest.fixture(scope="module")
def media(tmp_path_factory):
    d = tmp_path_factory.mktemp("media")
    # 1) "talking head": 3 spoken phrases separated by 1.6 s of dead air
    phrases = ["Today we fix the bad cut.", "Silence slows the story down.", "Now the pacing feels tight."]
    sr = 48000
    parts = [np.zeros(int(0.4 * sr), np.float32)]
    for i, p in enumerate(phrases):
        w = narration.tts_line(p, d / f"p{i}.wav", "en_US-joe-medium")
        parts += [decode_audio(w, sr), np.zeros(int(1.6 * sr), np.float32)]
    write_wav(d / "speech.wav", np.concatenate(parts), sr)
    dur = media_duration(d / "speech.wav")
    ffmpeg(["-f", "lavfi", "-i", f"testsrc2=size=1920x1080:rate=30:duration={dur}", "-i", str(d / "speech.wav"),
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(d / "talk.mp4")])
    # 2) shaky vertical 25 fps B-roll with no audio
    ffmpeg(["-f", "lavfi", "-i", "testsrc=size=1280x1280:rate=25:duration=4",
            "-vf", "crop=1080:1200:100+40*sin(n*1.7):40+30*cos(n*2.3),scale=720:1280,setsar=1",
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(d / "broll.mp4")])
    return {"dir": d, "talk": d / "talk.mp4", "broll": d / "broll.mp4", "phrases": phrases}


pytestmark = pytest.mark.skipif(not VOICE_OK, reason="piper voice not installed")


def test_probe_inventory(media):
    inv = {Path(i["path"]).name: i for i in probe.inventory(media["dir"])}
    assert inv["broll.mp4"]["video"]["width"] == 720 and inv["broll.mp4"]["video"]["fps"] == 25
    assert inv["broll.mp4"]["audio"] == []
    assert inv["talk.mp4"]["audio"][0]["channels"] == 1


def test_silence_and_jumpcut(media, tmp_path):
    sil = detect.silences(media["talk"], -40, 0.5)
    assert len(sil) >= 3
    e = speech.jumpcut_edl(str(media["talk"]), sil, 30, 1920, 1080, keep_pause=0.25)
    write_json(tmp_path / "jc.json", e)
    out = edl.render(tmp_path / "jc.json", tmp_path / "jc.mp4", preset="ultrafast")
    before, after = media_duration(media["talk"]), media_duration(out)
    assert after < before - 3.0, (before, after)          # dead air removed
    # remaining gaps are short, natural pauses — not zero, not long
    gaps = detect.silences(out, -40, 0.5)
    assert all(g["duration"] < 0.7 for g in gaps if 0.2 < g["start"] < after - 0.5), gaps
    # all words survive the cut
    tr = speech.transcribe(out)
    al = speech.align_script(" ".join(media["phrases"]).split(), tr["words"])
    assert al["match_ratio"] > 0.85, al


def test_timeline_reframe_ramp_broll_stab_and_export(media, tmp_path):
    e = {"fps": 30, "width": 1080, "height": 1920, "name": "vertical test",
         "clips": [
             {"src": str(media["talk"]), "in": 0.4, "out": 2.4, "label": "hook", "reframe": {"mode": "fill", "focus_x": 0.5}},
             {"src": str(media["broll"]), "in": 0, "out": 3, "label": "ramp", "ramp": [[0, 1.0], [0.5, 0.4], [1, 1.0]], "stabilize": True},
             {"src": str(media["talk"]), "in": 4.0, "out": 5.5, "label": "fit", "speed": 1.5, "reframe": {"mode": "fit"}},
         ],
         "overlays": [{"src": str(media["broll"]), "in": 0, "out": 1.0, "at": 0.5, "mode": "pip", "pip": {"w": 0.4, "x": 0.55, "y": 0.05}}]}
    write_json(tmp_path / "v.json", e)
    out = edl.render(tmp_path / "v.json", tmp_path / "v.mp4", preset="ultrafast")
    info = probe.describe(out)
    assert (info["video"]["width"], info["video"]["height"], info["video"]["fps"]) == (1080, 1920, 30)
    # ramp: 3 s at average speed < 1 → longer than 3 s; fit clip at 1.5x → 1 s
    assert 2.0 + 3.4 + 1.0 - 0.3 < info["duration"] < 2.0 + 6.0 + 1.0 + 0.3, info["duration"]
    files = edl.export_project(tmp_path / "v.json", tmp_path / "proj")
    names = {p.suffix for p in files}
    assert ".otio" in names and ".fcpxml" in names and ".xml" in names
    otio = json.loads((tmp_path / "proj" / "v.otio").read_text())
    assert otio["OTIO_SCHEMA"].startswith("Timeline")


def test_captions_ass_and_qc(tmp_path):
    words = [{"word": w, "start": i * 0.4, "end": i * 0.4 + 0.3} for i, w in enumerate("Pip found three solar panels today.".split())]
    captions.write_ass(words, tmp_path / "c.ass")
    txt = (tmp_path / "c.ass").read_text()
    assert "\\kf30" in txt and "Dialogue:" in txt
    assert captions.caption_qc(words) == []
    # burn-in actually renders with libass
    ffmpeg(["-f", "lavfi", "-i", "color=c=0x3b2a6b:s=1920x1080:d=3", "-vf", f"ass={tmp_path / 'c.ass'}", str(tmp_path / "c.mp4")])
    assert media_duration(tmp_path / "c.mp4") > 2.9


def test_align_flags_misheard_terms():
    script = "Pip learned how 3 solar panels power a city".split()
    heard = [{"word": w, "start": i * .3, "end": i * .3 + .25} for i, w in enumerate("Pip learned how three solar pals power city".split())]
    al = speech.align_script(script, heard)
    assert all(w is not None for w in al["words"])
    assert [w["word"] for w in al["words"]] == script           # script text wins
    kinds = {(i["script"], i["heard"]) for i in al["issues"]}
    assert ("panels", "pals") in kinds and any(i["type"] == "delete" for i in al["issues"])  # 'a' missing
    assert ("3", "three") not in kinds                          # number normalization is not an error


def test_mix_hits_loudness_target_and_ducks(media, tmp_path):
    dur = media_duration(media["dir"] / "speech.wav")
    audio.write_stem(tmp_path / "music.wav", audio.music_bed(dur))
    audio.write_stem(tmp_path / "fx.wav", audio.place([{"t": 1.0, "kind": "pop"}, {"t": 2.0, "kind": "whoosh"}], dur))
    audio.write_stem(tmp_path / "amb.wav", audio.ambience(dur))
    m = audio.mix(media["dir"] / "speech.wav", tmp_path / "mix.wav", tmp_path / "music.wav", tmp_path / "fx.wav", tmp_path / "amb.wav")
    assert m["pass"], m
    assert abs(m["integrated_lufs"] + 14) <= 1.0 and m["true_peak_dbtp"] <= -1.0


def test_qa_catches_black_and_frozen(tmp_path):
    # 2 s motion, 2 s black, 3 s frozen frame → QA must fail on both
    ffmpeg(["-f", "lavfi", "-i", "testsrc2=s=640x360:r=30:d=2", "-f", "lavfi", "-i", "color=black:s=640x360:r=30:d=2",
            "-f", "lavfi", "-i", "color=red:s=640x360:r=30:d=3", "-f", "lavfi", "-i", "sine=f=440:d=7",
            "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1[v]", "-map", "[v]", "-map", "3:a",
            "-pix_fmt", "yuv420p", "-c:a", "aac", str(tmp_path / "bad.mp4")])
    rep = qa.check(tmp_path / "bad.mp4", tmp_path / "qa", {"width": 640, "height": 360, "fps": 30})
    failed = {c["check"] for c in rep["checks"] if not c["pass"]}
    assert not rep["pass"]
    assert any("black" in f for f in failed) and any("frozen" in f for f in failed)
    assert Path(rep["contact_sheet"]).exists()
