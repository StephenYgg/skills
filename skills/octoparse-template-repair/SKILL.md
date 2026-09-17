---
name: octoparse-template-repair
description: Inspect the Octoparse template repair queue in the configured Feishu Base, download a current RuleFile through the Template Admin API, reproduce the reported failure, and produce a repair report. Also migrate a repaired script to octopus-platform-sdk as a 304-group script when requested or when the user says “迁移到sdk” or “304组”. Use for BC template troubleshooting, repair intake, or SDK migration; do not use to publish or mutate live templates.
---

# Octoparse Template Repair

Use this workflow to turn one eligible Feishu repair record into a reproducible local diagnosis and a concrete repair plan.

## Boundaries

- Treat Feishu Base, Template Admin, and RuleFile URLs as read-only for diagnosis. The user's explicit request to process/fix a named template authorizes only the guarded owner/status transitions in `Record Ownership And Status`; it does not authorize version creation. Catalog publishing (`bccc template publish`, 维护中 → 已发布) is allowed only after the repair write-up **and** the user separately confirms that catalog change.
- Do not copy a version, set current, upload a RuleFile, or call `template publish` unless the user separately authorizes that operation. When they ask to ship a new RuleFile version, follow **Ship a repaired RuleFile**.
- Never echo tokens, proxy credentials, cookies, authorization headers, or signed URL query values. Report their presence and risk without their values.
- Preserve the downloaded RuleFile byte-for-byte at the template directory root. If implementation is requested, create `<id>-<slug>/fixed/` and put every repaired `.py` working copy there; never place a repaired file beside the original RuleFile.
- Keep SDK migration output separate from repair output: create `<id>-<slug>/fixed-migration-sdk/` and put migrated 304-group `.py` files there. Do not move, overwrite, or mix files from `fixed/`.
- Limit live tests to the issue's representative input and the smallest useful page/item count. Do not turn diagnosis into a broad crawl.

## Find Eligible Records

Speak using Feishu **table name + view name**. Deduplicate by 模板ID.

| 表 | 视图 | table / view |
|---|---|---|
| PY模板修缮需求 | PY模板修复需求 | `tblEsTqAFIAgzkQv` / `vewW32R8DZ` |
| 重点模板异常-监控同步 | PY模板修复需求 | `tblmFq6Mkwd2ZJlj` / `vewW32R8DZ` |
| 模板启动异常-监控同步 | PY模板修复需求 | `tblcrcBlp4XIAiVZ` / `vewW32R8DZ` |

`重点模板异常-监控同步` also has views `时间排序和0数据` and `时间排序和字段缺失`. `模板启动异常-监控同步` also has view `异常启动` (checkboxes `已处理/修复`, `验证正常（误报）`). Do not start `重点模板异常-监控同步` unless asked.

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
- Use the Base's canonical field names from `+field-list`: in the current repair queue, the user-facing completion-time concept “修复处理完成时间” is stored in `处理完成时间`, the completion note is `处理结果备注`, the validation screenshot column is `处理结果截图`, and requester acceptance is `验收成功（需求人填写）`. Resolve field IDs on every run; do not assume the legacy `验收提示` or `截图/测试文档` names still exist.
- When claiming the record, ask `预计多久可以完成？` before setting an estimate. If the user supplies a duration, calculate `预计完成时间` from the claim timestamp and write it with the start transition; if the user does not provide one, leave `预计完成时间` unchanged/blank and continue without guessing.
- Record the previous owner/status/time fields, the guarded decision, the write result, and the post-write values in the report. Never log access tokens or user IDs beyond the display name needed for the audit.

After a post-repair MCP revalidation task finishes, **export the rows**. Having any data is **not** a completed repair.

### Pre-acceptance field audit (required)

Do this after the repaired script has produced exportable rows, and **before** asking the user to confirm 原因 / 评论 / 截图.

1. **Baseline vs repair (only when the original script produced rows)**

   If the **original** RuleFile / baseline MCP already exported ≥1 row, save that export and list its field names (and which of those fields had values). After the repair export, compare:

   - fields present before but missing after
   - fields that had values before but are empty after
   - fields newly added

   Report that delta. **Skip this comparison when the original/baseline was 0 rows** (including the typical “运行 0 数据” queue item). Do not invent a before-dataset.

2. **outputSchema (always)**

   Read the live version schema:

   ```bash
   bccc --json template output-schema get <templateId> <versionId>
   ```

   Parse `data.outputSchema` (it is often a JSON **string**). Field names are `properties` keys. `bccc template output-field list` may return empty `modules`; do not treat that as “no schema”. If `output-schema get` fails, report the error and fall back to exported keys, but still say schema was unavailable.

   Check every schema field on every repaired export row: present, and non-empty (`null` / `""` / whitespace = empty). Report missing keys and empty fields by name.

3. **Empty-field gate**

   A field has no value when it is missing, `null`, `""`, or whitespace-only. Non-empty title/price with other blanks is still incomplete. Example: `以下字段没有值：description, seller`.

   Do **not** treat empty fields as acceptable unless the user **explicitly** says to ignore those named fields (for example `description 可以忽略`). Guessing optional fields does not count.

