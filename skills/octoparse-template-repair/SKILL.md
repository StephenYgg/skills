---
name: octoparse-template-repair
description: Inspect the Octoparse template repair queue in the configured Feishu Base, download a current RuleFile through the Template Admin API, reproduce the reported failure, and produce a repair report. Also migrate a repaired script to octopus-platform-sdk as a 304-group script when requested or when the user says “迁移到sdk” or “304组”. Use for BC template troubleshooting, repair intake, or SDK migration; do not use to publish or mutate live templates.
---

# Octoparse Template Repair

Use this workflow to turn one eligible Feishu repair record into a reproducible local diagnosis and a concrete repair plan.

## Boundaries

- Treat Feishu Base, Template Admin, and RuleFile URLs as read-only for diagnosis. The user's explicit request to process/fix a named template authorizes only the guarded owner/status transitions in `Record Ownership And Status`; it does not authorize version creation or publishing.
- Do not add a template version, set a current version, publish, or upload a repaired RuleFile unless the user separately authorizes that operation.
- Never echo tokens, proxy credentials, cookies, authorization headers, or signed URL query values. Report their presence and risk without their values.
- Preserve the downloaded RuleFile byte-for-byte at the template directory root. If implementation is requested, create `<id>-<slug>/fixed/` and put every repaired `.py` working copy there; never place a repaired file beside the original RuleFile.
- Keep SDK migration output separate from repair output: create `<id>-<slug>/fixed-migration-sdk/` and put migrated 304-group `.py` files there. Do not move, overwrite, or mix files from `fixed/`.
- Limit live tests to the issue's representative input and the smallest useful page/item count. Do not turn diagnosis into a broad crawl.

## Find Eligible Records

Run:

```bash
python3 <skill-dir>/scripts/list_candidates.py
```

The script resolves the configured Base URL with `lark-cli`, resolves the owner name to an exact `open_id`, and performs two server-side queries:

1. `当前状态 = 新提交 AND 负责人为空`
2. `当前状态 = 新提交 AND 负责人包含杨伟铭`

It paginates serially, projects only `模板ID`, `模板名称`, `当前状态`, `负责人`, `问题描述`, and `问题参数`, then de-duplicates by `record_id`. Do not replace these cloud filters with local filtering of a default page.

When the user names a template, match it by `模板ID` first and otherwise by an unambiguous exact name. For a one-off trial request without a named template, choose one record with a non-empty template ID and actionable problem parameters, and state the selection rationale. For a real repair request with multiple possible records, show the candidates and ask the user which one to change.

## Record Ownership And Status

When the user says to process/fix a specific template, first refresh that record by `record_id` and inspect the real `负责人` and `当前状态` fields. Read the Base field definitions before writing and use the `lark-cli base +record-upsert --record-id ...` form (or the equivalent guarded record update), as described by the `lark-base` skill.

- If `负责人` is empty, update `负责人 = 杨伟铭` and `当前状态 = 处理中` in one record update before editing files. Set `修复开始时间` to the current timestamp in the Base's accepted date format.
- If `负责人` is already `杨伟铭`, ensure `当前状态 = 处理中` with an idempotent update and refresh `修复开始时间` only when beginning a new repair attempt; do not clear or replace other fields.
- If `负责人` is any other person, do not change either field. Report that the template is already being handled by that person and stop unless the user explicitly says to force takeover (for example, `强制指定这个是我来改`). Only then may the owner be changed to 杨伟铭 and status set to 处理中.
- Re-read immediately before the write, write both start fields together, then re-read to verify. If the owner changed between reads or the write result is ambiguous, stop and report the conflict instead of overwriting another worker. The CLI has no guaranteed compare-and-swap; do not pretend a local check is a global lock.
- Use the Base's canonical field names from `+field-list`: in the current repair queue, the user-facing completion-time concept “修复处理完成时间” is stored in `处理完成时间`, the completion note is `处理结果备注`, and the validation screenshot column is `处理结果截图`. Resolve field IDs on every run; do not assume the legacy `验收提示` or `截图/测试文档` names still exist.
- When claiming the record, ask `预计多久可以完成？` before setting an estimate. If the user supplies a duration, calculate `预计完成时间` from the claim timestamp and write it with the start transition; if the user does not provide one, leave `预计完成时间` unchanged/blank and continue without guessing.
- Record the previous owner/status/time fields, the guarded decision, the write result, and the post-write values in the report. Never log access tokens or user IDs beyond the display name needed for the audit.

After a post-repair MCP revalidation task reaches the expected successful data result, ask `MCP 复验已通过，是否确认这个模板完成？` and wait for an explicit confirmation. If the user confirms, refresh the same record and the current field definitions, then:

