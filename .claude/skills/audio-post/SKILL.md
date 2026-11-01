---
name: audio-post
description: Professional audio post-production — dialogue cleanup/noise reduction, EQ, compression, de-essing, voice-over leveling, music beds and sidechain ducking, synchronized SFX, ambience, stereo mix, two-pass loudness normalization to platform targets, and measured true-peak/clipping checks. Use whenever a video needs sound, music, SFX, mixing, or a loudness check.
---

# Audio post

Narration must stay prominent and intelligible; music and SFX support it.

## Order of work
1. **Dialogue first** — clean and level the voice (`DIALOGUE_CHAIN` in `musevid/audio.py`):
   - `recorded`: high-pass 80 Hz → `afftdn` denoise → −2.5 dB @250 Hz (mud) → +2.5 dB @3.2 kHz (presence) → `deesser` → `acompressor` 3:1 → limiter.
   - `tts`: same tone shaping, **no denoise** (adds artifacts to clean TTS), gentler compression.
2. **SFX from cues** — `beats.json` `sfx[]` references the same cues as the visuals, so sound and picture can't drift. Kinds: `whoosh` (camera moves/transitions), `pop` (element appears), `chime` (reveal), `impact` (hits/landings), `riser` (build into a reveal; use negative offset so it peaks on the cue), `click`, `boing`. Repeats get ±3% pitch variation (no machine-gun effect). Phrase reveals as riser → impact/chime.
3. **Music** — `music_bed(dur, bpm, mood)`: procedural, seeded, license-free (pad + arpeggio + soft pulse). Licensed tracks: record source + license in the production folder.
4. **Ambience** — `ambience(dur, kind)` room tone / outdoor bed at −24…−28 dB.
5. **Mix** — music is **sidechain-ducked** by the narration (`sidechaincompress`, attack 40 ms, release 450 ms), then `amix` (no auto-normalize).
6. **Master** — two-pass `loudnorm` (measure → apply with measured values, linear) + true-peak limiter.
7. **Measure the final file** — never assume.

```bash
$PY -m musevid mix narration.wav mix.wav --music music.wav --sfx sfx.wav --amb amb.wav --platform youtube --dialogue tts
$PY -m musevid loudness final.mp4     # integrated LUFS, LRA, true peak, sample peak
```
Or as part of `musevid.produce --stages audio`.

## Targets
| Platform | Integrated | True peak |
|---|---|---|
| youtube / tiktok / instagram | −14 LUFS | ≤ −1 dBTP |
| podcast | −16 LUFS | ≤ −1 dBTP |
| broadcast (EBU R128) | −23 LUFS | ≤ −1 dBTP |

QA fails if integrated is off by > 1 LU, true peak exceeds the ceiling, any sample clips, a dead-air gap ≥ 1.5 s appears mid-video, or narration is < 6 dB above the bed (`speech_to_music_ratio`).

## Listening
An agent can't hear. Substitute measurements + ASR: re-transcribe the **final mix** and compare with the script (if music masks words, the match ratio drops), check speech-over-bed dB, and check SFX timestamps against cue frames. Tell the user a human listen is still recommended for taste (music choice, SFX character).
