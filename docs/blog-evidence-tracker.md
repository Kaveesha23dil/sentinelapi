# Authentic development evidence inventory

No final blog is being written here. Screenshot inventory was inspected with
`rg --files screenshots`: only checklist READMEs existed, with no captured images.

| Milestone | Screenshots captured | Remaining evidence |
| --- | --- | --- |
| Step 3.2 API integration | 0/9 | screenshots/03-api-integration/README.md |
| Step 3.3 security | 0/8 | screenshots/03-security/README.md; isolation and actual 429 still unverified |
| Step 4 database | 0/7 | screenshots/04-database/README.md |
| Step 5 traffic collection | 0/8 | screenshots/05-traffic-collection/README.md |

Step 5 genuine non-image evidence under infrastructure/telemetry:

- logging-configuration.json: supported DevOps OFF → BASIC, scoped to DemoCommerce.
- log-format-observations.json: field names and sanitized real record metadata.
- gateway-precheck.json: real OAuth routing smoke results, separately from older milestones.
- prerequisite-verification.json: retained Step 4 test marker and actual migration revision.
- runtime-privileges.json: authenticated collector/monitor role permission checks.
- test-results.json: 57 executed tests, migration cycle and separate demo restart marker.
- e2e-verification.json: six real completed gateway requests matched to DB/API;
  checkpointed collector restart/replay kept both scoped counts at six.
- outage-verification.json: real gateway 200, monitoring 503 during PostgreSQL outage,
  unchanged collector checkpoint, one real event recovered exactly once.
- runtime-status.json: bounded current-log/DB/API matching and current service health.

JSON reports are evidence files, not screenshots. Fabricated test data is labeled
and isolated in test databases. It must never illustrate real WSO2 traffic.
Before any screenshot is marked captured, verify file existence, open it, inspect
redaction and confirm the actual service/test window. Do not generate or rebuild UI.

Git provenance: feature/api-traffic-collector, persistence 090d129, collector
7345a5e, monitoring 48d141f. Resolve the final evidence commit via
`git log -1 --format=%H -- docs/step-5-verification.md`. GitHub PR evidence remains
pending until approved feature push and actual PR creation. Step 3.3 remains
incomplete independently of the verified Step 5 collection path.

## Step 6 — 2026-10-23 (partial; live verification pending)

- Branch: feature/rule-based-threat-detection, base Step 5 merge 3c2be39.
- Verified pure strategy checkpoint: 4cc8368; other implementation awaits database checks.
- Architecture: docs/threat-detection-architecture.md.
- Rule catalog: docs/detection-rule-catalog.md.
- Exact executed tests, failures and blocked live acceptance: docs/step-6-verification.md.
- Screenshot checklist/manual instructions: screenshots/06-threat-detection/README.md.
- Screenshot status: 0/8 captured; available-surface inventory apps=[] / browsers=[].
- No Step 6 real-traffic report, database alert proof or live evidence JOIN exists yet.
- scripts/simulate_threat_traffic.py is a bounded local runner, not itself evidence.
- Synthetic tests never substitute for WSO2 telemetry. Existing Step 5 reports are
  historical proof only and were not overwritten or relabeled as Step 6.
- Prepared PR text: docs/step-6-pr.md; no push or remote PR. No merge approval given.

## Step 7 — experimental ML, 2026-10-23

- Branch feature/ml-anomaly-detection; verified merged main base 1770c21.
- Authentic evaluation artifacts: infrastructure/ml/evaluation, including all
  requested PNG/JSON/Markdown outputs, per-window CSV and model metadata/checksum.
- Data: 25,953 explicitly synthetic events, 360 training/180 evaluation minutes.
  Current real DB profile unavailable; prior Step 5 evidence has 21 real rows.
- Actual model iforest-a51ad3e496475a8d; metrics and limitations in ml-evaluation.md.
  No live anomaly, attack classification, production accuracy or latency claimed.
- Evidence folder: screenshots/07-ml-anomaly-detection. Three numbered generated
  charts are actual executed experiment results and have been visually inspected.
  Zero application screenshots captured; six required manual captures pending.
  README.md specifies exact capture instructions and redaction precautions.
- Tests: 140 passed across disjoint host/collector/demo suites, two known Windows
  collector failures, plus four subtests; 29 DB checks collected but unexecuted.
  Actual JUnit reports are retained under infrastructure/ml, including failures.
- Local checkpoints: 33c1d76, dde43d0, e0a2c93, 0db122b, 321fbaa. Resolve final docs
  checkpoint with `git log -1 --format=%H -- docs/step-7-verification.md`.
- PR text: docs/step-7-pr.md. No feature push, remote PR or merge authorized.
  GitHub capture remains pending approved push and actual PR creation.
