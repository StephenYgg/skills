# Sanitized AgentHub And Advisor Cases

Observed during an October 2026 integration. Re-query current versions, grants,
schemas and runtime state. Do not copy previous credentials, endpoints, Job IDs
or dates into a new deployment.

## AgentHub

Code: `octopus-agent-hub`, EF Core/MySQL entity mappings and migrations.
Observed database: `agent_hub`.

| Business table | Source key | Meaning |
| --- | --- | --- |
| agent_task | TaskId | Task/enterprise/owner, current generation and delivery state, soft deletion |
| agent_task_turn | Id | User turn, Prompt, model/agent, dispatch status and times |
| billing_transaction | Id | Usage/charge ledger, tokens by kind, credits, wallet and charge state |

Orleans membership/reminders and migration history are runtime/internal data,
not automatically part of the analytical whitelist. TaskId plus UsageSeq is a
business uniqueness rule for billing, not a reason to replace the source Id key.
AgentHub stores application UTC instants in DATETIME(6); that is an application
convention, not timezone metadata in the MySQL type.

## Advisor

Code: `octoparse_ai_advisor`, TypeScript/Hono/LangGraph, Drizzle schemas and
`SessionRepository`. Observed database: `octoparse_advisor`.

| Business table | Source key | Meaning |
| --- | --- | --- |
| advisor_sessions | id | User/locale/status, turn count, metadata including cumulative tokens |
| advisor_messages | id | message_id/session_id/turn_id, role, text and structured response |
| advisor_session_events | id | event_type plus JSON business/analytics payload |
| advisor_feedback | id | Current up/down/comment for message_id, updateable and physically deletable |

The user selected only these four. advisor_collection_jobs was empty but a valid
optional business table; advisor_graph_checkpoints was empty, reserved, and had
only a composite unique key. Do not silently add either table to this scope.

Advisor used TIMESTAMP(3) with a +08:00 source session. Target values were
validated against source wall-clock values and millisecond precision. Do not
describe that as UTC-normalized warehouse storage without a deliberate conversion
and snapshot/binlog verification.

## What Failed And Why

Recent 1,000-row samples understated historical JSON sizes. A target
VARCHAR(65533) rejected an older message payload, causing the entire multi-table
Job to fail while some target tables were empty and others partially populated.
Exact SeaTunnel status contained `column=payload, capacity=65533`.

Full historical profiling found message payloads up to 94,675 bytes and event
payloads up to 180,329 bytes. The user expanded message content to 262,144 bytes
and both payload columns to 1,048,576 bytes. The observed StarRocks 2.5.19 had a
1 MiB VARCHAR limit. STRING was not an unlimited workaround. These are version-
specific observations; check the current deployment before proposing SQL.

After retrying, monitoring showed feedback then messages then events then
sessions filling at different times. Only after four-table source/target counts,
ID ranges/sums and latest timestamps matched, and post-start records arrived,
was historical catch-up accepted. No synthetic production writes were needed.

## Analytical Semantics

- message_sent and advisor_message_sent can describe the same user action.
- llm_tokens_used and advisor_run_completed can both carry token metrics.
- Current feedback rows and historical feedback_submitted/message_rated events
  are different facts. An upsert need not change created_at; a removal emits DELETE.
- Assistant content can include expanded audit text; payload.text may be the
  displayed reply. Preserve this distinction when defining metrics or samples.
- Redis-backed degraded responses do not guarantee every UI-visible state made
  it into MySQL. CDC faithfully mirroring MySQL does not fix upstream omissions.
- Event payload.event_id may be useful for DWD deduplication; preserve raw ODS
  source rows by their actual primary key.

## Scheduling

Observed peer LongRunning plans used `*/30 * * * *`, meaning scheduler-local
00/30 minute checks, not daily snapshots. Preparation used Hangfire Cron.Never
(`0 0 31 2 *`) after verifying deployment behavior. These are local conventions,
not universal defaults. The plan admission check/create was not atomic, and
failure handlers could re-enqueue despite a finite Step retry count.
