# SentinelAPI development journal

## 2026-10-20 — Step 3.2, partial integration preparation

Starting checkpoint: `ce04982` (`feat: implement DemoCommerce FastAPI service`).
Initial working tree contained untracked `AGENTS.md` and an empty
`docs/development-journal.md`; preserved the former and populated this journal.
Inspected README, Compose, ignore rules, existing FastAPI models/routes and tests
before editing. Backend source and Compose were not changed.

Verified the running WSO2 image is `wso2/wso2am:4.5.0`. Both named SentinelAPI
containers are on `sentinelapi-network`. Backend Docker health is healthy;
WSO2 is running with no Docker HEALTHCHECK. Host health returned HTTP 200.
Docker DNS backend health returned HTTP 200 both from the backend container and
from WSO2. Machine-generated sanitized evidence is in
`infrastructure/wso2/environment-verification.json`.

Exported the actual backend OpenAPI response unchanged into
`infrastructure/wso2/democommerce-openapi.json`: OpenAPI 3.1.0, five paths and
six operations, including payment simulation. Structural/reference checks pass;
installed WSO2 import validation remains pending. Prepared supported API import
properties without applying them.

Inspected official WSO2 4.5 documentation and the installed Publisher v4 and
Developer Portal v3 OpenAPI definitions. Exported only the public development
certificate through Docker to a temporary location. Scoped client trust now
validates HTTPS and hostname without `-k`, system-wide trust changes or private
key extraction. Anonymous catalog returned HTTP 200/count 0; this cannot exclude
unpublished APIs. Publisher/Dev Portal settings returned HTTP 200. Candidate
gateway orders URL returned HTTP 404 route-not-found, not the required 401.
No API creation, deployment, publication, application or token success is claimed.

Commands and actual results:

```text
host GET /health                                       HTTP 200, healthy
docker network inspect sentinelapi-network              both containers attached
docker exec sentinelapi-wso2 curl http://democommerce:8000/health
                                                        HTTP 200, healthy
existing venv: python -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
                                                        12 passed, 1 warning, 0.81 s
python3.14.exe scripts/export_democommerce_openapi.py    structural check PASS
python3.14.exe -m unittest discover -s scripts/tests -v  9 passed (tooling unit tests)
scripts/verify_wso2_environment.ps1                     PASS; live evidence saved
```

The backend warning concerns Starlette TestClient's deprecated use of httpx;
no dependency upgrades were made in this integration milestone. The tooling unit
tests use synthetic responses and are not substitutes for live gateway checks.

Added repeatable export, environment verification, authenticated read-only
discovery/validation and gateway smoke tools. Smoke testing requires an actual
invoke URL and a subscribed application's token via environment or hidden prompt.
It checks authentication, expected statuses, response semantics and gateway
write/direct-backend read-back, without printing token values or response headers.

Initial Docker/Python failures were caused by restricted execution context;
approved host checks resolved them. Initial TLS failures were resolved by
per-client public certificate trust. HTTP 8280 is not published; HTTPS 8243 is.
Browser inventory was empty and in-app browser creation failed, so **0/9
screenshots captured**. Detailed safe manual captures are documented in
`screenshots/03-api-integration/README.md`.

Remaining blocker: authenticated Publisher access. Requested the name/path of an
existing local credential source, never its secret value. Exact manual Publisher
and Dev Portal steps, supported REST equivalents, actual results and limitations
are in `docs/wso2-api-integration.md`. No WSO2 authentication was disabled and no
container, database, volume or existing API configuration was replaced.

Step 3.2 remains incomplete. No completion commit or push: the mandatory live
gateway tests have not passed. Push still requires explicit user approval after
a successful completion commit. Step 3.3 and the final blog were not started.

Final access probe: unauthenticated Publisher inventory returned HTTP 401;
anonymous Dev Portal inventory returned HTTP 200/count 0; the candidate gateway
orders route returned HTTP 404. Saved these real results to
`infrastructure/wso2/access-verification.json` with TLS verification enabled.
Final tooling regression run: 9 passed. Reviewed all 13 Step 3.2 files for JSON
syntax, whitespace and common credential patterns; checks passed. The staged
diff is empty and generated Python caches are ignored. Current branch is `main`.


