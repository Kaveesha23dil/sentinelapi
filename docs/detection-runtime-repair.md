# Detection runtime repair and controlled local alert validation

Verified 2026-10-24 on `fix/detection-runtime-and-monitoring`, branched from the clean documentation checkpoint `4365fa1`. Implementation commit: `3d4bc69`. This focused repair preserves that documentation history and the separate unmerged Step 9 branch. It does not claim ML, production readiness, a real-world attack or full dashboard acceptance.

## Verified root causes

1. **Host import path:** `sentinelapi` lives under `backend/`, not the repository root. The existing root command did not install that directory as a package or add it to PYTHONPATH. The working `.venv-step6` already contains the dependencies. No duplicate package, package move or dependency upgrade was needed.
2. **Stale telemetry, not failed authentication:** the deployed health route existed and its token was configured. Its authenticated response was 503 with database available/collector stale. The collector reported source_fresh=false. Resuming the established bridge made the old probe exit 0 before any monitoring replacement; this isolates freshness as the health failure's observed cause. Existing monitoring SELECT grants were present.
3. **Old monitoring image/build configuration:** the running image was built on 2026-10-22 and lacked the source's session route. Monitoring had only `image`, so `docker compose build monitoring` had no build definition. An explicit shared Dockerfile build now allows that command. Only the stateless monitoring container was updated; its session route now returns 200 and invalid status filters return 422.
4. **No detector deployment/roles:** no detector was running, detector/security roles did not exist, and there were zero rules/checkpoints/alerts. Uvicorn did not start the worker. The existing Step 6 Compose worker is now running with the intended scoped identity.
5. **Provisioning could rotate passwords unintentionally:** the previous routine always issued ALTER ROLE, even on a routine grant refresh. The default now creates missing roles and preserves existing passwords; rotation needs explicit `--rotate-existing-passwords`. Privileged/non-login pre-existing runtime roles are refused. No existing password was rotated in this repair.

No schema/model mismatch was found: project revision is `b7d000000001`, current columns/constraints are present, guarded migration checks pass, and the actual worker writes alerts/checkpoints using the existing schema. Rule thresholds, evidence adapters, evaluator semantics and lateness were not weakened.

## Files changed

| File | Purpose |
|---|---|
| compose.yaml | Build monitoring directly from the established collector Dockerfile; pass optional detector/security secrets into owner tools through Compose, without CLI values |
| compose.step6.yaml | Explicit init, healthy-DB dependency and 60-second stop grace for the separate detector |
| backend/sentinelapi/detection/provision.py | Idempotent scoped grants, no implicit password rotation, privilege guard and sanitized failures |
| backend/sentinelapi/detection/worker.py | SIGTERM/SIGINT stop handling finishes the current cycle and disposes the engine |
| backend/sentinelapi/monitoring/healthcheck.py | Testable authenticated probe with allowlisted reasons; no credentials/bodies/errors printed |
| backend/tests/test_runtime_startup.py | Probe failures, role safety and worker shutdown/failure-domain regressions |
| backend/tests/test_detection_postgres.py | Actual PostgreSQL seed idempotence preserving reviewed configuration |
| infrastructure/sql/security-alerts.sql; scripts/show_security_alerts.ps1 | Read-only real alert output for Screenshot 06 |
| .gitignore; .dockerignore | Exclude private backups from Git and Docker build context |

Documentation/journal and sanitized verification summarize actual results. `.env`, dumps, source/checkpoint state, raw event/correlation IDs, tokens, model artifacts and private runtime scripts remain uncommitted.

## Actual deployment and database observations

- Initial project telemetry: **75** `wso2-gateway` events. Final checked count: **99**; a private identity-set comparison proved all original 75 remain present.
- Project Alembic revision stayed **b7d000000001**. No project migration, checkpoint reset, traffic rewrite, manual alert insert or volume deletion was performed.
- PostgreSQL, WSO2 and the collector container were not recreated. The existing backup was found at the supplied ignored path; restore was not tested.
- Monitoring and collector report **healthy**. Authenticated monitoring health is 200 and its CLI exits 0; missing credentials still return 401. Session is 200; `status_code=999` is 422.
- Detector/security roles have no superuser, CREATEDB, CREATEROLE, replication or BYPASSRLS attributes. Detector can read traffic, insert alerts and update checkpoints, but cannot insert traffic. Runtime does not use the owner identity.
- Five rules were seeded. Only error_rate is enabled, with window 300s, threshold strictly >0.5 and minimum 20 requests. Other live adapters remain unavailable and disabled.
- The worker advanced its DB checkpoint, stopped cleanly with **exit 0 / OOM false**, then resumed the existing checkpoint. Alert count remained one and evidence remained 16: no restart duplicate.
- Authenticated security API returned HTTP 200 with one detector-origin alert and 16 evidence rows; unauthenticated access remained 401. Its serializer intentionally exposes a safe explanation rather than the stored title; the screenshot query selects the actual database title directly.

