# Step 8 verification

Status: seven-screen dashboard implemented and tested; live acceptance pending.
Step 7's ML remains experimental. No Step 9 or final blog work was begun.

## Precheck

Started clean on feature/security-dashboard at c8fad4a, the merged Step 7 PR #3.
Fetched origin and verified HEAD/main/origin-main were identical. No dependent branch
was needed. Inspected empty frontend, backend routes/auth/schema, Compose, actual
tests and Step 7 journal before editing. No reset/discard/force-push occurred.

Step 7's report has 140 passed plus four subtests, two known Windows collector
O_DIRECTORY failures, and 29 unexecuted DB checks. Those limits were preserved.
Docker is unavailable, PostgreSQL was internal-only, and live WSO2-to-ML acceptance
was already pending. This run cannot certify current traffic, real alerts, model
deployment or database coverage. Retained Step 5 evidence of 21 real gateway rows
was not relabeled as current dashboard data.

## Implemented and tested

- Seven responsive views, design tokens, self-hosted Inter, shadcn sources, accessible
  navigation/controls, skeletons/empty/errors, error boundary and lazy routes.
- Typed/Zod-validated client, cancellation, independent server-verified monitoring/
  security capabilities, memory-only credentials, cache isolation and no demo fallback.
- Authenticated inventory/timeseries/endpoints/session routes, server method/status
  filtering and safe incident event/audit extensions over existing schema. No migration.
- Analyst/admin incident transitions with confirmation; admin rule editing; backend
  remains responsible for all permissions and transition/configuration validation.
- Bounded live polling, explicit historical demo anchor, actual synthetic evaluation
  provenance, version mismatch warnings and page-limited raw-score histogram.
- Standalone Docker/Nginx/Compose frontend config; no persistent service was changed.

## Actual checks and commands

From frontend:

```powershell
npm run lint
npm run typecheck
npm test -- --reporter=dot --reporter=json --outputFile=../infrastructure/dashboard/frontend-tests.json
npm run build
npm run test:browser
```

Lint: passed with zero warnings/errors. Typecheck: passed. Production build: passed,
with separate page/fixture/chart chunks, no final chunk-size warnings. Frontend:
**32 tests passed** across three files. Chromium: **five tests passed**, including
axe A/AA scans on seven desktop screens, authentic screenshots, 390px overflow check,
filters/pagination, demo isolation, reload, and two clearly labeled mocked API tests
for capability-driven status updates/invalidation and 401/403 handling. The mocked
status persists across reload/reconnect in that test; this is not real DB durability.

From repository root:

```powershell
$env:PYTHONPATH='backend;scripts;collector'
.\.venv-step6\Scripts\python.exe -m pytest backend/tests/test_dashboard_api.py backend/tests/test_ml_features.py backend/tests/test_ml_model.py backend/tests/test_ml.py backend/tests/test_detection_rules.py backend/tests/test_security_api.py backend/tests/test_detection_migration.py backend/tests/test_validation.py scripts/tests -q --junitxml=infrastructure/dashboard/backend-tests.xml
.\.venv-step6\Scripts\python.exe -m pytest collector/tests/test_collector.py demo-services/democommerce/tests -q --junitxml=infrastructure/dashboard/collector-demo-tests.xml
```

Backend/tool suite: **126 passed plus four subtests**, one pre-existing AnyIO warning.
Collector/demo: **30 passed, two failed**, same existing Linux-only O_DIRECTORY calls
on Windows; collector code was not changed. Python disjoint total **156 passed, two
known platform failures**, plus four subtests. Actual JUnit reports retain failures;
only trailing whitespace in traceback lines is normalized for Git.

**32 PostgreSQL/monitoring tests collected, NOT executed**: existing test_postgres,
test_detection_postgres, test_ml_postgres, collector test_monitoring and three new
test_dashboard_postgres checks. Use --collect-only -q to repeat collection. Real
execution requires an existing guarded sentinelapi_test_* database and migrations.
New backend HTTP/SQL-contract tests use mocks and are not counted as real DB proof.

JSON reports are in infrastructure/dashboard. The browser HTML report is ignored
runtime output in frontend/playwright-report; screenshot 09 records its actual
five-pass result. Dependency installs reported zero known npm audit vulnerabilities
at installation time; this is not a general security certification.

## Failures found and resolved

Sandbox registry access failed (EACCES); approved dependency installation succeeded.
Initial frontend tests needed explicit demo configuration, async lazy-route waits
and non-ambiguous record selectors. Formatter/React fast-refresh helpers were
separated appropriately. Initial lint needed browser globals for deployment config.
Initial build warned about a monolithic bundle/static fixture import; lazy pages and
a separate demo-clock module resolved both. Chromium was initially absent; installed
the actual Playwright browser and reran. The new Node 26 browser contract test needed
an explicit JSON import attribute. Responsive testing detected a real 550px document
at a 390px viewport: an absolutely positioned table accessibility label escaped its
scroll container. Positioning that container fixed it; the browser assertion passed.
Final passing evidence supersedes these development failures without hiding the
unresolved collector failures or unexecuted DB checks.

## Authentic screenshots and live acceptance

Nine captures were created and visually reviewed: seven application screens, one
390px responsive screen, and the actual browser test HTML report. All app captures
visibly show DEMO DATA. GitHub PR screenshot 10 is pending. Exact manual Windows
instructions: screenshots/08-security-dashboard/README.md. No reconstructed interface,
test result or alert image was used. Screenshot references are synthetic service/
event IDs; credentials and private client identities are absent.

Real acceptance still requires:
1. Restore access to the existing Docker host, verify actual WSO2/collector/DB and
   resolve Step 6/7 live verification without recreating persistent containers.
2. Deploy reviewed backend code and owner-run limited grants; run the 32 guarded
   DB checks on a separate disposable test database. Validate frontend Docker config.
3. Start only the approved new dashboard service, or use npm run dev with the real
   loopback APIs. Verify server capabilities using existing private credentials.
4. Send bounded authorized WSO2 requests with existing tooling; match actual gateway,
   persisted rows, monitoring responses and Overview/Traffic results by UTC range.
5. Inspect genuine alerts/evidence/history and allowed changes. Reload, reconnect,
   and verify the persisted state. If no alert exists, preserve the genuine empty state.
6. Verify actual ML readiness/model/report provenance; never relabel synthetic-only
   evaluation or demo anomalies as live detection. Capture live evidence separately.
7. Obtain feature push/PR approval; no merge without separate approval.

## Files and Git

New frontend foundation/config/lockfile, shared UI/client/hooks, seven views, unit/
browser tests and Docker deployment files; new monitoring/dashboard.py and two backend
test files. Updated monitoring/app.py, detection/api.py/provision.py, .gitignore and
README. New compose.step8.yaml, architecture/verification/prepared PR docs, actual
reports and screenshot evidence. Journal and evidence tracker record local checkpoints.
No credentials, runtime database, node_modules, build output or browser traces committed.
PR body is prepared in docs/step-8-pr.md; no push or remote PR is claimed.

For Step 9 planning only: prioritize outstanding live acceptance, production identity/
TLS design, scoped-grant deployment, telemetry completeness and operational monitoring.
No Step 9 implementation is included.
