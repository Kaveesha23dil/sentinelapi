# Step 3.2 — DemoCommerce and WSO2 integration

Verification date: 2026-10-20. **Status: partial; gateway integration is not yet
complete.** Docker/network and backend checks pass. Real OpenAPI exported;
authenticated Publisher discovery, API import, revision deployment, publication,
subscription and token-based gateway tests remain pending because no existing
WSO2 credential or scoped token was available to this session. No WSO2 API,
container, volume, database or authentication setting was changed.

## Environment and evidence

| Component | Observed state |
| --- | --- |
| Host | Windows, PowerShell, Docker Desktop |
| WSO2 | `sentinelapi-wso2`, image `wso2/wso2am:4.5.0`, running; no Docker HEALTHCHECK configured |
| WSO2 published ports | `127.0.0.1:9443` management; `127.0.0.1:8243` HTTPS gateway; HTTP 8280 is not published |
| Backend | `sentinelapi-democommerce`, image `sentinelapi/democommerce:local`, running and Docker healthy |
| Backend port | `127.0.0.1:8000` |
| Network | Both containers attached to `sentinelapi-network` |
| Backend runtime | Existing Dockerfile uses `python:3.12-slim`; host test venv declares Python 3.12.10 |
| Backend API | DemoCommerce API 1.0.0, OpenAPI 3.1.0 |
| Repository starting commit | `ce04982 feat: implement DemoCommerce FastAPI service` |

`infrastructure/wso2/environment-verification.json` is machine-generated,
sanitized evidence from the live environment, with its own UTC timestamp.
`infrastructure/wso2/access-verification.json` records the actual TLS-verified
catalog, Publisher authorization and unsuccessful candidate gateway probes.
`compose.yaml` manages the backend only and references an external network.
The separately managed WSO2 container was preserved. Do not use Compose to
recreate it or assume the repository contains its complete provisioning history.

## Architecture and routing

The intended request path is client → HTTPS WSO2 gateway → Docker DNS name
`democommerce:8000` → existing FastAPI route. The Publisher configures APIs;
Developer Portal exposes published APIs and subscriptions; the Key Manager
issues OAuth tokens; the gateway enforces authentication/subscription policy
and forwards accepted requests. Publishing and deploying are distinct actions:
a catalog entry does not prove a gateway revision is running.

The requested API context is `/democommerce`, version `1.0.0`. WSO2 commonly
exposes a versioned context, but **the deployed context and invoke URL have not
been verified**. The candidate
`https://localhost:8243/democommerce/1.0.0/api/v1/orders` currently returns the
gateway's HTTP 404 route-not-found body. This does not demonstrate OAuth
enforcement. Once deployed, copy the actual HTTPS API base URL from Developer
Portal and confirm it against Publisher deployment details. The gateway strips
the API context/version and preserves `/api/v1/orders` for the backend.
`localhost:8000` inside WSO2 would refer to the WSO2 container, so the correct
production endpoint is `http://democommerce:8000`.

## API artifacts and supported interfaces

`infrastructure/wso2/democommerce-openapi.json` is the unmodified byte export
of `http://localhost:8000/openapi.json`. It contains these actual operations:

| Method | Backend path |
| --- | --- |
| GET | `/health` |
| GET | `/api/v1/users/me` |
| GET, POST | `/api/v1/orders` |
| GET | `/api/v1/orders/{order_id}` |
| POST | `/api/v1/payments/simulate` |

All expected methods and local `$ref` targets pass the structural check. This
is not a full OpenAPI conformance check or proof WSO2 accepts OpenAPI 3.1.
Installed Publisher validation/import must still be run. Do not silently change
the exported version or remove schema constraints if import rejects it; retain
this source and document any separately derived compatibility artifact.

`democommerce-api-properties.json` is **prepared, not applied**. Its fields
match the installed Publisher API schema: API name/context/version, HTTP API,
Synapse gateway, HTTPS transport, OAuth2, Unlimited plan and production endpoint.
No alternate unauthenticated configuration was prepared.

Official references:

