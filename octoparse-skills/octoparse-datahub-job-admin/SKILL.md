---
name: octoparse-datahub-job-admin
description: Create or update Octoparse DataHub Jobs, JobPlans and Steps through bccc, including SeaTunnel CDC configuration, descriptions and cron schedules. Use for administration requests; does not independently authorize triggering, stopping, resetting or deleting runtime jobs or database data.
---

# Octoparse DataHub Job Administration

Read [the command/body reference](references/bccc-contract.md) for provisioning
and [the runtime semantics](references/seatunnel-and-plans.md) before configuring
startup, scheduling or retries. Confirm the installed CLI with --help when it
differs from these recorded contracts.

## Establish Scope

Check `bccc info --json` for the intended environment, then fetch the exact
definitions. List/search with pagination to find duplicate names, IDs and source
whitelists. Preserve existing user configuration and parameter expressions.
Do not use unpaged endpoints for routine monitoring.

Analysis and configuration creation do not authorize execution. A request to
translate a description is not permission to replace source credentials, change
the table list or rename a plan. Explain mutations briefly before performing them.

## Provision

Confirm target tables against the selected source whitelist. Use a verified
source URL option for the deployed connector (`url` in newer source docs;
`base-url` exists in local legacy configs). Do not blindly copy an alias.

Use a legitimate runtime source connection reachable by SeaTunnel. dbbb often
uses JumpServer proxy credentials; they are not interchangeable with underlying
MySQL credentials. Do not extract stored credentials by default. If the user
explicitly wants the current account staged temporarily, securely obtain only
that connection through an authorized local mechanism or ask for it, mark the
readiness limitations, and keep the plan untriggered until replaced.

Use [the sanitized SeaTunnel template](assets/mysql-starrocks.template.json)
when a fresh configuration is needed. It is not runnable until the source,
target, timezone, whitelist and credentials are replaced. Reassess its example
resource limits for the current workload. The template deliberately omits
server-id rather than sending an empty string.

For a new pipeline, create Job, Plan and Step as separate bccc operations with
stable IDs/names. Before each create verify absence, and after each create read
it back and record its ID. If a write times out, query before retrying: do not
create duplicate Jobs, Plans, batches or Step entries. Report partial provisioning
without deleting it or pretending it is complete.

## Update Conservatively

Job/Plan updates are complete-body replacements. Fetch the latest object,
construct only the endpoint's accepted fields, apply the requested changes,
re-read immediately before writing and stop on drift. bccc has no guaranteed
compare-and-swap: a local re-read narrows but does not eliminate concurrent edits.
Read back afterwards; compare all requested fields and all preserved fields.
Plan steps are separate records, not saved by the plan update endpoint.

The helper previews or applies a narrow Job/Plan patch while checking environment,
concurrent drift and readback. It emits field names, never definitions/passwords:

```bash
python3 <skill-dir>/scripts/patch_datahub.py --kind job --id JOB_ID \
  --environment op-prod --patch /protected/description-patch.json
# Only after the user authorized this exact mutation:
python3 <skill-dir>/scripts/patch_datahub.py --kind job --id JOB_ID \
  --environment op-prod --patch /protected/description-patch.json --apply
```

## Credentials And Runtime Safety

Capture and parse CLI JSON in process; do not print raw `job get` results.
Use 0600 request files inside private temporary directories, delete them in
finally blocks, and archive only sanitized definitions. Treat failed rows and
errorMsg as potentially containing conversations, tokens and signed URLs.

Before authorized scheduling/triggering, inspect active batches and exact-name
SeaTunnel instances. Do not combine start and trigger or stop a healthy instance
to apply a description/cron change. Preserve LongRunning for streaming Jobs;
do not turn them into concurrent Repeatable jobs. Review queue growth, retry
chains and non-atomic admission; a Step retry cap is not a global restart cap.

## Finish

Report environment, changed IDs/fields, Job/Plan/Step readiness, actual cron
interpretation and timezone, runtime instance count, and whether any execution
was requested. Save sanitized templates and Plan settings in the service docs.
After user-run schema fixes, update the archived DDL too. No implicit Git actions.
