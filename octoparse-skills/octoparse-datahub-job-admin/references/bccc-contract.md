# bccc DataHub Contract

Recorded from the locally installed CLI during the integration; inspect --help
and current service DTOs before relying on changed versions.

## Query And Create

```bash
bccc info --json
bccc datahub job list --keyword KEYWORD --current 1 --page-size 100 --json
bccc datahub job get JOB_ID --json
bccc datahub plan list --keyword KEYWORD --current 1 --page-size 100 --json
bccc datahub plan get PLAN_ID --json
bccc datahub step get PLAN_ID JOB_ID --json
bccc datahub job create --file /protected/job.json --yes --json
bccc datahub plan create --file /protected/plan.json --yes --json
bccc datahub step create --file /protected/step.json --yes --json
```

Capture definition commands without echoing secrets. Paginate until total/pages
are exhausted. A get 404 may mean absent, but never treat a timeout/auth error
as proof of absence. Job ID is a string; Plan and Step IDs are GUIDs. SeaTunnel
runtime IDs are Int64 strings, not JavaScript Number values.

Job body:

```json
{
  "id": "sync-service-cdc",
  "name": "Service CDC to StarRocks",
  "description": "Synchronize the explicitly selected business tables.",
  "jobType": 0,
  "jobConfig": "JSON_SERIALIZED_SEATUNNEL_CONFIG",
  "jobParameters": []
}
```

jobConfig is a string, not an object. Current jobType=0 means SeaTunnel.
Job id/name max length is 64, description max length 128. Parameter definitions
contain name/description; do not drop them during a narrow description edit.

Plan body:

```json
{
  "name": "sync-service-cdc-plan",
  "description": "Long-running CDC; scheduler settings require explicit activation.",
  "cron": "0 0 31 2 *",
  "runType": 2
}
```

runType: OnlyOnce=0, Repeatable=1, LongRunning=2. Current Plan create/update does
not persist jobPlanSteps. Plan creation generates its ID; persist that result
before attempting Step creation.

Step body (supply the returned plan ID):

```json
{
  "jobPlanId": "PLAN_GUID",
  "jobId": "sync-service-cdc",
  "step": 1,
  "runAfterSucceed": false,
  "maxRetry": 3,
  "checkIntervalMinutes": 5,
  "parameterValues": []
}
```

Parameter values may contain value/expression. Preserve them; do not evaluate
expressions in a client-side update. Recorded LongRunning plans allow one Step.
These retry/interval values are examples, not mandatory defaults.

## Complete Replacements

```bash
bccc datahub job update JOB_ID --file /protected/complete-job.json --yes --json
bccc datahub plan update PLAN_ID --file /protected/complete-plan.json --yes --json
bccc datahub step update STEP_ID --file /protected/complete-step.json --yes --json
```

Use accepted request fields rather than feeding the entire GET DTO back to PUT.
After a Plan update, compare the original/persisted steps as well as plan fields.

## Execution And Diagnostics

```bash
bccc datahub lot list --plan-id PLAN_ID --page-size 5 --json
bccc datahub lot steps LOT_ID --json
bccc datahub lot logs LOT_ID JOB_STEP_ID --json
bccc datahub seatunnel status RUNTIME_JOB_ID --json
bccc datahub seatunnel running --json
```

Empty logs are not proof of success. Fetch the exact runtime ID from the Step,
then inspect status even when it is absent from the running list.

Only when separately authorized, choose one execution entry point:

```bash
bccc datahub plan start PLAN_ID --yes --json
# OR trigger the registered recurring job, not both:
bccc datahub plan trigger PLAN_ID --yes --json
```

The name of a Hangfire recurring job may depend on the Plan name. A name change
is not a description change and may leave stale scheduling in some deployments.
