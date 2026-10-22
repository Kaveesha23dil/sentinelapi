# Step 3.3 verification — 2026-10-22

**Incomplete; no completion commit or push.** Initial worktree clean at e2532f3.
Step 3.2 has an unresolved route requirement: existing `/democommerceapi/1.0.0`
works; the earlier `/democommerce` requirement remains unmet. Asked whether to
accept the existing route. No API replacement, Compose isolation apply, or
rate-policy change occurred while that prerequisite remains unresolved.

## Actual results

| Check | Result |
| --- | --- |
| Docker Compose validation | exit 0, repeated |
| Network membership | both SentinelAPI containers attached |
| DemoCommerce container | running, healthy, still publishes 127.0.0.1:8000 |
| WSO2 container | running; loopback 8243 and 9443 published |
| Publisher inspection | PUBLISHED, APPROVED deployment, OAuth2, six secured operations |
| Gateway GET orders, no token | HTTP 401 |
| Gateway GET orders, malformed token | HTTP 401 |
| Application policy discovery | HTTP 200; 10PerMin exists, 10 requests / 1 minute, stopOnQuotaReach true |
| Gateway GET orders, subscribed token | HTTP 200 |
| Gateway POST order | HTTP 201 |
| Gateway missing order | HTTP 404, expected backend response |
| Gateway read created order | HTTP 200, matches creation |
| Direct backend read-back | HTTP 200, matches gateway |
| Token lifetime | 300 seconds; revocation submitted |
| Backend Pytest | 12 passed, 1 Starlette/httpx deprecation warning, 0.93 s |
| Tooling unittest final run | 18 passed; synthetic tests, not live security proof |
| Container logs | zero ERROR lines in last 100 stdout lines per container; stderr not counted |

An unrelated database container was observed and left untouched. Initial sandbox
Docker lookup failed; approved host execution resolved access. The public local
TLS certificate was saved temporarily for scoped client trust; no private key or
global trust modification. This bootstrap does not independently authenticate a
remote server. The smoke test reused the existing app/subscription and created
one in-memory order. Its redacted result refreshed gateway-verification.json,
which still explicitly reports step_3_2_complete false for the context mismatch.

Commands actually run:

```powershell
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
docker compose config --quiet
docker network inspect sentinelapi-network --format '{{range .Containers}}{{.Name}} {{end}}'
python scripts/integrate_wso2.py --from-container --ca-file <temporary-public-cert.pem> --test-existing
.\demo-services\democommerce\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
python -m unittest discover -s scripts/tests -q
git diff --check
```

## Remaining configuration and verification

1. Resolve the route decision. Then inspect Docker consumers and remove only
   `ports: 127.0.0.1:8000:8000` from compose.yaml. Preserve network/health.
   Validate Compose and run `docker compose up -d --no-deps democommerce`.
   Verify host connection refusal AND WSO2 internal health AND authenticated routing.
2. Admin Portal `https://localhost:9443/admin` → Rate Limiting Policies →
   Application Policies. Inspect existing policy names and quotas. Reuse 10PerMin
   if correct. Only if absent, Add Policy: name 10PerMin, request count 10,
   unit time 1 minute, Save. Do not duplicate or change normal clients' policy.
3. Developer Portal `https://localhost:9443/devportal` → Applications. Search
   SentinelAPIRateLimitClient before adding. Select 10PerMin, JWT, subscribe to
   DemoCommerceAPI 1.0.0 with an allowed subscription tier, and generate Production
   client_credentials keys with a short expiry. Keep credentials in secure runtime
   storage. Preserve SentinelAPITestClient. Publisher Resources must show security
   enabled for all operations; any API change requires save and gateway revision deployment.
4. In a fresh quota window run the command below. Credentials come from
   WSO2_CLIENT_ID/WSO2_CLIENT_SECRET or hidden prompts. Optional WSO2_EXPIRED_TOKEN
   and WSO2_UNSUBSCRIBED_TOKEN are memory-only. Never paste secrets into commands.

   ```powershell
   python scripts/verify_api_security.py --gateway-url https://localhost:8243/democommerceapi/1.0.0 --ca-file <trusted-public-cert.pem> --throttle --results infrastructure/wso2/security-verification.json
   ```

   This checks 401/401/200, host isolation, internal health and observed throttling
   (max 25 GETs). It fails if no 429 is observed or the token is already throttled
   before any 200. Investigate policy propagation/Traffic Manager on failure;
   never increase traffic without bounds. The read-only test creates no orders
   and submits token revocation on exit. Retain the dedicated app for repeatability.
5. Test a genuine expired token and a separate unsubscribed application's token.
   Re-run smoke, backend/tooling tests, Compose validation and sanitized logs.
   Review diff/staged changes for secrets. Commit only when mandatory checks pass:
   `feat: secure DemoCommerce API with OAuth and rate limiting`. Request push approval.

Pending: isolation, expired/unsubscribed tokens, low-quota configuration and actual
429. No Step 3.3 enforcement success is claimed. All eight screenshots are pending;
see screenshots/03-security/README.md. Computer-use inventory had no apps/browsers.

Additional live read: Developer Portal v3 `GET /throttling-policies/application`
returned 10PerMin, 20PerMin, 50PerMin and Unlimited. No policy was added. Reuse
10PerMin rather than following the conditional creation step above. Dedicated
application assignment and enforcement remain pending. Malformed-token testing
used a fixed invalid string, never a real credential.
