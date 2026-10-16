---
name: octoparse-starrocks-cdc-schema
description: Generate or adjust Octoparse CDC target StarRocks CREATE TABLE and ALTER statements from verified source schemas. Use for business-commented ODS DDL, primary-key/delete compatibility, JSON/text capacity and timezone/version checks; does not authorize executing production DDL.
---

# Octoparse StarRocks CDC Schema

Start from live source DDL, field semantics and the user's selected tables.
Use the sibling source-analysis skill if these are missing. Read
[the capacity/time reference](references/capacity-and-time.md) before sizing
large text, JSON or temporal fields.

## Establish Target Constraints

Check `SELECT current_version()` and representative SHOW CREATE TABLE output via
the target dbbb instance. Verify exact names, key model, replicas, partitions,
distribution and supported string/time types. An existing single-replica table
is evidence of a convention, not a guarantee of acceptable durability.

## Generate DDL

- For row mirroring with CDC upsert/delete, use a Primary Key model compatible
  with the deployed sink. Keep source keys, source column names and nullability;
  put target primary-key columns first. Do not add date/session columns to a key
  merely for partitioning, since updates/deletes may no longer locate the row.
- Keep auto-increment IDs as incoming values, not a second generated sequence.
  Do not replace storage IDs with a business unique key without a defined mapping.
- Map enums to sufficient strings, numeric precision to compatible numeric types,
  and JSON/text using measured bytes plus version-supported limits. Distinguish
  raw source fidelity from an intentionally projected analytical schema.
- Use meaningful Chinese column COMMENT values when the user requests them.
  Describe business meaning/units/state values, not source type boilerplate.
- Choose bounded bucket counts from volume/throughput and deployed conventions;
  do not over-partition small ODS tables or copy large workload settings blindly.
- Use IF NOT EXISTS for creation scripts, but explain that it does not repair
  an existing schema. Include separate ALTER statements for existing tables.

Schema capture on the source does not ensure target DDL propagation. Verify
the installed SeaTunnel source, sink, engine and specific DDL support before
enabling schema evolution; manual commented DDL remains a supported choice.

## Execution And Verification

Generate SQL for a read-only user; do not execute DDL through borrowed write
credentials or treat bccc Job creation as a schema-write channel. Execute only
when the user authorizes it and a legitimate write channel is available.

Before a permitted ALTER, assess rewrite/lock/compaction cost, ingestion impact
and reversibility. Preserve column nullability/comments, check current schema
and wait for asynchronous ALTER completion before restarting ingestion. Verify
both information_schema and SHOW ALTER TABLE status where accessible.

Archive the final CREATE definition plus migration SQL under the service docs.
Refresh all affected examples after capacity fixes. Record what was generated,
actually executed and verified, including precision/retention limits and any
unvalidated throughput or deletion behavior.