- Upload the validation screenshot to the attachment field whose canonical name is `处理结果截图` using `lark-cli base +record-upload-attachment` and the resolved field ID. Do not use the legacy `截图/测试文档` field when a newer result-screenshot column exists.
- Update `当前状态 = 已完成`, `处理完成时间` to the current timestamp, and `处理结果备注` with a concise record-specific block containing **原因** (confirmed root cause), **修复方案** (implemented changes), and **验收方法** (the exact MCP input, expected non-zero/required-field criteria, and any remaining canary constraint). Preserve `负责人` and all other fields.
- Read `需求提出人` from the refreshed record and create a Base record-local comment with `lark-cli drive +add-comment --type bitable --block-id <table-id>!<record-id>!<view-id>`. The comment content must start with a `mention_user` element for that submitter's open_id, then include the repair description, MCP result, and the fact that the screenshot is in `处理结果截图`.
- If the attachment field is not writable, do not pretend the upload succeeded: upload the screenshot to Drive, put its link in the same @submitter comment, and record the field-permission error in the report. If the comment or mention fails, report it rather than silently posting an unmentioned comment.

If the owner is no longer 杨伟铭 (or is another non-empty owner), do not mark it complete; report the ownership conflict. If the user does not confirm, leave the record in 处理中 and do not set the completion time.

## Prepare The Template

From the user's requested working directory, run:

```bash
python3 <skill-dir>/scripts/prepare_template.py --template-id <id>
```

This reads the template shell, resolves `currentVersion.templateVersionId`, reads that exact version, and downloads its original `ruleFile` into `<id>-<slug>/`. It also creates `<id>-<slug>/fixed/` for repaired copies and writes `template-metadata.json` without copying the Base64 `body` into the workspace.

The required layout is:

```text
<id>-<slug>/
|-- <original-rule-file>        # byte-for-byte RuleFile snapshot
|-- template-metadata.json
|-- REPORT.md
`-- fixed/
    `-- <repaired-rule-file>.py  # every local repair candidate
```

Keep tests and fixtures outside `fixed/` unless they are part of the executable RuleFile. Reports and summary indexes must link to the path under `fixed/`.

The preparation script uses temporary files and exclusive destination creation. An existing identical RuleFile is reused; a different existing file or version metadata is a conflict to inspect, not something to overwrite. It refuses a symlink in the `fixed/` path.

Read [references/admin-api.md](references/admin-api.md) when diagnosing API routing, response shape, current-version selection, or a missing RuleFile.

## MCP Execute And Revalidate

When an Octoparse MCP exposes `execute_task` (or equivalent task-create/poll/data-result tools), use it for a cloud baseline before changing a template:

1. Create one new, bounded task with the exact template ID and the Feishu `问题参数`. Keep the smallest page/item/input limits that can demonstrate the issue.
2. Poll that task to a terminal state and inspect the returned rows, not only the task status. Record the task ID, effective input, target status/final URL when available, row count, required-field signals, and error/stop reason without recording credentials or large bodies.
3. Compare the MCP result with the local harness result. A Finished task with zero rows is still a failed data-quality outcome.

After the user says the repair is complete (for example, `已修复，开始验证`), create a **new** MCP task for revalidation; never resume, retry, or reuse the baseline task. Use the repaired/draft template reference supplied by the user or an explicitly authorized draft version, and run the same bounded input so before/after rows and required fields are comparable. If the repaired file exists only locally and no executable draft/reference is available, stop at local smoke and state that cloud revalidation needs a draft/version or deployment authorization; do not publish one implicitly.

For MCP-unavailable environments, record `MCP execute_task unavailable` as an environment gap and keep the local bounded smoke. Do not invent task IDs or present local output as cloud output.

## SDK Migration (304 Group)

Use this phase when the user explicitly asks to “迁移到sdk”, “迁移为 304 组”, or “304组”, and offer it by default after an ordinary repair: ask `本次修复候选是否还要迁移为 304 组、使用 octopus-platform-sdk 的脚本？` before starting the migration. Do not silently publish or change the live template.

When the user confirms migration:

