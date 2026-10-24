# Portfolio release verification

Source baseline `891a269`; branch `docs/portfolio-release-evidence`; executed 2026-10-24. This is a fresh verification record, separate from earlier milestone counts. The only test harness change adds `SENTINEL_SCREENSHOT_DIR` so browser captures do not overwrite evidence. Application code, running containers, WSO2 settings, project telemetry and production checkpoints were not changed during this release audit.

## Actual test results

| Group | Passed | Failed | Skipped | Errors | Scope |
|---|---:|---:|---:|---:|---|
| Backend/tools/DemoCommerce host | 155 + 4 subtests | 0 | 0 | 0 | Unit, contracts, synthetic model/feature/inference and service tests |
| Guarded PostgreSQL | 21 | 0 | 0 | 0 | Actual persistence, detection, seeding, migration and dashboard SQL checks in separate test DB |
| Linux collector/monitoring | 31 | 0 | 0 | 0 | 20 collector fixtures + 11 DB-backed monitoring/collector checks |
| Direct Windows collector | 18 | **2** | 0 | 0 | Existing POSIX directory-fsync portability failures |
| Frontend unit | 36 | 0 | 0 | 0 | Four test files |
| Chromium | 7 | 0 | 0 | 0 | Actual demo rendering/accessibility plus explicit mocked API workflows |
| Lint/typecheck/production build | Passed | — | — | — | Lint/typecheck rerun after screenshot-directory option |
| ML/PostgreSQL collection | — | — | — | — | Two collected, zero executed; not runtime skips |

Do not sum overlapping migration/collector cases across groups/platforms. Host JUnit contains 159 cases because four passing subtests are separate XML cases; console count is 155 plus four subtests. No failing assertion was removed. The Windows failures are `test_checkpoint_recovery_and_transport_gc` and `test_checkpoint_does_not_advance_on_write_failure`, both from `os.O_DIRECTORY` in transport publishing. Their fix is on unmerged Step 9, not quietly included in this documentation branch. The deployed Windows-host bridge uses Linux transport and is working, which does not erase the direct Windows fixture failures.

Pre-existing AnyIO deprecation warnings remain. Browser emitted a color-environment warning; build printed plugin timing information. Neither is represented as application performance or a passing security audit. [Sanitized counts](../infrastructure/portfolio-release/test-summary.json). Raw XML, browser reports/traces and host paths stay ignored under `.runtime/portfolio-release/` or frontend output directories.

## Exact executed commands

From repository root:

```powershell
$env:PYTHONPATH='backend;collector;scripts'
.\.venv-step6\Scripts\python.exe -m pytest backend/tests scripts/tests demo-services/democommerce/tests --ignore=backend/tests/test_postgres.py --ignore=backend/tests/test_detection_postgres.py --ignore=backend/tests/test_ml_postgres.py --ignore=backend/tests/test_dashboard_postgres.py -q --junitxml=.runtime/portfolio-release/host-tests.xml
.\.venv-step6\Scripts\python.exe -m pytest collector/tests/test_collector.py -q --junitxml=.runtime/portfolio-release/windows-collector.xml
.\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_ml_postgres.py --collect-only -q
```

Docker tests reused the existing **separate guarded** `sentinelapi_test_detection_runtime_20261024` database. No project database migration/reset/downgrade or persistent-container restart was performed:

```powershell
docker compose -f compose.yaml -f compose.step6.yaml --profile tools run --rm --no-deps -e POSTGRES_DB=sentinelapi_test_detection_runtime_20261024 -v "${PWD}/.runtime/portfolio-release:/results" persistence python -m pytest -p no:cacheprovider tests/test_postgres.py tests/test_detection_postgres.py tests/test_detection_migration.py tests/test_dashboard_postgres.py -q --junitxml=/results/database-tests.xml
docker compose -f compose.yaml -f compose.step6.yaml --profile tools run --rm --no-deps -e POSTGRES_DB=sentinelapi_test_detection_runtime_20261024 -v "${PWD}/.runtime/portfolio-release:/results" telemetry-tests python -m pytest -p no:cacheprovider /app/collector/tests/test_monitoring.py /app/collector/tests/test_collector.py -q --junitxml=/results/linux-collector-tests.xml
```

The database must already be separately provisioned/migrated; do not substitute the project name to bypass fixture guards. ML/PostgreSQL tests were collected only: no live model acceptance or full migration/reliability certification is inferred from collection.

