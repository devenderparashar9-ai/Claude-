---
name: render-qa
description: Final render verification and delivery — confirm the MP4 exists, inspect duration/resolution/aspect/fps/pixel format, A/V drift, black or frozen frames, loudness/true-peak/clipping, dead air, caption QC, extract contact sheet and per-cue frames, review them visually, fix and re-render, then deliver MP4 + captions + project files + QA report. Use after every render and before telling the user a video is done.
---

# Render QA + delivery

**Never claim success from a successful command or a storyboard.** A video is delivered only when the automated report passes *and* you have looked at the frames.

## 1. Automated checks
```bash
$PY -m musevid qa build/<name>.mp4 build/qa --width 1920 --height 1080 --fps 30 --platform youtube --timing build/narration/timing.json
# exit code 2 = failed checks; report in build/qa/qa_report.json
```
Checks: file exists · video+audio streams · resolution · fps · `yuv420p` · A/V duration drift < 100 ms · duration in range · no unintended black frames (`blackdetect`) · no frozen picture ≥ 2.5 s (`freezedetect`) · integrated loudness ±1 LU of target · true peak ≤ ceiling · zero clipped samples · no dead-air ≥ 1.5 s · narration ≥ 6 dB over bed. `produce --stages qa` adds caption QC, narration issues, and a frame at every cue.

## 2. Look (mandatory)
Read `build/qa/contact_sheet.png` and every `build/qa/cue_frames/*.png` (one per narration cue, +0.35 s):
- character on-model; lighting consistent (purple shadow, gold rim)
- the action matches the word being spoken at that frame
- captions spelled right, readable, not on faces
- transitions clean; nothing cropped awkwardly; no rendering glitches (missing fonts → boxy fallback text, blank layers)

## 3. Listen (by proxy)
Re-transcribe the final MP4 and align to the script: match ratio should stay ≥ the narration's. Check `mix_loudness.json` and `speech_over_bed_db`.

## 4. Fix → re-render
Fix at the source (script/beats/theme/component), never by patching the output. Re-run only the affected stages (`--stages animate,master,qa` for visuals, `audio,master,qa` for sound). Repeat until clean.

## 5. Deliver
- `build/<name>.mp4` — H.264/AAC, faststart
- `build/<name>.srt` (upload as YouTube captions) and `.ass` (styled burn-in)
- editable project: Remotion source + `productions/<name>/` (animated); `.otio/.fcpxml/.xml` (footage edits)
- `build/qa/qa_report.json` + contact sheet
Send files with SendUserFile; state plainly what was verified and what still needs a human (taste, a real listen on speakers).
