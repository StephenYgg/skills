# Visual Guide

## Editorial Function

Every image must do at least one job:

- establish the subject as a cover;
- show the real product, interface, object, or event;
- explain a mechanism or comparison;
- visualize verified data;
- provide a meaningful transition between major sections.

Do not add generic futuristic imagery merely to satisfy the image count.

## Choose The Production Method

Use `$imagegen` for original raster covers, editorial illustrations, conceptual scenes, and other non-factual visuals. Follow the complete `$imagegen` workflow, inspect every result, and move final images into the article package's `assets/` directory.

Use deterministic tools such as Mermaid, Graphviz, matplotlib, or HTML/canvas rendering for data charts, timelines, architecture diagrams, and labeled technical explanations. Render the result to PNG or WebP for the final Markdown. Never ask image generation to invent labels, numbers, UI screenshots, benchmark charts, or architectural relationships.

Use official or user-provided images only when publication rights and attribution are clear. Do not hotlink third-party images. Do not generate fake product screenshots, company announcements, people, logos, or events that could be mistaken for documentary evidence.

## Counts

- Article: 3-4 images total.
- Post: 1-6 images total.

For an article, a useful default is:

1. one cover;
2. one subject or product image;
3. one explanatory diagram or verified chart;
4. one comparison or consequence image when the content supports it.

Do not manufacture an unnecessary fourth image.

## Composition

- Keep cover art legible at thumbnail size and leave a clear focal point.
- Avoid text inside generated images unless essential; add labels deterministically when accuracy matters.
- Avoid watermarks, fake interface chrome, unrelated circuitry, humanoid robots, and glowing brains unless they are the actual subject.
- Match the article's concrete topic rather than using a generic blue-purple AI aesthetic.
- Preserve real brand assets and product interfaces; never distort them through generative editing.

## File And Markdown Rules

- Use stable names: `cover.png`, `figure-01.png`, `figure-02.png`.
- Keep files under the package's `assets/` directory.
- Reference every delivered image from the publishable Markdown unless the user asks for selectable variants.
- Write specific alt text describing visible content and editorial purpose.
- Record origin, attribution, and generation prompt in `image-manifest.md`.
- Inspect each final file for incorrect text, invented details, visual artifacts, accidental logos, and mismatch with the surrounding claim.

When platform policy requires AI-content disclosure, include the required disclosure in the publishable package. Verify the current policy rather than guessing its wording.