From frontend:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
$env:SENTINEL_SCREENSHOT_DIR='../.runtime/portfolio-release/browser-captures'
npm.cmd run test:browser
```

Lint/typecheck were repeated after the small screenshot-output option. Browser assertions are unchanged. All existing evidence bytes remain intact; new test screenshots are ignored runtime artifacts. The browser reused the running Vite server and tested demo/mocked workflows, not a privately authenticated live dashboard session.

## Synthetic ML reproduction

```powershell
$env:PYTHONPATH='backend'
$env:MPLCONFIGDIR='.runtime/portfolio-release/matplotlib'
.\.venv-step6\Scripts\python.exe -m sentinelapi.ml.experiment --output .runtime/portfolio-release/ml-evaluation --artifacts .runtime/portfolio-release/ml-artifacts
```

Actual evaluation time: `2026-10-24T09:18:36.740064+00:00`; model `iforest-a51ad3e496475a8d`. Reproduced 360 training and 180 held-out minutes. ML matrix [[56,4],[66,54]], precision .9310344828, recall .45, F1 .6067415730, FPR .0666666667. Rule matrix [[60,0],[96,24]], precision 1, recall .2, F1 .3333333333, FPR 0. [Actual metrics](../infrastructure/portfolio-release/synthetic-ml-metrics.json).

All generator events/labels are controlled synthetic. Rule history is 300 seconds versus ML's 60-second windows; no production accuracy or superiority claim. Artifact binaries remain ignored. Repeats require fresh artifact roots because save refuses overwrite. Earlier committed charts were not regenerated or modified by this audit.

## Current working architecture and boundaries

The requested linear chain separates into request and observation paths: WSO2 routes to DemoCommerce; **WSO2**, not DemoCommerce, emits BASIC logs into bridge → collector → PostgreSQL. Rules read stored gateway events and write alert/evidence records. Monitoring and security APIs expose those under separate credentials. React implements authenticated API clients and independent demo fixtures. Optional ML inference is source-integrated in the worker but not configured live.

Read-only runtime observation at `2026-10-24T09:29:49.649657+00:00` found:

- WSO2, DemoCommerce, PostgreSQL, collector, monitoring, detector and security API running. Monitoring/collector/PostgreSQL/DemoCommerce report Docker healthy; WSO2/detector/security do not have a Docker health status to claim.
- Authenticated monitoring probe `state=healthy`, exit 0; health/session HTTP 200; invalid status query 422; no-token health 401.
- Authenticated security list/detail HTTP 200: one detector-origin medium/open risk-50 alert and 16 evidence rows; no-token list 401. Credentials were read inside containers, not printed or saved.
- Revision `b7d000000001`, 99 gateway events: 40 HTTP 200, one 201, 26 HTTP 401, 23 HTTP 404 and nine HTTP 429.
- Five rules, only error_rate enabled; worker role `sentinelapi_detector`; checkpoint progress observed without publishing checkpoint state.
- One actual alert, “Observed API error-rate spike”, detected `2026-10-24T07:52:41.065997+00:00`, with 16 links.
- **No configured ML artifact; zero ML windows.** No claim of live Isolation Forest scoring.

[Current runtime record](../infrastructure/portfolio-release/runtime-observations.json) and [sanitized API results](../infrastructure/portfolio-release/api-observations.json). The current audit did not generate traffic, revoke credentials, provision roles or restart services. The earlier [controlled repair](detection-runtime-repair.md) supplies the 24-request source/DB/evidence correlation and original-75-record preservation proof. These are separate evidence scopes, not a newly repeated workload.

## Docker startup responsibilities

| Process | Actual startup responsibility |
|---|---|
| WSO2 | Existing independently managed Docker installation; not created/restored by Compose |
| DemoCommerce/PostgreSQL/collector/monitoring | Base compose.yaml, with scoped credentials and prerequisite migration/role setup |
| Host log bridge | Separate host PowerShell process: `scripts/bridge_api_logs.py --follow`; not launched by Compose |
| Rule worker | Separate Step 6 `detector` service; Uvicorn does not launch it |
| Security/ML API routes | Separate Step 6 security-api service; no model inference is triggered by serving Uvicorn |
| Optional ML worker integration | Step 7 image/artifact overlay; trusted, approved API-scoped artifact required |
| React | Separate Vite process or optional Step 8 Nginx container; only Vite rendering tested here |

Base/Step 6/Step 8 `config --quiet` passed. The Step 7 deployment overlay was inspected but not activated with an approved model. No full `config` output exposed secrets. Read the [safe deployment runbook](final-deployment.md) before migration/provision/start; `--no-recreate` protects existing containers but does not update stale code. No persistent service was recreated for release documentation.

## Git and privacy audit

Fetched origin/main remains `f931455`; the six local documentation/repair commits at baseline are not on a remote branch. Step 9 remains separate/unmerged. All 256 tracked baseline paths were inventoried; application modules, tests, migrations, Compose/Dockerfiles, prior reports and new screenshots were reviewed. This is not an audit of third-party binaries or every lockfile dependency's source.

Reachable Git text scan covered **330 blobs**, matching current local credential bytes and private-key/JWT/token signatures without emitting values. It found no selected signature/local-credential matches and no tracked or historical `.env` (except allowed examples), dumps, private runtime/checkpoint/log artifact paths. [Scope and results](../infrastructure/portfolio-release/git-secret-audit.json). This is not proof that arbitrary historical passwords cannot exist or that image pixels can be scanned as text. The new authorized screenshot visibly contains a token and remains excluded; image review is a separate necessary control.

Two already-versioned historical failure reports (`infrastructure/dashboard/collector-demo-tests.xml` and `infrastructure/ml/collector-tests.xml`) contain local Windows paths. Their evidence bytes/history were not rewritten or removed. The paths are not transcribed into current summaries; owner review of their existing public-history privacy is a remaining release decision. No credential match was found by the scoped scan. New raw reports remain ignored rather than adding more host-path-bearing traces.

All 31 raw PNGs remain unchanged locally. Thirteen reviewed copies have matching hashes. Metadata has no authoritative capture time. A broad root-PNG ignore prevents accidental staging of originals, including safe duplicates; only explicitly reviewed final-blog copies are selected. The current schema, backups, secrets and source checkpoint files are preserved. [Full evidence audit](release-evidence-audit.md).

Known remaining issues: direct Windows fixture failures, unmerged Step 9, clean recaptures for excluded evidence, dependency review, backend isolation, live ML and authenticated dashboard acceptance, retention/backup restoration and production identity/TLS. No benchmark or fresh vulnerability audit was performed, and no public release/tag/PR/blog/video/deployment was created.
