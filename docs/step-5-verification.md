# Step 5 verification — 2026-10-22

Real local gateway collection and database/API integration are verified.
**Overall milestone acceptance remains pending:** Step 3.3 still lacks backend
host-port isolation and actual rate-limit enforcement; screenshots, feature push
and PR review are pending. This is not a production-readiness certification.

## Repository and prerequisite checks

Initial worktree was clean on `feature/api-traffic-collector`, already at cf9abb8.
Local main and origin/main were also at the verified Step 4 commit. `git fetch
origin` succeeded. The requested branch already existed, so no branch reset,
overwrite or unnecessary new branch was performed. No push to main occurred.

Inspected Compose, .gitignore, README, backend/persistence, empty collector,
gateway/security scripts and milestone documents. WSO2 is independently deployed;
its mounts list was empty. DemoCommerce and WSO2 were running on
sentinelapi-network. PostgreSQL was healthy with no published host port.

Step 3.3 is **not complete**, despite its commit title. DemoCommerce still maps
127.0.0.1:8000 and no actual 429 evidence exists. The earlier context requirement
also remains historically unresolved: current routing is /democommerceapi/1.0.0.
This work preserved that API, its OAuth security, subscription checks and backend.

Step 4 initially reported revision 4061c4c0ee19 at head, with no Alembic drift.
The original fabricated persistence marker remained present in its retained test
database. A subsequent check recorded the preserved marker and new main revision
in prerequisite-verification.json. No main database downgrade or volume reset.

The existing live gateway smoke passed again: no token 401, subscribed token
200, order creation 201, backend missing-order 404, read-back 200 and identical
direct-backend 200. Test tokens stayed in memory and revocation was submitted.
Only the existing smoke test created one in-memory DemoCommerce order.

## Logging and transport actually configured

Official 4.5 API Logs documentation and installed log4j2 properties were inspected.
Supported DevOps GET/PUT changed only DemoCommerceAPI from OFF to BASIC, without
restarting/recreating WSO2. Neither STANDARD nor FULL was enabled. Before/after
evidence: infrastructure/telemetry/logging-configuration.json.

Actual file: /home/wso2carbon/wso2am-4.5.0/repository/logs/api.log. Prefix contains
timestamp, INFO, API_LOG and API name; inline JSON contains verb, correlationId,
apiTo, flow, sourceIP on requests and statusCode on responses. Container log
timezone was UTC. Safe transformed observations are in log-format-observations.json.
No raw source addresses, headers, credentials or payloads were saved there.

The Windows bridge reads bounded chunks and writes sanitized immutable flow
records to a named spool via a network-disabled helper. The collector reads the
spool read-only, writes its checkpoint volume and inserts PostgreSQL batches with
retry/backoff. It never receives Docker socket access or WSO2 credentials.
The bridge was left running as an explicit host development process; it is not
installed as a Windows service. Its restart requirement is documented and stale
source transport causes unhealthy status. See telemetry-architecture.md.

The nullable-measurement migration 71a9c2e16b05 applied successfully and Alembic
found no drift. Only latency_ms/client_identifier nullability changed. Existing
data survived; missing measurements are NULL. Dedicated collector SELECT/INSERT
and monitor SELECT-only roles were provisioned and actual privileges checked.
Neither role has UPDATE/DELETE or elevated role privileges.

## End-to-end proof

`scripts/verify_telemetry_e2e.py` made six controlled requests to the real local
gateway using the existing subscribed application and a short-lived token.
The proof's UTC window is 10:27:22.557773 through 10:27:36.315507.

| Observation | Actual result |
| --- | --- |
| Gateway statuses | 200, 200, 200, 200, 404, 401 |
| Source flow records | 22: REQUEST_IN 6, REQUEST_OUT 5, RESPONSE_IN 5, RESPONSE_OUT 6 |
| Unique completed source identities | 6 |
| Matching PostgreSQL event rows | 6 |
| Matching monitoring events | 6 |
| Overview count | 6, breakdown 200:4 / 401:1 / 404:1 |
| Latency/client identifiers | NULL, verified directly in PostgreSQL |
| Monitoring without token / invalid token | 401 / 401 |
| After collector restart and source-response replay | DB 6, API 6; replay batch checkpointed |

The source UUIDs were matched to deterministic event IDs, then checked directly
in PostgreSQL and through authenticated monitoring. REQUEST/RESPONSE flow entries
were not counted as separate requests. **The gateway-rejected 401 generated BASIC
logs in this deployment.** The backend's failed 404 also generated logs.
The above counts are scoped to the proof window, not the growing database total.
See e2e-verification.json for exact non-secret event IDs and observations.

