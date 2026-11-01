---
name: captions-narration
description: Narration (local Piper TTS with take selection), transcription (faster-whisper word timestamps), script-to-ASR alignment, pronunciation checks, subtitle generation (SRT, ASS karaoke), caption QC, dialogue-based editing and voice-over retiming. Use for any voice-over, transcript, subtitle, caption or "what does this say" task.
---

# Captions + narration

## Narration (TTS)

```bash
cd pipeline && $PY -m musevid narrate ../productions/<name>/script.json ../productions/<name>/build/narration
```
- Script JSON: `voice`, `pace`, `lines[{id,text,pause_after,pace?}]`, optional `pronounce {"word": "respelling"}` (affects TTS input only, never captions).
- Each line: up to 4 takes → each is re-transcribed → best match kept → cached by content hash (Piper sampling is stochastic; cache makes re-runs reproducible). Delete `build/narration/lines/<id>.*.wav` to force new takes.
- Output `timing.json`: line bounds, per-word times (script text, ASR timing, clamped inside line bounds), `issues`, `takes`, per-frame `mouth` envelope for lip-sync.
- **Voice licenses**: `en_US-joe-medium` (CC0) and `en_US-libritts_r-medium` (CC BY 4.0, 904 speakers via `"speaker": N`) are commercial-safe. `lessac`, `ryan`, `hfc_*` datasets are non-commercial — don't use for monetized videos.
- Cloud alternatives (ElevenLabs, OpenAI TTS, vidIQ `voiceover_generate` MCP) need accounts/credits — ask the user first.

### Pronunciation workflow (real example)
Joe voice said "photons" as "Phopons" in every take. Test respellings by synthesizing and transcribing 3× each; `"fo tons"` was heard as "photons" 3/3 → added to `pronounce`. Do this for every name/term the ASR flags.

## Transcription

```bash
$PY -m musevid transcribe input.mp4 -o transcript.json --prompt "Pip, photovoltaic, inverter"
```
`--prompt` biases spelling of names/jargon. Output has word timestamps + confidence + `flags`:
- **Hallucination over silence** ("Thank you for watching.") — real, happened on our narration tail. Read the first and last lines yourself.
- Low-confidence words → proofread list.
Decoding uses FFmpeg → numpy (avoids a PyAV/faster-whisper version incompatibility).

## Alignment (never trust ASR blindly)

```bash
$PY -m musevid align script.txt transcript.json -o aligned.json
```
Script text wins; ASR timing wins. Every replace/insert/delete is reported. Numbers ↔ words ("3" vs "three") are normalized, not errors. Human-check every issue involving names, numbers, technical terms.

## Captions

```bash
$PY -m musevid captions build/narration/timing.json build/<name> --width 1920 --height 1080   # → .ass + .srt + QC
ffmpeg -i video.mp4 -vf "ass=build/<name>.ass" -c:a copy burned.mp4     # burn-in (libass)
```
- Phrases break on punctuation, pauses > 0.45 s, 5 words / 28 chars / 2.6 s.
- ASS karaoke uses `\kf` (word fills gold exactly while spoken) + subtle pop-in. In Remotion, `Captions` does the same with springs.
- QC: overlaps, words < 60 ms, reading speed > 20 cps.
- Keep captions out of faces; vertical video → raise `margin_v` above platform UI.

## Dialogue-based editing / retiming

- Cut by transcript: choose phrases, map to source ranges, write an EDL (see `footage-editing`); cut at phrase ends, never mid-idea.
- After cutting, retime captions with `speech.retime_words(words, keep_ranges)`.
- Voice-over placement: narration is the timeline — move visuals to the words, never stretch the voice. If VO changes, re-run `narrate` + `cues`; visuals follow automatically.
- Ducking is in `audio-post`.