- [WSO2 4.5 product APIs overview](https://apim.docs.wso2.com/en/4.5.0/reference/product-apis/overview/)
- [WSO2 4.5 Publisher API v4](https://apim.docs.wso2.com/en/4.5.0/reference/product-apis/publisher-apis/publisher-v4/publisher-v4/)

Also inspected the actual installed `publisher-api.yaml` and `devportal-api.yaml`
under `/home/wso2carbon/wso2am-4.5.0/repository/deployment/server/webapps/`.
They document Publisher v4, Developer Portal v3, scoped OAuth, OpenAPI
validation/import, revision deployment, application key and token generation.
Temporary copies were placed outside Git. Authentication is required to discover
unpublished APIs: an empty anonymous Developer Portal list does not prove there
are no existing Publisher APIs.

## Reproduce environment and schema checks

Run from the repository root in host PowerShell, with Docker Desktop running:

```powershell
.\scripts\verify_wso2_environment.ps1
.\demo-services\democommerce\.venv\Scripts\python.exe scripts/export_democommerce_openapi.py
.\demo-services\democommerce\.venv\Scripts\python.exe scripts/export_democommerce_openapi.py --check
.\demo-services\democommerce\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
.\demo-services\democommerce\.venv\Scripts\python.exe -m unittest discover -s scripts/tests -v
```

Export the **public certificate only** through the trusted Docker access path:

```powershell
docker exec sentinelapi-wso2 sh -c 'echo | openssl s_client -connect localhost:9443 2>/dev/null | openssl x509 -outform PEM' | Set-Content -Encoding ascii "$env:TEMP/sentinelapi-wso2-public.pem"
$env:WSO2_CA_FILE = "$env:TEMP/sentinelapi-wso2-public.pem"
```

This trusts that certificate in the Python client only. It does not import a
machine-wide root, export a private key, skip hostname validation or use `-k`.
Observed certificate: self-signed, CN/SAN `localhost`, valid 2025-02-13 through
2027-05-19. For a different host, use the correct trusted CA and matching hostname.

For authenticated discovery, obtain an existing Publisher token with
`apim:api_view` (or the documented list scope) and `apim:api_create` or
`apim:api_manage` for validation. Use the hidden prompt:

```powershell
.\demo-services\democommerce\.venv\Scripts\python.exe scripts/discover_wso2.py
```

The tool paginates the Publisher catalog, prints only matching API identity
fields and WSO2's OpenAPI validation boolean, and makes no configuration changes.
It accepts `WSO2_PUBLISHER_TOKEN` as an alternative to the hidden prompt. Do not
type tokens into command lines or save shell transcripts containing credentials.
This authenticated tool is prepared but **not executed against WSO2** yet.

## Exact remaining Publisher procedure

Browser automation is unavailable in this session. Perform these steps using
the existing local administrator account; do not send credentials in chat.

1. Open `https://localhost:9443/publisher`. Trust the verified local development
   certificate through your normal local trust process. Sign in using the existing
   account. Search all APIs for both `DemoCommerceAPI` and context `/democommerce`.
   Inspect any match and version before creating anything. Reuse an exact match;
   stop and review a conflicting context/name rather than deleting or duplicating it.
2. If absent: select **Create API > REST API > Import Open API**. Upload
   `infrastructure/wso2/democommerce-openapi.json`. Run validation. Stop if it
   fails, recording the actual error; do not invent or silently rewrite endpoints.
3. Set name `DemoCommerceAPI`, context `/democommerce`, version `1.0.0`,
   endpoint `http://democommerce:8000`, and create the API. The installed REST
   equivalent is `POST /api/am/publisher/v4/apis/import-openapi`, multipart fields
   `file` and `additionalProperties` (the prepared JSON properties file).
4. In **API Configurations > Endpoints**, confirm/save the production endpoint.
   In **Resources**, verify all six operations above and retain authentication
   on every operation (`Application & Application User`). In **Runtime** or
   **Security**, select OAuth2; retain mandatory authentication and subscription
   validation. Do not select API Key as a substitute or disable operation security.
5. In **Subscriptions**, enable the `Unlimited` subscription policy for local
   testing. Confirm/save changes. Keep gateway transport HTTPS.
6. Open **Deploy > Deployments**, create a revision with description
   `Step 3.2 DemoCommerce integration`, choose the actually listed local gateway
   environment and its vhost, and deploy. Wait for confirmed successful deployment.
   REST equivalents: `POST /apis/{apiId}/revisions` with a description, then
   `POST /apis/{apiId}/deploy-revision?revisionId={revisionId}` with an array of
   `{name, vhost, displayOnDevportal:true}` objects using discovered gateway values.
   Do not assume an environment name or discard existing revisions to free space.
7. Open **Lifecycle** and choose **Publish**. REST equivalent:
   `POST /apis/change-lifecycle?action=Publish&apiId={apiId}`. Check the API is
   `PUBLISHED`; re-read `/apis/{apiId}/deployments` and confirm deployment.
8. In Developer Portal, inspect the API and copy its actual HTTPS invoke URL.
   Do not derive the URL from the requested context alone. Record the actual
   context, revision and environment in this document after successful verification.

## Application, subscription and OAuth flow

1. Open `https://localhost:9443/devportal`, sign in, and find the published API.
2. Under **Applications**, search for `SentinelAPITestClient`. Reuse it if
   present; otherwise add it with `Unlimited` application throttling and JWT
   token type. The subscription plan and application policy are separate limits.
3. Subscribe that application to `DemoCommerceAPI` version `1.0.0`, plan
   `Unlimited`. Confirm the subscription is active, not merely workflow-pending.
4. In the application's **Production Keys > OAuth2 Tokens**, use the resident
   Key Manager and generate keys with `client_credentials` grant support. Reuse
   existing suitable keys; do not regenerate or expose the consumer secret.
5. Generate an application access token for **300 seconds**. Confirm the actual
   returned expiry; request duration alone is not proof of the lifetime. Keep it
   only in the hidden smoke-test prompt or a process environment variable.
6. The installed REST equivalents are Dev Portal v3 `/applications`,
   `/subscriptions`, `/applications/{applicationId}/generate-keys`, and
   `/applications/{applicationId}/oauth-keys/{keyMappingId}/generate-token`.
   Key generation uses `keyType: PRODUCTION` and
   `grantTypesToBeSupported: [client_credentials]`. Token generation uses
   `validityPeriod: 300`, `consumerSecret` and supported scopes. Never save/print
   the raw key-generation or token response. Revoke the short-lived test token
   after testing using the supported OAuth revocation flow, or allow its verified
   short lifetime to expire.

Publisher automation tokens and gateway application tokens serve different
audiences/permissions. Do not use a privileged Publisher token to stand in for
the subscribed test application's gateway token.

## Gateway smoke test

Set the actual API base URL (including the deployed context/version, excluding
`/api/v1/orders`) without placing a token in the command:

```powershell
$env:WSO2_GATEWAY_URL = Read-Host 'Paste actual HTTPS API base URL from Developer Portal'
.\demo-services\democommerce\.venv\Scripts\python.exe scripts/smoke_wso2_gateway.py
```

Enter the short-lived token at the hidden prompt. The script checks 401 without
a token, 200 listing orders with the token, 201 creating an order, the backend's
404 for a missing order, 200 reading the created order through the gateway, and
an identical direct-backend read-back. Status failures exit nonzero. A gateway
404 cannot satisfy the missing-order test. Tokens, headers and raw response
bodies are never printed. HTTPS verification stays enabled and redirects are
not followed. The test creates one in-memory demo order; it does not simulate
payment or delete data. Optional `--results <path>` writes redacted results only
on successful completion; use a fresh output filename for each run.

## Actual execution results

| Check | Actual result |
| --- | --- |
| Host `GET http://localhost:8000/health` | HTTP 200, healthy, service `democommerce-api`, version `1.0.0` |
| Docker status | Backend running/healthy; WSO2 running, no Docker healthcheck |
| Network membership | Both on `sentinelapi-network` |
| Backend-container request to `http://democommerce:8000/health` | HTTP 200, healthy |
| WSO2-container curl to the same backend DNS URL | HTTP 200, healthy |
| Backend pytest command above | **12 passed**, 1 Starlette/httpx deprecation warning, 0.81 s |
| Local tooling regression suite | **9 passed**; synthetic responses, not live gateway tests |
| OpenAPI export/check | Valid JSON; OpenAPI 3.1.0; 5 paths; 6 required operations; local references resolve |
| Trusted `GET /api/am/publisher/v4/settings` | HTTP 200; unauthenticated environment list empty (not proof of missing gateways) |
| Trusted `GET /api/am/devportal/v3/settings` | HTTP 200 |
| `GET /api/am/publisher/v4/apis?limit=100` without token | HTTP 401; authenticated duplicate discovery requires authorization |
| Anonymous `GET /api/am/devportal/v3/apis?limit=100` | HTTP 200, count 0; unpublished/private APIs not discoverable anonymously |
| Candidate gateway `GET /democommerce/1.0.0/api/v1/orders` without token | **HTTP 404**, gateway route-not-found; expected final authentication rejection not achieved |
| HTTP gateway at localhost:8280 | Connection refused; port is not published; use actual HTTPS gateway |
| Authenticated Publisher inventory and WSO2 OpenAPI validation | Not executed: credential/token unavailable |
| Required authenticated 200/201/404 tests and live gateway-to-backend proof | Not executed: API deployment and test application/token unverified |

## Troubleshooting and actual solutions

- Sandbox PATH/filesystem initially hid Docker and the Python 3.12 base
  interpreter, producing `docker not recognized` and `No Python at ...` errors.
  Host execution with approval found Docker at
  `%LOCALAPPDATA%/Programs/DockerDesktop/resources/bin/docker.exe` and ran the
  existing venv tests successfully. No backend source or virtualenv was replaced.
- Initial Windows HTTPS calls failed with Schannel credential/trust errors.
  Python confirmed a self-signed certificate. Exporting only the public
  certificate via Docker and passing it as a per-client CA fixed HTTPS access
  while preserving certificate and hostname validation.
- HTTP gateway access failed because only 8243/9443 are published. No port or
  container change was required; continue with the verified HTTPS listener.
- No browser/app surfaces were available; opening `iab` failed. The exact
  screenshot checklist is in `screenshots/03-api-integration/README.md`.
- Missing administrative authorization remains unresolved. Use an existing
  credential locally or supply only the variable name/ignored file path of an
  available credential to the agent. Do not guess default passwords, disable
  authentication, or treat anonymous discovery as a duplicate check.

## Security limits and completion gate

This remains a local demo. Direct localhost:8000 access bypasses the gateway;
the backend uses a fixed demo user, in-memory orders, and simulated payments.
The shared Docker network does not prevent another attached container from
calling the backend. The backend hop is HTTP, WSO2 uses a development certificate,
and Unlimited throttling is only for testing. No production identity propagation,
backend isolation/mTLS, production secret management, or production rate policy
was implemented in this step.

No screenshots were captured. All nine requested filenames and safe manual
capture instructions are in the screenshot checklist. No completion commit,
staging or push was performed because essential gateway tests have not passed.
Pre-existing untracked `AGENTS.md` was left untouched. Existing README content
was preserved despite containing apparent PowerShell scaffolding text.
Final review covered all 13 Step 3.2 files: JSON parsing, whitespace and common
credential-pattern checks passed. `git diff --check` was clean and the staged
diff was empty. Python caches are ignored by the existing ignore rules. Pattern
checks supplement review and are not a universal guarantee of secret detection.

Before creating `feat: integrate DemoCommerce API with WSO2 gateway`, finish
authenticated discovery, import/validation, OAuth resource security, revision
deployment, publication, active subscription, short-lived token generation,
all live smoke checks and a fresh review of diff/staged files for secrets.
Then stage only Step 3.2 artifacts, commit, and request user approval before
pushing to the existing GitHub main branch. Capture screenshot 14 only after
the push succeeds. Do not include the temporary certificate, tokens or caches.

## Interview understanding and Step 3.3 prerequisites

Be able to explain management-plane versus gateway responsibilities, Docker DNS
versus localhost, API context/version versus backend resource paths, OAuth token
issuance versus subscription authorization, revision deployment versus API
publication, TLS trust, and why an infrastructure 404 is not an authentication
test. Backend read-back of a gateway-created order provides stronger routing
evidence than matching health endpoints alone.

Step 3.3 was not started and its exact scope has not been supplied. Its
prerequisites are a completed Step 3.2 gateway verification, recorded actual
invoke URL/API/revision/application identifiers without secrets, reproducible
smoke tests, reviewed evidence, an approved Git checkpoint/push, and confirmation
of the next milestone's requirements. Do not infer or implement the next scope.
