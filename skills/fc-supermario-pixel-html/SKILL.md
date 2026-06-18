---
name: fc-supermario-pixel-html
description: Use when creating interactive UI, retro pixel web interfaces, FC/NES-style dashboards, landing sections, controls, buttons, headings, icons, HUDs, or background animation layers with bundled Super Mario-like sprites and ui-ux-pro-max guidance.
---

# fc-supermario-pixel-html

Create static `HTML/CSS/JS` interactive UI experiences from the bundled local sprites. The primary output is a usable UI: dashboards, landing sections, panels, controls, buttons, headings, icons, HUDs, and animated background scenes. World 1-1 and character choreography are reusable visual material, not the only target.

## Required Workflow Dependency

Use `$ui-ux-pro-max` before designing or building the page. Treat it as a design-decision dependency, not a runtime dependency.

Run a design-system search for the user request, then map the result to this skill:

```bash
python skills/ui-ux-pro-max/scripts/search.py "retro pixel interactive UI dashboard background animation buttons icons" --design-system -p "FC Pixel UI"
python skills/ui-ux-pro-max/scripts/search.py "animation accessibility controls keyboard reduced motion" --domain ux
python skills/ui-ux-pro-max/scripts/search.py "static html interactive UI responsive controls" --stack html-tailwind
```

The final page must open as static HTML without `$ui-ux-pro-max`.

## Workflow

1. Read `references/style-guide.md` before writing visual code.
2. Read `references/ui-patterns.md` before composing panels, navigation, cards, buttons, headings, or icons.
3. Read `references/animation-scenes.md` before adding background animation, sprite choreography, or game-rule motion.
4. Use bundled assets from `assets/source/` and generated sprites from `assets/sprites/`.
5. Run `python scripts/extract_sprites.py --check`; fix manifest problems before building.
6. Run `python scripts/extract_sprites.py` to crop sprites when needed.
7. Run `python scripts/build_demo.py` to generate `dist/index.html` for a working sample.

Do not fetch external Mario/Nintendo assets. The bundled source sheets are the asset authority for this skill.

## Output Rules

- Default to one static `index.html` with HTML, CSS, and vanilla JavaScript.
- Lead with a functional UI surface; use the game scene as a background, hero, status, icon, or interaction layer.
- Use local raster sprites, inline SVG, CSS keyframes, and small JS timelines.
- Keep pixel edges crisp with `image-rendering: pixelated`.
- Use integer scaling for sprites.
- Convert sprites into UI material: icon chips, button badges, empty-state art, section dividers, animated backgrounds, progress/HUD indicators, and status feedback.
- Include at least one real interaction: pause, replay, speed, scene switch, camera control, coin click, or block hit.
- Support `prefers-reduced-motion`.
- Avoid fake loading, placeholder skeletons, generic gradients, glass cards, and complex game engines.

## Sprite Manifest

`assets/sprites/sprites.json` is the single source of truth for sprite crops.

Each sprite must include:

```json
{
  "id": "mario.small.idle.0",
  "category": "character",
  "source": "playable",
  "bbox": [2, 8, 12, 16],
  "output": "characters/mario-small-idle-0.png",
  "tags": ["mario", "small", "idle"],
  "anchor": [6, 16]
}
```

Use short, stable, lowercase IDs. Do not encode sheet coordinates in names. Exclude sheet labels, palette notes, tilemap previews, signatures, and explanatory text from new sprite entries.

## Parallel Work

Use at most five parallel subagents, only for independent work: manifest/cropping, documentation, demo construction, verification, and review. Merge through `sprites.json` and scripts; do not create a scheduler or framework.

## Verification

Before delivery:

- `python scripts/extract_sprites.py --check`
- `python scripts/extract_sprites.py`
- `python scripts/build_demo.py`
- Open `dist/index.html` and verify the page reads as an interactive UI, not only a game screenshot.
- Verify headings, buttons, icons, cards/panels, focus states, and at least one background animation are present.
- Verify World 1-1 scroll, Mario state changes, coin, stomp, mushroom, flower, fireball, pause, replay, speed, and reduced-motion behavior when the scene layer is used.
