---
name: write-ai-tech-article
description: Write source-grounded Chinese AI and technology articles or short posts for general readers, with local images and Markdown delivery. Use when creating deep technology analysis, explainers, trend commentary, Toutiao or Baijiahao drafts, 800-character articles, 100-250-character posts, or publication packages based on the local OneDrive LLM Wiki and other verifiable sources.
---

# AI Technology Writing

Create evidence-led Chinese technology writing for general readers. Prefer a clear thesis, concrete data, and useful explanation over generic summaries, inflated claims, or formulaic platform copy.

## Required References

Read these files before drafting:

1. Read `references/editorial-style.md` for audience, voice, depth, and structure.
2. Read `references/source-policy.md` before opening the local Wiki or selecting evidence.
3. Read `references/platform-and-output.md` for article/post modes and Markdown packaging.
4. Read `references/visual-guide.md` before sourcing or generating images.

## Workflow

1. Determine the topic, output mode (`article` or `post`), target platform, timeliness, and intended reader value. Ask only when a missing choice would materially change the result.
2. Resolve the Wiki root and apply the restricted-source rules before searching. Treat the Wiki as read-only during writing.
3. Read `wiki/index.md`, `wiki/current-status.md`, and `wiki/source-catalog.md`; search compiled `wiki/` pages first and open `raw/` only to verify a claim.
4. Build a private evidence ledger before drafting. Record each important claim, its source, date, public-release status, and whether it is a fact, inference, or unverified lead.
5. Verify time-sensitive claims against current primary sources when tools and network access are available. If verification is unavailable, narrow or remove the claim instead of presenting it as current fact.
6. Select one defensible thesis. Create an outline in which every section advances the thesis with evidence, mechanism, consequence, or a clearly labeled judgment.
7. Draft for a general audience using the requested mode. Explain technical terms through their practical meaning; do not remove the technical substance.
8. Plan images by editorial function, then source or generate them. Use `$imagegen` for original raster illustrations and covers; use deterministic charts or diagrams for factual data and technical relationships.
9. Produce the Markdown package defined in `references/platform-and-output.md`. Keep the evidence ledger private and keep machine-local source paths out of publishable Markdown.
10. Run `python scripts/validate_article.py <publishable-markdown> --mode article` or `--mode post`. Fix every reported error.
11. Perform a final human-quality pass: verify the thesis, evidence, calculations, dates, public-release safety, copyright, image relevance, and platform fit.

## Evidence Rules

- Do not invent facts, data, quotations, personal experience, product behavior, or causal explanations.
- Distinguish reported facts from the author's analysis. Use uncertainty directly when evidence is incomplete.
- Prefer primary sources. Treat aggregated news and `raw/tech-daily/` entries as discovery leads, then inspect their linked originals when a claim matters.
- Use multiple sources for synthesis when practical. Do not rewrite one article paragraph by paragraph.
- Never make restricted Octopus project material publishable. Follow the deny rules in `references/source-policy.md` even when it would improve the article.
- Never expose private file paths, internal URLs, credentials, customer data, source code, security findings, or unpublished product plans.

## Quality Standard

Reject drafts that merely list developments, repeat marketing language, or conclude that a topic is "worth watching" without explaining why. A publishable draft must contain:

- one explicit central judgment;
- verifiable facts or data supporting that judgment;
- an explanation of the underlying mechanism or tradeoff;
- a concrete implication for ordinary readers;
- no unsupported certainty, fake tension, or clickbait mismatch;
- the required number of relevant local images.

Do not imitate a living writer's distinctive voice. Use the editorial qualities associated with strong reporting in publications such as 36Kr and WIRED, and with evidence-rich technical discussion on Hacker News: original reporting discipline, technical clarity, skepticism, and meaningful conclusions.

## Publication Boundary

Create drafts and local publication packages only. Do not log into, upload to, or publish on Toutiao, Baijiahao, or another external platform unless the user explicitly requests that separate action and approves the final draft.
