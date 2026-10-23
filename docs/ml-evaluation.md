# Step 7 executed evaluation

Provenance: controlled synthetic, not genuine WSO2 end-to-end traffic. Model
`iforest-a51ad3e496475a8d`; 360 training minutes, 180 held-out minutes (60 normal,
120 injected scenarios). The report's UTC evaluation_date is authoritative.

| Detector | Precision | Recall | F1 | False-positive rate | TN / FP / FN / TP |
| --- | ---: | ---: | ---: | ---: | --- |
| Isolation Forest | 0.931034 | 0.450000 | 0.606742 | 0.066667 | 56 / 4 / 66 / 54 |
| Step 6 error-rate rule | 1.000000 | 0.200000 | 0.333333 | 0.000000 | 60 / 0 / 96 / 24 |

The existing rule evaluator executes on the exact original generated events and
timestamps. It uses its existing 300-second history, threshold > 0.5 errors and
minimum 20 requests. ML scores the same labeled final 60-second windows. This is
a comparison of configured detectors with different history sizes, not proof
that either technique is superior. Other rules remain unsupported by trusted
client/route evidence and are not enabled for comparison. Volume scenarios are
outside the error-rate rule's purpose. Five-minute scenario blocks permit sustained
error behavior; benign bursts and moderate ambiguous scenarios are retained.

Both detectors miss many scenarios. A false positive is disagreement with the
controlled label, not evidence of a safe request in deployment. No production
attack labels or accuracy estimates exist. No live latency was measured; 120s
lateness plus up to a minute of window accumulation, polling and backlog affect
operational latency. Precision/recall/F1 are null when positive support is absent;
FPR is null when no negative windows exist. Undefined precision is null, not 1.

## Reproduction (PowerShell from repository root)

```powershell
.\.venv-step6\Scripts\python.exe -m pip install -r backend/requirements-ml.txt -c backend/requirements-ml-constraints.txt
$env:PYTHONPATH='backend'
$env:MPLCONFIGDIR='.runtime/matplotlib'
.\.venv-step6\Scripts\python.exe -m sentinelapi.ml.experiment --output infrastructure/ml/evaluation --artifacts .runtime/ml/reproduction
```

Use a new artifact root on repeat runs: save refuses to overwrite any model
directory. Same data/config yields the same model version and predictions;
training/evaluation wall-clock timestamps and binary checksums may differ.
The model hash is recorded in each local manifest, never inferred from this card.

Historical profiling requires existing private database environment and connectivity:

```powershell
.\.venv-step6\Scripts\python.exe -m sentinelapi.ml.cli profile --start 2026-10-22T00:00:00+00:00 --end 2026-10-23T00:00:00+00:00 --output .runtime/ml/real-profile.json
```

For real-data experimental fitting use `train` plus `--api-id <verified UUID>`,
`--split-at <UTC instant>`, a fresh artifact root and reviewed contamination.
The end must cover only finalized minutes. Real traffic has no attack labels:
that command does not generate attack precision or recall. Keep private DB
credentials in the existing environment; never paste them into commands/evidence.

Actual generated artifacts: confusion_matrix.png, anomaly_score_distribution.png,
model_comparison.png, evaluation_metrics.json, evaluation_summary.md and the complete
evaluation_windows.csv. The metadata JSON copy and environment constraints support
reproduction. No large binary model is committed.
