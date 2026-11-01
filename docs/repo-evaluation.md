# Video-editing skill repositories — evaluation

Inspected 2026-11-01. Every repository was shallow-cloned into an isolated
directory and read file by file. **No install script, setup script or package
script from any of them was executed.** Verdicts are about fit for *this*
production system (local, CLI, cloud container, cartoon explainers), not about
general quality.

Legend — **Adopt**: ideas/rules distilled into our skills (with attribution).
**Reference**: worth reading; nothing copied. **Skip**: incompatible, redundant
or needs a service we don't have.

## The 14 requested repositories

| # | Repository | Last commit | License | What it actually is | Hard dependencies | Verdict |
|---|---|---|---|---|---|---|
| 1 | ElSalvatore-sys/video-editor-plugin | 2026-02-24 | **none** | Claude plugin: one 624-line ffmpeg/Remotion/Whisper cookbook skill, slash commands, Remotion template | macOS (`h264_videotoolbox`), `~/design-assets/` folder | **Reference only** — no license means no reuse. Recipes duplicate #3/#4 |
| 2 | imtamiliniyan/claude-video-skills | 2026-07-26 | MIT | 5 skills (router, talking-head, long-form, motion-design, reel script) + Remotion | AssemblyAI **or** OpenAI API key; `anthropic` SDK for transcript polish | **Adopt ideas**: intake router, transcript "polish" pass. Skip the cloud ASR bridge — we run Whisper locally |
| 3 | vibegameengine/video-motion-craft | 2026-09-08 | MIT + Apache-2.0 parts | One skill: Remotion motion craft + FFmpeg/Whisper editing; 12 non-negotiable motion rules; beat-sync; sound-design method; review checklist | Node, FFmpeg, Whisper | **Adopt** — best motion-design rules in the set; has proper third-party notices. Supersedes #5 (it already incorporates it) |
| 4 | blazerior/videoediting-claude-skill | 2026-09-11 | MIT | Transcript→EDL→ffmpeg pipeline for real footage, word-level ASS subs, HTML→PNG overlays, batch mode, 17 documented ffmpeg failures | faster-whisper, Chrome, Python | **Adopt** — best footage-editing method (cutting rules, "look at frames", Whisper hallucination check) |
| 5 | haidrrrry/claude-remotion-skill | 2026-08-12 | MIT | Remotion motion-graphics skill; same 10 rules as #3 | Node | **Duplicate** of #3 (which credits it). Keep attribution, don't install separately |
| 6 | OpenClip-App/agent-skills | 2026-08-07 | MIT | 10 thin skills wrapping the OpenClip **remote MCP server** | OpenClip account; clipping pipeline is **paid** (`complete_upload` starts billing) | **Skip** for now. Optional integration if the user signs up |
| 7 | wilwaldon/Claude-Code-Video-Toolkit | 2026-02-25 | **none** | A single README — curated list of tools | — | **Reference** (discovery list only) |
| 8 | voidash/claudepipe | 2026-04-03 | MIT | 1029-line `/footage` pipeline: spec-first, narration-driven timing, per-beat validation; React "studio" app | Google **Chirp 2** ASR (GCP), Gemini; Nepali/English | **Adopt ideas**: "narration drives the timeline", spec as single source of truth, keep ASR timestamps but fix ASR text. Skip GCP ASR |
| 9 | rendleyhq/video-editing-skill | 2026-06-10 | MIT (frontmatter only, no LICENSE file) | Thin client: send brief to Rendley's hosted agent | Rendley account/API key; files must be public https | **Skip** — editing happens on their servers, nothing to learn locally |
| 10 | Vossy/claude-video-editing-skill (Shorz) | 2026-10-04 | MIT | Skill for the **Shorz desktop app** MCP server | Shorz Electron app running locally | **Skip** — cannot run in a cloud container |
| 11 | notque/claude-code-toolkit → `skills/content/video-editing` | 2026-10-30 | MIT | 6-layer pipeline with **gates** per phase, EDL contract, ffmpeg filter references. (Path in request moved; old path is 404 in the tree) | ffmpeg, node | **Adopt**: phase gates, "EDL is the contract", concat list from EDL order not glob |
| 12 | affaan-m/everything-claude-code → `skills/video-editing` | 2026-10-29 | MIT | Capture→Claude→FFmpeg→Remotion→ElevenLabs/fal.ai→Descript pipeline; DaVinci Fusion assets | ElevenLabs, fal.ai (paid APIs); Descript/CapCut (GUI) | **Adopt ideas** (checkpoint before NLE changes; rendered ≠ approved). Do **not** run the repo-wide installer — it installs global git hooks |
| 13 | Sampet/claude-code-skills → `.agents/skills/video-editing` | 2026-03-22 | MIT | **Fork of #12** (diff vs #14 = one heading line) | same as #12 | **Duplicate** — skip |
| 14 | GRJY/Claude-Code-skill → `.agents/skills/video-editing` | 2026-06-20 | MIT | **Fork of #12** | same as #12 | **Duplicate** — skip |