## Actual PostgreSQL outage and recovery

The deliberate local outage stopped/started only SentinelAPI PostgreSQL. With it
stopped, a real WSO2 request still returned 200, while monitoring returned a safe
503. The new source flow was durably spooled and the collector checkpoint stayed
unchanged. After PostgreSQL restarted, the corresponding event appeared once in
PostgreSQL and monitoring returned 200. Finally restored PostgreSQL and submitted
token revocation. See outage-verification.json.

The latest disposable test database marker also survived an actual later
PostgreSQL restart and a new reader process. test-results.json reports both the
executed suite and this separate fabricated-data persistence check. These test
records are never represented as WSO2 telemetry and remain in a dedicated test DB.

## Executed test results

| Check | Actual result |
| --- | --- |
| Database + collector + monitoring Pytest | 57 passed, 0 failed/errors/skips, 1 warning; console 1.18 s / JUnit 1.179 s |
| Host WSO2 tooling + bridge simulations | 23 passed, 0.049 s |
| Existing DemoCommerce Pytest | 12 passed, 1 warning, 0.64 s |
| Main migration current | 71a9c2e16b05, head |
| Main/disposable Alembic drift checks | No new upgrade operations detected |
| Disposable upgrade twice and downgrade/upgrade | Passed |
| Retained Step 4 marker | Still present |
| Dedicated runtime privilege checks | Passed |
| Real gateway/database/API/replay proof | Passed, six unique requests |
| Real PostgreSQL outage buffering/recovery | Passed, one new event recovered |

The collector suite includes valid BASIC parsing, malformed/truncated JSON,
unknown statuses and missing identifiers, flow correlation/deduplication,
sanitization, idempotent PostgreSQL insertion, bounded outage retry, checkpoint
retention/recovery, API authentication, pagination/filtering, UTC validation,
status breakdowns, stale health and safe database-error responses. Host tests
simulate rename rotation, copy-truncation, incomplete final records and failed
transport acknowledgement. A forced live WSO2 log rotation was not performed.

Warnings: the collector image's Starlette TestClient uses a deprecated AnyIO
BlockingPortal alias. DemoCommerce has its existing Starlette/httpx warning.
Neither warning caused failures. No dependency-upgrade project was started.

Final runtime source/database/API matching, negative gateway authentication,
container health and PostgreSQL port checks are in runtime-status.json. That
snapshot selects the current file's last 64 KiB, not an assumed complete archive.
At 10:51:49 UTC it matched 21 unique completed source records to 21 PostgreSQL
rows and 21 monitoring events. Overview: 200:11, 201:1, 401:6, 404:3. PostgreSQL,
collector, monitoring and DemoCommerce were healthy; WSO2 was running with no
configured Docker healthcheck. Monitoring health returned HTTP 200 and database
port inspection returned no published binding. A later authenticated health
probe and Docker status check also passed. The host suite's final extra case
checks bounded retry when the source-checkpoint lock is briefly busy.
The full Step 3.3 security verifier cannot pass while isolation/429 remain unmet;
passing unit tests and live OAuth checks do not imply rate-limit success.

## Commands and reproducibility

```powershell
git fetch origin
git branch -vv
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker inspect sentinelapi-wso2 --format '{{json .Mounts}}'
docker compose config --quiet
docker compose build persistence collector
docker compose run --rm --no-deps persistence alembic current
docker compose run --rm --no-deps persistence alembic upgrade head
docker compose run --rm --no-deps persistence alembic check
docker compose run --rm --no-deps persistence python -m sentinelapi.db.provision_telemetry_roles
python scripts/configure_api_logs.py --ca-file <trusted-public-cert.pem> --apply
docker compose up -d --no-deps collector monitoring
python scripts/bridge_api_logs.py --follow
python scripts/verify_telemetry_e2e.py --ca-file <trusted-public-cert.pem>
# Deliberate local downtime test; set WSO2_CA_FILE first:
python scripts/verify_telemetry_outage.py
python scripts/collect_telemetry_status.py
python -m unittest discover -s scripts/tests -q
.\demo-services\democommerce\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
git diff --cached --check
```

Full disposable tests were run with a scoped evidence mount:

