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
