# Final technical verification

Executed 2026-10-24 against source baseline `f931455` on the existing documentation branch. Runtime outputs stay ignored under `.runtime/step10`; sanitized summaries are in `infrastructure/finalization`. No service recreation, SQL migration, volume operation, load test or restart was performed.

## Current execution

| Check | Pass | Fail | Skip | Interpretation |
|---|---:|---:|---:|---|
| Python offline combined suite | 156 + 4 subtests | 2 | 0 | Unit/contracts/synthetic/collector fixtures; no real PostgreSQL |
| Frontend unit | 36 | 0 | 0 | Four files |
| Chromium | 7 | 0 | 0 | Demo application rendering/accessibility and mocked API contracts |
| DB-dependent collection | — | — | — | 32 collected, zero executed; not runtime skips |
| Frontend lint/typecheck/build | passed | — | — | All three commands completed successfully |
| Synthetic ML reproduction | reproduced | — | — | Same model identity/predictions/metrics; new actual evaluation timestamp |

Python console: `2 failed, 156 passed, 1 warning, 4 subtests passed in 13.88s`. XML represents the four subtests as separate cases: do not add them twice when comparing totals. Both failures are `collector/tests/test_collector.py` directory fsync paths accessing `os.O_DIRECTORY` on Windows. They are existing defects fixed only on the unmerged Step 9 branch. The AnyIO warning is pre-existing. No failure was removed or relabeled as a pass.

Frontend browser console: `7 passed (22.1s)`. The suite refreshed real screenshot files 01–08; only 02 differed in Git. The legacy report screenshot 09 still shows five tests and is not current evidence. Browser tests do not contact a live database or certify gateway authorization.

## Exact commands

From repository root:

```powershell
$env:PYTHONPATH='backend;scripts;collector'
.\.venv-step6\Scripts\python.exe -m pytest backend/tests scripts/tests collector/tests demo-services/democommerce/tests --ignore=backend/tests/test_postgres.py --ignore=backend/tests/test_detection_postgres.py --ignore=backend/tests/test_ml_postgres.py --ignore=backend/tests/test_dashboard_postgres.py --ignore=collector/tests/test_monitoring.py -q --junitxml=.runtime/step10/host-tests.xml
.\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_postgres.py backend/tests/test_detection_postgres.py backend/tests/test_ml_postgres.py backend/tests/test_dashboard_postgres.py collector/tests/test_monitoring.py --collect-only -q
$env:PYTHONPATH='backend'
$env:MPLCONFIGDIR='.runtime/step10/matplotlib'
.\.venv-step6\Scripts\python.exe -m sentinelapi.ml.experiment --output .runtime/step10/ml-evaluation --artifacts .runtime/step10/ml-artifacts
```

From frontend:

```powershell
npm.cmd run lint
npm.cmd run typecheck
npm.cmd test
npm.cmd run build
npm.cmd run test:browser
```

PowerShell's execution policy rejected `npm`'s .ps1 shim in the earlier startup attempt; `npm.cmd` works without changing policy. The existing Vite server was reused. Raw browser reports and Python tracebacks remain ignored because they include local paths. Reviewed summaries contain no credentials or personal host paths.

## Current runtime observations

Read-only loopback TCP checks: 5173, 8000, 8010, 8243 and 9443 listened; 8020 did not. Port listeners alone do not establish service identity/readiness.

| HTTP probe | Observation |
|---|---|
| DemoCommerce `/health` | 200 |
| Monitoring overview, no token | 401 |
| Monitoring overview, existing private token | 200, zero requests in default recent interval |
| Monitoring health, private token | 503, database reported available, collector stale-or-unavailable |
| Monitoring session | 404 |
| Monitoring events `status_code=999`, private token | 200 instead of source contract's 422 |
| Security alerts, no token | Connection failed on 8020 |
| Gateway orders, no token, verification enabled | SSLCertVerificationError; OAuth status not established |

The local monitoring token was read only into memory from ignored configuration, never printed or saved. Only allowlisted status/count/health fields were retained. These observations confirm deployment drift/staleness; they do not prove independent DB access or fresh ingestion. No credential was sent outside loopback.

Docker was not found on PATH or the standard checked installation paths. WSL lists docker-desktop, but invoking its Docker shim is explicitly unsupported. No Docker mutation was attempted. The older DemoCommerce virtual environment references a missing Python installation; the existing `.venv-step6` uses a working Python 3.12.14 interpreter. Live services may be running independently; this audit did not start or update them.

## ML reproduction

Actual new evaluation timestamp: `2026-10-24T02:56:24.780393+00:00`. Model `iforest-a51ad3e496475a8d`, 360 training and 180 held-out minutes. ML confusion matrix `[[56,4],[66,54]]`; rule `[[60,0],[96,24]]`. ML precision 0.9310344828, recall 0.45, F1 0.6067415730, FPR 0.0666666667. Rule precision 1, recall .2, F1 .3333333333, FPR 0. See retained sanitized [metrics](../infrastructure/finalization/synthetic-ml-metrics.json).

All data is controlled synthetic; no live inference latency or malicious-intent accuracy was measured. Different detector history lengths preclude a claim of general model superiority. Model artifacts remain ignored; historical committed chart/metric files were not overwritten.

## Step 9: historical branch evidence, not this run

Reviewed `test/end-to-end-validation` at `b9f6098`, its `docs/step-9-verification.md`, security/performance reports, machine summaries and local raw XML. No cherry-pick or merge occurred.

| Historical Step 9 check | Recorded result |
|---|---|
| Host after its Windows fix | 161 passed + four subtests, zero failures |
| Default e2e | 15 passed, 19 skipped |
| Explicit live-security | 2 passed, 10 failed, 5 skipped |
| DB collection | 32 collected; none executed |
| Frontend | 36 unit passes; lint/typecheck/build pass |
| Browser | 8 passed, 1 live skip |
| Synthetic experiment | Same model/results reproduced |
| Benchmark wrapper | Exit 2, NOT RUN; no measurements |
| Bandit/dependency audits | 4 medium/47 low/0 high; installed Python 12 advisories across 3 packages; npm 0 known advisories at that time |

These results belong to different source/test inventories; do not sum them with current counts. Historical advisories are not a current vulnerability scan, and installed-environment findings do not identify deployed versions. Step 9's local raw JUnit files were checked against its committed summary; findings remain unresolved. Re-run applicable checks after approved integration and dependency review.

## Checks still required

Latest live migrations/grants and guarded DB tests; full fresh gateway/log/DB/rule/ML/dashboard correlation; approved real-API model; replay and persistence checks; valid/invalid/expired/unsubscribed gateway authorization under trusted TLS; observed dedicated low-quota throttling; backend isolation; Docker frontend/header validation; performance and server-resource sampling. Restarts/outage tests require a maintenance plan and explicit approval. No missing prerequisite was converted into an end-to-end pass.
