# Step 6 detection architecture

Status: implementation with offline verification; live deployment and acceptance pending.
Base: Step 5 merge `3c2be39` on `feature/rule-based-threat-detection`.
No gateway, persistent container, volume or existing records were changed.

## Evidence boundary

Inspected collector parser, normalizer, schema, Step 5 reports and BASIC field observations.
The prior Step 5 real proof matches six gateway completions to six persisted events;
it is historical evidence, not a new Step 6 ingestion check. Current runtime could
not be inspected: Docker is unavailable in this execution environment.

Stored gateway fields are event UUID, API, completion timestamp, method, sanitized
route template, HTTP status and source. `client_identifier` and `latency_ms` are
NULL. sourceIP is deliberately discarded and is not a verified application identity.
`/{unmapped}` collapses paths and does not prove an unknown gateway resource.
An observed 401 is an HTTP error, not confirmed authentication-attack evidence.
The inspected BASIC deployment emitted a no-token 401, but that does not prove
complete gateway-rejection coverage. No route/authentication classifier was added.

## Processing and persistence

`sentinelapi.detection.rules` contains pure, deterministic strategies and strict
configuration validation. The live adapter constructs observations from actual
`wso2-gateway` rows, without inventing missing fields. Only API-level error-rate
detection is live-eligible. The other strategies are independently testable with
explicit synthetic observations and remain disabled. Enabling them via the API
returns 409; direct database enablement is skipped with a sanitized warning.

Run the worker as a separate process with `python -m sentinelapi.detection.worker`.
It runs synchronous database work in an asyncio thread, outside the WSO2 request
path. Failure rolls back the cycle, logs a fixed safe message and retries in five
seconds. It cannot change gateway responses or call the gateway.

Each cycle advances at most 60 event-time seconds, stays 120 seconds behind the
current time, and re-evaluates the previous 120 seconds for late events. The
indexed time query adds at most 300 seconds of aggregation history. It retrieves
at most 10,001 rows and refuses a window exceeding 10,000, rolling back without
advancing the checkpoint. This is bounded in memory/time range, not a guarantee
of fixed CPU latency: evaluation at each distinct completion time can be quadratic
inside the cap. Busy deployments should benchmark and replace this with rolling
per-API deques/aggregates before raising the cap. Capacity failures need operator
attention; the worker does not silently truncate evidence or skip events.

Windows use `(end - duration, end]` and are evaluated at observed completion times.
Thus arbitrary minute boundaries do not hide a threshold crossing. Error-rate
aggregation groups by API; client-specific strategies group by verified client
and API. Event UUIDs deduplicate inputs; conflicting duplicates fail validation.
Queries select completed gateway records only; multiple BASIC flow records do
not become multiple requests. Evidence is capped at 100 deterministic event UUIDs.
For error-rate alerts these are error-event references; the denominator is retained
as request_count. Late discoveries never rewrite an earlier alert's frozen evidence.

A transaction-scoped PostgreSQL advisory lock permits one worker at a time.
Seeding is insert-only and never overrides configured rules. Alerts, evidence and
checkpoint advancement commit atomically. Checkpoint state survives process restarts.
The first run bootstraps a bounded recent interval (initial watermark = now minus
420 seconds, with another 120-second replay overlap). It does not scan all history.
Arrival lateness beyond the replay horizon is not covered. Historical replay and
baseline materialization are remaining operational work; do not reset production
checkpoints casually or claim complete historical coverage.

## Incidents, lifecycle and risk

An additive Alembic revision extends existing security_alerts and creates
detection_checkpoints. Nullable metadata preserves legacy demonstration alerts.
No existing alerts are deleted. The unique SHA-256 incident fingerprint uses
rule UUID, version, API, target and UTC epoch bucket of the rule's window duration.
Repeated sliding-window crossings in one bucket retain the first alert/evidence.
Sustained incidents may produce one alert in each neighboring bucket. A rule
configuration version change creates a distinct incident namespace.

Alerts retain rule/version, API, severity, timestamps, window, measured value,
threshold and explanation. Medium severity maps to a fixed policy score of 50;
this is prioritization, not a calibrated probability or ML output.
Lifecycle: open -> investigating/resolved/dismissed; investigating -> resolved/dismissed.
Terminal states cannot reopen; idempotent updates return the existing state.

## Management API and deployment

The six requested routes live under `/api/v1/security`. Lists use bounded pagination;
alerts and summary support aware timestamp, API, rule, status and severity filters.
Default range is 24 hours, maximum 31 days. Evidence detail exposes only IDs and
validated count fields, never arbitrary JSON, request bodies, headers or addresses.
Validation errors do not echo input. Older demo descriptions are replaced in API
responses by an explicit legacy label, without changing stored records.

Separate deployment secrets map to reader, analyst and admin service principals.
All can read; analyst/admin can change alert status; admin alone can change rules.
Tokens must be distinct, at least 32 characters, and non-placeholder. Missing auth
configuration returns 503; invalid tokens 401; insufficient roles 403. No token is
accepted as a client identity. Audit records use the service role, old/new status
or validated old/new rule config. Individual human attribution/OIDC is future work.
Mutation rows lock through commit; audit writes and updates share a transaction.

`compose.step6.yaml` is an explicit opt-in overlay defining NEW detector/security-api
services. It leaves existing services intact and uses a distinct image tag. The API
binds only 127.0.0.1:8020. No runtime deployment was performed. Before first use:

1. Make a protected database backup and confirm PostgreSQL/collector are healthy.
2. Build the new image with the overlay. Run Alembic upgrade/check with the existing
   owner tools against a disposable test database first, then upgrade the project DB.
3. Supply private DETECTOR_DB_PASSWORD and SECURITY_DB_PASSWORD (32+ characters)
   and distinct SECURITY_READER_TOKEN / SECURITY_ANALYST_TOKEN / SECURITY_ADMIN_TOKEN.
   Extend the owner tools environment explicitly; these values must not enter Git.
4. Run `python -m sentinelapi.detection.provision` with owner connectivity and those
   two passwords. Review actual grants; never use owner credentials for runtime.
   This explicit provisioning command sets passwords for its two named roles.
5. Start ONLY new services with
   `docker compose -f compose.yaml -f compose.step6.yaml up -d --no-deps detector security-api`.
   Do not run broad `up`, `down`, `down -v` or force recreation of persistent services.

Scoped detector grants: SELECT on events/APIs/rules/alerts/evidence/checkpoint,
INSERT on rules/alerts/evidence/checkpoint, UPDATE on checkpoint. Security API:
SELECT alerts/evidence/rules, UPDATE alert status and rule config/enabled/timestamp,
INSERT audit only. Existing monitoring/collector roles are unchanged. Provisioning,
Compose validation and real permission checks still require a Docker-equipped host.

## Limitations and next milestone

Error ratios also rise during backend failures, deployments or intended 404 tests;
an alert is an explainable observation, not proof of malicious intent. Gateway
quotas may prevent a downstream threshold being reached. Rate limiting enforces
request admission; this worker observes completed telemetry afterward. Future ML
would learn statistical patterns and requires verified identities, reliable data,
baselines and labeled evaluation. No ML or dashboard work is included here.