Only when (1) was done or correctly skipped, (2) is done, and (3) every remaining empty field is explicitly ignored, may you ask about writing 原因 / 评论 / 截图. Until then: do not write `处理结果备注`, do not comment, do not upload `处理结果截图`.

Then ask `字段已齐（或你已明确忽略：…）。是否把原因、评论和截图写回飞书？（此时不改当前状态为已完成）` and **wait for an explicit yes**. Silence, `已修复`, `开始验证`, MCP passing, or “有数据了” is not that yes.

If the user confirms, refresh the same record and the current field definitions, then:

- Upload the validation screenshot to the attachment field whose canonical name is `处理结果截图` using `lark-cli base +record-upload-attachment` and the resolved field ID. Do not use the legacy `截图/测试文档` field when a newer result-screenshot column exists.
- Write `处理结果备注` with a concise record-specific block containing **原因** (confirmed root cause), **修复方案** (implemented changes), and **验收方法** (the exact MCP input, expected non-zero/required-field criteria, and any remaining canary constraint). Preserve `负责人` and all other fields.
- **Do not** set `当前状态 = 已完成`. **Do not** write `处理完成时间`. Leave `当前状态 = 处理中` until the hard rule below is met.
- Read `需求提出人` from the refreshed record and create a Base record-local comment with `lark-cli drive +add-comment --type bitable --block-id <table-id>!<record-id>!<view-id>`. The comment content must start with a `mention_user` element for that submitter's open_id, then include the repair description, MCP result, and the fact that the screenshot is in `处理结果截图`. Tell the submitter that they need to check `验收成功（需求人填写）` after they accept the result.
- If the attachment field is not writable, do not pretend the upload succeeded: upload the screenshot to Drive, put its link in the same @submitter comment, and record the field-permission error in the report. If the comment or mention fails, report it rather than silently posting an unmentioned comment.

Then, in the same repair write-up turn (still `处理中`), use `bccc` (not Template Admin HTTP by hand) for publish status and a cost check. Prefer `--json`. Use the environment that owns the template (`global-prod` for Octoparse overseas). If `bccc` cannot reach BC, set the local HTTP proxy plus `NODE_USE_ENV_PROXY=1`; do not print proxy credentials.

1. Template catalog status (维护中 → 已发布)

   Run `bccc --json template get <templateId>` and read `data.status`:

   | `status` | Meaning |
   |---|---|
   | `0` | New / hidden |
   | `1` | 已发布 (Published) |
   | `2` | 维护中 (Maintaining) |
   | `3` | Obsoleting |

   If status is `2` (维护中), ask `当前模板状态是维护中，是否改为已发布？` and wait. Do not publish on silence.

   If the user says yes, publish the current version only:

   ```bash
   bccc template publish <templateId> --version-id <currentVersionId> --yes
   ```

   Take `currentVersionId` from `data.currentVersion.templateVersionId` (or `data.currentVersion.id`) on the same get. Then `template get` again and confirm `status === 1`. Do not call `template maintain`. Do not invent a version ID.

   If status is already `1`, skip the question. If `bccc` fails, report it and leave catalog status unchanged.