## 2026-10-20 ? Step 3.2 resumption: live gateway verification passed

Found manual checkpoint c7f4aa4, with local main and origin/main tracking at that commit. Authenticated discovery found DemoCommerceAPI 1.0.0 already PUBLISHED at `/democommerceapi`, production endpoint `http://democommerce:8000`, six OAuth-secured resources, Unlimited and an existing gateway deployment. No duplicate API was created. The requested context `/democommerce` still returned gateway HTTP 404.

Resolved the prior credential blocker using the existing configured super_admin values from the WSO2 container in process memory. No secrets were printed or saved. Used supported DCR, Publisher v4 and Dev Portal v3 APIs. The matching installed Publisher component is 9.31.86. WSO2's OpenAPI validator accepted the real exported 3.1.0 document.

A supported Publisher PUT persisted HTTPS transport but retained the original API context. Matching WSO2 source confirms that context is deliberately restored during update. The script now refuses this mismatch before mutation; no API, database, volume or container was deleted or recreated. Requested user decision: accept `/democommerceapi` explicitly, or authorize backup/replacement of only the API to obtain `/democommerce` and restore its subscription.

Created SentinelAPITestClient (JWT, Unlimited), its active Unlimited subscription and production client_credentials key mapping, then reused them on retries. An initial token request for 300 seconds yielded an actual 3,600-second JWT. Rejected that lifetime and submitted the diagnosed unsuitable token for revocation. Updated the supported string property `application_access_token_expiry_time` to 300 on this test application's OAuth configuration. Both the final response and JWT exp minus iat confirmed 300 seconds. Initial attempts before lifetime diagnostics may also have issued one-hour tokens whose values were not retained; these are not the final test token.

Created and deployed revision 3a8ce000-e880-4803-85a9-6ca3e035463b to Default/localhost. Publisher lists it as APPROVED. Its successDeployedTime is null; actual routing tests, not that field, supply runtime proof. Existing revisions remain in history.

Executed against the actual Developer Portal invoke URL `https://localhost:8243/democommerceapi/1.0.0` at 16:51:30 UTC:

| Live check | Actual result |
| --- | --- |
| Orders without token | HTTP 401 |
| Orders with subscribed OAuth token | HTTP 200 |
| Create order | HTTP 201 |
| Nonexistent order | HTTP 404 with backend response |
| Read created order through gateway | HTTP 200, matches creation |
| Direct backend read-back | HTTP 200, identical gateway-created order |

The final token was submitted for revocation after testing. Only redacted IDs, lifetime, deployment details and test results were saved in infrastructure/wso2/gateway-verification.json. Its gateway checks passed flag is true, while requested_context_matches and step_3_2_complete are false pending the context decision.

Rechecked Docker network/health successfully. Existing backend pytest: 12 passed, one Starlette/httpx deprecation warning, 0.97 seconds. Tooling suite: 12 passed, including guards against duplicate API identity and mutation of an API with a different immutable context. Those unit tests are separate from the six live gateway checks. The backend source and Compose were preserved.

Added scripts/integrate_wso2.py, scripts/wso2_local_auth.py and scripts/tests/test_wso2_integration.py. Refreshed evidence and rewrote the integration guide around current results. Browser/app inventory remains empty; 0/9 screenshots captured. The real-screen manual checklist now identifies functional screens ready for capture.

No new completion commit or push in this resumption while the context decision remains pending. c7f4aa4 is the pre-existing manual checkpoint, not evidence that this run's changes are committed. Step 3.3 and the final blog were not started.

Final review: 17 Step 3.2 artifacts passed Python/JSON syntax, whitespace and common credential-pattern checks. Tooling tests reran: 12 passed. Git staged diff is empty; backend and Compose diff is empty. No credential values or private keys were found in reviewed artifacts. Existing cache ignore rules exclude generated Python caches. Context decision is still pending, so no new completion commit was made.

## 2026-10-22 — Step 3.3 preparation and Step 3.2 re-verification