The existing host bridge remains necessary. It is running for this validation, not installed as a Windows service. Do not launch a second bridge against the same source checkpoint. If it stops, freshness/health should fail again; do not remove the health check to hide that condition.

## Genuine controlled validation

Used existing `SentinelAPITestClient`, whose existing application policy was Unlimited. No application, subscription, quota, gateway policy, rule threshold or log level was changed to induce a result. TLS verification remained enabled with the public certificate retrieved from the operator-controlled local WSO2 container. Management/application credentials stayed in memory; test-token and management-token revocations were submitted afterward.

The existing `simulate_threat_traffic.run` helper sent **24 bounded read-only gateway requests** from `07:49:18.637089` to `07:50:56.476292` UTC: **4 HTTP 200** order-list responses and **20 HTTP 404** nonexistent-order responses. All 24 issued correlation references matched 24 BASIC RESPONSE_OUT completions; deterministic identities matched 24 persisted gateway events. No sanitized flow was fabricated/replayed to manufacture this result.

At `07:52:24` UTC there was still no alert: the normal watermark had not reached the qualifying response. At `07:52:41.065997` UTC the worker created:

| Stored field | Actual value |
|---|---|
| Title | Observed API error-rate spike |
| Severity / risk / status | medium / 50.00 / open |
| First detected | 2026-10-24 07:52:41.065997+00 |
| Window | 07:45:38.137–07:50:38.137 UTC, 300 seconds |
| Measured / threshold | 0.800000 / 0.500000 |
| Requests at first qualifying end | 20 |
| Unique linked evidence | 16 actual controlled gateway error responses |

The first qualifying end had 16 errors among 20 requests; it need not wait for all 24 requests. Evidence is an immutable bounded incident snapshot, so later observations do not imply missing evidence merely because the total workload had 20 errors. The 120-second lateness allowance was respected, not bypassed. Nine previously collected HTTP 429 events remain preserved; the new 24-request run did not itself produce 429. This validates a rule signal under controlled local behavior, not malicious intent.

Sanitized source/count/API/test results: [verification.json](../infrastructure/detection-runtime/verification.json). Private raw identity comparisons and XML are ignored under `.runtime/detection-runtime/`.

## Exact Windows PowerShell commands

Run from repository root in the Docker Desktop **host** PowerShell. Docker was available there even when the restricted shell's PATH lookup failed.

```powershell
git status --short --branch
git switch -c fix/detection-runtime-and-monitoring

# Import smoke check; does not launch a duplicate worker or require DB credentials.
$env:PYTHONPATH='backend'
.\.venv-step6\Scripts\python.exe -c "from sentinelapi.detection.worker import run_once, seed_rules; print('worker import passed')"

docker compose -f compose.yaml -f compose.step6.yaml config --quiet
docker compose -f compose.yaml -f compose.step6.yaml build monitoring detector persistence
docker compose --profile tools run --rm --no-deps persistence python -m sentinelapi.detection.provision

# This repair updated ONLY stateless monitoring. Review before applying elsewhere.
docker compose up -d --no-deps monitoring
docker compose -f compose.yaml -f compose.step6.yaml up -d --no-deps --no-recreate detector security-api

# Separate terminal; already running during this validation, so avoid duplicates.
$env:PYTHONPATH='backend;collector;scripts'
.\.venv-step6\Scripts\python.exe scripts/bridge_api_logs.py --follow

# Authenticated local probe; its token comes from the container environment.
docker exec sentinelapi-monitoring python -m sentinelapi.monitoring.healthcheck
docker inspect sentinelapi-monitoring --format '{{.State.Health.Status}}'

# Only the new detector was stopped/started, not PostgreSQL or the collector.
docker compose -f compose.yaml -f compose.step6.yaml stop -t 60 detector
docker inspect sentinelapi-detector-1 --format '{{.State.Status}} {{.State.ExitCode}}'
docker compose -f compose.yaml -f compose.step6.yaml start detector
```

The normal local worker command, **only when** scoped detector POSTGRES_* credentials and a reachable DB are privately configured, is:

```powershell
$env:PYTHONPATH=(Resolve-Path .\backend).Path
.\.venv-step6\Scripts\python.exe -m sentinelapi.detection.worker
```

Alternatively run from `backend` using `..\.venv-step6\Scripts\python.exe -m sentinelapi.detection.worker`. This fixes imports, not database connectivity. The internal DB has no host binding; prefer Compose rather than publishing it or using owner credentials. Compose already sets the image's working directory/import path correctly. Do not start a second host worker just to check imports.

To repeat bounded traffic, privately obtain a short-lived subscribed token from the existing application and set `WSO2_SIMULATION_TOKEN`/`WSO2_CA_FILE` without literal secret values in history. Then run:

```powershell
.\.venv-step6\Scripts\python.exe scripts/simulate_threat_traffic.py error-rate
```

