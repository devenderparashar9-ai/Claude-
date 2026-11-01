---
name: cartoon-style
description: House style bible and character-acting rules for the rounded-cartoon explainer channel (Pip). Use when writing a script/storyboard for an animated video, designing or posing characters, building environments, planning camera moves, or reviewing frames for on-model consistency, purple shadows / golden rim lighting, and narration sync.
---

# Cartoon style bible + acting

The look is enforced in code — `animation/src/theme.ts` (palette, springs, easings) and
`animation/src/components/Lit.tsx` (lighting). Don't inline colours; don't bypass `Lit`.

## Look (non-negotiable)

- **Rounded characters**, big heads (~40% of height), mitten hands, constant ink outline (`OUTLINE`, colour `ink` #2a1840 — never pure black; whites are `cream`).
- **Lighting**: key light from the sun, upper-left. Every shape gets a **purple shadow crescent** lower-right (`shade()` mixes toward `#5a3d9a`) and a **warm golden rim** upper-left (`rimOf()`). Use `<Lit d=... fill=...>` for shapes and `<Limb>` for arms/legs.
- **Environment**: layered parallax (sky p=0, sun/far hills p=0.3, mid hills 0.6, action plane 1, foreground >1 blurred). Cohesive palette; cartoon diorama scale is fine.
- **Grade**: `<Grade>` on top — warm soft-light wash, purple vignette, seeded grain. Time-of-day can shift (`dusk`) to support the story (lights reading at night).

## On-model consistency

- Pip's proportions, palette and outline are constants in `characters/Pip.tsx`. Only pose/expression params change. Never redraw him per shot.
- New character → new component with its own model sheet; render `ModelSheet`-style still and **look at it** before animating.
- Review every shot's stills for: face shape, eye spacing, outline weight, hoodie colour, rim on the light side, purple shadow on the far side, contact shadow under feet.

## Acting rules (from cartoon-animation practice)

1. **Every shot has an event** — something changes between first and last frame.
2. **One read at a time.** Don't start a new read while the viewer is still taking in the last. Cause → reaction in sequence, not on top of each other.
3. **Fast actions, slow meanings**: anticipate (squash, look toward it), act fast, then hold so it registers.
4. **Lead the eye**: character looks/points at the thing before it appears; camera moves to it.
5. **Follow-through**: hair curl lags, arms overshoot (`SPRING.snappy`), landing squash after a hop.
6. **Always alive**: blink (`blinkAt`), breathe (`breathe`), micro camera drift — nothing freezes ≥ 2.5 s (QA checks this).
7. **Lip-sync only when the character is the speaker on screen**; otherwise mouth closed with expression — reads as voice-over.
8. Real object interactions (pointing at the sun, the city lighting up, a bulb popping over the head) — not static images with a zoom.

## Storyboard → beats

Write the script first, then `beats.json`: a named cue per action, anchored to a **word** (`{"line": "l3", "word": "hit", "offset": 0}`; negative offset = anticipation). Every camera move, pose change, graphic reveal and SFX references a cue. Plan camera per line:

| Purpose | Move | Easing |
|---|---|---|
| Introduce | slow push-in on the speaker | `EASE.camera` |
| Reveal a concept | pan/tilt to it, motivated by a look/point | `EASE.camera` |
| Detail | fast push to close-up, then **iris** into an insert diagram | push `EASE.camera`, iris `EASE.inOut` |
| Journey | tracking move along the path (wire, road) | `EASE.camera` |
| Payoff | whip-cut (motion blur + flash + whoosh) to character close-up | — |

## Review checklist per still

on-model? · lit correctly? · one clear read? · caption not covering face? · action matches the word being spoken (see `qa/cue_frames/`)? · nothing cropped awkwardly (no half-faces at frame edge unless intentional)?