Clean starting worktree at e2532f3. Host Docker access resolved the initial sandbox CLI lookup failure. Both SentinelAPI containers are on sentinelapi-network; DemoCommerce healthy and still published at 127.0.0.1:8000. Compose validation passed. Live Publisher confirmed PUBLISHED, APPROVED gateway revision, OAuth2 and six secured resources. Reused existing application/subscription and reran smoke: no token 401, valid token 200, create 201, missing order backend 404, read-back 200 and matching direct-backend 200. Token lifetime 300 seconds; revocation submitted. One in-memory order created.

The existing context /democommerceapi still differs from the earlier /democommerce requirement; requested user decision before declaring Step 3.2 complete. No Compose apply, WSO2 replacement, policy change or persistent-container recreation. Existing scripts depend on host 8000, so removal requires switching to isolation-aware checks. Added secure runtime-credential security verifier and six synthetic guard tests, including bounded traffic and observed-429 requirements. Final tooling: 18 passed. Backend: 12 passed, 1 deprecation warning, 0.93 seconds. Compose validation exit 0. Sanitized last-100 stdout log check: zero ERROR lines per container; stderr not counted.

Added architecture, verification and genuine screenshot checklist documentation. Computer-use inventory empty; 0/8 screenshots captured. Mandatory isolation, expired/unsubscribed token and actual throttling tests remain pending. No completion commit or push; e2532f3 is the starting checkpoint only. Exact commands, manual configuration and limitations are in docs/step-3-3-verification.md. No PostgreSQL integration or final blog work started.
Additional live checks: malformed token HTTP 401. Developer Portal v3 application policy discovery HTTP 200, existing 10PerMin is 10 requests per one minute with stopOnQuotaReach true; also 20PerMin, 50PerMin and Unlimited. No duplicates created; dedicated assignment and 429 enforcement remain pending.

## 2026-10-22 — Step 4 PostgreSQL foundation

Started clean at dc6df2f. Step 3.3 precheck remains incomplete: backend still publishes host 8000 and no actual gateway 429 was recorded. This foundation does not certify that milestone. Re-ran actual published OAuth gateway routing: 401 without token, 200 with subscribed token, 201 creation, expected backend 404, 200 read-back and matching direct backend 200. Existing token lifetime 300 seconds; revocation submitted. Saved separate sanitized Step 4 precheck evidence rather than modifying earlier milestone records.

Added PostgreSQL 17.11-bookworm, a named volume, an internal database network, pg_isready healthcheck and health-dependent tools runner. No host 5432 mapping; unrelated database, WSO2 and DemoCommerce containers/config preserved. Ignored .env generated locally with random secret, never printed; .env.example has only a rejected placeholder. Dedicated synchronous SQLAlchemy/psycopg module is separate from demo business data and exposes no new HTTP routes or collector.

Autogenerated/reviewed initial Alembic revision 4061c4c0ee19 creates all seven tables with UUID keys, TIMESTAMPTZ, JSONB, FKs/checks/indexes. Main database upgrade head succeeded twice and alembic check found no drift. Guarded disposable test database downgrade/base and upgrade passed. Final database Pytest: 26 passed, zero failures/errors/skips, 1.06 s. An initial Alembic path-separator warning was fixed; final run had no warnings. Existing backend: 12 passed, one unchanged deprecation warning, 0.66 s. Existing WSO2 tooling: 18 passed, distinct from live gateway smoke.

Committed fabricated demo-test events only to dedicated sentinelapi_test_* databases. Marker 04ee5eb5-df0c-47e3-9fae-823c6a6d4055 survived a PostgreSQL restart and was read from a new process at 07:32:52 UTC. Test databases retained; no volumes removed or main-data downgrade. No real WSO2 telemetry is claimed. Final inspected tables/indexes, JUnit counts and restart evidence are in infrastructure/database/database-verification.json. Repeatable verification is scripts/verify_database.ps1.

