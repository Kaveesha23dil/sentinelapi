# Step 7 verification - experimental / incomplete live acceptance

## Precheck

Started clean on feature/ml-anomaly-detection at 1770c21, identical to main and
origin/main after successful fetch. Step 6 PR #2 is merged; no dependent branch
was needed. The retained Step 6 journal still marks live verification incomplete.
Reviewed existing schemas, collector, rules/worker, role-authenticated routes,
database guards, migrations and journal before edits. No reset/discard/push.

Docker is not installed/on PATH; the standard Program Files Docker executable is
absent. PostgreSQL was internal-only in retained evidence; no usable live DB
connection is available here. Current data counts, Step 6 grants, alert persistence
and WSO2-to-ML demonstration remain pending. Retained Step 5 evidence proves 21
historical rows, not sufficient current coverage for meaningful production fitting.

## Executed checks

```powershell
$env:PYTHONPATH='backend;scripts;collector'
.\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_ml_features.py backend/tests/test_ml_model.py backend/tests/test_ml.py backend/tests/test_detection_rules.py backend/tests/test_security_api.py backend/tests/test_detection_migration.py backend/tests/test_validation.py scripts/tests -q --junitxml=infrastructure/ml/host-tests.xml
.\.venv-step6\Scripts\python.exe -m pytest collector/tests/test_collector.py -q --junitxml=infrastructure/ml/collector-tests.xml
.\.venv-step6\Scripts\python.exe -m pytest demo-services/democommerce/tests -q --junitxml=infrastructure/ml/demo-tests.xml
```

Supported host suite: **110 passed, four subtests passed**, one existing AnyIO
deprecation warning. Collector: **18 passed, two failed** in existing Linux-only
`os.O_DIRECTORY` transport/fsync calls on Windows (checkpoint recovery and failed
write tests), matching the documented Step 6 limitation; no collector code changed.
DemoCommerce: **12 passed**, same existing warning. Disjoint total: **140 passed,
two pre-existing platform failures**, plus four subtests. JUnit files are actual
executions; failing report is retained rather than replaced by a green subset.

Initial new-suite failures were an old metadata table-count assertion (updated
8 to 9 for the additive table), then an overbroad DDL test matching ON DELETE
RESTRICT as a destructive DELETE (corrected to DELETE FROM). Subsequent supported
host suite passed. No database tests were passed off as executed.

PostgreSQL/monitoring suite: **29 collected, not executed**, including two new real
DB ML alert/evidence/idempotence tests. Collection command uses test_postgres.py,
test_detection_postgres.py, test_ml_postgres.py and collector/tests/test_monitoring.py
with --collect-only. The existing fixture refuses non-sentinelapi_test_* databases.
DDL generation is tested, but migration application/drift, actual DB constraints,
role grants and transactions still require real PostgreSQL.

Synthetic experiment executed, producing actual CSV/JSON and three inspected PNG
charts. Model/metrics are in ml-model-card.md and ml-evaluation.md. No model was
loaded into a live detector, no live anomaly or alert was observed. No production
data or WSO2 configuration was changed. Training artifacts remain ignored locally.

## Required live acceptance procedure

1. Restore access to the existing Docker host without recreating persistent services.
   Check real Step 5 ingestion and Step 6 rule alert/grants first.
2. Owner applies additive Alembic upgrade and scoped role provisioning. Run the
   29 collected DB/monitoring tests only on a separate guarded test database.
3. Profile real history by API; document temporal coverage, exclusions, collector
   lag and provenance. Fit only an adequately reviewed per-API baseline with a
   chronological holdout. Keep any synthetic-trained deployment experimental.
4. Approve exact trusted artifact/checksum, mount read-only, enable experimental
   mode deliberately. Do not edit a synthetic API identity to impersonate a live
   API baseline. Verify unavailable/incompatible model behavior and worker health.
5. Use existing authorized local WSO2 test tooling and short-lived in-memory tokens
   to send bounded normal and unusual requests. Save sanitized actual gateway,
   collector and DB counts, then wait for window closure and lateness allowance.
6. Query authenticated ML anomalies and the linked Step 6 alert detail. Match raw
   score, feature summary, model version, event references and window identifier.
   If no anomaly is observed, record that outcome without fabricating an alert.
7. Reprocess the same finalized window in a controlled test transaction/replay and
   prove score/alert/evidence counts remain unchanged. Test restart/DB outage and
   late-event policy. Never rewind production checkpoints casually.
8. Capture the six pending screenshots and obtain push/PR review approval.

## Git and evidence

No push, remote PR creation or merge authorized. Prepared PR text:
docs/step-7-pr.md. Local checkpoints are recorded in development-journal.md after
creation. Three evaluation chart artifacts are available as numbered evidence;
six application/terminal/GitHub captures remain pending with exact instructions in
screenshots/07-ml-anomaly-detection/README.md. Step 8 and final blog not started.

## Changed-file inventory

- New backend package: sentinelapi/ml/{features,dataset,model,experiment,cli,worker,api}.py,
  package initializer and dedicated Dockerfile; pinned ML requirements/constraints.
- New additive migration b7d000000001_ml_windows.py and compose.step7.yaml.
- Updated db/models.py, detection/worker.py, detection/provision.py and monitoring/app.py.
- New test_ml_features.py, test_ml_model.py, test_ml.py and test_ml_postgres.py;
  updated existing test_postgres.py and test_validation.py table inventories.
- New ML architecture, model card, evaluation, verification and prepared PR documents;
  updated development-journal.md and blog-evidence-tracker.md.
- New infrastructure/ml precheck, actual test reports, complete evaluation CSV/JSON/
  Markdown, model metadata and three plots; numbered chart copies/manual checklist
  under screenshots/07-ml-anomaly-detection. No model binaries or private data.
