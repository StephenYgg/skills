# Evidence Ledger

## Title Candidates

1. Stripe 买下 OpenRouter：模型外面那一层，已经标上了天价
2. 模型还在卖智力，资本已经在买 token 账单
3. 同样的任务，账单可以差一个数量级

Selected: title 1.

## Source Window

Latest five compiled Tech Daily snapshots after the previous article (which used 2026-08-09 to 2026-08-13). 2026-08-20 has no compiled GitHub/HN snapshot because those collectors failed.

| Snapshot | GitHub unique repos | Other public leads used | Public-use status | Notes |
| --- | ---: | --- | --- | --- |
| `2026-08-16-tech-daily.md` | 8 | Anthropic token-saving 36Kr lead | Discovery only | GitHub 8, Hacker News 10, 36Kr 10 |
| `2026-08-17-tech-daily.md` | 7 | Stripe/OpenRouter 36Kr lead; TechCrunch Anthropic revenue | Discovery only | Frontmatter lists 137 items; log records 27 GitHub/HN/36Kr items plus extra publishers in the file |
| `2026-08-18-tech-daily.md` | 11 | TechCrunch OpenRouter report | Discovery only | 131 items; Hacker News collector failed |
| `2026-08-19-tech-daily.md` | 15 | OpenRouter joining Stripe | Discovery only | GitHub 13 unique in log plus extra; Hacker News collector failed |
| `2026-08-21-tech-daily.md` | 17 | DeepSeek Harness 36Kr lead; caveman | Discovery only | 27 items; GitHub 17, 36Kr 10; Hacker News collector failed |

## Recurrence Calculation

Count each GitHub project at most once per daily snapshot.

| GitHub project | Days present | Dates |
| --- | ---: | --- |
| `akitaonrails/ai-memory` | 4 | 08-16, 08-18, 08-19, 08-21 |
| `cordiverse/cordis` | 3 | 08-16, 08-17, 08-18 |
| `basecamp/omarchy` | 3 | 08-16, 08-17, 08-19 |
| `OpenCut-app/OpenCut` | 3 | 08-16, 08-17, 08-19 |
| `public-apis/public-apis` | 3 | 08-16, 08-17, 08-19 |
| `harry0703/MoneyPrinterTurbo` | 3 | 08-18, 08-19, 08-21 |

The previous article already covered workflow/memory assets. This draft uses the same window only as a discovery index, then follows public primary sources on metering, token cost, and agent harnesses. Recurring memory projects are recorded here but not used as the thesis.

## Claims

| Claim | Status | Source | Source date | Public status | Notes |
| --- | --- | --- | --- | --- | --- |
| OpenRouter announced it is joining Stripe | Fact | https://openrouter.ai/blog/announcements/openrouter-is-joining-stripe/ | 2026-08-19 | Public | Official company post; deal not closed |
| NYT reported a $7.5B price; Stripe did not disclose terms | Reported fact | https://techcrunch.com/2026/08/19/stripe-confirms-its-acquiring-ai-model-marketplace-openrouter/ | 2026-08-19 | Public | TechCrunch summary of NYT; price is reported, not official |
| OpenRouter Series B was $40M at $1.3B valuation in May 2026 | Reported fact | Same TechCrunch article citing prior round | 2026-05 (round) / 2026-08-19 (report) | Public | Used only as a before/after comparison |
| OpenRouter processes 10T+ tokens/day, 400+ models, 10M+ developers | Fact | OpenRouter official blog above | 2026-08-19 | Public | Company self-description, not independently audited |
| Same Claude Code task can cost an order of magnitude more tokens; cache hits bill input at 0.1x; `/clear` and model/effort switches affect cache | Fact | https://claude.com/blog/maximizing-the-value-of-your-claude-code-sessions | 2026-08-14 | Public | Official Anthropic guidance |
| Anthropic annualized revenue reached $65B by end of July 2026 | Reported fact | https://www.bloomberg.com/news/articles/2026-08-17/anthropic-hits-65-billion-in-annualized-revenue-as-usage-soars | 2026-08-17 | Public | Anonymous sources; company declined to comment |
| caveman reports 33.2% fewer provider-reported input tokens and 18/18 quality in a pinned Claude Code benchmark | Fact | https://github.com/JuliusBrussee/caveman/blob/main/docs/WRAP-BENCHMARK.md | checked 2026-08-22 | Public | Author benchmark; not production telemetry |
| Independent discussion questioned caveman's earlier output-compression claims | Fact | https://news.ycombinator.com/item?id=47284821 | 2026-08 | Public | Used as a limitation, not as a competing benchmark |
| DeepSeek Harness v0.1.0-rc.8 released 2026-08-19; README formula is Model + Harness = Agent | Fact | https://github.com/deepseek-ai/deepseek-harness/releases/tag/v0.1.0-rc.8 and repository README | 2026-08-19 | Public | GitHub primary |
| rc.8 can install Claude Code and Codex as subagents | Reported fact | https://www.mindstudio.ai/blog/deepseek-harness-rc8-native-vision-claude-code-codex-subagents-concurrent-web-search/ | 2026-08-20 | Public | Secondary changelog summary; 36Kr used only as discovery |
| llmfit finds which models run on local hardware | Fact | https://github.com/AlexsJones/llmfit | checked 2026-08-22 | Public | Repository description; no cost or quality claim |
| Metering/routing/harness layers are becoming the priced infrastructure around models | Inference | Cross-source synthesis | 2026-08-22 | Public | Bounded to this window; not a market-share claim |
| Users should check who meters, whether workflows lock to one model, and whether sessions can be cleared | Inference | Editorial judgment from Anthropic guidance plus OpenRouter/Harness design | 2026-08-22 | Public | Presented as advice, not measured user behavior |

## Limits

- Tech Daily snapshots are discovery indexes. Generated summaries were not used as evidence.
- OpenRouter token volume and developer counts are company statements.
- Anthropic revenue is leaked/reported run-rate, not an audited filing.
- Caveman numbers are a pinned benchmark of 18 tasks.
- DeepSeek Harness star-count claims in 36Kr (first-day 30k, etc.) were not independently confirmed on the repository page and are not used.
- No restricted Octopus project source or derivative was opened or used.
- Cover image generation via `$imagegen` failed in this session (invalid API key). The first draft used a local Pillow renderer. That version was replaced with official source images from OpenRouter, Anthropic, and DeepSeek after the user rejected the generated art. TechCrunch/Bloomberg/36Kr news photographs were not copied.