Computer-use inventory empty: 0/7 genuine screenshots, all pending manual capture under screenshots/04-database. Architecture, workflow, actual results, limitations and Step 5 prerequisites documented. No telemetry ingestion, React dashboard or final blog started. Step 4 database checks pass locally; Step 3.3 remains blocked independently. The associated local checkpoint is the commit adding docs/step-4-verification.md, subject feat: add PostgreSQL persistence for security events (resolve hash with git log -1 --format=%H -- docs/step-4-verification.md). GitHub push requires explicit approval; screenshot evidence of that push remains pending.

## 2026-10-22 — Step 5 real gateway collection

Started clean on feature/api-traffic-collector at cf9abb8, also the main/origin-main checkpoint; git fetch origin succeeded. Branch already existed, so no reset or branch overwrite. Step 3.3 remains incomplete: host backend port 8000 still exposed and no actual 429 evidence. Step 4 migration was verified at head without drift, and the original retained fabricated test marker remained present. No WSO2 container, PostgreSQL volume or unrelated configuration was replaced.

Inspected official WSO2 4.5 API Logs documentation and actual log4j2 configuration. Supported DevOps GET/PUT changed only DemoCommerceAPI OFF to BASIC. Actual API logs contain timestamp/API prefix and inline JSON with request/response flow, method, correlation ID, target and status; requests also contain sourceIP, which is discarded before transport. Observed no latency or stable client identity, so migration 71a9c2e16b05 makes only those measurements nullable, preserving existing data. Missing data remains NULL. STANDARD/FULL never enabled.

Built modular collector, parser, route sanitizer, deterministic completed-response UUIDs, bounded reader/batches, retry/backoff, atomic checkpoints, health and a Windows host bridge with rotation/truncation handling. Transport writes only sanitized data into a named spool via network-disabled helper; collector mounts it read-only and never receives Docker socket/WSO2 credentials. Source transport offsets follow durable spool acceptance; collector acknowledgements follow successful DB commits. Dedicated runtime database roles were authenticated and checked: collector SELECT/INSERT only, monitor SELECT only with transaction read-only; neither can UPDATE/DELETE/create databases/roles.

Added authenticated FastAPI monitoring overview/events/API stats/health, bounded UTC filters/pagination and safe errors on loopback 8010. Initial real proof failed with URLError because Docker did not publish a port from the internal-only database network. Added a separate monitoring network, kept PostgreSQL private, and reran successfully. Actual six-request proof (10:27:22–10:27:36 UTC): 200,200,200,200,404,401; 22 flow records yielded six unique RESPONSE_OUT events, six PostgreSQL rows and six API events. After collector restart and replay, counts stayed six and the replay batch was checkpointed. Both backend 404 and gateway-rejected 401 generated BASIC records here; no universal rejection coverage is claimed. Short-lived test tokens remained memory-only; revocation submitted.

Real PostgreSQL outage test: gateway remained 200, monitoring returned safe 503, collector checkpoint stayed unchanged and one real event was buffered. After PostgreSQL restarted, that event appeared exactly once and monitoring returned 200. Existing/new disposable persistence markers survived PostgreSQL restart and new processes. Test databases retained, never substituted for real telemetry. Final database/collector/monitor suite: 57 passed, 1 AnyIO deprecation warning, 1.18 s (JUnit 1.179); host tooling/bridge simulations: 22 passed, 0.069 s; DemoCommerce: 12 passed, one existing warning, 0.64 s. Alembic upgrade/repeat/drift and disposable downgrade/upgrade passed. No production downgrade, data wipe or invented measurements.

The host bridge is running as an explicit development process, not a Windows service. Stale bridge freshness makes health fail. Source retention loss, timestamp precision/correlation reuse, production transport supervision, TLS/SSO and retention/restore policy remain limitations. Step 5 collection path is verified locally; overall acceptance remains pending Step 3.3 security work, screenshots and PR review. No Step 6 detection, React dashboard or final blog started.

