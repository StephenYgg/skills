#!/usr/bin/env python
import json
import shutil
from pathlib import Path


def skill_dir_from_script():
    return Path(__file__).resolve().parents[1]


def load_manifest(skill_dir):
    path = Path(skill_dir) / "assets" / "sprites" / "sprites.json"
    return json.loads(path.read_text(encoding="utf-8"))


def find_sprite(manifest, sprite_id):
    for sprite in manifest["sprites"]:
        if sprite["id"] == sprite_id:
            return sprite
    raise KeyError(f"missing sprite: {sprite_id}")


def copy_demo_assets(skill_dir, out_dir, manifest):
    assets_dir = Path(out_dir) / "assets"
    if assets_dir.exists():
        shutil.rmtree(assets_dir)
    assets_dir.mkdir(parents=True, exist_ok=True)

    for sprite in manifest["sprites"]:
        source = Path(skill_dir) / "assets" / "sprites" / sprite["output"]
        if not source.is_file():
            raise FileNotFoundError(f"missing cropped sprite: {source}")
        target = assets_dir / "sprites" / sprite["output"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def demo_sprite_data(manifest):
    ids = [
        "level.world-1-1.overworld",
        "mario.small.idle.0",
        "mario.small.walk.0",
        "mario.small.walk.1",
        "mario.small.walk.2",
        "mario.small.jump.0",
        "mario.big.idle.0",
        "mario.big.walk.0",
        "mario.big.walk.1",
        "mario.big.walk.2",
        "mario.big.jump.0",
        "mario.fire.walk.0",
        "mario.fire.walk.1",
        "mario.fire.walk.2",
        "enemy.goomba.ground.walk.0",
        "enemy.goomba.ground.walk.1",
        "enemy.goomba.ground.squash.0",
        "enemy.koopa.green.walk.0",
        "enemy.koopa.green.walk.1",
        "enemy.koopa.green.shell.0",
        "item.coin.spin.0",
        "item.coin.spin.1",
        "item.question.block.0",
        "item.pipe.top.0",
        "item.fireball.small.0",
        "effect.stomp.flash.0",
    ]
    data = {}
    for sprite_id in ids:
        sprite = find_sprite(manifest, sprite_id)
        data[sprite_id] = {
            "src": f"assets/sprites/{sprite['output']}",
            "w": sprite["bbox"][2],
            "h": sprite["bbox"][3],
            "anchor": sprite.get("anchor", [0, 0]),
        }
    return data


def build_html(manifest):
    sprites_json = json.dumps(demo_sprite_data(manifest), separators=(",", ":"))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pixel UI Command Center</title>
  <style>
    :root {{
      --sky: #5c94fc;
      --paper: #fff6d6;
      --coin: #f8d030;
      --coin-dark: #b87800;
      --ink: #111111;
      --scale: 3;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      overflow-x: hidden;
      background: #111827;
      color: var(--paper);
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    }}
    main {{
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 20px;
    }}
    .shell {{ width: min(100%, 1120px); }}
    .hero-grid {{
      display: grid;
      grid-template-columns: minmax(0, .9fr) minmax(0, 1.35fr);
      gap: 18px;
      align-items: stretch;
    }}
    .intro, .info-panel {{
      border: 4px solid #0f172a;
      outline: 2px solid #f8fafc;
      background: #fff6d6;
      color: #111;
      padding: 16px;
      box-shadow: 0 6px 0 #7c2f00;
    }}
    .eyebrow {{
      margin: 0 0 10px;
      color: #7c2f00;
      font-size: 12px;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(24px, 4vw, 44px);
      line-height: 1.05;
      letter-spacing: 0;
    }}
    .lead {{
      margin: 12px 0 0;
      color: #1f2937;
      font-size: 14px;
      line-height: 1.55;
    }}
    .badge-row {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
      margin-top: 14px;
    }}
    .sprite-chip {{
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 44px;
      border: 3px solid #111;
      background: #5c94fc;
      color: #fff;
      padding: 8px;
      font-size: 12px;
      text-transform: uppercase;
    }}
    .sprite-chip img {{
      width: 24px;
      height: 24px;
      object-fit: contain;
      image-rendering: pixelated;
      flex: 0 0 auto;
    }}
    .tabs {{
      display: flex;
      gap: 8px;
      margin-top: 14px;
    }}
    .tab-button {{
      border: 3px solid #111;
      background: #fff;
      color: #111;
      min-height: 38px;
      padding: 8px 10px;
      font: inherit;
      font-size: 12px;
      cursor: pointer;
    }}
    .tab-button[aria-selected="true"] {{
      background: var(--coin);
      box-shadow: 0 4px 0 var(--coin-dark);
    }}
    .view-panel {{
      margin-top: 12px;
      color: #1f2937;
      font-size: 13px;
      line-height: 1.5;
    }}
    .view-panel[hidden] {{ display: none; }}
    .scene-panel {{
      position: relative;
      min-width: 0;
    }}
    .hud {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 10px;
      color: #fff;
      font-size: 12px;
      line-height: 1.4;
      text-transform: uppercase;
    }}
    .hud span {{
      display: block;
      color: var(--coin);
    }}
    .stage {{
      position: relative;
      width: 100%;
      aspect-ratio: 16 / 9;
      overflow: hidden;
      border: 4px solid #0f172a;
      outline: 2px solid #f8fafc;
      background: var(--sky);
      image-rendering: pixelated;
    }}
    .pixel {{
      position: absolute;
      image-rendering: pixelated;
      image-rendering: crisp-edges;
      user-select: none;
      pointer-events: none;
    }}
    .map {{
      width: auto;
      height: 100%;
      max-width: none;
      left: 0;
      top: 0;
      transform: translateX(calc(var(--camera) * -1px));
    }}
    .sprite {{
      width: calc(var(--w) * var(--scale) * 1px);
      height: calc(var(--h) * var(--scale) * 1px);
      transform: translate(calc(var(--x) * 1px), calc(var(--y) * 1px));
      transition: opacity 140ms ease-out;
    }}
    .sprite img {{
      width: 100%;
      height: 100%;
      display: block;
      image-rendering: pixelated;
    }}
    .hero {{ z-index: 5; filter: drop-shadow(0 3px 0 rgba(0,0,0,.35)); }}
    .coin {{
      z-index: 4;
      pointer-events: auto;
      cursor: pointer;
      animation: coin-bob 700ms steps(2) infinite;
    }}
    .enemy, .effect, .fireball, .powerup {{ z-index: 4; }}
    .fireball {{ z-index: 6; filter: drop-shadow(0 0 6px #f97316); }}
    .collected {{
      opacity: 0;
      transform: translate(calc(var(--x) * 1px), calc((var(--y) - 34) * 1px));
    }}
    .powerup {{
      width: calc(16 * var(--scale) * 1px);
      height: calc(16 * var(--scale) * 1px);
      transform: translate(calc(var(--x) * 1px), calc(var(--y) * 1px));
    }}
    .powerup::before {{
      content: "";
      display: block;
      width: 16px;
      height: 16px;
      transform: scale(var(--scale));
      transform-origin: top left;
      background: var(--pixels);
    }}
    .mushroom {{
      --pixels:
        linear-gradient(#000 0 0) 4px 2px/8px 2px no-repeat,
        linear-gradient(#e23d28 0 0) 2px 4px/12px 6px no-repeat,
        linear-gradient(#fff 0 0) 4px 5px/3px 3px no-repeat,
        linear-gradient(#fff 0 0) 9px 5px/3px 3px no-repeat,
        linear-gradient(#f6c27a 0 0) 4px 10px/8px 5px no-repeat,
        linear-gradient(#000 0 0) 3px 12px/2px 2px no-repeat,
        linear-gradient(#000 0 0) 11px 12px/2px 2px no-repeat;
    }}
    .flower {{
      --pixels:
        linear-gradient(#e23d28 0 0) 5px 1px/6px 6px no-repeat,
        linear-gradient(#fff 0 0) 6px 2px/4px 4px no-repeat,
        linear-gradient(#f8d030 0 0) 7px 3px/2px 2px no-repeat,
        linear-gradient(#00a844 0 0) 7px 7px/2px 8px no-repeat,
        linear-gradient(#00a844 0 0) 4px 10px/4px 3px no-repeat,
        linear-gradient(#00a844 0 0) 8px 11px/4px 3px no-repeat;
    }}
    @keyframes coin-bob {{
      0%, 100% {{ margin-top: 0; }}
      50% {{ margin-top: -6px; }}
    }}
    .controls {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      margin-top: 14px;
    }}
    .pixel-button {{
      border: 3px solid var(--ink);
      background: var(--coin);
      color: var(--ink);
      box-shadow: 0 4px 0 var(--coin-dark);
      padding: 9px 12px;
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }}
    .pixel-button:focus-visible,
    .tab-button:focus-visible,
    .speed:focus-visible {{
      outline: 3px solid #f8fafc;
      outline-offset: 3px;
    }}
    .pixel-button:active {{
      transform: translateY(3px);
      box-shadow: 0 1px 0 var(--coin-dark);
    }}
    .speed {{ accent-color: var(--coin); cursor: pointer; }}
    .status {{ min-height: 24px; color: #bfdbfe; font-size: 13px; }}
    @media (max-width: 640px) {{
      main {{ padding: 12px; }}
      .hero-grid {{ grid-template-columns: 1fr; }}
      .badge-row {{ grid-template-columns: 1fr; }}
      .hud {{ grid-template-columns: repeat(2, 1fr); font-size: 11px; }}
      .pixel-button {{ flex: 1 1 auto; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *,
      *::before,
      *::after {{
        animation-duration: 0.001ms !important;
        animation-iteration-count: 1 !important;
        scroll-behavior: auto !important;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="shell" aria-label="Pixel UI Command Center with World 1-1 background animation">
      <div class="hero-grid">
        <div class="intro">
          <p class="eyebrow">FC pixel interface kit</p>
          <h1>Pixel UI Command Center</h1>
          <p class="lead">A static HTML interface that uses local sprites for headings, buttons, icons, HUD counters, cards, and background animation.</p>
          <div class="badge-row" aria-label="Sprite icon examples">
            <div class="sprite-chip"><img data-icon="coin" alt="Coin icon">Rewards</div>
            <div class="sprite-chip"><img data-icon="block" alt="Question block icon">Upgrade</div>
            <div class="sprite-chip"><img data-icon="fireball" alt="Fireball icon">Power Mode</div>
            <div class="sprite-chip"><img data-icon="pipe" alt="Pipe icon">Route</div>
          </div>
          <div class="tabs" role="tablist" aria-label="UI views">
            <button class="tab-button" data-tab="overview" role="tab" aria-selected="true" aria-controls="overview-panel" type="button">Overview</button>
            <button class="tab-button" data-tab="scene" role="tab" aria-selected="false" aria-controls="scene-panel" type="button">Scene</button>
          </div>
          <div class="view-panel" data-view="overview" id="overview-panel" role="tabpanel">
            Sprite assets become UI tokens: coin counters, power-up badges, route icons, action buttons, and fixed HUD feedback.
          </div>
          <div class="view-panel" data-view="scene" id="scene-panel" role="tabpanel" hidden>
            The World 1-1 band is background choreography. It stays behind the UI layer and follows grounded movement rules.
          </div>
          <div class="controls">
            <button class="pixel-button" data-action="pause" type="button">Pause</button>
            <button class="pixel-button" data-action="replay" type="button">Replay</button>
            <label>Speed <input class="speed" data-action="speed" type="range" min="0.5" max="2" value="1" step="0.25"></label>
          </div>
          <p class="status" data-message>Auto-play background animation: grounded run, coin, stomp, mushroom, flower, fireball.</p>
        </div>
        <div class="scene-panel" aria-label="World 1-1 animated background module">
          <div class="hud" aria-live="polite">
            <div>Mario<span data-score>000000</span></div>
            <div>Coins<span data-coins>00</span></div>
            <div>World<span>1-1</span></div>
            <div>Status<span data-status>Ready</span></div>
          </div>
          <div class="stage" data-stage style="--camera:0">
            <img class="pixel map" data-map alt="World 1-1 overworld scrolling map">
            <div class="sprite hero" data-hero><img alt="Mario"></div>
            <button class="sprite coin" data-coin="0" aria-label="Collect coin"><img alt=""></button>
            <div class="sprite enemy" data-goomba><img alt="Goomba walking"></div>
            <div class="sprite enemy" data-koopa><img alt="Koopa walking"></div>
            <div class="pixel powerup mushroom" data-mushroom hidden role="img" aria-label="Power mushroom"></div>
            <div class="pixel powerup flower" data-flower hidden role="img" aria-label="Fire flower"></div>
            <div class="sprite fireball" data-fireball hidden><img alt="Fireball"></div>
            <div class="sprite effect" data-effect hidden><img alt="Stomp effect"></div>
          </div>
        </div>
      </div>
    </section>
  </main>
  <script>
    const SPRITES = {sprites_json};
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const WORLD = {{ width: 3376, height: 240, groundY: 208, walkMax: 24, runMax: 40 }};
    const GROUND_Y = 208 * 3;
    const PHYSICS = {{ walkMax: 24, runMax: 40, acceleration: 0.45, runAcceleration: 0.7 }};

    const stage = document.querySelector("[data-stage]");
    const map = document.querySelector("[data-map]");
    const hero = document.querySelector("[data-hero]");
    const score = document.querySelector("[data-score]");
    const coins = document.querySelector("[data-coins]");
    const statusText = document.querySelector("[data-status]");
    const message = document.querySelector("[data-message]");
    const goomba = document.querySelector("[data-goomba]");
    const koopa = document.querySelector("[data-koopa]");
    const mushroom = document.querySelector("[data-mushroom]");
    const flower = document.querySelector("[data-flower]");
    const fireball = document.querySelector("[data-fireball]");
    const effect = document.querySelector("[data-effect]");
    const coin = document.querySelector("[data-coin]");
    const speed = document.querySelector("[data-action='speed']");
    const pause = document.querySelector("[data-action='pause']");
    const tabs = Array.from(document.querySelectorAll("[data-tab]"));
    const panels = Array.from(document.querySelectorAll("[data-view]"));

    const show = (node, visible) => {{ node.hidden = !visible; }};
    const sprite = (id) => SPRITES[id];
    const setSprite = (node, id) => {{
      const frame = sprite(id);
      node.dataset.sprite = id;
      node.style.setProperty("--w", frame.w);
      node.style.setProperty("--h", frame.h);
      const img = node.querySelector("img");
      if (img) img.src = frame.src;
    }};
    const setTopLeft = (node, x, y) => {{
      node.style.setProperty("--x", Math.round(x));
      node.style.setProperty("--y", Math.round(y));
    }};
    const placeByFeet = (node, id, feetX, feetY) => {{
      const frame = sprite(id);
      setSprite(node, id);
      setTopLeft(node, feetX - frame.anchor[0] * 3, feetY - frame.anchor[1] * 3);
    }};
    const placePowerup = (node, feetX, feetY) => {{
      setTopLeft(node, feetX - 8 * 3, feetY - 16 * 3);
    }};

    map.src = SPRITES["level.world-1-1.overworld"].src;
    document.querySelector("[data-icon='coin']").src = SPRITES["item.coin.spin.0"].src;
    document.querySelector("[data-icon='block']").src = SPRITES["item.question.block.0"].src;
    document.querySelector("[data-icon='fireball']").src = SPRITES["item.fireball.small.0"].src;
    document.querySelector("[data-icon='pipe']").src = SPRITES["item.pipe.top.0"].src;

    tabs.forEach(tab => {{
      tab.addEventListener("click", () => {{
        const view = tab.dataset.tab;
        tabs.forEach(item => item.setAttribute("aria-selected", String(item === tab)));
        panels.forEach(panel => {{ panel.hidden = panel.dataset.view !== view; }});
      }});
    }});

    let state;
    function reset() {{
      state = {{
        start: performance.now(),
        paused: false,
        pauseAt: 0,
        speed: Number(speed.value),
        score: 0,
        coins: 0,
        form: "small",
        velocity: 0,
        camera: 0
      }};
      score.textContent = "000000";
      coins.textContent = "00";
      statusText.textContent = reduceMotion ? "Reduced" : "Ready";
      message.textContent = reduceMotion
        ? "Reduced motion: showing the overworld scene without auto-scroll."
        : "Auto-play: grounded acceleration, coin, stomp, mushroom, flower, fireball.";
      [mushroom, flower, fireball, effect].forEach(node => show(node, false));
      [coin, goomba, koopa].forEach(node => {{
        node.classList.remove("collected");
        show(node, true);
      }});
      placeByFeet(hero, "mario.small.idle.0", 130, GROUND_Y);
      placeByFeet(goomba, "enemy.goomba.ground.walk.0", 620, GROUND_Y);
      placeByFeet(koopa, "enemy.koopa.green.walk.0", 820, GROUND_Y);
      placeByFeet(coin, "item.coin.spin.0", 405, GROUND_Y - 132);
      placePowerup(mushroom, 700, GROUND_Y);
      placePowerup(flower, 890, GROUND_Y);
      placeByFeet(fireball, "item.fireball.small.0", 940, GROUND_Y - 56);
      placeByFeet(effect, "effect.stomp.flash.0", 620, GROUND_Y);
      stage.style.setProperty("--camera", 0);
    }}
    reset();

    function collectCoin() {{
      if (coin.classList.contains("collected")) return;
      coin.classList.add("collected");
      state.score += 100;
      state.coins += 1;
      score.textContent = String(state.score).padStart(6, "0");
      coins.textContent = String(state.coins).padStart(2, "0");
      statusText.textContent = "Coin";
    }}
    coin.addEventListener("click", collectCoin);

    function targetSpeed(t) {{
      if (t < 800) return 0;
      if (t < 2600) return PHYSICS.walkMax;
      if (t < 3400) return 0;
      if (t < 5200) return PHYSICS.runMax;
      return PHYSICS.walkMax;
    }}
    function integrateVelocity(target, dt) {{
      const accel = target > PHYSICS.walkMax ? PHYSICS.runAcceleration : PHYSICS.acceleration;
      const delta = accel * dt / 16.67;
      if (state.velocity < target) state.velocity = Math.min(target, state.velocity + delta);
      if (state.velocity > target) state.velocity = Math.max(target, state.velocity - delta * 1.35);
      return state.velocity;
    }}
    function marioFrame(t, speedPx) {{
      if (speedPx < 1) return state.form === "big" ? "mario.big.idle.0" : "mario.small.idle.0";
      const frameRate = speedPx > PHYSICS.walkMax ? 95 : 150;
      const frame = Math.floor(t / frameRate) % 3;
      if (state.form === "fire") return `mario.fire.walk.${{frame}}`;
      if (state.form === "big") return `mario.big.walk.${{frame}}`;
      return `mario.small.walk.${{frame}}`;
    }}
    function timeline(ms) {{
      const t = reduceMotion ? 0 : ms * state.speed;
      const dt = 16.67 * state.speed;
      const speedPx = integrateVelocity(targetSpeed(t), dt);
      state.camera = Math.min(1900, state.camera + speedPx * 0.42);
      stage.style.setProperty("--camera", state.camera);

      let feetX = 130 + state.camera + 40;
      let feetY = GROUND_Y;
      let frame = marioFrame(t, speedPx);
      if (t > 1650 && t < 2350) {{
        const jump = Math.sin((t - 1650) / 700 * Math.PI) * 96;
        feetY = GROUND_Y - jump;
        frame = state.form === "big" ? "mario.big.jump.0" : "mario.small.jump.0";
      }}
      placeByFeet(hero, frame, feetX - state.camera, feetY);

      placeByFeet(goomba, t > 2550 ? "enemy.goomba.ground.squash.0" : `enemy.goomba.ground.walk.${{Math.floor(t / 260) % 2}}`, 620 - state.camera, GROUND_Y);
      placeByFeet(koopa, t > 6900 ? "enemy.koopa.green.shell.0" : `enemy.koopa.green.walk.${{Math.floor(t / 300) % 2}}`, 820 - state.camera, GROUND_Y);
      placeByFeet(coin, `item.coin.spin.${{Math.floor(t / 300) % 2}}`, 405 - state.camera, GROUND_Y - 132);
      placePowerup(mushroom, 700 - state.camera, GROUND_Y);
      placePowerup(flower, 890 - state.camera, GROUND_Y);

      if (t > 1250) collectCoin();
      if (t > 2550) {{
        show(effect, true);
        placeByFeet(effect, "effect.stomp.flash.0", 620 - state.camera, GROUND_Y);
        statusText.textContent = "Stomp";
      }}
      if (t > 3700) {{
        show(mushroom, true);
        state.form = "big";
        statusText.textContent = "Power";
      }}
      if (t > 5200) {{
        show(flower, true);
        state.form = "fire";
        statusText.textContent = "Fire";
      }}
      if (t > 6000) {{
        show(fireball, true);
        placeByFeet(fireball, "item.fireball.small.0", 940 + (t - 6000) * 0.18 - state.camera, GROUND_Y - 56);
        statusText.textContent = "Fireball";
      }}
      if (t > 6900) statusText.textContent = "Clear";
    }}
    function loop(now) {{
      if (!state.paused) timeline(now - state.start);
      requestAnimationFrame(loop);
    }}
    requestAnimationFrame(loop);

    pause.addEventListener("click", () => {{
      state.paused = !state.paused;
      if (state.paused) {{
        state.pauseAt = performance.now();
        pause.textContent = "Resume";
        statusText.textContent = "Paused";
      }} else {{
        state.start += performance.now() - state.pauseAt;
        pause.textContent = "Pause";
      }}
    }});
    document.querySelector("[data-action='replay']").addEventListener("click", reset);
    speed.addEventListener("input", () => {{ state.speed = Number(speed.value); }});
  </script>
</body>
</html>
"""


def build_demo(skill_dir=None, out_dir=None):
    skill_dir = Path(skill_dir or skill_dir_from_script())
    out_dir = Path(out_dir or (skill_dir / "dist"))
    manifest = load_manifest(skill_dir)
    copy_demo_assets(skill_dir, out_dir, manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    html = build_html(manifest)
    (out_dir / "index.html").write_text(html, encoding="utf-8")
    return out_dir / "index.html"


def main():
    output = build_demo()
    print(f"OK: built {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
