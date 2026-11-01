# Muse Video Studio

An integrated production system for **animated cartoon explainers** and **professionally
edited videos**, driven by Claude Code skills and real tools (FFmpeg, Remotion,
faster-whisper, Piper TTS, OpenTimelineIO). Everything here was run and verified, not just described.

```
productions/<name>/script.json + beats.json
        │  narrate (Piper, best-of-N takes, ASR-verified)        → narration.wav, timing.json (word times)
        │  cues    (every action anchored to a spoken word)       → cues.json → Remotion
        │  animate (Remotion: rigged character, camera, graphics) → video_silent.mp4
        │  audio   (SFX from the same cues, music, ambience, ducking, 2-pass loudness) → mix.wav
        │  master  (mux + SRT/ASS)                                → <name>.mp4
        └  qa      (geometry, black/frozen, loudness, true peak, clipping, dead air,
                    intelligibility through the mix, contact sheet, frame at every cue)
```

## Quick start

```bash
bash scripts/setup.sh                      # fresh container: venv, voices, whisper, node_modules (~3 min)
cd pipeline
~/venv-video/bin/python -m musevid.produce ../productions/solar-pip --comp SolarPip
~/venv-video/bin/python -m pytest -q       # 7 end-to-end tests on real media
```

Footage editing:
```bash
PY=~/venv-video/bin/python
$PY -m musevid probe raw/ -o work/inventory.json
$PY -m musevid jumpcut raw/talk.mp4 -o work/edl.json      # speech-aware silence removal
$PY -m musevid render-edl work/edl.json out/cut.mp4
$PY -m musevid export-project work/edl.json out/project   # .otio / .fcpxml / Premiere .xml
$PY -m musevid qa out/cut.mp4 out/qa --width 1920 --height 1080 --fps 30
```

## Layout

| Path | Contents |
|---|---|
| `.claude/skills/` | `video-production` (router), `cartoon-style`, `motion-graphics`, `captions-narration`, `footage-editing`, `audio-post`, `render-qa` |
| `pipeline/musevid/` | probe · detect (scenes/silence/black/freeze) · edl (render + NLE export) · speech (whisper, alignment, jump cuts) · narration (TTS) · captions (SRT/ASS karaoke) · audio (SFX/music/ambience synth, dialogue chain, ducking, loudness) · qa · produce |
| `animation/` | Remotion project: `theme.ts` (style bible), `components/Lit.tsx` (purple-shadow / gold-rim lighting), `characters/Pip.tsx` (rig + model sheet), `world/` (parallax camera, environment), `graphics/` (explainer inserts), `components/Overlays.tsx` (captions, titles, transitions, grade) |
| `productions/solar-pip/` | Demo: "How Sunlight Becomes Electricity" |
| `docs/repo-evaluation.md` | The 14 requested repos + awesome-list candidates: what they are, licenses, dependencies, duplicates, verdicts |
| `docs/muse-capabilities.md` | What this environment can and cannot do, tested |
| `docs/THIRD_PARTY_NOTICES.md` | Attribution |

## Licensing notes

Original code here is yours. Remotion has its own license (free for individuals and companies
of up to 3 people). The voices used (Piper `joe`: CC0; `libritts_r`: CC BY 4.0) are
commercial-safe; several popular Piper voices are **not** (see `captions-narration` skill).
Fredoka font: SIL OFL. All music and SFX are generated procedurally, so there's no licensing to track.