Computer-use inventory had no apps/browsers: 0/8 screenshots, all pending manual capture. Sanitized actual evidence is in infrastructure/telemetry; architecture, commands, limitations and prepared draft PR text are documented. Commits on the feature branch: 090d129 persistence, 7345a5e parser/collector, 48d141f monitoring. The final evidence commit introduces docs/step-5-verification.md (resolve with git log -1 --format=%H -- docs/step-5-verification.md). No feature push or remote PR yet; explicit push approval and separate merge approval required.
Final review: added and executed a bounded busy-lock retry test for the end-to-end verifier; host suite now 23 passed in 0.049 seconds. Runtime snapshot at 10:51:49 UTC matched 21 source completions, 21 PostgreSQL rows and 21 monitoring events, with 200:11 / 201:1 / 401:6 / 404:3. PostgreSQL, collector, monitoring and DemoCommerce healthy; WSO2 running with no configured Docker healthcheck. PostgreSQL host binding remained null. Later authenticated monitoring health and Compose validation passed. No screenshot files appeared; all captures remain pending.

Documentation QA repaired legacy Windows-1252 bytes in the journal to valid UTF-8 while preserving valid existing UTF-8 text; trimmed a trailing blank line from the verification document.

## 2026-10-23 — Step 6 rule-based detection (partial)

Started clean on feature/rule-based-threat-detection at Step 5 merge 3c2be39.
Fetched origin successfully; main base unchanged. The explicit Step 6 request
supersedes the stale milestone marker in AGENTS.md. Inspected collector/schema
and historical genuine telemetry reports; did not treat synthetic fixtures as
live traffic. Docker is unavailable here, so current ingestion/database state and
live alert creation remain unverified. No persistent service or data changed.

Implemented five deterministic strategies, strict config, sliding UTC windows,
verified-client guards, explicit route/auth evidence guards and baseline readiness.
Committed independently verified pure rules/tests as 4cc8368. Additive migration,
incident persistence/evidence, bounded async worker/checkpoints, scoped role
provisioning, six role-protected management routes and safe local simulation are
implemented in the working tree pending PostgreSQL verification. Only API error
rate is eligible for live use; four other rules remain fixture-only/disabled.

Final supported-host suite: 89 passed + four subtests; collector compatible subset:
18 passed, two deselected after their actual Windows os.O_DIRECTORY failures;
DemoCommerce regressions: 12 passed. Final disjoint passing count 119, plus four
subtests. Expanded run before the added migration test: 106 passed, two collector
failures. PostgreSQL/monitoring integration: 27 collected, NOT executed. Compile
and whitespace checks passed. See step-6-verification.md for exact commands,
initial failures, environment recovery and limitations. No invented DB results.

Screenshot inventory returned no apps/browsers. 0/8 captured; exact manual Windows
instructions and checklist saved under screenshots/06-threat-detection. Architecture,
rule catalog, acceptance procedure and unpublished PR text prepared. No push/PR/merge.
Step 6 is incomplete until real PostgreSQL, grants and WSO2 alert proof pass; no
Step 7 implementation started. Documentation commit is discoverable with
`git log -1 --format=%H -- docs/step-6-verification.md`.

## 2026-10-23 — Step 7 experimental ML anomaly detection

Started clean on feature/ml-anomaly-detection at 1770c21. Fetched origin successfully;
HEAD/main/origin-main were identical, including merged Step 6 PR #2. The explicit
Step 7 request supersedes AGENTS.md's historical Step 3.2 marker. Inspected actual
schema, collector, worker, alerts, auth/grants, migrations, tests and prior journal.
The Step 6 merge does not establish runtime acceptance: its journal still records
live PostgreSQL/WSO2 verification pending. Docker is absent here and PostgreSQL was
internal-only; no current database or gateway claim is made. Retained Step 5 evidence
records 21 genuine gateway rows with absent latency/client measurements. No WSO2
configuration, persistent service, volume or existing database data was modified.

Implemented ordered api-60s-v1 feature extraction, five-request eligibility,
deduplication/conflict checks, UTC fixed windows and finalized-minute policy.
Excluded unsupported latency and client identity. Added bounded historical read-only
profiling, per-API deterministic Isolation Forest training, chronological splitting,
version/provenance/schema/environment metadata and trusted checksum-verified local
joblib bundles. Artifacts remain under ignored .runtime; no binary model committed.
Documented deserialization risks, missing data, late-event replay and baseline limits.

