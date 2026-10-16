# SeaTunnel And Plan Semantics

## CDC Source And Sink

- MySQL-CDC initial is the documented default in the inspected upstream version:
  full historical snapshot followed by ongoing binlog capture, not snapshot-only.
- earliest replays the earliest available binlog; it does not reconstruct history
  that predates retained logs. latest does not seed existing rows.
- Restarts with restored offsets can continue incrementally, but a new submission
  may start a new snapshot. Inspect DataHub's actual submission/resume behavior;
  do not promise recovery merely because checkpoint.interval is set.
- Clearing target data never by itself resets source progress. A safe reload
  requires an explicit source-state/replay strategy and authorization.
- Omit server-id to use the installed connector's automatic allocation when
  that matches the deployment. An empty string may fail parsing. Fixed IDs/ranges
  must not conflict with other active replication clients on that MySQL source;
  a range does not create a job or one reader per table.
- schema-changes.enabled controls source schema delivery, not arbitrary target
  DDL. Check the sink/engine version and exact ALTER support before enabling it.
- Target schema_save_mode=ERROR_WHEN_SCHEMA_NOT_EXIST rejects missing tables;
  data_save_mode=APPEND_DATA does not clear existing rows. For SR CDC deletes,
  enable_upsert_delete=true requires a compatible Primary Key model.
- JSON Stream Load handles embedded newlines/quotes better than ad hoc CSV;
  test the actual payload mapping. Strict mode and zero filter tolerance expose
  malformed/oversized records instead of silently losing them.

Small observed workloads began with parallelism=1, pool=4, 2 MiB/s and 2,000
rows/s limits, 60-second checkpoints, 1,000-row/4 MiB sink thresholds and 3 write
retries. They are starting points, not universal capacity guarantees. Include
snapshot catch-up, downstream compaction and multi-table/per-writer buffers.

## Scheduling Is An External Mutation

Read service behavior before provisioning Plans. In the observed DataHub code,
creating/updating a Plan immediately registers a Hangfire recurring job, using
TimeZoneInfo.Local. There was no exposed enabled/disabled flag.

For preparation-only work, a verified supported unscheduled expression was
Hangfire Cron.Never: `0 0 31 2 *`. This is not a general scheduler standard and
does not prohibit manual triggering or LongRunning failure-handler restarts.
If unsupported, create only the Job and explain the scheduling limitation.

After acceptance, peer CDC Plans used `*/30 * * * *` with LongRunning (2):
every scheduler-local hour at minute 00/30, not once daily and not a daily reload.
Read current peers and clarify actual schedules rather than guessing what
"same time as others" means. Keep the active streaming instance running.

## Concurrency And Retry Limits

Observed LongRunning admission checked existing lots, then created a new lot
without atomic per-Plan acquisition. Do not claim strict single-flight. Avoid
concurrent start/trigger/cron transitions, confirm existing active batches and
exact-name runtime counts, and report duplicate instances rather than stopping
one arbitrarily. A local check is not multi-instance coordination.

Step maxRetry does not bound total Plan restarts: LongRunning failure handlers
can re-enqueue the Plan. Watch for permission/schema failures repeatedly creating
lots or loading snapshots. Do not keep retrying a deterministic length error.
Stopping a runtime job alone may not stop the owning Plan's re-enqueue chain;
coordinate the full recovery under explicit stop/pause/reset authorization.
