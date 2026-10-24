# Safe local deployment and reproduction

Baseline `f931455`, original documentation audit 2026-10-24. This is a source-reviewed runbook, not a verified one-command deployment. A subsequent [focused runtime repair](detection-runtime-repair.md) accessed Docker through the host environment and verified controlled rule alerts, authenticated monitoring and selected service startup. Read that report for actual executed commands and current results. Existing WSO2, PostgreSQL and volumes were preserved.

## Prerequisites and private configuration

Docker Desktop/Compose on host PATH; Python 3.12; Git; compatible Node/npm; existing separately managed WSO2 4.5.0; trusted local public certificate matching the gateway hostname. Compose does not provision WSO2 or provide a complete restore bundle.

Copy `.env.example` only if `.env` is absent. Replace all relevant placeholders with distinct private owner/collector/monitor/detector/security passwords and role-specific bearer tokens. Never overwrite existing secrets or put them in screenshots, Vite variables or commands. `.env` is ignored. Compose substitution does not export its values into the host process environment.

```powershell
git status --short --branch
docker version
docker compose version
docker ps -a --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
docker network inspect sentinelapi-network
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step8.yaml config --quiet
```

Only use `config --quiet` in evidence: expanded output exposes secrets. Inspect selected state/mount/network fields, not entire environments. On a new installation only, create a missing `sentinelapi-network` and attach the separately provisioned gateway after review. Preserve existing WSO2 configuration, embedded storage and credentials. Back up WSO2 and PostgreSQL externally and validate restoration before cutover; no automated restore is verified here.

Never use volume deletion, `down -v`, project DB downgrade or unreviewed container recreation. Startup below uses `--no-recreate`; stale services may need an explicitly approved deployment change.

## Local Python/frontend

Use an installed Python 3.12 interpreter. A copied virtual environment can point to a missing executable (the older DemoCommerce environment does on this host). The existing `.venv-step6` works for audit tests. Create it only if absent; inspect before modifying an existing environment.

```powershell
py -3.12 -m venv .venv-step6
.\.venv-step6\Scripts\python.exe -m pip install -r backend/requirements-ml.txt -c backend/requirements-ml-constraints.txt
.\.venv-step6\Scripts\python.exe -m pip install -r demo-services/democommerce/requirements.txt
$env:PYTHONPATH='backend;collector;scripts'
# Separate frontend terminal
cd frontend
npm.cmd ci
npm.cmd run dev
```

Audit dependency advisories before external use; pinned versions are not a security certification. Open http://127.0.0.1:5173 and Explore demo for explicit read-only fixtures. `frontend/.env.example` configures upstreams 8010/8020, not credentials. Connect backend only after real services are ready.

## Database bootstrap and migrations

Build tools/images without replacing running services; after external backup and revision review:

```powershell
docker compose build persistence collector democommerce
docker compose up -d --no-recreate postgres
docker compose --profile tools run --rm --no-deps persistence alembic current
docker compose --profile tools run --rm --no-deps persistence alembic upgrade head
docker compose --profile tools run --rm --no-deps persistence alembic check
```

Wait for database readiness before running tools. Head is `b7d000000001` after `a6d1023f0001`, `71a9c2e16b05` and `4061c4c0ee19`. Upgrade initializes an empty schema or applies pending revisions without resetting traffic. Changing POSTGRES_PASSWORD in `.env` does not rotate an initialized database's owner password automatically.

Provision runtime roles using the owner credential. Detection provisioning creates missing roles and refreshes scoped grants without rotating existing passwords; rotation now requires explicit `--rotate-existing-passwords`. Telemetry role provisioning is separate and can rotate its existing passwords, so use the intended secrets rather than generating mismatches.

```powershell
docker compose --profile tools run --rm --no-deps persistence python -m sentinelapi.db.provision_telemetry_roles
# Private .env substitution now passes these two optional secrets into owner tools.
docker compose --profile tools run --rm --no-deps persistence python -m sentinelapi.detection.provision
```

Real DB tests need a separate guarded `sentinelapi_test_*` database with migrations; never point them at project data. See [database architecture](database-architecture.md) and `scripts/verify_database.ps1`. That script includes a PostgreSQL restart unless `-SkipRestart`; obtain approval for disruptive checks. It retains test DBs for inspection. Current audit collected 32 DB tests without executing them.

## Restore/inspect WSO2 API configuration

1. Preserve protected WSO2 storage and export actual definitions/revisions/application/subscription settings before changes. Checked-in OpenAPI/properties are not a full restore bundle; no clean-machine WSO2 recovery is claimed.
2. Inspect DemoCommerceAPI 1.0.0 at `https://localhost:9443/publisher`. Actual context is `/democommerceapi`; properties JSON holds requested `/democommerce`, not the deployed context. Do not import a duplicate or edit the database to hide this difference.
3. Use `infrastructure/wso2/democommerce-openapi.json` for six secured operations. Backend is `http://democommerce:8000` through Docker DNS; gateway-local localhost is wrong.
4. Confirm mandatory OAuth2 and secured resources, save and deploy a revision to the actual Default environment/vhost, publish, and verify the Developer Portal application/subscription. Publishing alone does not prove routing.
5. Reuse the test application where possible. Keep short-lived OAuth credentials private, trust the reviewed public certificate via `WSO2_CA_FILE`, and revoke test tokens afterward.