1. Create `<id>-<slug>/fixed-migration-sdk/` and write only the migrated executable `.py` there. Keep the original RuleFile at the template root and the repaired legacy-compatible candidate under `fixed/`.
2. Follow [references/sdk-migration.md](references/sdk-migration.md). The migrated script must use the SDK runtime lifecycle (`Runtime` when available), a plain executor class, `Runtime.get_input()`, `Runtime.push_data()`, and `Runtime.log`; it must not inherit or import the legacy executor contract.
3. Preserve the repaired script's input names, output field names, target request semantics, `curl_cffi` behavior, and existing proxy implementation unless the issue explicitly requires a change. Remove legacy status-reporting fields and dynamic package installation.
4. Include a local argparse/JSON debug path, but keep platform execution as the default when invoked without CLI arguments. Convert output values to strings when the dataset contract requires it.
5. Run `py_compile`, `--help`, the migration unit/fixture tests, and one bounded smoke using the issue's input. If the SDK or cloud runner is unavailable locally, report the exact dependency/runtime gap instead of installing packages dynamically.
6. Update the repair report with the migration path, SHA-256, 304-group classification, behavioral differences, validation results, and any cloud acceptance gap. The migration report must include the same concurrency/resource-bound review as the repair candidate.

### 1053 KKoip/static proxy integration

For the Kompass/DataDome migration when the user asks to use the 1053 proxy setup, read the current 1053 RuleFile through the Admin API and reuse its route shape without printing credentials:

- Resolve the KKoip authenticated HTTP template from 1053, render the requested two-letter country (normally `FR`) and a fresh eight-digit session ID for the first attempt.
- Resolve the six-node static proxy pool from 1053 for bounded retries. Use KKoip on attempt 0, then static nodes in deterministic order for attempts 1 through the retry limit; the same selected proxy and browser User-Agent must be passed to a DataDome solver call.
- Allow `KKoipProxyUrlTemplate`, `StaticProxyUrls`/`StaticProxyPool`, `CapSolverApiKey`, and their environment-variable equivalents to override the defaults. An explicit empty KKoip template and empty static list may opt back into the SDK platform proxy allocator.
- If the 1053 RuleFile supplies a built-in CapSolver credential, keep it out of logs and reports, cap solver tasks, and state that the source now carries a paid secret. Prefer 304 secret injection/rotation before deployment.
- Add a local `--builtin-proxy-pool` smoke switch (or equivalent) and test KKoip-to-static route selection without making broad crawls. A local `ERR_EMPTY_RESPONSE` is a proxy transport failure, not evidence that the 304 cloud exit also fails.

## Diagnose And Trial Run

1. Compare the Feishu `问题参数` with the version parameter contract. Use actual `ParamName` values, types, required flags, and limits rather than labels guessed from the issue text.
2. Statically inspect the RuleFile before import or execution. Identify top-level network calls, dynamic package installation, monitoring hooks, notification/reporting endpoints, hardcoded credentials, proxy acquisition, retry decorators, and the runtime entrypoint.
3. Locate the compatible local `py_executor` implementation. Prefer an existing project environment. If the full runtime cannot be loaded, use a small diagnostic harness that preserves `ctx.param`, `MainKeys`, `upload`, logging, and finish semantics, and disclose the difference.
4. Run one representative issue input with the minimum page/item limit. Use a subprocess timeout. Disable unrelated notification side effects where possible, but do not silently change the scraper's target request or parser behavior.
5. Count uploads. Process exit code `0` is not evidence of success: a template can swallow an error, upload zero rows, and still finish successfully.
6. Probe the target response only as needed to test the failed assumptions. Record HTTP status, final URL, response size, semantic markers, selector/data-source counts, retry path, and uploaded row count. Do not save or print large response bodies unless necessary.
7. Separate observed facts from inferences. A valid page plus zero matching selectors supports a parser-drift diagnosis; an access-denied page supports a request/session/proxy diagnosis instead.

For implementation after diagnosis:

- Keep input and output contracts compatible unless the user authorizes a change.
- Prefer stable semantic attributes or structured data over generated CSS classes.
- Bound pages, items, retries, proxy rotations, and elapsed time. Detect no-progress pagination and deduplicate by a stable business key.
- Treat a valid request with zero expected entities as a diagnosable failure, not an unconditional successful finish.
- Add fixture-based parser tests and one bounded live smoke test when network access is available.

## Report

Write `<id>-<slug>/REPORT.md` and follow [references/report-contract.md](references/report-contract.md). When SDK migration is performed, also link the migrated file under `fixed-migration-sdk/` and document its 304-group validation. A report is incomplete without a specific repair plan and its validation criteria.

Before finishing, explicitly review concurrency and resource amplification:

- requests per input x maximum inputs x retries;
- nested retry multiplication, proxy/session churn, and upstream pressure;
- whether pagination and dedupe have hard bounds;
- whether a repair adds jobs, events, DB rows, cache keys, or other per-request side effects;
- whether multiple workers can duplicate work or create unbounded background activity.

State the risk and mitigation in the report even when the conclusion is that the change adds no new concurrency behavior.
