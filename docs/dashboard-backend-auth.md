# Dashboard backend authentication repair

Verified locally on 2026-10-24 on branch `fix/dashboard-backend-auth`.

## Cause and deployment decision

Compose's private `.env` is an interpolation source, not an implicit container
`env_file`. The base monitoring service inherited collector/database settings and
mapped only `MONITORING_API_TOKEN`. Reader/analyst/admin tokens were mapped only
by `compose.step6.yaml` to the separate security API on port 8020. Consequently
the combined application on 8010 returned security-authentication-unconfigured.
The dev and production frontend security proxies also targeted that separate API.

The base monitoring service now requires the reader token, preserving its existing
environment mapping, database identity, volumes, health probe and host port. Both
frontend proxies now use the combined monitoring application (host 8010/container
8001). No blanket `env_file`, public token variables or CORS wildcard was added.
Browser requests stay on the frontend origin and proxies forward Bearer headers;
the successful browser requests verify this same-origin arrangement. Direct
cross-origin browser clients are not enabled by this change.

The combined service deliberately receives no analyst/admin tokens. Read-only
deployments do not require write-role secrets. The opt-in Step 6 security service
still requires all three distinct security tokens and remains available on 8020
for explicitly configured write-capable clients. The monitoring DB role retains
its read-only default. New additive SELECT grants cover alert, evidence, rule,
ML and selected audit-history data. `sentinelapi.db.provision_dashboard_reader`
provides the repeatable owner-run grant operation without password changes.

## Actual runtime work and evidence

The initial monitoring and collector containers were unhealthy. The authenticated
health probe reported `collector-stale`, with `source_fresh=false` and a stale
bridge heartbeat. The existing host `scripts/bridge_api_logs.py --follow` process
was resumed after checking for duplicates. Health authentication and freshness
requirements were preserved. The bridge runs as a hidden host process, not an
installed Windows service; stopping it will correctly make health fail again.

Four compromised API tokens were replaced using Python `secrets.token_urlsafe(48)`
directly in ignored `.env`. Values were never emitted or placed in command-line
arguments. Monitoring was rebuilt, then only monitoring and security-api were
recreated with `--no-deps`. No PostgreSQL recreation, volume removal, schema
reset, test records, detector recreation or collector recreation occurred.
The initial immediate post-start exec probe failed; a subsequent probe verified
both required tokens as CONFIGURED. No repair/rotation script was rerun.

Compose validation with base + Step 6 + Step 8 overlays passed using
`config --quiet`. Step 7 ML overlay was inspected but is not deployed; it requires
an approved model directory and digest. No `.env` import or tools profile is
needed for monitoring. The monitoring image remains `sentinelapi/collector:local`.

Database before/after: **99 traffic events, 1 security alert, 16 evidence links,
0 ML windows**. Read-only SQL and live API counts matched. The detector alert
detail and related-events endpoints each confirmed 16 evidence/linked events.
The API service is DemoCommerceAPI, version 1.0.0. There are five detection rules;
Error Rate is enabled, the other four lack trusted telemetry adapters and remain
disabled. No rule or alert status was changed by the rejected PATCH checks.

Live results on `http://localhost:8010`:

| Request | Actual result |
| --- | --- |
| GET monitoring/session, security/session without token | 401 each |
| Same endpoints with invalid token | 401 each |
| GET monitoring/session with monitoring token | 200 |
| GET security/session with reader | 200, reader/security:read |
| Cross-use monitoring/reader credentials | 401 each |
| GET monitoring/health with monitoring token | 200 |
| GET monitoring/overview, events, services | 200 each |
| GET security/alerts, rules, alert detail, linked events, history | 200 each |
| PATCH security/alerts/{actual_id} with reader | 403 |
| PATCH security/rules/{actual_id} with reader | 403 |
| GET ml/model, ml/anomalies | 200; unavailable model, zero anomalies |
| GET ml/evaluation through frontend | 503, explicitly unavailable |
| Authenticated container probe / Docker monitoring health | healthy / healthy |

Live Chromium verification used private `.env` credentials in password fields,
with no traces or header logging. Both session requests returned 200. All six
sections loaded through same-origin proxies; no demo fallback appeared. Storage
remained empty. Last 7 days showed 99 requests, 58 client errors (58.6%), zero
server errors, one active signal and one registered API. Latency and service
heartbeat metrics are unavailable, not synthesized. ML artifact/evaluation is
unconfigured and there are no stored ML windows. Screenshots under
`screenshots/dashboard-auth/1.png` through `6.png` are real live captures, visually
reviewed for credentials; captures never included the credential popup.

The production dashboard was also built and started as a new service on
`http://localhost:8080`. All six live checks passed there through nginx, as well
as on the dev frontend at `http://127.0.0.1:5173`. The final six captures are from
the production dashboard. Compose's orphan notice referred to the intentionally
preserved Step 6 detector/security services; no orphan-removal command was used.

## Executed automated checks

- Backend focused pytest group: **55 passed, 0 failed, 0 skipped** (one existing
  AnyIO deprecation warning). Includes security auth/authorization, dashboard
  HTTP contracts, authenticated health probe and three new deployment tests.
- Frontend Vitest: **37 passed, 0 failed, 0 skipped** (includes a new same-origin
  security credential routing regression).
- Existing Chromium suite: **7 passed, 0 failed, 0 skipped**, 16.8 seconds. These
  are explicitly fixture/mock tests, distinct from the six live screen checks.
- Frontend build, typecheck and lint passed. The initial lint run caught missing
  Node globals in the new live-check script; conversion to ES modules fixed it.
- The first live browser attempt stopped at an ambiguous reader text locator;
  selecting the first matching visible label fixed the verifier, with no app change.