2. Cost comment when the new version added paid exits

   Compare the **pre-repair** RuleFile (the snapshot at `<id>-<slug>/` plus that version's `settings`) with the **post-repair current** RuleFile (`bccc --json template version get <templateId> <currentVersionId>` and its `ruleFile`). If the snapshot is missing, use the previous current version from `bccc --json template version list <templateId>`.

   Detect only **newly added** capability (absent in old, present in new). Search file text case-insensitively; never print tokens, proxy userinfo, or API keys.

   - **IP proxy added** when `settings.isUseProxy` went from false/absent to true, or the new RuleFile newly contains a residential/script proxy (`kkoip`, `ipweb`, `OCTOPARSE_MANAGED_PROXY`, `cloud/proxy`, `getProxy`) that the old file did not.
   - **DataDome CapSolver added** when the new RuleFile newly uses CapSolver for DataDome (`capsolver` together with `datadome`, or a CapSolver DataDome task type that the old file did not have). CapSolver alone for another captcha is not this case.

   If either fired, add a **separate** Base record-local comment (same `drive +add-comment` bitable block-id as the completion comment). Mention `需求提出人`. Chinese text, no secrets:

   - IP proxy only: `本次修复新增加了 IP 代理，可能提高了成本，是否考虑要调整模板价格。`
   - DataDome CapSolver only: `本次修复新增加了 DataDome 的 CapSolver 处理，可能提高了成本，是否考虑要调整模板价格。`
   - Both: `本次修复新增加了 IP 代理和 DataDome 的 CapSolver 处理，可能提高了成本，是否考虑要调整模板价格。`

   If neither fired, do not post this comment. Wait for the user before changing `pricePerData` or any price field.

If the owner is no longer 杨伟铭 (or is another non-empty owner), do not write the repair note or mark it complete; report the ownership conflict. If the user does not confirm the write-up, leave the record in 处理中 and do not set the completion time.

### Hard rule: `已完成` only after requester acceptance

**Never** set `当前状态 = 已完成` because MCP passed, the user said the repair is done, or the write-up (原因 / 评论 / 截图) is finished.

The only allowed trigger is that `验收成功（需求人填写）` is checked. Resolve that exact field from `+field-list` every run. Treat it as checked only when the refreshed cell is truthy (`true`, checked, `是`, or `1`). Empty, `false`, unchecked, or missing is not acceptance.

When the user asks to set 已完成:

1. Re-read the record immediately.
2. If `验收成功（需求人填写）` is **not** checked, refuse. Report the current value and that 需求人 has not accepted. Do not write `当前状态` or `处理完成时间`, even if the user insists in the same turn.
3. If it **is** checked, and `负责人` is still 杨伟铭, then set `当前状态 = 已完成` and `处理完成时间` to now (or leave `处理完成时间` to the table auto-fill when that field is not writable). Re-read to verify.
4. If the owner changed, stop and report the conflict.

Do not check `验收成功（需求人填写）` yourself. That column is for the requester.

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

## Ship a repaired RuleFile

Use this only when the user explicitly asks to publish/ship a **new RuleFile version** (not `template copy`, and not catalog `template publish` unless they also asked for 已发布). Use `bccc --json`. Same environment/proxy rules as other `bccc` calls.

Do **not** copy the Template. Copy the **TemplateVersion**.

1. `bccc --json template version list <templateId>` and note the source version (`id` / `version` / `type` / `ruleFile` / `settings`). Source is usually `currentVersion.templateVersionId`.
2. `bccc --json template version copy <templateId> <sourceVersionId>`. The copy route does **not** accept `isSetCurrent`. The new version exists but is **not** the template current version. The copy response does not include the new id; list versions again and take the new row (new `id`, incremented `version`).
3. **Before** pointing the template at the copy: upload the repaired file, then write that URL onto the **copy**.

   ```bash
   bccc --json template file upload --file <repaired.py> --content-type text/x-python
   ```

   Use `data.uplaodRes` as `ruleFile`. Then `bccc template version update <templateId> <newVersionId> --file body.json` with at least:

   - `type`: same as source (`8` = Python). Always send `type`; omitting it can default to XOML (`0`) and break the version.
   - `ruleFile`: the upload URL
   - `isUseProxy`, `canSecondSplit`, `stepTotal`: copy from source unless the repair changed them
   - `isSetCurrent`: `false` on this write

   Omit `ruleFile` on later updates that must keep the body.
4. Point the template at the copy. `bccc template version set-current <templateId> <newVersionId>` writes **three fields together** on `template.currentVersion` (do not PATCH them one-by-one, do not invent a template-level JSON of only one of them):

   | Field | Meaning |
   |---|---|
   | `templateVersionId` | New version row id |
   | `version` | Version number (1, 2, …) |
   | `type` | Script type (`8` = Python) |

   Confirm with `bccc --json template get <templateId>` that those three match the copy.
5. Then set the copy comment with another `template version update` (no `ruleFile`). Format:

   `yyyyMMdd stephen 修复了<根因>，处理了<做法>`

   Example: `20260916 stephen 修复了Google Play搜索页旧XPath失效导致0数据，处理了稳定详情链接解析并迁移304 SDK`

This is **not** `bccc template publish` (catalog status 1). After set-current, if the RuleFile is a 304 SDK script, set Template `groupId` to `304` (see SDK Migration step 7) **before** MCP. Then run the pre-acceptance field audit.

## MCP Execute And Revalidate

When an Octoparse MCP exposes `execute_task` (or equivalent task-create/poll/data-result tools), use it for a cloud baseline before changing a template:

1. Create one new, bounded task with the exact template ID and the Feishu `问题参数`. Keep the smallest page/item/input limits that can demonstrate the issue.
2. Poll that task to a terminal state and **export the rows**. Inspect every field on those rows, not only the task status or row count. Record the task ID, effective input, target status/final URL when available, row count, **which fields are empty**, and error/stop reason without recording credentials or large bodies. If this baseline has rows, keep the export for the later before/after field comparison. If it is 0 rows, skip that comparison later.
3. Compare the MCP result with the local harness result. A Finished task with zero rows is still a failed data-quality outcome. A Finished task with rows but blank fields is also incomplete until the user explicitly ignores those fields. After repair, also compare against `bccc template output-schema get`.

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
7. **Cluster group 304 (required for a shipped 304 SDK RuleFile).** The octopus-platform-sdk script only runs on cluster group 304. After `version set-current` of that RuleFile, set the **Template** `groupId` to `304` before MCP. Do not copy a Template; update the existing one:

   ```bash
   bccc --json template get <templateId>
   # PUT with the GET fields plus groupId: 304 (name is required; keep status/kinds/users)
   bccc --json template update <templateId> --file body.json
   bccc --json template get <templateId>   # confirm data.groupId === 304
   ```

   If `groupId` is null, the dispatcher may send the task to group 8 and the SDK process `ExecutorCrashed` with 0 rows. This is not a parser failure. Confirm `groupId` is 304 before treating a 0-row MCP as a script bug.

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
