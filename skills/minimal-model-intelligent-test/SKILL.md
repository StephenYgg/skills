---
name: minimal-model-intelligent-test
description: Use when the user asks to test model intelligence, especially with an offline known-model snapshot and a one-shot self-contained SVG animation HTML opened in the default browser.
---

# Minimal Model Intelligent Test

When the user asks to test model intelligence, create a minimal, self-contained browser artifact for a quick model-and-rendering test.

## Fixed behavior

- Do not use the network, web search, package installation, or model/API calls.
- State only the latest model names known from current model knowledge; do not over-confirm or imply that the list was live-verified. Use this snapshot unless the user supplies a different one:
  - GPT: GPT-5
  - Gemini: Gemini 2.5 Pro
  - Claude: Claude Opus 4.1
  - DeepSeek: DeepSeek-V3.1
  - GLM: GLM-4.5
- Create exactly one HTML file in `/Users/stephen/tmp/` (the user's `tmp` directory). Keep it self-contained: inline CSS, inline JavaScript, and inline SVG; no external assets or dependencies.
- Put the model snapshot in the HTML's upper-left corner. Include a short visible note such as `基于已知信息，未联网`.
- Directly below that snapshot, add one extra visible line for the currently executing model. Take the name from this session's own identity (system prompt / self-identification). Do not look it up on the network. Label it clearly, for example `当前模型: <name>`.
- Directly below the current-model line, add one extra visible line for this model's knowledge cutoff date. Use only built-in training knowledge. Do not search the web, and do not call any tools. Label it clearly, for example `知识截止日期: YYYY-MM`.
- For the animation request, draw a pelican riding a bicycle as 2D SVG. Include at least two animated wheel rotations, a pedaling cue, and subtle forward-motion scenery so the animation is visibly alive.
- Generate the HTML once. After writing it, open that exact file with the system default browser. Do not inspect, patch, regenerate, or “fix” the HTML after opening it.

## Execution

1. Make the temporary directory if it does not exist.
2. Write the complete HTML in one operation. Prefer ASCII source where practical; Chinese model labels are allowed because they are user-facing content.
3. Open it with `open /Users/stephen/tmp/<filename>.html` on macOS (or the platform's equivalent default-browser command).
4. Report the five known model names, the current executing model, the knowledge cutoff date, the exact file path, and that it was opened. Do not claim live freshness.

## Concurrency note

This is a one-shot local file operation with no server, queue, shared cache, or remote side effect. Avoid retries or background jobs; a single invocation creates one bounded artifact.
