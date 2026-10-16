# Read-Only Inspection Patterns

Discover exact instance/database labels rather than deriving a database name
from a CLI instance name. Never put credentials in notes or command output.

```bash
dbbb instance --json
dbbb experience context DATABASE --instance INSTANCE --json
dbbb experience search KEYWORD --instance INSTANCE --limit 10 --json
dbbb connect INSTANCE --json
dbbb query 'SHOW DATABASES' --limit 30 --json
```

Complete all queries for one instance before switching to another. The shared
dbbb session is process-global local state, not an isolated connection per shell.
If a connect fails, stop that branch of queries instead of reading the old instance.

```sql
SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'SOURCE_DB'
ORDER BY TABLE_NAME;

SHOW CREATE TABLE SOURCE_DB.BUSINESS_TABLE;

SELECT @@global.log_bin, @@global.binlog_format,
       @@global.binlog_row_image, @@global.gtid_mode,
       @@global.binlog_expire_logs_seconds,
       @@global.time_zone, @@session.time_zone;

SHOW GRANTS;
```

If dbbb rejects a statement as unsupported/read-only, use another supported
read form or report the limitation. Do not invoke the raw DB driver to bypass it.

## Payload Measurements

```sql
SELECT COUNT(*) AS sampled_rows,
       MAX(OCTET_LENGTH(content)) AS max_content_bytes,
       MAX(OCTET_LENGTH(CAST(payload AS CHAR))) AS max_payload_bytes
FROM (
  SELECT content, payload
  FROM SOURCE_DB.MESSAGES
  ORDER BY id DESC LIMIT 1000
) AS recent;
```

This proves only the maximum inside that sample. Historical profiles should use
bounded indexed intervals such as `WHERE id >= LOWER_ID AND id < UPPER_ID`,
aggregating maxima and over-limit counts per chunk. Inspect EXPLAIN when the
source cost is uncertain. Avoid simultaneous full JSON scans on the primary.
Do not output raw conversations or error rows to measure their lengths.

## Time And Semantics

For a few IDs, compare CAST(time_column AS CHAR), UNIX_TIMESTAMP(time_column)
and an application UTC timestamp if present. MySQL TIMESTAMP is session-timezone
sensitive; DATETIME is not, even when code treats it as UTC. Record the intended
warehouse convention and test snapshot and later binlog records separately.

Read code for enum conversions, soft-delete filters, upserts and real DELETE
statements. Never infer append-only from a creation timestamp or physical key.
Use canonical event types for metrics; ODS mirroring and DWD business dedupe
are separate tasks.
