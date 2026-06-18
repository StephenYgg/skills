# Style Guide

Use this guide for static FC/NES-style interactive UI pages built from local sprites.

## Visual Direction

Target a usable UI with pixel-art personality. The game material should support the interface as background animation, icons, button details, HUD feedback, section art, or interactive accents. Do not make a plain game screenshot unless the user explicitly asks for a scene-only demo.

Use:

- Crisp local sprites
- Low-color, high-contrast palettes
- Compact HUD or dashboard metrics
- Visible UI layer above foreground/background layers
- Buttons, headings, tabs, panels, and icons that reuse sprite vocabulary
- Short, readable English UI labels

Avoid:

- Glassmorphism, oversized cards, and generic gradients
- Blurry scaled images
- Long explanation text inside moving scene areas
- Placing controls where sprites or camera motion can cover them
- External image hotlinks

## UI composition

Use a clear two-layer model:

```text
page
  animated scene/background layer
  UI layer: nav, heading, controls, cards, tabs, status, CTA
```

The UI layer is the product. The scene layer adds motion, context, and nostalgia. Keep primary text and controls outside the character path unless they are fixed HUD elements.

Recommended first viewport:

- A direct heading or product title.
- One primary action and one secondary action.
- A visible animated background panel or band using World 1-1, enemies, coins, blocks, or pipes.
- A small control cluster for pause/replay/speed or scene selection.
- 2-4 compact cards or status chips that use sprite icons.

## Palette

Recommended defaults:

```css
:root {
  --sky: #5c94fc;
  --underground: #1b5a99;
  --ground: #c84c0c;
  --ground-dark: #7c2f00;
  --brick: #b83f1d;
  --coin: #f8d030;
  --coin-dark: #b87800;
  --pipe: #00a844;
  --pipe-dark: #006c2c;
  --ink: #111111;
  --paper: #fff6d6;
  --white: #ffffff;
}
```

Keep each scene to a small number of dominant colors. Foreground sprites must remain more legible than decorative effects.

## Typography

Prefer pixel fonts for HUD and short labels:

```css
font-family: "Press Start 2P", "Silkscreen", "Pixelify Sans", ui-monospace, monospace;
```

If network fonts are not allowed, use the system monospace fallback. Keep body copy readable; do not use tiny pixel text for long paragraphs.

## Pixel Assets

Every raster sprite needs crisp scaling:

```css
.pixel {
  image-rendering: pixelated;
  image-rendering: crisp-edges;
}
```

Use integer scale factors where possible:

- Mobile: 2x
- Tablet: 3x
- Desktop: 4x

Do not mix high-resolution illustration with pixel sprites in the same scene.

## Components

Buttons should feel like game controls:

```css
.pixel-button {
  border: 3px solid var(--ink);
  background: var(--coin);
  color: var(--ink);
  box-shadow: 0 4px 0 var(--coin-dark);
  cursor: pointer;
}
```

Use:

- Buttons for commands.
- Tabs or segmented controls for modes.
- Cards only for repeated content or control panels.
- HUD bars for status, score, progress, or counters.
- Sprite icons for chips, labels, feature cards, and empty states.

Do not nest cards inside cards. Do not rely on text-only rectangular pills when a sprite icon can communicate the state.

## Layout

Use a stable stage:

```css
.stage {
  position: relative;
  width: min(100%, 1200px);
  aspect-ratio: 16 / 9;
  overflow: hidden;
}
```

Rules:

- Default World 1-1 views must use the overworld crop, not the full source sheet with the underground bonus room visible.
- The underground bonus room is separate content; show it only after a pipe transition.
- HUD height must not shift when score changes.
- Use absolute positioning for sprites and layers.
- Prevent horizontal page scroll on mobile.
- Keep text outside the moving action path unless it is part of the HUD.

Use hover/focus color changes and active press states. Do not use large scale transforms that shift layout.

## Sprite icons

Use sprites as UI icons when the meaning is clear:

- Coin: reward, count, collect, credits.
- Mushroom: upgrade, growth, unlock.
- Flower: power, launch, advanced mode.
- Goomba/Koopa: obstacle, enemy, risk, challenge.
- Pipe: route, portal, integration, transition.
- Block/brick: module, step, section divider.

Give decorative sprite icons empty `alt`; give meaningful icon images concise `alt` text.

## Accessibility

Always include:

- `alt` text for meaningful images
- Visible keyboard focus
- Buttons with text labels
- Reduced motion support

```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    scroll-behavior: auto !important;
  }
}
```

## Delivery Check

- Sprites are not blurred.
- Local paths work from the generated HTML.
- No external image dependency.
- The scene is usable at 375px, 768px, 1024px, and 1440px widths.
- Animations do not cover controls or important text.
- Interactive elements have visible hover and keyboard focus states.
