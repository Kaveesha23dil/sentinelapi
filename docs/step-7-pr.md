# feat: add experimental ML API anomaly detection

Base: main. Head: feature/ml-anomaly-detection. Status: prepared locally, not pushed.

Adds fixed per-API UTC traffic windows, deterministic Isolation Forest training,
trusted artifact validation, a bounded out-of-band ML worker, additive score storage
and anomaly alerts/evidence using the existing security lifecycle. Four authenticated
read-only ML endpoints expose readiness, evaluation and paginated anomaly results.

Includes explicitly synthetic chronological experiments, CSV/JSON reports and three
actual plots. ML precision 0.9310, recall 0.4500, F1 0.6067, FPR 0.0667 on 180
controlled held-out windows. These results are experimental and do not establish
production attack detection. Latency/client features are deliberately unsupported.

Validation: supported suite 110 passed plus four subtests; DemoCommerce 12 passed;
collector 18 passed and two known Windows os.O_DIRECTORY failures. 29 PostgreSQL/
monitoring checks collected but not executed because Docker/live DB are unavailable.
Migration application, scoped grants, Step 6 runtime verification, real data profiling
and WSO2-to-ML alert/replay proof remain required. Production readiness is false.

No database/WSO2 state changed and no binary models, credentials or raw sensitive logs
are included. Six screenshots remain pending; three authentic evaluation charts are
included. Review as experimental; do not merge as completed live acceptance.
