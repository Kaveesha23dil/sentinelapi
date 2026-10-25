# Choreo deployment review — 2026-10-24

## Status and findings

Not deployed. No cloud endpoint has been obtained or verified. No push, cloud
build trigger, or deployment was performed. Compose and persistent containers
were preserved. This user-authorized cloud preparation supersedes the older
Step 3.2 scope marker for this task.

Initial working tree: clean, branch `feature/choreo-deployment`.
`git ls-remote origin refs/heads/feature/choreo-deployment` returned
`aae898ea421833fa41ca1a24991410dfdfcccc69`, matching HEAD/tracking branch.
That pushed commit contains `backend/Dockerfile.choreo` and `USER 10002`.
New changes remain local and uncommitted.

The original Dockerfile builds successfully with context `backend`. Requirements,
Python 3.12, startup `sentinelapi.monitoring.app:app`, bind `0.0.0.0:8001`, and UID
10002 work locally. Dependency installation used cached layers; no clean-download
or cloud vulnerability-scan pass is claimed. The image excludes ML training packages.

No Choreo manifest was tracked. Added context-local schema 1.2 component manifests
for backend port 8001 and frontend port 8080. Both use Project visibility; review
any public exposure separately. Backend base path is `/`; schemaFilePath is omitted
for the documented wildcard-route default. Validate endpoint preview in console.

The user-reported GraphQL HTTP 500 and empty build table suggest failure during
build submission, before normal image-build logs exist. This is an inference,
not a confirmed platform outage. Saved source paths, repository access, permissions,
missing configuration, stale metadata and orchestration faults remain candidates.
Only WSO2 can trace correlation ID `09415394-0f98-4140-9579-4b11d6595145`.

Chrome had a Choreo-titled window, but automation could not reliably inspect its
target window. No private APIs were replayed, no session credentials were read,
and no usable console screenshot was saved. HTTP 500 evidence remains user-reported.

## Supported UI workflow — after approval

1. Verify Choreo GitHub App access to `Kaveesha23dil/sentinelapi`. Review the saved
   source: branch `feature/choreo-deployment`, Docker preset, context `/backend`,
   Dockerfile `/backend/Dockerfile.choreo` (repository-relative console paths).
2. After an approved push, confirm the selected SHA and detected REST endpoint,
   port 8001, base path `/`, Project visibility. Do not change context to repository
   root with the existing backend Dockerfile.
3. Open Build and choose **Build Latest**. Confirm a build ID appears, then inspect
   status, logs and security scans. If HTTP 500 occurs without a build record,
   capture only sanitized response text, correlation ID and exact UTC request
   time; use the support draft instead of repeated retries.
4. Before deployment, rotate and revoke all compromised API tokens and DB passwords
   at their issuers. Update dependent secrets together and verify old values fail.
   Rotation was not performed in this review. Never supply secrets through chat.
5. Configure runtime DB settings and secrets, `MONITORING_API_TOKEN`, and distinct
   `SECURITY_READER_TOKEN`, `SECURITY_ANALYST_TOKEN`, `SECURITY_ADMIN_TOKEN` for
   required roles. Configure port 8001 and process probe `/healthz`.
6. Deploy only after approval. Copy the actual environment-specific URL from the
   console/connection. Verify `/healthz` returns 200, authenticated session and
   database-backed routes work, and unauthorized requests remain rejected.
   A process probe alone is not cloud deployment acceptance.

## Supported CLI commands

Neither `wdp` nor `choreo` was installed in PATH. Current official documentation
uses `wdp`. Follow its Windows installation instructions and check `wdp --help`.
These documented command forms were not executed. Replace PROJECT, COMPONENT,
TRACK and BUILD_ID with real identifiers; display names may differ from identifiers.

```powershell
wdp --version
wdp login
wdp list components --project=PROJECT
wdp describe component COMPONENT --project=PROJECT
# Build submission only after approval
wdp create build COMPONENT --project=PROJECT
wdp describe build BUILD_ID --project=PROJECT --component=COMPONENT
wdp logs build --project=PROJECT --component=COMPONENT --deployment-track=TRACK --build-id=BUILD_ID
# Deploy only after approval and credential rotation
wdp create deployment COMPONENT --env=Development --project=PROJECT --build-id=BUILD_ID
wdp describe deployment --project=PROJECT --component=COMPONENT --env=Development -o json
```

The documented CLI is the supported automation route established in this review.
No separate public build REST API contract was established; do not replay or
reverse-engineer console GraphQL requests.

## React deployment

Existing local Dockerfile and proxy still use `monitoring:8001`. New independent
`frontend/Dockerfile.choreo` uses numeric UID 10002 and a TLS-verifying Nginx proxy.
Choose a Web Application component, Docker context `/frontend`, Dockerfile
`/frontend/Dockerfile.choreo`, port 8080. Set server-side `SENTINEL_API_URL` to
the **actual verified HTTPS API base URL**, including gateway prefix if present
and a trailing slash. Missing/insecure values fail startup. This is public routing
configuration, never a token or URL containing credentials.