Read [integration details](wso2-api-integration.md) before running `scripts/integrate_wso2.py --from-container --test-existing`. It uses Docker authority for local management access and exercises writes, including a demo order; it is not read-only inventory. No TLS-verification bypass is acceptable.

For rate limits, inspect 10PerMin and assign a dedicated test application after approval; preserve normal clients. With authorized credentials and a fresh quota window, the bounded `scripts/verify_api_security.py --gateway-url https://localhost:8243/democommerceapi/1.0.0 --ca-file <trusted-public-cert.pem> --throttle --results <private-review-output.json>` sends at most 25 GETs. No observed HTTP 429 is currently retained. Unlimited configuration does not prove quota enforcement.

## Collector, APIs and detector

```powershell
docker compose up -d --no-recreate democommerce collector monitoring
docker compose -f compose.yaml -f compose.step6.yaml build detector
docker compose -f compose.yaml -f compose.step6.yaml up -d --no-recreate --no-deps detector security-api
```

Detector/security share the built image. Existing services remain on old code until an approved update. Compare deployed routes/image IDs to source before claiming acceptance.

Enable BASIC logging only for the intended API through the supported DevOps API; inspect `scripts/configure_api_logs.py` and [telemetry architecture](telemetry-architecture.md). Do not enable FULL payload logging for evidence. Start the explicit host bridge in a separate terminal:

```powershell
$env:PYTHONPATH='backend;collector;scripts'
.\.venv-step6\Scripts\python.exe scripts/bridge_api_logs.py --follow
```

Compose does not launch this bridge; missing bridge activity makes telemetry stale. The host checkpoint writer already guards POSIX-only directory fsync, and the deployed transport helper runs inside Linux. That actual Windows-host/Docker bridge path worked in the focused repair. Direct Windows transport unit fixtures still hit O_DIRECTORY; their portability fix remains on unmerged `test/end-to-end-validation`. Those fixture failures were not the cause of the stale bridge in this validation.

## Experimental ML

Offline reproduction needs no live DB:

```powershell
$env:PYTHONPATH='backend'
$env:MPLCONFIGDIR='.runtime/step10/matplotlib'
.\.venv-step6\Scripts\python.exe -m sentinelapi.ml.experiment --output .runtime/step10/ml-evaluation --artifacts .runtime/step10/ml-artifacts
```

Use fresh artifact roots on repeats; save refuses overwrite. This generates synthetic data/charts, not gateway traffic. Keep historical evidence unchanged. For real-history profile/train, use `sentinelapi.ml.cli` with explicit aware UTC ranges, a verified API UUID and chronological split; [evaluation instructions](ml-evaluation.md).

Optional deployment: set `ML_MODEL_HOST_DIR` to one immutable reviewed model-version directory, `ML_APPROVED_SHA256` to an independently approved artifact hash, and explicitly enable `ML_ALLOW_EXPERIMENTAL=true`. Hashes are not signatures; joblib can execute code. A synthetic model cannot score an unrelated live API by changing metadata.

```powershell
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step7.yaml config --quiet
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step7.yaml build detector
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step7.yaml up -d --no-recreate --no-deps detector security-api
```

These start new services but preserve existing image/config. Replacing an existing detector/security deployment requires approval. Rules and ML have independent transactions/failure handling; neither runs in the gateway request path.

## Controlled traffic and real acceptance

```powershell
# Privately supply WSO2_SIMULATION_TOKEN and WSO2_CA_FILE in the process environment.
$env:PYTHONPATH='backend;collector;scripts'
.\.venv-step6\Scripts\python.exe scripts/simulate_threat_traffic.py normal
.\.venv-step6\Scripts\python.exe scripts/simulate_threat_traffic.py error-rate
```

The helper allows only the local gateway and at most 24 read-only GETs, two seconds apart, stopping on 401/403/429. The error scenario requests nonexistent orders. Inspect generated outcome files before publishing correlation references. HTTP outcomes alone do not prove ingestion/detection. Match actual BASIC completions, DB event IDs, monitoring counts and alert evidence over the same UTC interval; allow bridge polling, backlog and 120-second lateness. Unrelated normal traffic may prevent the ratio threshold. Preserve empty states if no real alert exists.

Connect the real dashboard, verify capabilities, investigate actual evidence and reload/reconnect to check persisted changes. Fixture/mocked tests do not establish this chain.

Optional Nginx dashboard (both API upstreams must exist on monitoring-network):

```powershell
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step8.yaml build dashboard
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step8.yaml up -d --no-recreate --no-deps dashboard
```

Loopback 8080 uses production config with demo disabled. This Docker frontend has not been accepted live here. Other loopback ports: 8000 backend, 8010 monitoring, 8020 security/ML, 5173 Vite, 9443 management, 8243 gateway. No host DB port.

## Safe shutdown

Ctrl+C the host bridge and foreground Vite process. Preserve containers/networks/volumes:

```powershell
docker compose -f compose.yaml -f compose.step6.yaml -f compose.step8.yaml stop dashboard detector security-api monitoring collector democommerce
# Only when deliberately ending database availability:
docker compose stop postgres
```

Use the same ML overlay if active, with its required environment set. WSO2 is independent; stop it separately only when intended. No data deletion or reset is needed. [Actual audit verification](final-verification.md).