```powershell
docker compose run --rm --no-deps --volume "${PWD}/infrastructure/telemetry:/evidence" telemetry-tests python -m sentinelapi.db.verify prepare --report /evidence/test-results.json
# After an actual PostgreSQL restart and health recovery:
docker compose run --rm --no-deps --volume "${PWD}/infrastructure/telemetry:/evidence" telemetry-tests python -m sentinelapi.db.verify restart-check --report /evidence/test-results.json
```

Do not run unqualified compose down, delete volumes, or reset the database. The
old security and Step 4 evidence is preserved; this run's gateway precheck has a
separate telemetry artifact. No credentials, token values or raw log files enter Git.

## Problems, limitations and Git

The first end-to-end attempt failed with URLError because this Docker host did
not publish monitoring's port on an internal-only network. Added a separate
monitoring network; its port now binds only 127.0.0.1:8010, while PostgreSQL stays
internal. Re-ran the real proof successfully. Initial inline shell quoting errors
were resolved with dedicated scripts; no log configuration/data was overwritten.

Source IDs must be valid UUIDs; missing ones are rejected rather than guessed.
Identity assumes one RESPONSE_OUT per completion and uses millisecond-resolution
source time. Reused correlation/method/route in the same source millisecond can
collide; different completion timestamps are distinct. No assertion of universal
exactly-once gateway semantics or complete rejection coverage is made. Query
templates and current transport are DemoCommerce-specific. Gateway archive loss
before bridge recovery cannot be reconstructed from missing logs. Host bridge
supervision, production TLS/SSO, retention/restore procedures and clock monitoring
remain operational work. Local HTTP monitoring is loopback-only and authenticated.

Commits are on feature/api-traffic-collector: 090d129 (persistence), 7345a5e
(parser/collector), 48d141f (monitoring/Docker). The final verification commit is
the one introducing this document; resolve it with
`git log -1 --format=%H -- docs/step-5-verification.md`.
No feature push or remote PR yet; approval is required. PR text is prepared in
docs/step-5-pr.md with main as base. Merging requires separate approval.

Computer-use inventory returned no apps/browsers: **0/8 screenshots captured**.
All items in screenshots/05-traffic-collection/README.md remain pending. No image
was generated or reconstructed. No Step 6 detection or final blog was started.

## File inventory

- .dockerignore
- .env.example
- .gitignore
- backend/migrations/versions/71a9c2e16b05_nullable_observed_fields.py
- backend/pytest.ini
- backend/requirements.txt
- backend/sentinelapi/db/models.py
- backend/sentinelapi/db/provision_telemetry_roles.py
- backend/sentinelapi/db/schemas.py
- backend/sentinelapi/db/verify.py
- backend/sentinelapi/db/verify_runtime_privileges.py
- backend/sentinelapi/db/verify_step4_marker.py
- backend/sentinelapi/monitoring/__init__.py
- backend/sentinelapi/monitoring/app.py
- backend/sentinelapi/monitoring/healthcheck.py
- collector/Dockerfile
- collector/tests/test_collector.py
- collector/tests/test_monitoring.py
- collector/traffic_collector/__init__.py
- collector/traffic_collector/checkpoint.py
- collector/traffic_collector/config.py
- collector/traffic_collector/health.py
- collector/traffic_collector/identity.py
- collector/traffic_collector/main.py
- collector/traffic_collector/normalizer.py
- collector/traffic_collector/parser.py
- collector/traffic_collector/reader.py
- collector/traffic_collector/sanitizer.py
- collector/traffic_collector/transport.py
- collector/traffic_collector/verify_db.py
- collector/traffic_collector/writer.py
- compose.yaml
- docs/blog-evidence-tracker.md
- docs/development-journal.md
- docs/step-5-pr.md
- docs/step-5-verification.md
- docs/telemetry-architecture.md
- infrastructure/telemetry/e2e-verification.json
- infrastructure/telemetry/gateway-precheck.json
- infrastructure/telemetry/log-format-observations.json
- infrastructure/telemetry/logging-configuration.json
- infrastructure/telemetry/outage-verification.json
- infrastructure/telemetry/prerequisite-verification.json
- infrastructure/telemetry/runtime-privileges.json
- infrastructure/telemetry/runtime-status.json
- infrastructure/telemetry/test-results.json
- screenshots/05-traffic-collection/README.md
- scripts/bridge_api_logs.py
- scripts/collect_telemetry_status.py
- scripts/configure_api_logs.py
- scripts/inspect_api_logs.py
- scripts/query_monitoring.py
- scripts/tests/test_telemetry_bridge.py
- scripts/verify_telemetry_e2e.py
- scripts/verify_telemetry_outage.py
