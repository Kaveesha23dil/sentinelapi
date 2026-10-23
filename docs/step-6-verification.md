# Step 6 verification — 2026-10-23

**Step 6 is not fully complete.** Offline strategies and HTTP auth/validation are
verified. New PostgreSQL migration, worker transactions, management persistence,
scoped grants, current ingestion and genuine alert creation remain unverified.
No new live alert or end-to-end result is claimed.

## Branch and preserved state

Initial tree was clean on feature/rule-based-threat-detection at `3c2be39`, the
Step 5 merge shared by local main. `git fetch origin` succeeded after the sandbox
initially denied writing FETCH_HEAD; origin/main remained `3c2be39`. The requested
branch already existed with the correct base, so no switch/reset/rebase was needed.
The newer user request explicitly selects Step 6 over the stale Step 3.2 marker
in AGENTS.md. No persistent service was deleted, restarted or recreated; no
WSO2 configuration, production records, PostgreSQL volumes or demo data changed.

Inspected backend models, migrations, repositories/DTOs, monitoring auth/API,
collector normalization/parser/transport/tests, Compose, local WSO2 verification
tools, Step 4/5 architecture, verification and saved telemetry observations.
There was no existing detector implementation to reuse.

Step 5 source evidence distinguishes genuine WSO2 completions from labeled
`demo-test` persistence fixtures. Historical Step 5 proof is retained unchanged.
Its six real requests produced six database/API events; its runtime snapshot
reported 21 real gateway completions and 21 database rows. These reports are not
fresh Step 6 database queries. Current collector health, migration revision and
record counts could not be checked in this environment.

## Environment blockers

- `docker` is not on PATH; the standard Docker Desktop executable path also does
  not exist. No PostgreSQL host port is published by Compose. Therefore no safe
  live DB, collector or WSO2-container verification path was available.
- The existing DemoCommerce venv points to a missing user Python312 installation.
  Used bundled Python 3.12.14 to create ignored `.venv-step6` instead.
- Initial pip download failed with WinError 10013 under the sandbox. Re-ran with
  approved network access; pinned backend dependencies installed successfully.
- Computer screenshot inventory returned `apps: []`, `browsers: []`. All eight
  screenshot entries remain pending; no success output was reconstructed.

## Executed tests

Commands run from repository root unless stated otherwise. Set the Windows module
path first: `$env:PYTHONPATH='backend;collector;scripts'`.

1. First expanded run (before metadata-count correction and simulation additions):
   100 passed, 3 failed, four subtests passed. One expected schema-count assertion
   needed to change from seven to eight ORM tables; corrected. Two failures are
   existing collector directory-fsync tests using POSIX `os.O_DIRECTORY` on Windows.
2. Re-run including simulation tests: 106 passed, 2 failed, four subtests passed.
   Same two Windows/POSIX collector failures; no collector production behavior changed.
3. Final supported-host suite:

   ```powershell
   ./.venv-step6/Scripts/python.exe -m pytest -q -p no:cacheprovider backend/tests/test_detection_rules.py backend/tests/test_detection_migration.py backend/tests/test_security_api.py backend/tests/test_validation.py scripts/tests
   ```

   **89 passed, four subtests passed, one dependency deprecation warning**, 1.22s.
   The warning concerns Starlette's AnyIO BlockingPortal alias.
4. Collector subset:

   ```powershell
   ./.venv-step6/Scripts/python.exe -m pytest -q -p no:cacheprovider collector/tests/test_collector.py -k 'not checkpoint_recovery_and_transport_gc and not checkpoint_does_not_advance_on_write_failure'
   ```

   **18 passed, 2 deselected**, 0.58s. The deselected tests are the documented
   failures above, not presumed passes; rerun the entire collector suite in Linux.
5. From `demo-services/democommerce`, using the absolute Step 6 venv Python:
   `python -m pytest -q -p no:cacheprovider tests` — **12 passed**, one same
   dependency warning, 0.57s. This is isolated TestClient regression testing,
   not live gateway traffic.
6. PostgreSQL collection-only check:
   `python -m pytest --collect-only -q -p no:cacheprovider backend/tests/test_detection_postgres.py backend/tests/test_postgres.py collector/tests/test_monitoring.py`
   — **27 tests collected**. They were NOT executed, not marked passed, and not
   pointed at the project database. Five new tests cover recovery/dedup/late events,
   disabled/normal behavior, capacity rollback, API lifecycle/audits and uniqueness.
