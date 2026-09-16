# SDK Migration Reference

This reference adapts the local `Script-Migration-SKILL.md` rules for a repaired Octoparse RuleFile. It is for producing a local candidate only; Admin API versions and Feishu records remain read-only.

## Runtime Contract

- Import the SDK runtime from `octopus` and use `async with Runtime` in platform mode.
- Read task input with `await Runtime.get_input()` and send rows with `await Runtime.push_data(...)`.
- Pass `Runtime.log` into the executor and use that logger inside scraper logic. Configure `logging.basicConfig` only in local CLI mode.
- Keep the executor as a plain class. Do not import or inherit `py_executor.base.BaseExecutor`, and do not use `py_executor.cli.invoke_for_debug`.
- SDK releases may expose the same runtime singleton under a compatibility name. If compatibility detection is needed, keep it isolated at import time and retain the `Runtime` lifecycle in the script.

## Scraper Preservation

- Preserve `MainKeys`/`mainKeys` and the existing parameter aliases and output schema.
- Preserve `curl_cffi` browser impersonation, proxy acquisition, headers, retry semantics, and API request shape unless the repair evidence requires a change.
- Convert values to strings before pushing when the template dataset is string-typed.
- Remove `reportStatu`, `reportStatus`, `templateId`, old `datas` status counters, and runtime `os.system("pip install ...")` calls.
- Do not replace an existing proxy implementation with SDK proxy helpers by default.

## Local Validation

- Provide a bounded argparse/JSON path for local debug and retain platform mode as the no-argument entrypoint.
- Compile the script, run `--help`, run fixture/unit tests, and execute one representative input with hard limits on inputs, pages, retries, response bytes, and elapsed time.
- Treat SDK import or cloud-runner dependency failures as explicit environment findings. Never add dynamic installation to make a migration pass.
- Record the migrated path and SHA-256 under `fixed-migration-sdk/`, behavioral differences from `fixed/`, and the remaining cloud 304-group canary criteria in `REPORT.md`.
- The surrounding repair workflow owns Base timestamps and completion notes: claim time goes to `修复开始时间`, an estimate is written only when the user supplies a duration, and completion writes `修复处理完成时间` plus a cause/solution/acceptance block in `验收提示` after explicit confirmation.