Integrated an independent ML transaction into the existing asynchronous worker,
additive ml_windows migration, atomic scores/alerts/evidence/checkpoints, overlapping
rule-alert correlation and scoped grants. Four read-only authenticated ML routes
expose artifact readiness, actual evaluation metadata and filtered/paginated anomalies.
No training/upload route or model execution in the WSO2 request path. Synthetic API
identity cannot be edited to masquerade as a live baseline. All trained models are
experimental and require explicit experimental deployment enablement.

Executed seed-42 controlled generation: 25,953 fabricated events, 540 minutes,
360 normal training minutes and 180 chronological held-out minutes (60 normal,
120 controlled scenarios). Rotating five-minute blocks include benign bursts and
ambiguous moderate volume, deliberately retaining hard cases. Model
iforest-a51ad3e496475a8d: 200 trees, contamination 0.05, random_state 42, n_jobs 1.
ML confusion matrix [[56,4],[66,54]], precision 0.9310344828, recall 0.45,
F1 0.6067415730, FPR 0.0666666667. Actual Step 6 error-rate evaluator on the exact
same events: [[60,0],[96,24]], precision 1.0, recall 0.2, F1 0.3333333333, FPR 0.
These are synthetic results, not production accuracy or proof of malicious intent.
No live latency, anomaly or alert was observed. Re-execution reproduced predictions
and model version. Retained genuine CSV/JSON and three visually inspected PNG charts.

Final supported-host command in step-7-verification.md: 110 passed plus four subtests,
one pre-existing AnyIO deprecation warning. Collector regression: 18 passed and two
existing Windows os.O_DIRECTORY failures, matching Step 6; DemoCommerce: 12 passed.
Disjoint executed total 140 passed, two platform failures, plus four subtests. The
29 PostgreSQL/monitoring integration tests were collected, NOT executed (includes
two new ML alert/evidence/idempotence tests). No false green report. JUnit evidence
retains the actual failures; only trailing whitespace in traceback lines was trimmed.
Compilation, feature/model tests, CLI help and final whitespace/credential-pattern
checks passed. Initial assertions needing updates: expected metadata table count and
DDL guard distinguishing ON DELETE RESTRICT from destructive DELETE FROM. A local
test-file refactoring command initially hit PowerShell quoting/Windows text-decoding
issues; corrected through stdin and explicit UTF-8 before the final passing run.

Created screenshots/07-ml-anomaly-detection with three authentic numbered chart
artifacts. Zero application/terminal/GitHub screenshots captured; six manual captures
remain pending with exact instructions. Architecture/model card/evaluation/verification,
evidence tracker and local PR text are prepared. Step 8 and final internship blog not
started. Step 7 remains experimental until real history, migrations/grants, live
WSO2-to-alert scoring and replay tests are verified on the existing Docker host.

Local checkpoints (no push or merge):
- 33c1d76 feat: add API traffic feature engineering
- dde43d0 feat: implement isolation forest training pipeline
- e0a2c93 feat: integrate ML anomaly scoring
- 0db122b feat: connect ML anomalies to security alerts
- 321fbaa test: add ML detection evaluation and benchmarks
- Final documentation checkpoint: resolve with
  `git log -1 --format=%H -- docs/step-7-verification.md`;
  subject `docs: document ML model and experiment results`.

Remote PR creation remains pending explicit approval to push only the feature branch.

## 2026-10-23 — Step 8 React security dashboard

Started clean on feature/security-dashboard at c8fad4a, merged Step 7 PR #3.
Fetched origin and confirmed HEAD/main/origin-main were identical. No dependency
branch needed, no reset/discard. Reviewed the empty frontend, actual backend routes,
auth/schema/grants, Compose, tests and Step 7 evidence. The explicit Step 8 request
supersedes AGENTS.md's historical milestone. Step 7 remains experimental despite
its merge. Docker/current PostgreSQL and the prior live acceptance remain unavailable.
No WSO2 config, persistent container, database data or volume was changed.