It stops on 401/403/429. If quota prevents enough requests, wait for the legitimate quota window; never change policy to make a test pass. Correlate actual completions and stored rows, then wait for the normal lateness watermark. Historical events outside bounded bootstrap are not recovered by resetting production checkpoints. The private orchestration used here reused that exact helper and existing management-token tooling; it is not a published secret-bearing test fixture.

## Executed tests

| Command group | Final actual result |
|---|---|
| Host rules/migration/contracts/provision/probe/startup/tools | 122 passed + 4 passing subtests; 0 failed/skipped/errors |
| Real PostgreSQL persistence/detection/seed/migration/dashboard SQL | 21 passed; 0 failed/skipped/errors |
| Linux collector/real-DB monitoring/startup | 48 passed; 0 failed/skipped/errors |
| Compose config --quiet; PowerShell parser; diff whitespace | Passed |

Groups overlap (migration/startup cases); do not sum as disjoint coverage. Synthetic DB fixtures were confined to a newly created `sentinelapi_test_detection_runtime_20261024` database, which remains for inspection. This test data is not the controlled live alert evidence. The pre-existing AnyIO warning remains. Initial test containers also reported cache-directory permission warnings; final runs used `-p no:cacheprovider`. A private snapshot parser initially mishandled multiline JSON, and an inline shell probe had quoting/field-selection errors; corrected script-based probes produced the actual results above. No failing assertion was weakened.

```powershell
$env:PYTHONPATH='backend;collector;scripts'
.\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_runtime_startup.py backend/tests/test_detection_rules.py backend/tests/test_detection_migration.py backend/tests/test_security_api.py backend/tests/test_dashboard_api.py backend/tests/test_validation.py scripts/tests -q --junitxml=.runtime/detection-runtime/offline-tests.xml

# A NEW separate guarded database was created once; do not replace/reuse project data.
docker exec sentinelapi-postgres createdb -U sentinelapi_owner sentinelapi_test_detection_runtime_20261024
docker compose --profile tools run --rm --no-deps -e POSTGRES_DB=sentinelapi_test_detection_runtime_20261024 persistence alembic upgrade head
docker compose --profile tools run --rm --no-deps -e POSTGRES_DB=sentinelapi_test_detection_runtime_20261024 -v "${PWD}/.runtime/detection-runtime:/results" persistence python -m pytest -p no:cacheprovider tests/test_postgres.py tests/test_detection_postgres.py tests/test_detection_migration.py tests/test_dashboard_postgres.py -q --junitxml=/results/database-tests.xml
docker compose --profile tools run --rm --no-deps -e POSTGRES_DB=sentinelapi_test_detection_runtime_20261024 -v "${PWD}/.runtime/detection-runtime:/results" telemetry-tests python -m pytest -p no:cacheprovider /app/collector/tests/test_monitoring.py /app/collector/tests/test_collector.py /app/tests/test_runtime_startup.py -q --junitxml=/results/collector-tests.xml
```

Use a new approved test DB name for a fresh run; an existing-name error is not permission to drop it. These commands retain test DBs and never downgrade the project database. Initial 20/47 passing counts were superseded by 21/48 after the final regression additions.

## Screenshot 06

Actual database query output was executed and verified. A PNG has **not** been captured. Run:

```powershell
Clear-Host
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/show_security_alerts.ps1
```

Widen the terminal so title/severity/risk/status/UTC time/evidence count fit. Win+Shift+S → select the actual table and save as `screenshots/final-blog/06-security-alerts.png`. Exclude unrelated history, personal host paths and notifications. Caption: **Controlled local WSO2 error-rate validation; genuine persisted alert, not a real-world attack.** Do not reconstruct the table or edit the returned values. [Evidence audit](release-evidence-audit.md).

## Credential rotation and remaining limits

Previously exposed passwords should be treated as compromised. Plan deliberate rotation of every affected value, keep replacements private and coordinate all dependent services. No existing credential was rotated here. Detector/security provisioning needs `--rotate-existing-passwords` to rotate those two roles; it does not rotate the owner, collector or monitoring roles. A container restart retains its original environment; applying a new credential requires reviewed runtime reconfiguration, not just editing `.env`. Obtain approval before any persistent-container recreation and preserve backups/checkpoints throughout the maintenance plan.

Other four rule adapters remain disabled; no live ML or dashboard-rendering acceptance is claimed. Existing broader dependency findings, backend isolation and Step 9 merge status remain separate work. This repair validates a genuine controlled gateway → collector → database → rule alert/evidence → authenticated API path. Screenshot capture is the remaining manual evidence action, not a missing alert.

No push performed. Prepare review with:

```powershell
git push -u origin fix/detection-runtime-and-monitoring
gh pr create --base main --head fix/detection-runtime-and-monitoring --title "fix: repair detection runtime and verify controlled alerts" --body-file docs/detection-runtime-pr.md
```

Push only after approval; no merge without approval. This branch includes the four earlier local documentation commits because it was created from the existing clean docs branch. Review that ancestry before choosing a final PR base or integrating it; do not rewrite/discard those commits to hide the dependency.
