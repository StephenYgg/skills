---
name: octoparse-cdc-onboarding
description: Plan or implement an Octoparse business database CDC pipeline into StarRocks using project code, dbbb, SeaTunnel and bccc DataHub. Use for end-to-end onboarding of new source tables; for a standalone schema, administration or diagnosis request use the corresponding specialized skill.
---

# Octoparse CDC Onboarding

Coordinate only the stages the user requested. Analysis, DDL generation,
production DDL execution, Job creation, scheduling, and triggering are separate
actions. Never infer permission to start, stop, clear data, reset CDC state,
change grants, commit, or push from permission to prepare a pipeline.

## Discover

1. Identify the source project, dbbb source/target instance names, and DataHub
   environment. Check `bccc info --json` before any administration.
2. Locate rather than assume repositories. Common local checkouts live under
   `~/Development/bzy-server/`; warehouse documentation belongs to the
   `octopus.datahub.service` checkout.
3. If asked to update master, inspect dirty state/remotes/divergence first.
   Fetch, then fast-forward only when safe. Do not merge/rebase divergent work
   or switch away from dirty work just to inspect a baseline.
4. Read existing dbbb experience before querying. Use fully qualified table
   names. Serialize instance switches because dbbb has a shared local session.

## Work Through The Stages

- For table selection and field semantics, use the sibling
  [source-analysis skill](../octoparse-warehouse-source-analysis/SKILL.md).
  User-selected scope wins over an earlier recommended list; empty business
  tables can be worth including, while nonempty internal tables can be excluded.
- For target models, comments and column capacity, use the sibling
  [schema skill](../octoparse-starrocks-cdc-schema/SKILL.md).
  dbbb is read-only: output DDL for the user when no authorized write channel
  exists. Do not reuse credentials to bypass its restrictions.
- For Job/Plan/Step creation or changes, use the sibling
  [administration skill](../octoparse-datahub-job-admin/SKILL.md).
  Plan creation may immediately register scheduling. If only preparation was
  authorized, keep the plan unscheduled using the verified deployment mechanism.
- For acceptance and troubleshooting, use the sibling
  [verification skill](../octoparse-cdc-verify-repair/SKILL.md).
  A streaming Job should remain RUNNING after its historical snapshot catches up.

Read [the sanitized cases](references/agenthub-advisor.md) when one of these
services is involved or when checking payload sizing and analytical semantics.
They are historical evidence, not live schema/configuration authority.

## Bound Production Impact

Prefer one explicit source whitelist per suitable business workload, not one
job per request or an unbounded table wildcard. Split jobs when throughput,
failure isolation or data handling policies justify it. Bound parallel readers,
connection pools, bytes/rows per second, sink batch bytes, retries and monitoring.
Do not promise end-to-end exactly-once or global single-flight without evidence.

## Archive And Close

Keep business-commented DDL, sanitized SeaTunnel configurations and Plan
definitions in the service repository's `docs/`. Record scope, versions,
timezone/storage convention, limits, actual validation and remaining gaps.
Refresh these artifacts after a fix; an old CREATE TABLE with IF NOT EXISTS
will not alter an already-created table.

Keep credentials and raw user content out of Git. Save reusable business
findings with dbbb experience append/finalize, not credentials or stale status
claims. End with created/changed IDs, validation evidence and what remains
unexecuted. Do not call a partially provisioned or partially copied pipeline done.