Built seven dark responsive React/TypeScript/Vite views using the requested palette,
Inter, Tailwind, official shadcn component sources, Router, TanStack Query, Recharts,
Lucide and Zod. Retained exact dependency versions and lockfile. Added typed validated
contracts, shared loading/empty/error/partial states, safe endpoint display, accessible
navigation, time filters, pagination, page-limited alert sorting, incident evidence/
audit, analyst/admin status confirmation, admin rule controls and ML provenance.
Synthetic-only evaluation is explicitly experimental; no anomalous behavior is
classified as proven malicious intent. API health/client identity/latency remain
unavailable where unsupported. Collector UUIDs are not labeled gateway correlation IDs.

Added actual authenticated read-only backend inventory/timeseries/endpoint aggregates,
server method/status filters, session capabilities and sanitized incident event/audit
queries. No schema migration. Limited new security role grants are implemented but
not applied here. Live tokens are supplied through a password dialog and verified
against backend capabilities; kept only in memory, never storage/URLs/query keys or
environment bundles. Independent credentials permit partial source access. Demo is
explicit, persistently labeled, read-only and never a live-error fallback. Production
Docker config disables its entry. No SSE/WebSocket infrastructure exists, so live
active views poll every 30s with background/inactive polling stopped appropriately.

Added isolated frontend Docker/Nginx/Compose configuration, loopback 8080 and only
monitoring-network; same-origin proxies avoid wildcard CORS/database exposure. Not
Docker-validated/applied here. Development browser URL: 127.0.0.1:5173 via npm run dev.
Production identity/TLS/BFF review is still required before external deployment.

Executed final checks: frontend lint zero errors/warnings; TypeScript and production
build pass; 32 component/client/contract tests pass. Five actual Chromium browser
tests pass, including axe A/AA scans for all seven desktop screens, mobile layout,
filters/pagination/refresh, demo isolation, and explicitly mocked capability-driven
updates/reload/reconnect and 401/403 handling. Mocked persistence is not real DB proof.
Backend/tool regressions: 126 passed plus four subtests, one existing AnyIO warning.
Collector/demo: 30 passed and two unchanged Windows os.O_DIRECTORY failures. Python
disjoint total 156 passed, two known platform failures, plus four subtests. The
32 real PostgreSQL/monitoring checks were collected, NOT executed, including three
new dashboard SQL/evidence/history checks. Actual reports retained under
infrastructure/dashboard; failure trace whitespace only was normalized for Git.

Resolved sandbox npm EACCES through approved installation; initial demo-config/lazy
test waits/duplicate selectors; deployment JS lint globals; bundle split/static demo
import warnings; missing Chromium; Node 26 JSON import attribute. Browser testing
found genuine mobile overflow from an absolutely positioned table accessibility label;
positioned its scroll container and verified 390px document width. Final build has
separate route/chart/fixture chunks without chunk-size warnings. Formatted source
with pinned Prettier for maintainability. Credential-pattern review found no matches.

Captured and visually reviewed nine real screenshots: seven demo-labeled app views,
one 390px responsive view, and actual five-pass Playwright HTML report. No generated/
reconstructed UI or test summary. GitHub PR capture 10 pending approval and actual PR.
README, architecture, verification, evidence tracker and concrete local PR body are
prepared. Step 8 implementation is ready for review; real WSO2 -> persisted traffic
-> dashboard, actual incident updates and ML provenance acceptance remain pending.
No Step 9 implementation or final technical blog. Task-owned preview/report processes
were identified for cleanup; npm run dev is the documented way to reopen the app.

Local checkpoints, no push or merge:
- 48ef53b chore: initialize SentinelAPI React dashboard
- 552dc46 feat: build security overview and API traffic pages
- 508a0b2 feat: add security alerts and incident investigation
- 70fb4c9 feat: add ML monitoring and detection rule views
- 227b518 test: add dashboard component and browser tests
- Documentation checkpoint: `git log -1 --format=%H -- docs/step-8-verification.md`,
  subject `docs: document dashboard architecture and usage`.

Prepared PR: docs/step-8-pr.md. Explicit approval is required before pushing only
feature/security-dashboard; separate approval is required before merge.
