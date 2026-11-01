---
name: footage-editing
description: Edit real/raw footage deterministically with FFmpeg via the musevid EDL pipeline — media inventory, scene/shot detection, silence removal and jump cuts, transcript-based cuts, trimming/sequencing, B-roll and picture-in-picture, speed changes and eased speed ramps, stabilization, reframing/aspect conversion, platform exports, and editable NLE project export (OTIO, FCPXML, Premiere XML).
---

# Footage editing (EDL → FFmpeg)

The **EDL JSON is the contract**: the edit is text, rebuilt with one command. Never hand-write per-cut FFmpeg commands; never order clips by filename glob. Source files are read-only.

## 1. Inventory (gate: every file probed, warnings read)
```bash
$PY -m musevid probe raw/ -o work/inventory.json
```
Reports codec, size, fps, rotation, audio layout, and warnings: **VFR** (conform first: `ffmpeg -i in -vf fps=30 -c:a copy cfr.mp4`), **HDR** (tone-map before mixing), rotation.

## 2. Analyse (detection informs judgment — doesn't replace it)
```bash
$PY -m musevid scenes raw/a.mp4 --threshold 0.3      # shot list
$PY -m musevid silences raw/a.mp4 --db -35 --min 0.4 # dead air
$PY -m musevid transcribe raw/a.mp4 -o work/a.json   # words for transcript cuts
```
Then **look at frames** (`qa.extract_frames` or a contact sheet). A transcript won't tell you the speaker stood up mid-sentence.

## 3. Cut
- Silence removal: `$PY -m musevid jumpcut raw/a.mp4 -o edl.json --keep-pause 0.25` — leaves 0.25 s of each pause (zero sounds like a stutter), alternates 1.0/1.08 punch-in so cuts read as angle changes. Protect dramatic pauses (`protect=[(s,e)]` in `speech.keep_ranges_from_silence`).
- Transcript cuts: pick phrases → `{"src","in","out","label"}` clips, cut at phrase ends.

EDL fields (see `pipeline/musevid/edl.py` docstring):
```json
{"fps":30,"width":1080,"height":1920,
 "clips":[{"src":"raw/a.mp4","in":1.2,"out":4.6,"reframe":{"mode":"fill","focus_x":0.4},"zoom":1.08},
          {"src":"raw/b.mp4","in":0,"out":3,"ramp":[[0,1],[0.5,0.35],[1,1]],"stabilize":true},
          {"src":"raw/c.mp4","in":5,"out":7,"speed":1.5,"reframe":{"mode":"fit"}}],
 "overlays":[{"src":"broll/x.mp4","in":0,"out":2.5,"at":3.0,"mode":"full"},
             {"src":"broll/y.mp4","in":0,"out":2,"at":8,"mode":"pip","pip":{"w":0.35,"x":0.6,"y":0.06}}]}
```
- `reframe.fill` crops around a focus point (16:9 → 9:16); `fit` pads.
- `speed` 0.25–4 (audio pitch-preserved via chained `atempo`); `ramp` expands into eased constant-speed steps.
- `stabilize` runs two-pass vid.stab (cached).
- B-roll overlays get 120 ms alpha fades; `keep_audio` mixes their sound.

## 4. Render + export
```bash
$PY -m musevid render-edl edl.json out/rough.mp4
$PY -m musevid export-project edl.json out/project   # .otio (Resolve/OTIO), .fcpxml (FCP/Resolve), .xml (Premiere)
```
Before modifying a live NLE project, save a versioned checkpoint; rendered ≠ editable ≠ approved — report them separately.

## 5. Platform exports
| Platform | Size | fps | Loudness |
|---|---|---|---|
| YouTube | 1920×1080 (or 3840×2160) | source (24/30/60) | −14 LUFS, TP ≤ −1 |
| Shorts/TikTok/Reels | 1080×1920 | 30 | −14 LUFS; keep text out of bottom 20% / right 15% |
| Square | 1080×1080 | 30 | −14 LUFS |
Encode H.264 `yuv420p`, AAC 48 kHz, `+faststart` (the renderer does this).

## Rules from real edits
cut at phrase ends · keep 0.2–0.3 s of pauses · never cut dramatic pauses · cards above faces, never on them · leave a stretch with no graphics · verify by looking (`hstack` stills) · generated data goes in `work/`, never back into the EDL.
Limits: object tracking and masked grading need Resolve/Premiere/AE.
