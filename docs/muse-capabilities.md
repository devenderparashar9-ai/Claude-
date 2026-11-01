# Environment capabilities (tested, not assumed)

This environment is Claude Code running in an ephemeral cloud container (Linux, 4 vCPU,
15 GB RAM, no GPU). Every row below was tested on 2026-11-01.

| Capability | Status | How it's used / caveats |
|---|---|---|
| Read & use `SKILL.md` skills | **Yes** | Project skills in `.claude/skills/<name>/SKILL.md` are loaded by Claude Code when this repo is opened. They persist because they're committed to git |
| Access GitHub | **Yes** | Public repos clone over HTTPS through the proxy. GitHub API (MCP) is scoped to this repository |
| Execute shell commands | **Yes** | bash |
| Python | **Yes** | 3.13; project venv at `~/venv-video` (rebuilt by `scripts/setup.sh`) |
| Node.js | **Yes** | 22.x, npm registry reachable |
| FFmpeg / FFprobe | **Yes** | 6.1.1 with libx264/x265, libass, vid.stab, rubberband, loudnorm, ebur128, scdet, freezedetect, sidechaincompress, deesser, afftdn |
| Remotion | **Yes** | 4.0.539, renders with the preinstalled Chromium headless shell (`--browser-executable`). ~1 min per 1000 1080p frames for this project, 4× concurrency |
| Transcription | **Yes, local** | faster-whisper `small.en` int8 on CPU (model from HuggingFace, ~480 MB). Needs FFmpeg decoding (PyAV in this build is incompatible; handled in code) |
| TTS | **Yes, local** | Piper with `en_US-joe-medium` (CC0) / `en_US-libritts_r-medium` (CC BY 4.0). Quality is good but not studio-grade |
| MCP servers | **Yes** | Connected: GitHub, vidIQ (YouTube analytics plus generation tools: voice-over, music, B-roll, video; **uses vidIQ credits/account**), Adobe Marketing Agent (marketing analytics, not editing). Not used automatically |
| Cloud TTS / video generation (ElevenLabs, fal.ai, Runway, etc.) | **Not configured** | Need the user's API key + paid account. Add as environment secrets, never in the repo |
| Desktop NLE control (Premiere/Resolve/AE MCP, Shorz, CapCut) | **No** | Needs those apps on a local machine. We export `.otio`/`.fcpxml`/`.xml` for hand-off instead |
| Hearing audio | **No** | An agent can't listen. Substitutes: ASR re-transcription of the final mix, loudness/true-peak/speech-over-bed measurements. A human listen is still recommended for taste |
| Seeing frames | **Yes** | Stills and contact sheets are reviewed as images |
| Persist across sessions | **Partly** | Container is wiped after inactivity. **Persistent:** everything committed to git (skills, code, productions). **Not persistent:** venv, ~620 MB of voice/ASR models, `node_modules`. Rebuild with `bash scripts/setup.sh` (~3 min), or add it to the environment's setup script so it runs automatically |

## External dependencies by feature

| Feature | Needs | Cost |
|---|---|---|
| Everything in the default pipeline | Nothing external after setup (HuggingFace + npm/PyPI downloads at setup) | Free |
| Remotion in a company of 4+ people | Remotion company license | Paid |
| Premium voices | ElevenLabs/OpenAI key | Paid per character |
| AI-generated footage/B-roll | fal.ai/Runway/vidIQ account | Paid/credits |
| Editing in Resolve/Premiere/FCP | The app, on the user's machine; import our `.fcpxml`/`.xml`/`.otio` | Resolve free; others paid |
