# Step 7 ML architecture

Status: experimental implementation, production readiness pending. Step 7 is the
current requested milestone; AGENTS.md's Step 3.2 marker is historical.

## Verified inputs

Step 5's retained `infrastructure/telemetry/runtime-status.json` records 21 genuine
gateway completions matched to PostgreSQL and monitoring at 2026-10-22 10:51 UTC:
200:11, 201:1, 401:6, 404:3. Latency/client measurements were all null. This is
historical evidence, not a current database query. Docker is absent on this host;
current data volume, duration, completeness and Step 6 live persistence cannot be
verified. Step 6 is merged, but its journal calls runtime verification incomplete.
No WSO2 configuration, database, container or persistent volume was modified.

## Feature contract

`backend/sentinelapi/ml/features.py` defines `api-60s-v1`, ordered fields:
request_count, error_4xx_ratio, error_5xx_ratio, unique_endpoints, get_ratio,
post_ratio, status_code_diversity. Endpoint diversity uses the collector's
sanitized route templates, not raw URLs. An unmapped template collapses unknown
paths; enumeration sensitivity is consequently limited. Latency and client
grouping are excluded because the actual BASIC telemetry does not support them.

Windows are fixed UTC `[start, end)` minutes per API, not overlapping observations.
No empty window is invented. Windows with fewer than five requests or missing
status/method/endpoint are ineligible. The first partial coverage minute and final
unfinished minute are excluded. UUID duplicates are removed; conflicting duplicates
fail closed. Out-of-order arrival cannot change sorting or feature order.

The worker finalizes at floor(now minus 120 seconds). It processes one minute at a
time and at most 10,000 events, rolling back on overflow. Bootstrap is the last five
finalized minutes; historical export is explicit. Events arriving after their
minute has been finalized are not automatically rescored: immutable results avoid
changing evidence silently. Operators must measure collector lag and review an
explicit historical replay with a newly reviewed artifact/version where necessary.
120 seconds is a development assumption, not proof of complete collection.

## Dataset and fitting

The bounded, read-only SQL adapter filters `source='wso2-gateway'`, supports an API
and UTC range, and exports counts/distributions only. A source string alone does
not prove origin; use the actual production database and cross-check collector
evidence, never the disposable fixture database. The CLI requires an explicit API
and chronological split to fit. Each model is scoped to exactly one API, preserving
baseline differences. One deployment currently serves one approved API model.

Pipeline: training-only median imputer, StandardScaler, IsolationForest. The input
validator deliberately rejects missing/nonfinite features before inference; the
imputer does not fabricate unavailable latency or categorical observations. At
least 60 eligible minutes are a technical guard, not statistical adequacy. An
operator must assess daily/weekly behavior and contamination before promotion.

The controlled generator labels every event/window as synthetic through IDs,
API identity and report provenance. It creates 360 normal training minutes and
180 chronological evaluation minutes. Evaluation rotates six five-minute blocks:
normal, benign burst, moderate errors, severe errors, moderate volume, severe
volume. Moderate volume overlaps benign bursts deliberately; no behavior-only
model can reliably distinguish identical feature distributions by intent. Labels
never enter the training matrix. No threshold tuning on held-out labels is done.

## Artifacts and inference

Models live under ignored `.runtime/ml/artifacts/<version>/`; directories are
immutable and existing versions are never overwritten. Metadata includes schema,
feature order, API, dataset digest, config, provenance, UTC training range/time,
Python/library versions and artifact SHA256. The saved bundle binds metadata to
the model. Version identity includes dataset windows, parameters and sklearn.

Only an operator-configured local directory plus an independently approved digest
can be loaded. Verify the exact bytes before deserialization, exact schema and
Python/sklearn/NumPy/joblib compatibility, then check bundled metadata. Restrict
artifact and manifest writes with OS permissions. Checksums are not signatures or
proof of trust: joblib/pickle can execute code. Never accept uploaded artifacts or
client-controlled loading/training requests. See [sklearn persistence guidance](https://scikit-learn.org/stable/model_persistence.html).

The existing async detector invokes ML through `asyncio.to_thread` in an independent
transaction and failure domain. Rules continue if ML is unavailable. Advisory lock,
unique `(window_id, model_version)` and transactional watermark prevent duplicate
scores and alerts. Raw double decision scores remain stored; negative means
anomalous. No probability or UI score calibration is invented. See
[IsolationForest score semantics](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.IsolationForest.html).

## Alerts and monitoring

An anomalous prediction creates a medium-policy-score security_alert with no
rule_id. The policy score 50 is not model confidence. alert_evidence stores exact
features/raw score/version/window, up to 100 event links, and up to 20 overlapping
rule-alert references. It states unusual behavior does not establish malicious
intent. `ml_windows` links scores to alerts; existing alert lifecycle is reused.
Normal windows are stored without alerts. The additive migration preserves all
existing records; downgrade is restricted to disposable test databases.

Four read-only `/api/v1/ml/{model,health,evaluation,anomalies}` routes reuse Step 6
reader/analyst/admin bearer authentication. Anomalies support bounded pagination,
API/model/date filters. Health checks approved artifact availability and version
compatibility without unpickling in HTTP; it explicitly does not certify worker
freshness or database completeness. Evaluation provenance/model version are
reported independently; clients must compare versions with the deployed model.
Missing artifacts/evaluation return safe unavailable states. No training route.

## Deployment

Install `backend/requirements-ml.txt` in a Python 3.12.14 virtual environment.
`requirements-ml-constraints.txt` records the experiment's resolved dependencies.
Apply Alembic upgrade as owner and rerun scoped role provisioning before enabling
ML. New detector grants: SELECT/INSERT ml_windows and UPDATE(alert_id); security
role SELECT only. Do not print or commit private role passwords.

`compose.step7.yaml` is an opt-in overlay with a dedicated ML image and read-only
artifact/report mounts, layered on compose.yaml and compose.step6.yaml. It was not
applied or Docker-validated here. Review deployment and obtain explicit approval
before any persistent container recreation. Set ML_MODEL_HOST_DIR, operator-reviewed
ML_APPROVED_SHA256 and ML_ALLOW_EXPERIMENTAL=true for this milestone. No model here
is production-ready. An experimental synthetic API model cannot score a real API
under a different ID; do not edit its manifest to bypass that protection.
