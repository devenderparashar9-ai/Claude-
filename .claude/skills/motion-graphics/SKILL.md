---
name: motion-graphics
description: Motion-design craft rules and Remotion patterns for titles, lower thirds, kinetic typography, transitions, explainer diagrams, charts, animated captions, intros/outros/end cards, parallax, camera moves, glow/particles/blur. Use before writing any Remotion/React/SVG animation code in animation/, or when a video "looks cheap / generic / AI-made".
---

# Motion graphics (Remotion)

Project: `animation/` (Remotion 4). Render with the preinstalled Chromium:
`npx remotion render src/index.ts <Comp> out.mp4 --browser-executable=$MUSEVID_CHROME`
(default path `/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`).
Official API rules: `npx remotion skills add` (Remotion's own skill, not vendored). Remotion license: free for individuals/≤3-person companies; larger companies need a company license.

## Craft rules (break one only deliberately, and note why)

1. **No linear easing.** Every `interpolate` gets an easing; entrances prefer `spring()`. Always clamp both sides. Helpers: `track()`, `ramp()`, `springAt()` in `src/lib/motion.ts`.
2. **Entrances animate 2–3 properties** (opacity + translate + scale/rotate). A lone fade is forbidden.
3. **Stagger** letters/words/items 0.5–6 frames. Nothing enters simultaneously.
4. **Exits exist and are faster** than entrances (~10 vs ~18 frames) — `inOut()`.
5. **Layered scenes**: background → assets → graphics/type → grade → grain/vignette. No flat fills.
6. **Idle things breathe**; camera has micro-drift; nothing frozen ≥ 2.5 s.
7. **Timing from fps and narration cues** — no magic frame numbers in components (`makeCue(P)('hit')`, `sec()`).
8. **One theme** (`src/theme.ts`): colours, easings, springs, font. No hex codes in components.
9. **Deterministic**: no `Math.random`/`Date.now`; use `rng(seed)`. Grain uses a frame-derived seed.
10. **Render → stills → LOOK → fix → re-render.** `node scripts/stills.mjs <Comp> /tmp/stills 30,120,...` then tile with ffmpeg and read the image.

## Building blocks in this repo

| Need | Component |
|---|---|
| Kinetic title (letter springs) | `KineticTitle` (`components/Overlays.tsx`) |
| Karaoke captions synced to words | `Captions` |
| Iris / circular reveal transition | `Iris` |
| Whip-cut | blur filter ramp ± 4 frames + flash + whoosh SFX (see `SolarPip.tsx`) |
| End card with staggered words | `EndCard` |
| Grade, vignette, grain | `Grade` |
| Lit cartoon shapes | `Lit`, `Limb`, `rrect`, `ellipse` |
| Particles along curves (photons) | `Photons` (screen-space bezier between parallax layers via `worldToScreen`) |
| Impact burst | `Burst` |
| Diagram insert with labels & flows | `SiliconInsert` (dash-offset flow along paths) |
| Morphing chart/graph | `InverterCard` (flat line → sine via eased amplitude) |
| Camera + parallax | `world/camera.ts` (`layerTransform`, `worldToScreen`) |

Fonts are vendored (`public/fonts`, OFL) and loaded in `src/fonts.ts` — renders work offline.

## Easing choices

- UI/props appearing: `SPRING.pop` (slight overshoot). Gestures: `SPRING.snappy`. Big body moves: `SPRING.soft`. Cartoon wobble: `SPRING.wobbly`.
- Camera: `EASE.camera` (slow start, long settle). Exits: `EASE.in`. Reveals: `EASE.out`.

## Charts/numbers

Animate counters with `interpolate` + `EASE.out`, format with `Intl.NumberFormat`; bars grow with stagger; always label units; only show figures you have verified.
