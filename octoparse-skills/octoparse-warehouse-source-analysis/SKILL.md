---
name: octoparse-warehouse-source-analysis
description: Analyze Octoparse business source tables and field meanings from application code plus dbbb production reads. Use for CDC table selection, field dictionaries, keys, mutation/deletion semantics, payload profiling and source prerequisites, not for creating DataHub jobs or changing databases.
---

# Octoparse Warehouse Source Analysis

Use code to explain meaning and production schema to establish what exists.
Do not infer business semantics from column names alone or apply migrations.

## Inspect The Baseline

Record repository branch/commit and whether it is the user's requested baseline.
Read applicable instructions, ORM mappings, migrations and write/query paths.
Typical entry points are EF Core DbContext/row classes and Drizzle schema plus
repository/service code. Read production configuration names without exposing
credentials; sample/UAT addresses are not production discovery evidence.

## Read With dbbb

Read [the inspection reference](references/inspection.md) for query patterns.
Check instance names and experience context/search first. Switch instances
serially, then run bounded queries under that session. Use fully qualified
schema.table names; do not use USE. Parallel reads on the same confirmed
instance are acceptable when their combined production cost is reasonable.

Get live DDL, primary/unique keys, nullability, time types, table size estimates,
actual counts when affordable, binlog settings, timezone and reader grants.
Label TABLE_ROWS as approximate; AUTO_INCREMENT is not COUNT(*).

## Explain Each Candidate

For every candidate table, record inclusion/exclusion rationale and evidence.
For included fields, explain business meaning, type/length/nullability, key or
join role, enum values and units, timestamps and timezone, payload structure,
and sensitive content. State uncertainty instead of inventing comments.

Trace inserts, updates/upserts, deletes and soft deletes. A table without
updated_at is not necessarily append-only. Confirm business IDs versus storage
keys, per-turn versus cumulative token/cost metrics, event time versus persisted
created_at, retries/deduplication, and cache/degraded persistence paths.

## Profile For CDC

Size strings in bytes using OCTET_LENGTH, including serialized JSON. Bound recent
samples, but never present a sampled maximum as a historical maximum. Use indexed
ID chunks or approved off-peak/replica aggregation to check older tails before
claiming the DDL can ingest history. Include full-row and transport overhead.

Check source replication prerequisites and managed-service binlog retention.
SELECT-only accounts do not prove replication capability. GTID is useful but
not a blanket requirement. A zero retention variable on a managed service does
not prove infinite retention.

Estimate request-to-event amplification and QPS x rows/event x bytes x retention.
Look for duplicate event families, global cache keys, check-then-act races and
unbounded queues that affect data quality/volume. This is an analytical risk
assessment, not permission to refactor production code or run a load test.

## Deliver

Output a selected-table list, field dictionary with code/schema references,
key/delete/time/capacity decisions, measured versus sampled evidence, privileges
and unknowns. Preserve the user's final table scope. Save sanitized reusable
knowledge via dbbb experience append/finalize. Do not create Job/DDL side effects
for an analysis-only request.