Both browser API prefixes proxy to that URL, retaining same-origin browser calls
and the existing CSP. No CORS relaxation or frontend embedded credential is needed.
The actual endpoint cannot be wired or tested until one exists. `https://wso2.com/`
was used solely for local Nginx syntax validation, not as a SentinelAPI endpoint.
Nginx resolves upstream at startup; roll the dashboard if upstream DNS changes.

Prefer the project connection URL. A public Choreo gateway's OAuth token does not
automatically satisfy backend service-token authentication. Resolve gateway versus
application Authorization before accepting a public route. Existing session UI
supplies credentials at runtime; production end-user identity/BFF integration is
a separate decision, and service tokens are not user identity.

## Cloud PostgreSQL and separate processes

Use managed PostgreSQL reachable from the selected data plane, restricted ingress,
backups/PITR, adequate storage and connection budgets across replicas. Set
`POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER` and secret
`POSTGRES_PASSWORD`. Optional `POSTGRES_SSLMODE=verify-full` and
`POSTGRES_SSLROOTCERT=/certificates/postgres-ca.pem` enable certificate/hostname
verification using a provider CA mount. Existing local defaults are preserved.

Run `python -m alembic upgrade head` from backend in a controlled migration job
with a migration owner, after backup/staging validation. Provision existing
telemetry/detection roles through reviewed tools; restrict API/worker/collector
privileges. No cloud migration or credential rotation was executed.

Deploy detection separately with `python -m sentinelapi.detection.worker`, not in
Uvicorn. Its ML Dockerfile needs repository-root context, separate ML requirements,
and its named USER changed to numeric 10002 before Choreo use. Validate model
provenance/hash, persistent artifacts, resources, retries and concurrency before
that separate deployment. The monitoring image does not install numpy/scikit-learn.

Deploy collector separately with `python -m traffic_collector.main`, close to
gateway logs or using a supported secure telemetry transport. Its existing
Dockerfile also needs repository-root context and a numeric USER change before
Choreo use. Preserve spool/checkpoints and coordinate replicas. Choreo cannot
implicitly read the local WSO2 container filesystem. The API's existing
`/collector-state/health.json` check needs a new health transport for independent
cloud components; monitoring health will otherwise report stale/unavailable.
`/healthz` intentionally checks process availability only.

## Verification and actual results

```powershell
# Repository root
docker build -f backend/Dockerfile.choreo -t sentinelapi/monitoring:choreo-check backend
docker run --rm --network none sentinelapi/monitoring:choreo-check python -c "import os; from sentinelapi.monitoring.app import app; print(os.getuid()); print(app.title)"
docker run --rm --network none sentinelapi/monitoring:choreo-check python -m pytest -q -p no:cacheprovider tests/test_cloud_database.py tests/test_cloud_probe.py tests/test_validation.py tests/test_runtime_startup.py tests/test_security_api.py tests/test_dashboard_api.py tests/test_detection_rules.py tests/test_detection_migration.py tests/test_ml_features.py
docker build -f frontend/Dockerfile.choreo -t sentinelapi/dashboard:choreo-check frontend
docker run --rm -e SENTINEL_API_URL=https://wso2.com/ sentinelapi/dashboard:choreo-check nginx -t
# In frontend/
npm.cmd test
npm.cmd run build
npm.cmd run lint
```

- Both final Docker builds passed (cached dependency layers).
- FastAPI import passed at UID 10002; final process probe returned HTTP 200.
- Focused backend suite: **106 passed**, one Starlette/AnyIO deprecation warning.
- Frontend: **37 passed** in four files; build and lint passed.
- Nginx template and syntax check passed. Missing URL and HTTP URL startup checks
  rejected configuration as intended.
- Broad backend pytest failed collection in two ML modules (missing numpy).
  Excluding those two modules: **108 passed, 1 failed, 22 errors**. Failure expects
  `/compose.yaml` outside the backend image; errors require a configured PostgreSQL
  test database. No private DB secrets were supplied. This is not a full-suite pass.

## Official sources checked

- [Docker services and UID requirements](https://wso2.com/engineering-platform/developer-platform/docs/develop-components/develop-services/develop-a-service-with-docker/)
- [Schema/location and wildcard route default](https://wso2.com/engineering-platform/developer-platform/docs/develop-components/manage-component-source-configurations/)
- [CLI installation, build, status, logs and deployment](https://wso2.com/engineering-platform/developer-platform/docs/choreo-cli/get-started-with-the-choreo-cli/)

## Commit preparation

Base: `aae898ea421833fa41ca1a24991410dfdfcccc69`. Proposed message:
`feat: prepare isolated Choreo deployment configuration`. Changes remain uncommitted
for review; nothing pushed. Remaining blockers: rotation, approved push, source
settings validation, build-submission diagnosis, cloud DB/migrations, separate
worker/collector health design, real URL wiring and cloud acceptance testing.