7. `python -m compileall -q backend/sentinelapi backend/migrations scripts/simulate_threat_traffic.py`
   and `git diff --check` passed. The migration test renders additive PostgreSQL
   DDL using Alembic Operations; this does not replace actual upgrade/drift checks.

These final disjoint executed passing suites total 119 tests plus four subtests.
The expanded Windows run still has the two known collector failures. No migration,
PostgreSQL integration, container privilege or WSO2 live test pass is asserted.

## Implemented versus live-verified

| Item | Status |
| --- | --- |
| Five deterministic rule strategies and strict config | Implemented; synthetic unit-tested |
| API-level HTTP error ratio on BASIC fields | Live-eligible implementation; genuine triggering pending |
| Flood / enumeration / auth failures / unusual activity | Fixture-only verification; trusted live adapters unavailable |
| Alert metadata / FK-linked evidence / unique fingerprint | Implemented; DDL generation checked; PostgreSQL application pending |
| Async worker / overlap / atomic checkpoint / retry | Implemented; real PostgreSQL tests pending |
| Six management routes / role checks / validation | HTTP unit checks pass; database-backed behavior pending |
| Local bounded traffic simulation | Implemented; client stubs tested; no live traffic issued |
| Screenshots | 0/8 captured, all pending |

## Remaining genuine end-to-end acceptance

On the original Docker-equipped host, first inspect current containers/health and
confirm owner migration state without replacing services. Build the new image,
then use the existing guarded `sentinelapi.db.verify prepare` runner in a fresh
`sentinelapi_test_*` database. It must execute the new PostgreSQL tests, existing
database tests, full collector suite, migration upgrade/idempotency/drift and
test-only downgrade/upgrade. Review actual grants using both runtime roles.
Only after those pass apply the additive project migration, provision scoped
roles, and start the two NEW services as documented in the architecture.

Use the existing certificate-validating subscribed-token workflow. Keep tokens in
private environment memory; never save them in commands or reports. With bridge
and collector healthy, run `scripts/simulate_threat_traffic.py normal`. It makes
at most 24 GETs, two seconds apart. Record exact outcomes and correlate activity
IDs through parsed BASIC logs, stable event UUIDs, PostgreSQL and monitoring API.
Wait at least five quiet minutes plus the two-minute watermark delay before the
error scenario, or account explicitly for background traffic in the ratio.

Run `scripts/simulate_threat_traffic.py error-rate`: four normal reads followed by
up to 20 missing-order reads, all through localhost:8243 and existing subscribed
authentication. No unknown-route scan or login attack is attempted. Stop on
401/403/429; the script does not bypass quotas. If 429 prevents reaching the
threshold, record gateway enforcement and leave live detector triggering pending.
The report stores actual timestamp/method/path/activity UUID/status only. It does
not claim collection/detection. Inspect these reports before committing evidence.

After the detector watermark catches up, verify a persisted alert with its exact
API/rule/version/window/count/ratio, JOIN its evidence UUIDs to actual observed
traffic_events, and fetch it with the authenticated security API. Prove normal
scenario counts did not trigger this rule and subsequent worker passes do not
duplicate its fingerprint. Capture the actual safe screens and inspect each PNG.
None of these eight live acceptance steps was completed in this session.

## Git checkpoints, PR and Step 7

`4cc8368` — `feat: implement rule-based API threat detection` includes the pure
strategies and passing unit tests only. Its staged diff was reviewed for secrets
and generated artifacts. Persistence, worker, deployment and API changes remain
in the working tree until relevant PostgreSQL checks pass; do not lose these files.
Documentation records this partial state. Resolve its later documentation commit
with `git log -1 --format=%H -- docs/step-6-verification.md`.

No push, remote PR or merge occurred. Prepared title/summary/limitations are in
step-6-pr.md. Do not request publication as a verified milestone before the
blocked checks pass. After verification, create small persistence/API/test commits,
inspect staged contents, request push approval and open the PR against main.

Step 7 preparation consists of stable observation/config/finding contracts and
explainable alert/evidence APIs. Before proceeding, finish Step 6 acceptance,
resolve prior Step 3.3 isolation/throttling gaps, establish trustworthy identities
and baseline provenance, and define Step 7 explicitly. No ML, React dashboard or
final WSO2 blog was started.
