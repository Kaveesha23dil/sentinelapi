# Step 4 verification — 2026-10-22

Database foundation implemented and verified locally. **Step 3.3 is still
incomplete**; this does not certify gateway isolation, rate limiting or real
telemetry ingestion. No Step 5 code, dashboard or final blog was written.

## Precheck and existing behavior

Started with a clean worktree at `dc6df2f`. Inspected actual Compose, README,
ignore rules, empty backend/collector folders, DemoCommerce and WSO2 scripts,
security architecture, verification evidence and journal. Compose previously
contained only DemoCommerce; WSO2 is separately deployed. An unrelated healthy
database container already publishes 5432; it was left untouched.

Docker inspection confirmed WSO2 and healthy DemoCommerce on sentinelapi-network.
Live Publisher found PUBLISHED DemoCommerceAPI, APPROVED revision, OAuth2 and six
secured operations. Authenticated gateway smoke was rerun successfully:

| Live gateway check | Actual HTTP result |
| --- | --- |
| Orders without token | 401 |
| Orders with subscribed token | 200 |
| Create demo order | 201 |
| Missing demo order | 404, expected backend response |
| Read created order | 200, matches creation |
| Direct backend read-back | 200, matches gateway |

The existing route is `/democommerceapi/1.0.0`; the earlier context question is
unresolved. Host port 8000 is still published. No actual 429 was recorded in the
repository and this run did not configure or exercise a rate policy. Step 3.3
is therefore not complete despite the prior commit title. Gateway evidence for
this precheck is saved separately in infrastructure/database/gateway-precheck.json.
The token remained memory-only, lifetime 300 seconds, revocation submitted.
One demo in-memory order was created by the existing smoke script.

## PostgreSQL and migrations

- PostgreSQL 17.11-bookworm: healthy, named volume mounted, internal database
  network only. Port inspection returned `{"5432/tcp":null}`: no host binding.
- Existing WSO2/DemoCommerce network and configuration preserved; no volumes or
  persistent containers removed/recreated. Only new PostgreSQL was restarted.
- Initial Alembic revision generated against the new empty database, reviewed for
  all columns, nullability, checks, FK actions and dependency order, then applied.
- Revision `4061c4c0ee19`: upgrade head exit 0; repeat upgrade head exit 0;
  `alembic check`: `No new upgrade operations detected.`
- Seven project tables plus alembic_version exist: api_services, traffic_events,
  traffic_aggregates, detection_rules, security_alerts, alert_evidence, audit_logs.
- Final main-database inspection confirmed PostgreSQL 17.11, UTC timezone,
  revision 4061c4c0ee19 and zero traffic_events. Actual project indexes are saved
  in infrastructure/database/project-schema.json. Docker inspection confirmed
  the named volume mount and an internal network containing only PostgreSQL
  after the ephemeral tools runner exited.
- Downgrade/base and upgrade tested only in a newly created disposable test DB.
  Downgrade now explicitly refuses non-test databases. Main database not downgraded.
- Main monitoring tables contain no claimed telemetry. Fabricated event examples
  and persistence markers are stored only in named sentinelapi_test_* databases.

## Actual automated results

| Suite/check | Result |
| --- | --- |
| Database/validation Pytest, final script | 26 passed, 0 failed/errors/skipped; console 1.06 s, JUnit 1.065 s |
| Existing DemoCommerce Pytest | 12 passed, 1 Starlette/httpx deprecation warning, 0.66 s |
| Existing WSO2 tooling unittest | 18 passed; synthetic guard tests |
| Existing live gateway smoke | Six checks passed, statuses above |
| Docker Compose config --quiet | Passed |
| Alembic schema comparison | No drift |
| Disposable migration cycle | Passed |
| New engine/process reads committed data | Passed |
| PostgreSQL restart then marker lookup | Passed |

The 26 database tests include 15 validation/metadata/config cases and 11 real
PostgreSQL cases: authenticated connection and UTC timezone, indexes, event
deduplication/conflict handling, API/time filtering, evidence relationships,
cross-API evidence rejection, status/latency/FK constraints, aggregates/audit
JSONB, fresh-engine persistence, transaction rollback and migration consistency.
Normal tests use rollback isolation. Persistence checks deliberately commit only
fabricated demo-test rows in the dedicated test database.

Final evidence at 07:32:44 UTC, restart confirmed 07:32:52 UTC:
`infrastructure/database/database-verification.json` records database name,
marker UUID, inspected tables/indexes, JUnit summary and actual restart lookup.
No record originated from WSO2 telemetry. Reports exclude credentials and headers.
Earlier test databases are retained, not wiped, for inspection.

## Commands actually used

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker network inspect sentinelapi-network --format '{{range .Containers}}{{.Name}} {{end}}'
docker compose config --quiet
docker compose up -d --no-deps postgres
docker compose build persistence
docker compose run --rm --no-deps --volume "${PWD}/backend:/app" persistence alembic revision --autogenerate -m "initial monitoring schema"
docker compose run --rm --no-deps --volume "${PWD}/backend:/app" persistence alembic upgrade head
# Repeated upgrade head, then alembic check.
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/verify_database.ps1
docker inspect sentinelapi-postgres --format '{{json .NetworkSettings.Ports}}'
.\demo-services\democommerce\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
python -m unittest discover -s scripts/tests -q
python scripts/integrate_wso2.py --from-container --ca-file <temporary-public-cert.pem> --test-existing
git diff --check
```

`verify_database.ps1` supplies runtime environment securely through Compose and
mounts only code/evidence. It runs migrations twice, drift checks, disposable
migration/test preparation, postgres restart and marker lookup in a new process.
See database-architecture.md for deployment and migration rationale.

## Problems and fixes

Sandbox PATH lacked Docker/Python; approved host commands provided access. No
global installation or WSO2 configuration change was needed. Generated a random
local database password in ignored .env without printing it; the existing
environment file is never overwritten by setup. No credentials enter Git.
The first 26-test run passed with an Alembic path_separator deprecation warning;
adding `path_separator = os` eliminated it on the final run. The existing
DemoCommerce Starlette warning remains unchanged. Image downloads/builds succeeded.

## Screenshots, Git and limitations

Computer-use inventory returned no apps/browsers: **0/7 images captured**.
All exact manual captures are pending in screenshots/04-database/README.md,
including GitHub evidence until an approved push. No generated screenshot exists.

The associated checkpoint is the commit introducing this document, with subject
`feat: add PostgreSQL persistence for security events`. Resolve its hash using
`git log -1 --format=%H -- docs/step-4-verification.md`. A local checkpoint does
not imply pushed GitHub status or completion of Step 3.3. Push requires approval.

Limitations: bootstrap role is privileged; no production runtime role, backups,
restore drill, encryption/TLS configuration, retention worker or immutable audit
enforcement. Rule updated_at relies on ORM updates, not a SQL trigger. Raw SQL can
bypass DTO privacy/cross-API evidence guards. Test databases are retained and may
accumulate. Pseudonymization must be implemented before actual event ingestion.

Before Step 5: finish the Step 3.3 isolation and observed-429 checks; define the
actual WSO2 telemetry source/transport and normalized event contract; implement
redaction/HMAC key handling, least-privilege ingestion credentials, idempotent
retry/backpressure and retention policy. No collector has been started here.
