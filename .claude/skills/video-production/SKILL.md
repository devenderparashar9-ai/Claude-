---
name: video-production
description: Entry point for ANY video request in this repo — animated cartoon explainers, editing raw footage, captions, voice-over, music/SFX, rendering, or delivering an MP4. Routes each production stage to the right skill and tool (musevid pipeline, Remotion studio, FFmpeg, Whisper, Piper) and enforces the render → inspect → fix → re-render loop. Use when the user says "make a video", "edit this footage", "animate", "explainer", "cartoon", "add captions", "voice-over", "render", "export for YouTube/TikTok".
---

# Video production — router

One integrated system. Tools live in this repo:

| Path | What |
|---|---|
| `pipeline/musevid/` | Python CLI: probe, scenes, silences, transcribe, align, jumpcut, EDL render, NLE export, narrate (TTS), captions, mix, loudness, QA, `produce` driver |
| `animation/` | Remotion studio: Pip character rig, lit-shape system, world/camera, explainer graphics, captions, grade |
| `productions/<name>/` | One folder per video: `script.json`, `beats.json`, `build/` (generated) |

Environment (verify with the preflight below; don't assume): `PY=~/venv-video/bin/python` (or `/home/user/venv-video/bin/python`), run CLI as `cd pipeline && $PY -m musevid <cmd>`.

## Preflight (run first, every session)

```bash
for t in ffmpeg ffprobe node npx; do command -v $t >/dev/null || echo "MISSING $t"; done
$PY -c "import faster_whisper, piper, opentimelineio" || echo "run: python3 -m venv ~/venv-video && ~/venv-video/bin/pip install -r pipeline/requirements.txt"
ls ~/models/piper/*.onnx /home/user/models/piper/*.onnx 2>/dev/null | head -1 || echo "voice model missing — see docs/setup.md"
(cd animation && [ -d node_modules ] || npm ci)
```
If something is missing, follow `docs/setup.md`. Never run third-party install scripts blindly.

## Execution order (never skip ahead — each stage's output is the next one's input)

| # | Stage | Skill | Gate (must exist / pass before moving on) |
|---|---|---|---|
| 1 | Story + audience | this skill | one-sentence premise, audience, platform, length in `script.json` |
| 2 | Script, storyboard, timing plan | `cartoon-style` | `script.json` lines (fact-checked), `beats.json` cues: every action anchored to a word |
| 3 | Characters + environments | `cartoon-style` | model sheet still rendered (`ModelSheet`) and **looked at** |
| 4 | Assets | `motion-graphics` | all props as lit SVG components; licenses recorded |
| 5 | Narration | `captions-narration` | `build/narration/timing.json`, match ≥ 0.9, issues reviewed |
| 6 | Animate (characters, camera, graphics) | `motion-graphics`, `cartoon-style` | review stills at every cue (`node animation/scripts/stills.mjs`) |
| 7 | Edit sequence / B-roll (footage jobs) | `footage-editing` | EDL JSON + rendered rough cut |
| 8 | SFX + music | `audio-post` | SFX events derived from the same cues (no hand-timed sounds) |
| 9 | Mix + grade | `audio-post`, `motion-graphics` | mix at platform target, measured |
| 10 | Render | `render-qa` | MP4 exists |
| 11 | Inspect → fix → re-render | `render-qa` | `qa_report.json` pass **and** contact sheet + cue frames reviewed |
| 12 | Deliver | `render-qa` | MP4 + SRT/ASS + editable project (if footage) + QA report |

Animated explainer, all stages after writing script/beats:
```bash
cd pipeline && $PY -m musevid.produce ../productions/<name> --comp <RemotionCompId>
# or stage by stage: --stages narrate,cues | animate | audio,master,qa
```

## Non-negotiables

- **Narration drives the timeline.** Visual timing comes from ASR word timestamps of the final narration; never hand-type frame numbers. Change `beats.json`, regenerate.
- **Never claim success from an exit code.** A render is done only after QA passes and you have looked at the frames.
- **Don't trust ASR.** Script text wins over ASR text; ASR wins on timing. Review every reported mismatch, especially names, numbers, technical terms.
- **Measure audio.** Loudness/true-peak come from `musevid loudness` on the final file, not from the settings used.
- **License hygiene.** Check every voice model's *dataset* license, every font (OFL OK), every music/SFX source. Procedural audio from `musevid.audio` is license-free.

## Adding new skills/tools (discovery checklist)

Candidates come from `clonn/awesome-agent-video-skills` and `zhuyansen/awesome-claude-video-skills`. Before integrating any:
1. Clone into an isolated temp dir; read SKILL.md, scripts, manifests. **Run nothing.**
2. What does it add that `docs/repo-evaluation.md` says we lack? If it duplicates, skip.
3. License: MIT/Apache/BSD/OFL/CC0 ok; AGPL or non-commercial → skip for monetized work.
4. Requirements: paid API, desktop app, GPU, account? Record in `docs/muse-capabilities.md`.
5. Maintenance: recent commits, docs, issues answered.
6. Integrate by distilling into our skills/tools with attribution in `docs/THIRD_PARTY_NOTICES.md`.
