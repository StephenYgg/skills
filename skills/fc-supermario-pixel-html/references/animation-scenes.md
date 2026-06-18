# Animation Scenes

Use CSS keyframes and small vanilla JavaScript timelines. Do not introduce a game engine for a static HTML UI.

Game motion is background choreography unless the user explicitly asks for a playable game. It should make the interface feel alive while preserving readable headings, usable buttons, and stable controls.

## UI layer rules

- Keep nav, headings, CTAs, tabs, and controls in a fixed or visually protected UI layer.
- Do not let enemies, projectiles, camera scrolling, particles, or coins cover primary text or buttons.
- Put rich motion in a hero band, background panel, footer rail, status strip, or decorative edge.
- Keep 1-2 animated focal points visible per view; avoid animating every component.
- Pause/replay/speed controls must affect the scene layer without disabling the main UI.

## Default World 1-1 Timeline

The bundled demo uses World 1-1 as an animated background scene. It should communicate these moments:

1. Mario enters and runs as the World 1-1 background scrolls.
2. A coin is collected and the HUD score changes.
3. A Goomba or Koopa is stomped.
4. A mushroom appears and Mario grows.
5. A flower appears and Mario enters fire form.
6. A fireball launches and hits an enemy.

This is choreography, not a full physics simulation.

## Interaction Choreography Rules

For hero bands, dashboard preview scenes, and UI background panels, drive related actions from a single timeline. Do not give Mario, coins, blocks, Goomba, and Koopa independent CSS animations that accidentally drift out of cause-and-effect order.

Required event rules:

- When Mario reaches a coin, the coin disappears. A coin may pop upward for a few frames, but it must not remain visible after collection.
- When Mario hits a question block from below, the question block bumps upward and a mushroom emerges from that block. The mushroom should rise from the block before moving away.
- Goomba starts in a walking state. After Mario stomps it, Goomba becomes squashed, then disappears after about 1 second.
- Koopa starts in a walking state. After Mario stomps it, Koopa becomes shell, then recovers back to normal Koopa after about 3 seconds unless the scene explicitly shows the shell being kicked away.
- After stomping Goomba or Koopa, Mario must perform a small stomp rebound rather than continuing flat along the ground.
- Mario jumps and stomp rebound motion must use gravity acceleration with a parabolic vertical path: `y = y0 + vy * t + 0.5 * g * t * t`. Do not use a linear `translateY()` tween for jumps.

Keep the scene physically readable: enemies stand on ground or platforms, items emerge from blocks, and characters are airborne only during jumps, rebounds, falls, or projectile-like states.

## Platform Physics Rules

Sprites must be grounded unless they are in a jump, fall, projectile, or flying state. Use sprite anchors as foot points:

```js
topLeftX = feetX - anchorX * scale
topLeftY = feetY - anchorY * scale
```

For World 1-1 overworld, use `GROUND_Y` from the map ground top (`y = 208`) multiplied by the display scale. Do not place enemies with arbitrary top-left coordinates.

Mario movement must use acceleration, not a simple linear tween:

```js
const physics = {
  walkMax: 24,
  runMax: 40,
  acceleration: 0.45,
  runAcceleration: 0.7
};
```

The `walkMax` value is about 60% of `runMax`, matching SMB1's walk/run speed relationship. Mario can pause, accelerate to walking speed, accelerate to running speed, and then continue at a cap.

Default enemy states:

- Goomba starts in walking frames and becomes squashed only after a stomp.
- Koopa starts in walking frames and becomes shell only after a stomp.
- Shell state may then be still or sliding; do not show shell as the default enemy.

World 1-1 display rules:

- Default scene is overworld only.
- The underground bonus room is a separate scene and must not be visible under the main route.
- Only switch to the underground bonus room after an explicit pipe-enter event.

## Scene Layers

Recommended DOM layers:

```text
stage
  map layer
  prop layer
  item layer
  enemy layer
  player layer
  effect layer
  hud layer
```

Animate position with `transform`, not `left` or `top`.

## Controls

Every generated demo should include:

- Pause/resume
- Replay
- Speed selector

Optional controls:

- Camera jump
- Scene selector
- Coin/block click targets

## Reduced Motion

When `prefers-reduced-motion: reduce` is true:

- Stop automatic camera scrolling.
- Keep the final composed scene visible.
- Allow replay only as a short state jump or very slow sequence.
- Disable shake, bounce, and particle effects.

In JavaScript:

```js
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
```

## Sprite Animation

Use frame arrays from `sprites.json`. Swap image `src` on a fixed interval or use CSS classes that point to cropped PNGs.

Rules:

- Use `steps()` for sheet animations.
- Keep sprite wrappers stable so frame size changes do not shift layout.
- Use anchors from the manifest for feet/ground alignment.

## Performance

Prefer:

- `transform`
- `opacity`
- class changes

Avoid animating:

- layout dimensions
- filters
- large box shadows

Keep moving objects few and meaningful. A rich pixel page should feel alive, not noisy.
