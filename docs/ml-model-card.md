# SentinelAPI Isolation Forest model card

Model: `iforest-a51ad3e496475a8d`. Schema: `api-60s-v1`.
Intended use: experimental operator triage of unusual per-API traffic minutes.
Not an attack classifier, authorization decision, automatic blocking mechanism,
calibrated probability, or production-ready model.

Training: 360 synthetic normal minutes for `synthetic-demo-api`, chronological
2026-01-01 00:00–06:00 UTC. Evaluation: next 180 minutes, 60 normal including benign
bursts and 120 injected error/volume scenarios. Seven supported features; no raw
client identities, IPs, payloads, tokens or latency. The generator uses seed 42.

IsolationForest: 200 trees, contamination 0.05, random_state 42, n_jobs 1,
default max_samples='auto'. Preprocessing is fitted only on training data.
Contamination is an experimental choice; it is not universally optimal or a
measured attack prevalence. Threshold is decision_function < 0, no calibration.

Measured synthetic results: precision 0.9310344828, recall 0.45,
F1 0.6067415730, false-positive rate 0.0666666667. Confusion matrix rows true
normal/scenario, columns predicted normal/anomalous: `[[56,4],[66,54]]`.
These values do not estimate production performance. Actual held-out CSV/report
and plots are in infrastructure/ml/evaluation. Evaluation timestamp is in the JSON.

Limitations: synthetic distributions, one API, narrow behavior coverage, no
daily/weekly seasonality, drift detection or automatic retraining; five-request
minimum omits low-volume anomalies. Benign bursts can resemble injected volume;
moderate unusual scenarios are frequently missed. A finalization delay does not
establish telemetry completeness. Live detection latency is unmeasured.

Historical retained evidence has only 21 verified gateway rows; current historical
volume cannot be queried here. No real traffic model was fitted. Promotion needs
verified Step 6 runtime persistence/grants, substantially broader real baselines,
reviewed chronological validation with independently documented labels, replay
and outage tests on PostgreSQL, privacy review, alert-volume review, drift and
operational latency monitoring, and operator approval of the exact artifact.

Artifacts are local ignored joblib bundles. Checksum and full training metadata
are generated into `.runtime/ml/artifacts/<version>/metadata.json`; binary models
are excluded from Git. Exact environment compatibility and trusted ownership are
required; joblib deserialization can execute code. See the architecture document
for controls and reproduction. All models currently set production_ready=false.