- Windows `npm.ps1` execution policy blocked the initial invocation; `npm.cmd`
  worked without changing execution policy. Docker required its installed full
  path and execution outside the restricted sandbox.
- Existing fixture browser captures initially touched one tracked old screenshot;
  it was restored byte-for-byte from HEAD. The successful repeat used the ignored
  `.runtime` capture directory. Existing evidence is preserved.

Guarded PostgreSQL integration suites were not run against the project DB; live
data validation used read-only queries. No claim of a full repository test run.

## Credential incident and coordinated database rotation

Before API rotation, 401 reachable Git blobs and current tracked files were
compared with the current private credential bytes without emitting values:
zero matches; `.env` was not tracked. This is not proof that arbitrary earlier
passwords, screenshots or unreachable history never contained secrets.
No private `.env`, dumps, runtime checkpoints or test traces belong in commits.

**Database passwords were not rotated in this repair and must still be treated
as compromised.** Rotation status was not independently established. Do not just
edit `POSTGRES_PASSWORD`: initialization variables do not alter existing roles.
Use this maintenance procedure to avoid losing owner access:

1. Inventory roles and every consumer: owner (`POSTGRES_PASSWORD`: PostgreSQL
   initialization metadata and owner tools), collector (`COLLECTOR_DB_PASSWORD`),
   monitor (`MONITORING_DB_PASSWORD`), detector (`DETECTOR_DB_PASSWORD`) and
   security API (`SECURITY_DB_PASSWORD`). Review local overrides and unattended
   tasks. Obtain explicit approval before recreating PostgreSQL, even with the
   existing named volume. Never run `down -v` or delete persistent services.
2. Verify a private tested backup and retain an authenticated owner connection
   through the whole operation. Store recovery credentials in restricted private
   storage outside Git. Pause bridge/detector and stop only DB-dependent runtime
   services during the maintenance window; preserve spool/checkpoints.
3. Generate independent replacement passwords with `secrets.token_urlsafe(48)`
   into a restricted ignored candidate configuration; never display values or
   pass them as command arguments. Keep the active `.env` intact until ready.
4. Using the retained owner connection, validate all existing roles and change
   all five role passwords in one transaction using `psycopg.sql.Identifier`
   and `psycopg.sql.Literal`, with no SQL echo/exception logging. Confirm DB
   statement/audit logging will not retain secret-bearing SQL. Validate candidate
   names/password lengths before any mutation. Commit the transaction only after
   all statements succeed; otherwise roll back. Existing telemetry provisioning
   rotates collector/monitor and detection provisioning has an explicit
   `--rotate-existing-passwords` option, but neither alone rotates all five.
5. Atomically install the candidate `.env`, clear stale process-environment
   overrides, run Compose `config --quiet`, then recreate collector, monitoring,
   detector and security-api with their original overlays and `--no-deps`.
   Synchronize the PostgreSQL container's stale environment metadata in the
   separately approved recreation, retaining its exact named volume. A database
   role change itself needs no PostgreSQL restart. Do not accidentally enable
   the optional ML overlay while doing this.
6. Verify new owner access over password-authenticated TCP in a second connection
   before releasing the retained connection. Verify every runtime role, grants,
   new health/session checks, evidence counts and checkpoint progression; resume
   the bridge. Confirm old passwords fail over TCP. If a step fails, keep the
   retained owner connection and either repair dependents or restore all old
   role passwords and private configuration consistently; never reset the DB.
7. Retire old credentials, invalidate private recovery copies when no longer
   needed, and reconnect the dashboard with the replacement API tokens privately.
   Do not paste credentials into chat. API tokens were already rotated here;
   previously supplied browser credentials must be replaced from local `.env`.

## Repeat verification (Windows PowerShell 5.1)

From the repository root, these commands do not print secret values:

```powershell
$docker = "$env:LOCALAPPDATA\Programs\DockerDesktop\resources\bin\docker.exe"
& $docker compose -f compose.yaml -f compose.step6.yaml -f compose.step8.yaml config --quiet
& .\.venv-step6\Scripts\python.exe scripts/verify_dashboard_auth.py --docker $docker
$env:PYTHONPATH = 'backend;collector'
& .\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_security_api.py backend/tests/test_dashboard_api.py backend/tests/test_runtime_startup.py backend/tests/test_dashboard_auth_config.py -q
Push-Location frontend
npm.cmd test -- --reporter=dot
npm.cmd run lint
npm.cmd run typecheck
npm.cmd run build
$env:SENTINEL_SCREENSHOT_DIR = '../.runtime/dashboard-auth/fixture-captures'
npm.cmd run test:browser -- --reporter=line
Pop-Location
# Requires the local frontend server; uses no request traces.
node frontend/scripts/verify-live.mjs
# To test a running production dashboard instead:
$env:SENTINEL_FRONTEND_ORIGIN = 'http://localhost:8080'
node frontend/scripts/verify-live.mjs
Remove-Item Env:SENTINEL_FRONTEND_ORIGIN
```

If no dev frontend is running, start `npm.cmd run dev` from `frontend` in another
PowerShell window. If the bridge stops, ensure no duplicate bridge process exists,
add the Docker directory to PATH and resume
`.\.venv-step6\Scripts\python.exe scripts/bridge_api_logs.py --follow`.

For another already-migrated deployment that needs the additive reader grants:

```powershell
& $docker compose build persistence
& $docker compose run --rm --no-deps persistence python -m sentinelapi.db.provision_dashboard_reader
```

Do not rerun the private repair script: it would rotate API tokens again.
The commit associated with this repair can be resolved using
`git log -1 --format=%H -- docs/dashboard-backend-auth.md`.
