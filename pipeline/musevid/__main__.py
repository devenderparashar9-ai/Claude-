"""musevid CLI — `python -m musevid <command> ...` (run from pipeline/ or with PYTHONPATH=pipeline)."""
from __future__ import annotations

import argparse
import json
import sys

from . import audio, captions, detect, edl, narration, probe, qa, speech
from .common import read_json, write_json


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="musevid")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("probe", help="inventory media + metadata"); s.add_argument("path"); s.add_argument("-o")
    s = sub.add_parser("scenes", help="shot list from scene detection"); s.add_argument("video"); s.add_argument("--threshold", type=float, default=0.3)
    s = sub.add_parser("silences"); s.add_argument("media"); s.add_argument("--db", type=float, default=-35); s.add_argument("--min", type=float, default=0.4)
    s = sub.add_parser("transcribe"); s.add_argument("media"); s.add_argument("-o", required=True); s.add_argument("--model", default="small.en"); s.add_argument("--prompt")
    s = sub.add_parser("align", help="script text onto ASR timings"); s.add_argument("script_txt"); s.add_argument("transcript_json"); s.add_argument("-o", required=True)
    s = sub.add_parser("jumpcut", help="silence removal → EDL"); s.add_argument("video"); s.add_argument("-o", required=True)
    s.add_argument("--db", type=float, default=-35); s.add_argument("--min", type=float, default=0.5); s.add_argument("--keep-pause", type=float, default=0.25)
    s.add_argument("--width", type=int, default=1920); s.add_argument("--height", type=int, default=1080); s.add_argument("--fps", type=int, default=30)
    s = sub.add_parser("render-edl"); s.add_argument("edl"); s.add_argument("out"); s.add_argument("--crf", type=int, default=18)
    s = sub.add_parser("export-project", help="EDL → .otio/.fcpxml/.xml"); s.add_argument("edl"); s.add_argument("out_dir")
    s = sub.add_parser("narrate", help="script.json → narration.wav + timing.json"); s.add_argument("script"); s.add_argument("out_dir"); s.add_argument("--fps", type=int, default=30)
    s = sub.add_parser("captions", help="word timings → .ass karaoke + .srt"); s.add_argument("timing"); s.add_argument("out_stem")
    s.add_argument("--width", type=int, default=1920); s.add_argument("--height", type=int, default=1080)
    s = sub.add_parser("mix"); s.add_argument("narration"); s.add_argument("out"); s.add_argument("--music"); s.add_argument("--sfx"); s.add_argument("--amb")
    s.add_argument("--platform", default="youtube", choices=list(audio.TARGETS)); s.add_argument("--dialogue", default="tts", choices=list(audio.DIALOGUE_CHAIN))
    s = sub.add_parser("loudness"); s.add_argument("media")
    s = sub.add_parser("qa"); s.add_argument("video"); s.add_argument("out_dir"); s.add_argument("--width", type=int); s.add_argument("--height", type=int)
    s.add_argument("--fps", type=float); s.add_argument("--platform", default="youtube"); s.add_argument("--timing")

    a = ap.parse_args(argv)
    dump = lambda d: print(json.dumps(d, indent=2, default=str))  # noqa: E731
    if a.cmd == "probe":
        inv = probe.inventory(a.path); write_json(a.o, inv) if a.o else dump(inv)
    elif a.cmd == "scenes":
        dump(detect.shots(a.video, a.threshold))
    elif a.cmd == "silences":
        dump(detect.silences(a.media, a.db, a.min))
    elif a.cmd == "transcribe":
        write_json(a.o, speech.transcribe(a.media, a.model, initial_prompt=a.prompt))
    elif a.cmd == "align":
        words = open(a.script_txt).read().split()
        write_json(a.o, speech.align_script(words, read_json(a.transcript_json)["words"]))
    elif a.cmd == "jumpcut":
        sil = detect.silences(a.video, a.db, a.min)
        write_json(a.o, speech.jumpcut_edl(a.video, sil, a.fps, a.width, a.height, keep_pause=a.keep_pause))
    elif a.cmd == "render-edl":
        edl.render(a.edl, a.out, a.crf)
    elif a.cmd == "export-project":
        dump([str(p) for p in edl.export_project(a.edl, a.out_dir)])
    elif a.cmd == "narrate":
        t = narration.build(a.script, a.out_dir, a.fps); dump({"duration": t["duration"], "match_ratio": t.get("match_ratio"), "issues": t["issues"]})
    elif a.cmd == "captions":
        t = read_json(a.timing)
        words = [w for ln in t["lines"] for w in ln.get("words", [])] if "lines" in t else t["words"]
        captions.write_ass(words, a.out_stem + ".ass", a.width, a.height); captions.write_srt(words, a.out_stem + ".srt")
        dump({"qc": captions.caption_qc(words)})
    elif a.cmd == "mix":
        dump(audio.mix(a.narration, a.out, a.music, a.sfx, a.amb, dialogue=a.dialogue, platform=a.platform))
    elif a.cmd == "loudness":
        dump(audio.measure(a.media))
    elif a.cmd == "qa":
        exp = {k: getattr(a, k) for k in ("width", "height", "fps") if getattr(a, k)}
        rep = qa.check(a.video, a.out_dir, exp, a.platform, read_json(a.timing) if a.timing else None)
        dump(rep); return 0 if rep["pass"] else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
