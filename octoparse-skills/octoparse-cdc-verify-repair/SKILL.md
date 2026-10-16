---
name: octoparse-cdc-verify-repair
description: Verify and troubleshoot Octoparse DataHub/SeaTunnel CDC into StarRocks using bccc status and dbbb source-target reads. Use when a sync was started, counts are incomplete, a snapshot stalls or ingestion fails; diagnosis is read-only unless repair actions are explicitly authorized.
---

# Octoparse CDC Verification And Repair

Read [the acceptance reference](references/acceptance.md) for source-target
comparison and historical lessons. Do not equate RUNNING, equal read/write
metrics or an empty log with complete synchronization.

## Find The Actual Execution

Inspect recent lots for the owning Plan, then its Step and exact SeaTunnel
runtime ID. Keep Int64 IDs as strings. The running-list endpoint omits failed
jobs; status by the exact ID is authoritative for that execution. Plan status
can lag runtime status because polling is delayed.

Commands: `bccc datahub lot list --plan-id ...`, `lot steps LOT_ID`,
`lot logs LOT_ID JOB_STEP_ID`, `seatunnel status RUNTIME_ID`, all with --json.
Parse output without dumping secrets, giant stack traces or raw failed rows.
Empty lot logs require exact runtime status, not an assertion of success.

## Observe With Bounds

Use dbbb for target existence/schema, actual counts and latest timestamps.
Complete a read group before switching source/target instances. Capture the
timestamp of each observation, schema changes and any source-target time
convention. Do not run production synthetic writes without authorization.

For bounded runtime monitoring without failed-row disclosure:

```bash
python3 <skill-dir>/scripts/monitor_cdc.py --environment op-prod \
  --runtime-id RUNTIME_ID --interval 30 --duration 300
```

The helper reads status only, not tables; pair it with serial dbbb source/target
observations. Default exit means the observation window ended, not that CDC
caught up. Stop a monitoring session on terminal failure or at its deadline;
do not leave a background watcher running without an explicit request.

During an initial snapshot tables can fill in different orders. Track measured
progress rather than restarting because a later table is temporarily empty.
If rows/metrics stop progressing, inspect source readiness, exact error and
backpressure/checkpoint state. Never increase retry counts for a deterministic
bad row to make a monitoring report look healthier.

## Accept Or Diagnose

Compare each selected table at a fixed source watermark where practical:
counts, key range, lightweight checksums and representative rows, including the
known failure row. Counts/ID sums alone do not prove content equality. Compare
new post-start records and updates with the same IDs to demonstrate incremental
flow; do not wait for FINISHED from a permanent streaming source.

Report snapshot caught up, increment observed, still copying, stopped/failed,
or inconclusive with measured evidence and residual differences. A quiet source
can prove historical parity but not newly generated increment propagation.

## Repair Boundaries

If a column capacity, timezone or mapping issue is found, use the sibling
schema skill to propose a compatible fix. Do not silently truncate JSON, skip
rows, raise filter tolerance, stop jobs, change grants, reset state or clear
target data. When a repair is authorized, verify schema completion, coordinate
Plan restart behavior and resume/reload semantics, then repeat acceptance.

After repair, refresh archived DDL/SeaTunnel/Plan docs and sanitized dbbb
knowledge. Separate observed recovery from untested crash recovery, delete
propagation or high-QPS safety. No implicit commits or production load tests.
