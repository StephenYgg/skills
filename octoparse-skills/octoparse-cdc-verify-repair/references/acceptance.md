# CDC Acceptance And Fault Isolation

## Table Checks

Get a source observation with count, key range and latest business times.
For append-heavy integer-key tables, retain max(id) as a watermark and compare
target rows WHERE id <= that value after catch-up. Check count, MIN/MAX(id),
SUM(id), selected samples and, for stronger assurance, bounded hashes/key-set
comparisons. Never claim ID sums prove byte-for-byte equality.

For UUID/session keys, compare counts plus selected IDs/timestamps or bounded
key/hash exports under an approved volume. Include deletes and mutable fields
in stronger acceptance; feedback may change without a new created_at value.
Read transactions separately on two live systems are not an atomic snapshot.
Explain small live-write differences instead of requiring a moving exact count.

Examples (adapt column names from live DDL):

```sql
SELECT COUNT(*), MIN(id), MAX(id), SUM(id)
FROM TARGET_DB.ODS_TABLE WHERE id <= WATERMARK;

SELECT id, LENGTH(payload), CAST(created_at AS CHAR)
FROM TARGET_DB.ODS_TABLE WHERE id = KNOWN_FAILED_ID;
```

Monitor latest source/target records and their timezone/precision as well as
their counts. Use source event time for event-age observations, but distinguish
quiet traffic from ingestion lag. Byte-length comparisons may differ after JSON
serialization; compare semantics when formatting differs.

## Runtime Evidence

SourceReceivedCount/SinkWriteCount count processed operations, including updates
and replay. They are not target row counts. Zero current difference is a useful
signal, not proof every source table was loaded or content was preserved.

The October 2026 Advisor length failure demonstrated:

1. A few tables populated while other tables were zero.
2. The Plan still looked active, but the runtime job was FAILED.
3. lot logs were empty; exact runtime status exposed the sink error.
4. `capacity=65533` was a target field bound, not a CDC permission problem.
5. Recent samples missed older oversized payloads in messages and events.
6. After user-authorized expansion and retry, per-table progress eventually
   reached parity, post-start increments arrived and the failed row was present.

## Common Diagnosis Paths

| Evidence | Next check |
| --- | --- |
| Value length beyond capacity | Source byte maxima/tails, target VARCHAR version limit, affected rows and other large columns |
| Too many filtered rows | Exact rejection cause before changing filter settings; preserve rejected data evidence without exposing content |
| Missing target table/schema | Whitelist-to-target name expansion, actual target schema and schema_save_mode |
| Replication access denied | Actual runtime source account privileges, not just dbbb reader grants |
| Duplicate server ID/disconnect | Active clients sharing the source, explicit ranges/automatic allocation; do not modify server-wide ID |
| Time offset differs | Snapshot/binlog path, MySQL TIMESTAMP vs DATETIME, source/session/connector zone and target convention |
| All RUNNING, counters frozen | Quiet source versus unread data, backpressure/checkpoint failure, source splits and sink buffers |
| Endless new lots/retries | LongRunning failure handler, scheduler, deterministic error and admission race |
| Cleared target missing history | Restored source offsets versus new snapshot; authorized reload needed |

## Repair Confirmation

Do not rerun a known deterministic failure repeatedly. Check whether the owning
LongRunning Plan can relaunch on its own before stopping anything. A failed
runtime may already have a successor; re-read the current lot list.

Before a restart, confirm no competing instance, all ALTER jobs are finished,
credentials are ready and startup/resume behavior is understood. A new initial
snapshot with Primary Key upserts can overwrite old rows, but does not guarantee
removal of obsolete target-only rows. Do not suggest a destructive cleanup as
an automatic consequence of reloading.
