# Source Policy

## Wiki Location

Resolve the root in this order:

1. Use the user-provided path when present.
2. Use `LLM_WIKI_ROOT` when set.
3. Fall back to `/Users/stephen/Library/CloudStorage/OneDrive-个人/Wiki`.

Require these files before treating the directory as the Wiki root:

- `AGENTS.md`
- `wiki/index.md`
- `wiki/current-status.md`
- `wiki/source-catalog.md`

If OneDrive content is unavailable or not hydrated locally, report the missing files and stop. Do not silently substitute unrelated sources.

## Read Order

1. Read `AGENTS.md` and obey the repository's read and confidentiality rules.
2. Read `wiki/index.md`, `wiki/current-status.md`, and `wiki/source-catalog.md`.
3. Search `wiki/` for compiled knowledge.
4. Read only the relevant compiled pages.
5. Open a `raw/` source only when the compiled page is incomplete or an important claim needs verification.

Treat the Wiki as read-only for article production. Do not update its index, log, source catalog, raw files, or compiled pages unless the user separately requests Wiki maintenance.

## Restricted Sources

Do not open, use, quote, summarize, transform, or publish material from these locations for public writing:

- `raw/projects-octoparse/`
- any `octopus-projects/` or `projects-octoparse/` directory under another root;
- `wiki/octopus-services/`
- `tools/out/`
- any path or catalog row marked `Internal` when its public-release status is not explicitly established, except the limited `raw/tech-daily/` discovery use below;
- any source whose name or metadata identifies confidential Octopus project code, architecture, operations, security, customers, credentials, or unpublished plans.

Treat summaries, graphs, and analysis derived from restricted sources as restricted too. Moving a fact into `wiki/` does not make it public.

`raw/tech-daily/` is the sole default exception to the `Internal` catalog rule: open it only as a discovery index because it points to public sources. Do not publish its generated summaries as evidence; follow the original link and verify the primary source where possible.

When classification is ambiguous, exclude the source and ask the user rather than risking public disclosure.

## Source Hierarchy

Prefer sources in this order:

1. Official product documentation, release notes, repositories, papers, filings, datasets, or direct statements.
2. Original reporting with named evidence and clear dates.
3. Reputable secondary analysis.
4. Aggregators, social posts, and discussion threads as leads or public reaction, not sole proof of technical facts.

For current events, record both the event date and source publication date. Verify claims likely to have changed since the Wiki entry was created.

## Evidence Ledger

Create `evidence.md` beside the draft. Keep it private and use this table:

```markdown
| Claim | Status | Source | Source date | Public status | Notes |
| --- | --- | --- | --- | --- | --- |
| ... | Fact / Inference / Unverified | URL or source title | YYYY-MM-DD | Public / Restricted / Unknown | ... |
```

Use only `Public` sources in publishable Markdown. Remove `Unverified` claims or label the uncertainty explicitly. Never paste a restricted local path into the public draft.

## Copyright And Attribution

- Paraphrase in original language and structure. Do not reproduce long passages from source articles.
- Keep direct quotations short, necessary, accurate, and attributed.
- Cite sources close to consequential claims or include a concise source section when the platform format permits.
- Do not reuse article photographs, screenshots, charts, or illustrations unless their use is authorized and attribution requirements are satisfied.
- Do not imply endorsement by a company, publication, or person.