## Discovered via the two awesome lists

`clonn/awesome-agent-video-skills` (MIT) and `zhuyansen/awesome-claude-video-skills` (CC0)
list ~250 projects. Roughly 60% are near-identical "Remotion motion graphics" skills.
Candidates were kept only if they add something the stack above lacks:

| Repository | License | Adds | Verdict |
|---|---|---|---|
| remotion-dev/skills (official) | none in repo | Authoritative Remotion API rules (captions, audio, fonts, transitions) | **Use via the official CLI**: `npx remotion skills add` — not vendored |
| JohnHeibel/ClaudeAnimationBase | MIT | **Cartoon character acting**: "reads" timing model, cause→reaction, every shot has an event, drawn key views instead of fake 3D | **Adopt ideas** for `cartoon-style` skill |
| digitalsamba/claude-code-video-toolkit | MIT | Full Remotion workspace: brands, transitions, commands | **Reference** — overlaps our Remotion project |
| heygen-com/hyperframes | Apache-2.0 | HTML/GSAP → deterministic video renderer | **Alternative** to Remotion; not needed while Remotion works |
| hetpatel-11/Adobe_Premiere_Pro_MCP, JUNKDOGE-JOE/after-effects-mcp | MIT | Drive local Premiere/AE | **Skip here** (needs desktop Adobe apps). Our OTIO/FCPXML export covers NLE hand-off |
| calesthio/OpenMontage, 0xsline/OpenChatCut | **AGPL-3.0** | Full agentic editors | **Skip** — copyleft would bind the whole project |
| SeeCut, vex, MotionTalk, JJKoubo … | **Non-commercial** licenses | — | **Skip** — incompatible with commercial YouTube use |

## Gaps none of the repositories filled — built here

1. **Local TTS** — every repo used ElevenLabs / edge-tts / cloud. We use **Piper** (MIT, offline, voice model from HuggingFace).
2. **Script-to-ASR forced alignment** — repos say "proofread"; we automate it: known script text + Whisper timestamps, every mismatch reported.
3. **Loudness *verification*** — repos run `loudnorm` once; we do two-pass loudnorm then **re-measure** the final file (integrated LUFS, true peak, LRA) and fail QA if off-target.
4. **Sidechain music ducking + procedural SFX/music** — license-clean audio generated locally.
5. **Automated QA report** — black frames, frozen frames, silence gaps, clipping, A/V duration drift, contact sheet.
6. **Editable project export** — OpenTimelineIO (`.otio`) and FCPXML via OTIO adapters, for Resolve / Premiere / FCP.
7. **A rigged cartoon character in code** — a reusable rounded-character rig with blink, lip-sync from narration amplitude, arm poses, squash/stretch, and a style bible enforcing purple shadows + gold rim light.

## License obligations

Only ideas and short rule paraphrases were taken; no source files were copied.
Attribution is in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).
**Remotion itself** is not MIT: it is free for individuals and companies of up to
3 people; larger companies need a Remotion company license (remotion.pro).
