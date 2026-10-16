# Capacity And Temporal Decisions

## Strings Are Byte-Bounded

Measure OCTET_LENGTH, not CHAR_LENGTH alone. MySQL utf8mb4 VARCHAR length counts
characters whereas StarRocks VARCHAR capacity counts bytes; include multibyte
business identifiers and strings when choosing target lengths. TEXT, MEDIUMTEXT
and JSON can exceed a naive VARCHAR(65533), even when recent examples do not.

The October 2026 Advisor source contained payloads around 95 KB and 180 KB,
missed by recent sampling. A too-small message column failed the whole multi-
table sink, leaving other targets empty. Keep strict rejection visible; do not
fix this by raising filter tolerance, truncating JSON or dropping records.

The observed StarRocks 2.5.19 supported VARCHAR up to 1,048,576 bytes. Check the
current version and authoritative docs/code before proposing a larger size.
STRING is an alias, not an unlimited escape hatch. A declared maximum is not
preallocated bytes per row, but larger actual values cost network, memory,
storage and compaction work. A byte batch threshold can still be exceeded by
an individual oversized record and is not a hard process-memory bound.

If valid source values exceed the deployed string limit, stop and design a
compatible alternative: tested JSON storage, normalized/extracted fields plus
an object-store reference/hash/byte length, deliberate row chunking with lifecycle
semantics, or another storage/version choice. Do not call that lossless ODS
without proving recoverability and update/delete behavior. Token context limits
are not bytes and do not imply the application stores the full model context.

## Time Must Be Deliberate

- MySQL TIMESTAMP converts through session time zones; DATETIME carries no zone.
- Connector server-time-zone is not a universal instruction to store UTC in SR.
- Preserve required fractions using the version's supported DATETIME behavior;
  do not invent DATETIME(3)/(6) syntax without checking support.
- Compare source epoch and displayed values with target values for the same IDs,
  once from the snapshot and once from later binlog changes. Label the final
  warehouse convention, whether UTC-normalized or source wall-clock.
- Changing only a timezone option after history was loaded can mix conventions.
  Plan migration/reload explicitly rather than silently reinterpreting history.

## Schema Changes

Source `schema-changes.enabled` and sink `schema_save_mode` are different:
the first controls source schema-change delivery; the second controls startup
treatment of target schema existence. Neither is an assurance that arbitrary
MySQL ALTERs, key changes, renamed tables or Chinese comments propagate.
Do not prescribe a universal source-first or sink-first DDL ordering: test the
connector's actual column mapping and chosen change while controlling ingestion.
