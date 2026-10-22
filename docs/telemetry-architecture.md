# WSO2 traffic collection architecture

This implementation collects real local gateway BASIC API Log records. It
does not run threat detection. Step 3.3 isolation and observed throttling remain
incomplete; working telemetry is not a substitute for those security checks.

## Observed WSO2 configuration and records

Used the [WSO2 API Manager 4.5 API Logs documentation](https://apim.docs.wso2.com/en/4.5.0/monitoring/observability/logs/monitoring-api-logs/)
and inspected the installed logger configuration. The supported DevOps API
`GET/PUT /api/am/devops/v0/tenant-logs/carbon.super/apis/{api-id}` was invoked
over certificate-validated HTTPS with existing local administrator credentials
kept in memory. DemoCommerceAPI changed from OFF to BASIC. No other API logging
level was changed; STANDARD/FULL were not enabled. It required no restart.
The safe before/after response is in logging-configuration.json.

Actual file: `/home/wso2carbon/wso2am-4.5.0/repository/logs/api.log`.
Installed PatternLayout: `[%d] %5p {%c} %X{apiName} - %m%ex%n`.
The local container clock was verified UTC. Records have a timestamp prefix,
INFO, `{API_LOG}`, API name, ` - ` and an inline JSON object. Actual fields:

| Flow | Observed BASIC fields |
| --- | --- |
| REQUEST_IN / REQUEST_OUT | sourceIP, verb, correlationId, apiTo, flow |
| RESPONSE_IN / RESPONSE_OUT | verb, correlationId, apiTo, flow, statusCode |

The raw target contains context/version and sometimes a numeric order ID. The
source has no trustworthy duration or stable application/client identity in
these records. Responses are stored with NULL latency/client_identifier, not
estimated latency or a fabricated client. No HMAC key is needed because source
addresses are discarded rather than retained as client identifiers.

In the controlled proof, six requests produced 22 flow records: six REQUEST_IN,
five REQUEST_OUT, five RESPONSE_IN, six RESPONSE_OUT. The missing backend-facing
flows belong to the rejected no-token request. **Gateway-rejected HTTP 401 did
emit BASIC RESPONSE_OUT here.** This observation is specific to this deployment
and does not establish coverage of every gateway rejection or transport failure.
The backend's HTTP 404 also appeared in the logs. Sanitized field observations
are saved in log-format-observations.json; these are text evidence, not screenshots.

## Transport without WSO2 recreation

WSO2 was created independently and has no mounts. No container configuration,
WSO2 filesystem mount, persistent volume or unrelated service was replaced.
Instead, an explicit Windows host bridge reads only the known API-log directory
using bounded `find`, `head`, `stat` and `dd` Docker exec operations. It holds
raw records only in bounded memory and immediately drops addresses, headers,
cookies, payloads and unknown fields. Docker authority stays with the host user;
the collector and transport helper have no Docker socket or WSO2 credentials.

The host invokes a short-lived network-disabled `log-transport` container with
sanitized JSON on stdin. It fsyncs an immutable chunk into the named
gateway-log-spool volume. The collector mounts that volume read-only and its
own checkpoint volume writable. Transport mounts checkpoints read-only and
removes spool chunks only after database-committed acknowledgements. Services
run as UID 10002, with read-only roots, dropped capabilities, no-new-privileges
and bounded tmpfs. No host directory is mounted into the running collector.

Run `python scripts/bridge_api_logs.py --follow` as the host-side process.
It polls every 15 seconds, with a nonblocking exclusive source-checkpoint lock.
Only one process can publish from that checkpoint at a time. Ctrl+C stops the
bridge without deleting state. It is a development host process, not an installed
Windows service. After a host reboot the bridge must be restarted; collector and
monitoring health become unhealthy when bridge freshness exceeds 60 seconds.

Each source read is at most 64 KiB, each sanitized chunk at most 128 KiB / 1000
flows, the spool at most 64 MiB / 4096 chunks, each collector cycle at most 100
chunks and each database insert batch at most 100 events. Spool pressure stops
source-checkpoint advancement. There is no unbounded read-all log operation.

The source checkpoint tracks inode, a prefix fingerprint, offset and observed
size. The bridge scans validated current/rotated filenames, drains readable
archives, detects inode changes, copy-truncation and mid-read rotation, and
retains incomplete final lines until they terminate. It refuses an oversized
unterminated record rather than silently skipping bytes. Missing known unread
archives cause an explicit failure. A 256-file inventory cap requires operator
review rather than silently dropping history. Tests simulate these cases; a
forced rotation of the real WSO2 log was not performed.

The installed logger rolls daily or at 10 MB, with strategy.max=20. This is not
a demonstrated global multi-day retention policy. A bridge offline longer than
gateway retention can lose source history. Existing BASIC gateway files still
contain sourceIP internally; protect those files and set a deliberate gateway
retention policy. Sanitization applies before the separate spool/database.

A future direct shared-log mount would require approval to replace the independent
WSO2 container. Before that action: inventory its full configuration and storage,
back up embedded databases, deployments and secrets to protected storage outside
Git, validate restore, reproduce configuration and ports, and approve a cutover
and rollback plan. That migration is unnecessary for this tested host bridge and
has not been attempted.

## Normalization, identity and recovery

The parser accepts only the configured API and known BASIC flow/method values,
valid UUID correlation IDs, valid timestamps and integer HTTP statuses 100–599.
Malformed/truncated/oversized records are rejected without logging their contents.
No synthetic fallback is used when required data is missing.

Only RESPONSE_OUT creates an event. The other three flows never create separate
requests. A UUIDv5 uses API identity plus correlation UUID, completion timestamp,
method and normalized route. Stable source replay therefore produces stable event
IDs across transport boundaries, process restarts and rotation. Completion time
distinguishes caller reuse of a correlation ID. This design relies on the observed
single RESPONSE_OUT per completed request; independently emitted RESPONSE_OUT
records with different timestamps are treated as different completions. It does
not infer completion for requests that never produce a valid response record.

Known DemoCommerce paths are allowlisted, numeric order IDs become `{order_id}`,
queries/fragments are discarded, and unfamiliar paths become `/{unmapped}`.
Missing correlation/status records are rejected, not replaced with demo records.
Source UUIDs are not stored directly in PostgreSQL; the deterministic event UUID
links proof records across source, database and API.

The database's unique event_id constraint plus ON CONFLICT DO NOTHING makes
repeated inserts idempotent. No existing event is overwritten. Service metadata
must match the configured gateway identity; conflicts fail safely. The writer
commits a transaction before advancing the collector acknowledgement ledger.
It retries transient connection errors four times with 1/2/4-second backoff;
failure retains the chunk and checkpoint. The outer loop keeps trying, reports
unhealthy and emits only a generic error. A crash after DB commit but before
checkpoint persistence causes a harmless replay. Acknowledgements are bounded
to the latest 4096 chunks; old replays remain protected by database uniqueness.

The host source offset advances after durable spool acceptance, not directly
after a DB commit. This is a transport checkpoint; the distinct collector
checkpoint advances only after database persistence. File and directory fsync
and atomic replacement protect the Linux spool/checkpoint boundary. Do not
delete named spool/state volumes to restart the collector.

## Database and authenticated monitoring API

Migration 71a9c2e16b05 changes only latency_ms and client_identifier nullability,
preserving Step 4 data. Its downgrade is restricted to disposable test databases
and refuses to invent values for NULL observations. Existing API/time, timestamp
and status/time indexes support the read paths; no additional index was needed.

The migration owner remains restricted to tooling. New sentinelapi_collector
gets SELECT/INSERT on api_services and traffic_events; sentinelapi_monitor gets
SELECT only and default_transaction_read_only=on. Neither role can create
databases/roles, update or delete events. Passwords and the monitoring token are
random, held in ignored .env/runtime environment and never emitted. Docker
administrators remain trusted because they can inspect container environments.

Monitoring binds only `127.0.0.1:8010`, requires a non-placeholder bearer secret
of at least 32 characters on every route, and disables access logging and public
API docs. Use `scripts/query_monitoring.py` with an environment token or hidden
prompt. It never prints request headers. PostgreSQL stays solely on its private
network. A separate monitoring network is necessary for Docker's loopback port
mapping on this host; PostgreSQL is not attached to that network.

| Route | Behavior |
| --- | --- |
| GET /api/v1/monitoring/overview | Time/API-filtered count, 4xx/5xx counts, status breakdown, nullable mean latency |
| GET /api/v1/monitoring/events | page 1–10000, page_size 1–100, stable timestamp/UUID ordering, total count |
| GET /api/v1/monitoring/apis/{api_id}/stats | Database service UUID, 404 if absent, same time-range statistics |
| GET /api/v1/monitoring/health | Authenticated database and collector/source freshness; 503 if unavailable/stale |

Time filters require timezone-aware instants, use half-open intervals, normalize
to UTC and allow at most 31 days; default is 24 hours. Queries select only
wso2-gateway source rows. Database failures return generic 503 responses and
query-validation failures do not echo submitted values. Sessions close per request
and the engine is disposed at shutdown. Synchronous routes keep database work
out of the async event loop.

## Reproduction and retention

Configure distinct strong secrets in ignored .env using .env.example as a guide.
Never capture expanded Compose config or inspect environment values in screenshots.

```powershell
docker compose config --quiet
docker compose up -d --no-deps --no-recreate --wait postgres
docker compose build persistence collector
docker compose run --rm --no-deps persistence alembic upgrade head
docker compose run --rm --no-deps persistence alembic check
docker compose run --rm --no-deps persistence python -m sentinelapi.db.provision_telemetry_roles
python scripts/configure_api_logs.py --ca-file <trusted-public-cert.pem> --apply
docker compose up -d --no-deps collector monitoring
python scripts/bridge_api_logs.py --follow
# In another terminal, with WSO2_CA_FILE set to the trusted certificate:
python scripts/verify_telemetry_e2e.py
```

Do not run unqualified compose up/down against WSO2 or recreate PostgreSQL.
The controlled outage verifier stops/starts only SentinelAPI PostgreSQL and
restores it in finally; run deliberately when local monitoring downtime is acceptable.
Disposable database tests retain clearly synthetic records, never substitute
them for real gateway traffic, and never downgrade main data.

No automated database retention deletion job is enabled. Establish a reviewed
event/evidence/audit retention policy, backup/restore procedure and encrypted
storage before production. Protect the named volumes; apply cleanup only after
successful ingestion/retention decisions, not as a troubleshooting reset.
