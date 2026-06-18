# UI Patterns

Use these patterns after `$ui-ux-pro-max` selects the design system. Keep the page a real interface first; use sprites as the visual language.

## Layout patterns

- **Command center**: heading, short subtitle, primary CTA, secondary button, animated World 1-1 background panel, status HUD, and compact cards.
- **Dashboard**: score/coin/time HUD, icon cards for metrics, tabs for views, and a side panel with controls.
- **Landing section**: product heading, sprite-backed CTA buttons, scrolling scene band, feature cards, and a fixed pause/replay control.
- **Tool surface**: toolbar buttons with sprite badges, mode tabs, preview stage, and settings panel.

## Components

- **button**: use blocky borders, 3-4px shadow, visible active press state, and optional sprite badge.
- **tabs**: use segmented controls for Overview, Scene, Assets, or Settings. Keep tab height stable.
- **cards**: use only for repeated items, metrics, or controls. Do not place cards inside cards.
- **headings**: keep headings outside the moving background path. Use pixel type for short titles only.
- **icons**: prefer cropped sprite icons for coins, mushrooms, flowers, enemies, pipes, and blocks; use inline SVG only for generic UI controls such as play, pause, replay, or arrows.
- **HUD**: show state such as score, coins, mode, speed, and status in fixed-width counters to avoid layout shift.

## Sprite-to-UI mapping

| Sprite family | UI meaning |
| --- | --- |
| Coin | reward, credits, points, count |
| Mushroom | upgrade, growth, unlock |
| Flower | power, advanced mode, launch |
| Fireball | action, send, execute |
| Goomba | risk, blocker, issue |
| Koopa | challenge, opponent, queue |
| Pipe | route, integration, portal |
| Brick/block | module, step, section |

## Interaction requirements

Every generated page should include at least one real UI interaction:

- Pause/replay/speed controls for background animation.
- Tabs that switch visible panels.
- Clickable coins or blocks that update HUD counters.
- Scene selector that changes the animated background band.
- Camera control that scrubs the World 1-1 map.

Keyboard focus must be visible, and the tab order must match visual order.

## Motion boundaries

Background animation must never make the page unusable:

- Keep the UI layer above the scene layer.
- Reserve a quiet area for headings and copy.
- Do not animate text position for core content.
- Respect `prefers-reduced-motion` by showing a composed static scene.
