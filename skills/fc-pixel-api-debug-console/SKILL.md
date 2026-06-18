---
name: fc-pixel-api-debug-console
description: Use when creating FC Pixel styled single HTML API debug consoles, internal endpoint testers, login/token debugging pages, or server-mounted browser tools that need request/response inspection and playful FC Mario-like state feedback.
---

# FC Pixel API Debug Console

Build server-mounted, single-file API debugging tools that combine practical HTTP inspection with FC Pixel UI interaction. This skill extends `$fc-supermario-pixel-html`; use that skill for sprite sources, visual rules, and asset validation.

## Required Dependencies

Before designing or editing UI, use `$fc-supermario-pixel-html` and follow its required `$ui-ux-pro-max` searches. Read its `SKILL.md` plus the relevant `references/style-guide.md`, `references/ui-patterns.md`, and `references/animation-scenes.md`.

Do not fetch external Mario/Nintendo assets. Use the bundled sprites from `$fc-supermario-pixel-html`, embed them as `data:image/png;base64`, and keep `image-rendering: pixelated`.

## When To Use

- A static HTML page is mounted under a service `wwwroot`, `public`, or static-assets path.
- The page logs in, obtains an `access_token`, and calls same-origin API endpoints.
- The user needs request headers, request body, response headers, response body, HTTP status, duration, token display, and exception output in one page.
- The UI should show FC Pixel feedback, such as question block login state, Mario growth after successful login, fireball loading, or brick decorations.

## Core Workflow

1. Make the debug surface functional first: login inputs, password reveal, request editor, send button, output panels.
2. Use `window.location.origin` for displayed environment and call APIs with relative paths. Do not add environment dropdowns when the file is served by the target service.
3. Prefer relative paths such as `/token` and `/api/...`. Do not require a local proxy for the primary server-mounted flow.
4. Store only non-password state in `localStorage`: username, `access_token`, expiry, selected request body. Never persist passwords.
5. On every request, write request headers, request payload, response headers, response body, HTTP status, duration, and exception details.
6. Wrap async actions in `try/catch/finally`; set buttons to `disabled` while pending and always restore them in `finally`.
7. Keep the page as one HTML file unless the user explicitly accepts companion assets.

## FC Pixel Interaction Pattern

- Login button triggers Mario to jump into a question block.
- Use gravity/parabolic motion for jumps, not linear `translateY` tweening.
- Successful login: question block becomes used/gray, cloud bubble shows logged-in state, Mario grows like after a mushroom.
- Failed login: question block remains unused, Mario still bumps the block, a cloud/bubble shows the failure reason, and the exception panel records the error.
- API send button: show a small fireball sprite beside the active button while the HTTP request is pending.
- Loading state: disable login/send/template buttons and password toggle, then restore on success or failure.
- Respect `prefers-reduced-motion`; shorten or skip choreography without hiding the final state.

## Visual Composition

- Use a clean background layer from FC World 1-1 material; remove map objects that compete with the custom interaction.
- Keep only one active, meaningful question block for login state.
- decorative bricks should be sparse, usually one row, same visual scale as the active block, with enough spacing to avoid covering the active block.
- Avoid clutter from extra pipes, many rows of bricks, duplicate question blocks, or foreground objects that look interactive but are not.
- Keep important UI panels outside the animated character path.
- Use no external image dependency; embedded raster sprites are acceptable for shareable HTML.

## API Debug Details

Recommended panels and fields:

- Login: username, password, password visibility toggle, login and clear buttons.
- Request: editable JSON body, quick presets, send button.
- Headers: request headers must include `Authorization: Bearer <access_token>` when calling protected APIs.
- Output: request headers, request body, response headers, response body, HTTP status, duration, exception, token.

Token parsing should tolerate common shapes:

```js
payload.access_token || payload.accessToken || payload.token ||
payload.data?.access_token || payload.data?.accessToken || payload.data?.token
```

## Same-Origin Rule

For server-mounted pages:

```js
function getBaseUrl() {
  return window.location.origin;
}

async function callOpenApi(path, init) {
  const response = await fetch(path, init); // relative paths follow current origin
  return {
    ok: response.ok,
    status: response.status,
    statusText: response.statusText,
    headers: Object.fromEntries(response.headers.entries()),
    bodyText: await response.text()
  };
}
```

Only discuss a local proxy if the user explicitly wants to open the HTML through `file://` and accepts running a local helper server.

## Verification

Run the inherited FC sprite checks:

```bash
python skills/fc-supermario-pixel-html/scripts/extract_sprites.py --check
python skills/fc-supermario-pixel-html/scripts/extract_sprites.py
python skills/fc-supermario-pixel-html/scripts/build_demo.py
```

Also verify the produced HTML:

- Inline scripts parse with `new Function(script)`.
- No `<img src>` points to external files.
- All sprites are embedded as `data:image/png;base64`.
- There is exactly one active login question block.
- Pending requests disable controls and show the fireball; `finally` restores state.
- Current environment is read from `window.location.origin`.
