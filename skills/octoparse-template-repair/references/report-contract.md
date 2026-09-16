# Repair Report Contract

Write the report in the language used by the requester. Include all sections below, but adapt heading wording when useful.

## Queue Record

- Base URL, table ID, view ID, record ID
- template ID and name
- status and owner filter match
- exact problem description and problem parameters, summarized without losing test values
- owner/status/time transition audit: previous values, guarded decision, write result, and post-write values for `负责人`, `当前状态`, `修复开始时间`, `预计完成时间`, and `修复处理完成时间` when the template was claimed or completed

## Template Snapshot

- Admin API base and read endpoints used
- template slug, current version ID/version/type
- RuleFile source URL without sensitive query values
- local original file path, byte count, and SHA-256
- local repaired file path under `<id>-<slug>/fixed/`, byte count, and SHA-256 when a repair candidate exists
- local migrated SDK file path under `<id>-<slug>/fixed-migration-sdk/`, byte count, and SHA-256 when a 304-group migration exists
- migration classification (`not requested`, `requested`, `304-group migrated`) and source candidate path
- parameter contract relevant to the issue

## Trial Run

- runtime/harness and material differences from cloud execution
- exact parameter mapping and bounded input
- MCP baseline task ID/status/result when `execute_task` was available; explicitly mark it unavailable otherwise
- observed request status and parser/runtime signals
- upload count, exit/final status, and whether the issue reproduced
- failed attempts or environmental limits, clearly separated from successful checks

When the user confirms that the repair is complete, add a separate revalidation record with a newly created MCP task ID. Compare it with the baseline task's input, terminal status, row count, required fields, and error/stop reason. Never report a resumed baseline task as a post-repair validation.

After a successful revalidation, record that 原因 / 评论 / 截图 were **not** written until the user explicitly confirmed that write-up. If they were written, record that confirmation. `当前状态` stayed `处理中` unless `验收成功（需求人填写）` was already checked. Never report `已完成` from MCP success or a repair write-up alone.

`当前状态 = 已完成` is allowed only after a fresh read shows `验收成功（需求人填写）` checked. Record that check, the write result, and `处理完成时间`. If the checkbox was empty, record that 已完成 was refused.

When the repair note is written, include the exact `处理结果备注` content: confirmed cause, repair solution, and reproducible acceptance steps/criteria. If no estimate was supplied at claim time, state that `预计完成时间` was intentionally left blank.

## Diagnosis

- evidence-backed root cause
- secondary defects that affect correctness or observability
- security-sensitive material found, described by type and location without values
- facts versus remaining hypotheses

## Repair Plan

Specify the code areas and behavioral changes, not only a general recommendation. Include:

- request/session/proxy changes, if any;
- parsing/data-source and pagination changes;
- empty-result and failure semantics;
- compatibility constraints for inputs and outputs;
- fixture tests, bounded live smoke test, and cloud acceptance criteria.

## Concurrency And Resource Bounds

Estimate maximum target requests and any nested retry/proxy amplification per task. Confirm hard caps, no-progress stopping, dedupe, and whether the plan adds per-request jobs/events/storage/cache side effects. State mitigation for any multiplication or stampede risk.

## Conclusion

Give the repair recommendation, confidence, remaining risks, and whether any online template or Feishu record was changed. Never imply that a diagnosis-only run published a fix.

When migration was requested, also state whether the SDK candidate passed local validation, which runtime API form it uses, and whether a cloud 304-group canary remains outstanding.

State whether cloud revalidation was performed after explicit user confirmation. A local-only candidate without a draft/version reference is not a cloud revalidation.
