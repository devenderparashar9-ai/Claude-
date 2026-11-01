# Third-party notices

This project contains original code. Its skills paraphrase rules and methods
learned from the following MIT-licensed projects. No source files were copied.

| Project | Copyright | License | What informed us |
|---|---|---|---|
| vibegameengine/video-motion-craft | © 2026 vibegameengine (MIT); parts © Vincent Wei, video-shotcraft (Apache-2.0) | MIT / Apache-2.0 | Motion rules (no linear easing, multi-property entrances, staggering, faster exits, idle breathing, deterministic seeds), sound-design phrasing (riser→impact), review checklist |
| haidrrrry/claude-remotion-skill | © 2025 haidrrrry | MIT | Original form of the motion rules above |
| blazerior/videoediting-claude-skill | © 2026 claude-videoediting-skill contributors | MIT | Transcript-driven EDL cutting rules, pause handling, Whisper hallucination check, "look at the frames" verification |
| voidash/claudepipe | © 2026 voidash | MIT | Narration-drives-timeline principle; keep ASR timestamps, correct ASR text |
| notque/claude-code-toolkit | © notque | MIT | Phase gates; EDL as contract; concat order from EDL |
| affaan-m/everything-claude-code | © affaan-m | MIT | Checkpoint before NLE edits; rendered vs editable vs approved are separate states |
| imtamiliniyan/claude-video-skills | © 2026 Tamil Iniyan | MIT | Intake router pattern; transcript polish pass |
| JohnHeibel/ClaudeAnimationBase | © JohnHeibel | MIT | Cartoon acting: "reads", cause→reaction, one focal action, every shot has an event |

Runtime dependencies (installed, not vendored): Remotion (Remotion License),
React (MIT), FFmpeg (LGPL/GPL build from the OS), faster-whisper (MIT),
OpenAI Whisper weights (MIT), Piper TTS (MIT) with the `en_US-lessac-high`
voice (see its model card on HuggingFace `rhasspy/piper-voices`),
OpenTimelineIO (Apache-2.0).

The MIT License text required by each project above:

> Permission is hereby granted, free of charge, to any person obtaining a copy
> of this software and associated documentation files (the "Software"), to deal
> in the Software without restriction, including without limitation the rights
> to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
> copies of the Software, and to permit persons to whom the Software is
> furnished to do so, subject to the following conditions: The above copyright
> notice and this permission notice shall be included in all copies or
> substantial portions of the Software. THE SOFTWARE IS PROVIDED "AS IS",
> WITHOUT WARRANTY OF ANY KIND.
