# Step 3.2 ? DemoCommerce and WSO2 integration

Verified 2026-10-20. **All six live gateway checks pass. The requested context remains unresolved:** the manually created API uses `/democommerceapi`, while the requested context is `/democommerce`. WSO2 retains an existing API's context during updates. No existing API, container, volume or database was deleted. Step 3.3 and the final blog were not started.

## Actual configuration

| Setting | Verified value |
| --- | --- |
| WSO2 | `wso2/wso2am:4.5.0`, `sentinelapi-wso2`; installed Publisher component 9.31.86 |
| Backend | `sentinelapi/democommerce:local`, `sentinelapi-democommerce`; existing Python 3.12 Dockerfile |
| Host/network | Windows, PowerShell, Docker Desktop; both containers on sentinelapi-network |
| Health | Backend Docker healthy; WSO2 running with no Docker HEALTHCHECK |
| API | DemoCommerceAPI 1.0.0, PUBLISHED |
| API ID | `f0d23a14-460c-4441-9c76-0f39bfd2efb3` |
| Actual context | `/democommerceapi` |
| Requested context | `/democommerce` ? not applied |
| Actual HTTPS invoke base URL | `https://localhost:8243/democommerceapi/1.0.0` |
| Production endpoint | `http://democommerce:8000` |
| Security | Mandatory OAuth2; all six operations require Application & Application User |
| Plan | Unlimited, subscription UNBLOCKED |
| Test application | SentinelAPITestClient, JWT, Unlimited application policy |
| Application ID | `71cddcdc-ae71-44e0-a061-54e057bca7a7` |
| Subscription ID | `14aa068a-99b5-4462-a0c1-ac9e1aaa40b7` |
| New revision UUID | `3a8ce000-e880-4803-85a9-6ca3e035463b` |
| Gateway deployment | Default, vhost localhost, APPROVED |
| Final test token | 300-second response lifetime; JWT exp minus iat also 300 seconds |

The deployment record has a null `successDeployedTime`; this is not used as proof of successful deployment. Its APPROVED revision and the actual authenticated routing/read-back checks establish that the gateway serves this backend. Earlier revisions remain in history.

## Architecture and real OpenAPI

The client reaches the HTTPS WSO2 gateway. The gateway validates OAuth and subscription authorization, removes the context/version prefix, and forwards the backend resource path through Docker DNS to `democommerce:8000`. `localhost:8000` inside WSO2 would refer to WSO2 itself. Publisher manages definitions and revisions; deployment installs a revision; publication exposes the API in Developer Portal; the Key Manager issues tokens. Publication alone does not prove routing.

WSO2 publishes only localhost ports 8243 and 9443. Its advertised HTTP URL on 8280 is not reachable from this host; use the verified HTTPS URL. Compose manages the backend and references an external network; it does not provision the separately managed WSO2 container.

`infrastructure/wso2/democommerce-openapi.json` is the unchanged real response from `http://localhost:8000/openapi.json`, OpenAPI 3.1.0, API version 1.0.0:

| Method | Backend path |
| --- | --- |
| GET | `/health` |
| GET | `/api/v1/users/me` |
| GET, POST | `/api/v1/orders` |
| GET | `/api/v1/orders/{order_id}` |
| POST | `/api/v1/payments/simulate` |

Structural/local-reference checks pass. **The installed WSO2 Publisher OpenAPI validator returned isValid true.** Authenticated inspection confirmed all six secured resources in the existing imported API. No duplicate API was imported. `democommerce-api-properties.json` retains the originally requested new-API context `/democommerce`; it is not an export of the deployed context.

## Discovery, supported configuration and actual changes

Resumption found manual commit `c7f4aa4`, titled `feat: integrate DemoCommerce API with WSO2 gateway`. Local main and its origin/main tracking reference pointed there. The API was already published at `/democommerceapi`, with the correct backend, OAuth2, Unlimited and an existing deployment. The requested test application did not exist.

Authenticated Publisher inventory was queried before creation. Existing super_admin credentials were resolved from the local container configuration into process memory. No values were printed or saved. Supported DCR `/client-registration/v0.17/register` and `/oauth2/token` provided scoped management access for `SentinelAPIStep32Automation`. This management client remains registered locally; no credentials are stored in Git.

A supported Publisher PUT preserved the existing API and secured resources and persisted HTTPS transport, but did not change the context. The matching [WSO2 9.31.86 PublisherCommonUtils implementation](https://github.com/wso2/carbon-apimgt/blob/v9.31.86/components/apimgt/org.wso2.carbon.apimgt.rest.api.publisher.v1.common/src/main/java/org/wso2/carbon/apimgt/rest/api/publisher/v1/common/mappings/PublisherCommonUtils.java#L479) explicitly restores the original context. The automation now stops before updating an existing API with a different requested context. No database edits or undocumented aliasing were used.

Created a revision using Publisher v4 `POST /apis/{apiId}/revisions`, then `POST /apis/{apiId}/deploy-revision?revisionId=...` with the actual discovered Default environment and localhost vhost. Re-read deployments and confirmed APPROVED status. Reused the PUBLISHED lifecycle state and read the actual HTTPS invoke URL from Developer Portal.

Created SentinelAPITestClient and its Unlimited subscription using Developer Portal v3 `/applications` and `/subscriptions`. Generated production OAuth credentials with client_credentials support via `/applications/{id}/generate-keys`. Subsequent attempts reused the application, subscription and OAuth key mapping without regenerating the consumer secret.

### Token lifetime issue and supported fix

A request with validityPeriod 300 and key-generation validityTime 300 initially yielded a 3,600-second JWT. It was rejected as unsuitable; the diagnosed unsuitable token was submitted for revocation. Updated only the test application's OAuth key configuration using `PUT /applications/{applicationId}/oauth-keys/{keyMappingId}`, preserving callback/grants and setting the string additional property `application_access_token_expiry_time` to `300`. The matching [resident Key Manager implementation](https://github.com/wso2/carbon-apimgt/blob/v9.31.86/components/apimgt/org.wso2.carbon.apimgt.impl/src/main/java/org/wso2/carbon/apimgt/impl/AMDefaultKeyManagerImpl.java) handles this property.

The next token's reported lifetime and JWT exp minus iat both confirmed 300 seconds. Gateway acceptance supplied the authentication proof; decoding JWT timestamps alone does not verify its signature. The final test token was submitted to `/oauth2/revoke` after testing. No token, consumer credential, Authorization header or decoded identity claim was printed or saved. Initial attempts before the lifetime diagnostic was implemented may also have issued one-hour tokens; their values were not retained. Do not confuse those attempts with the final verified short-lived token.

## Actual execution results

Final live gateway run: **2026-10-20 16:51:30 UTC**.

| Check | Actual result |
| --- | --- |
| Host backend health | HTTP 200, healthy |
| WSO2 to Docker DNS backend health | HTTP 200, healthy |
| Containers/network | Both running and attached; backend healthy |
| Existing backend pytest | 12 passed, 1 Starlette/httpx deprecation warning, 0.97 s |
| Tooling unit tests | 12 passed, synthetic tests separate from live gateway checks |
| OpenAPI structural/reference check | Passed |
| Installed Publisher OpenAPI validation | Passed |
| GET orders without token | HTTP 401 |
| GET orders with subscribed token | HTTP 200 |
| POST orders with token | HTTP 201 |
| GET nonexistent order with token | HTTP 404, backend Order not found response |
| Read created order through gateway | HTTP 200, matches creation response |
| Direct backend read-back | HTTP 200, identical gateway-created order |
| Requested /democommerce/1.0.0 route | HTTP 404; context decision remains pending |

Machine-readable evidence is in `environment-verification.json`, `access-verification.json` and `gateway-verification.json` under infrastructure/wso2. In the last file, passed true means the six gateway checks passed; requested_context_matches false and step_3_2_complete false explicitly record the mismatch. One in-memory demo order was created. No payment was triggered or data deleted. Direct backend read-back proves the gateway write reached this DemoCommerce instance.

## Reproduce securely

Run from repository root in host PowerShell with Docker Desktop available:

```powershell
.\scripts\verify_wso2_environment.ps1
$python = '.\demo-services\democommerce\.venv\Scripts\python.exe'
& $python scripts/export_democommerce_openapi.py --check
& $python -m pytest -q -p no:cacheprovider demo-services/democommerce/tests
& $python -m unittest discover -s scripts/tests -v
```

Obtain only the local public certificate through Docker and retain certificate/hostname validation:

```powershell
docker exec sentinelapi-wso2 sh -c 'echo | openssl s_client -connect localhost:9443 2>/dev/null | openssl x509 -outform PEM' | Set-Content -Encoding ascii "$env:TEMP/sentinelapi-wso2-public.pem"
$env:WSO2_CA_FILE = "$env:TEMP/sentinelapi-wso2-public.pem"
& $python scripts/integrate_wso2.py --from-container
& $python scripts/integrate_wso2.py --from-container --test-existing
```

The certificate CN/SAN is localhost, valid 2025-02-13 through 2027-05-19. No private key was exported, system trust changed or TLS verification skipped. Initial sandbox Docker/Python restrictions were resolved with approved host execution; the backend and interpreter were not replaced.

The inspect command reads API state without changing API configuration; it uses DCR for management authentication. `--from-container` explicitly selects the configured local administrator credential source. Alternatively omit it and use a secure local process environment (WSO2_USERNAME / WSO2_PASSWORD), or the hidden password prompt. Never put real values in saved command lines or transcripts.

`--test-existing` reuses the current API/application/subscription and verifies actual routing. Add `--deploy-existing` only when a fresh revision is needed; it keeps prior history and does not delete revisions to bypass limits. The successfully executed deployment/test command was:

```powershell
& $python scripts/integrate_wso2.py --from-container --test-existing --deploy-existing
```

For an already-issued short-lived token, use the standalone hidden prompt:

```powershell
$env:WSO2_GATEWAY_URL = 'https://localhost:8243/democommerceapi/1.0.0'
& $python scripts/smoke_wso2_gateway.py
```

That tool also accepts WSO2_TEST_TOKEN from the process environment. It requires HTTPS, does not follow redirects, prints no bearer values, and distinguishes a gateway routing 404 from the backend's order-not-found 404.

## Screenshots, Git and outstanding decision

Browser/app inventory was empty on resumption. **0/9 screenshots captured**; no synthetic images were produced. Exact real-screen instructions and filenames are in `screenshots/03-api-integration/README.md`. Functional screens can now be captured manually. Screenshot 14 must wait for a successful approved final checkpoint push.

The pre-existing manual checkpoint is c7f4aa4. This run has not created another commit or pushed. The user has been asked to accept `/democommerceapi` as an explicit deviation, or authorize backup/replacement of only this API to obtain `/democommerce`, followed by subscription restoration and fresh verification. No deletion is authorized by elapsed time. Containers, volumes and databases would remain untouched.

After the context decision is resolved and the approved configuration passes, review/stage only Step 3.2 files and commit `feat: integrate DemoCommerce API with WSO2 gateway`. Ask the user before pushing.

## Security limitations and interview understanding

This remains a local demo. Direct localhost:8000 access bypasses the gateway; the backend has a fixed demo identity, in-memory orders and simulated payments. The shared Docker network allows other attached containers to call the HTTP backend. WSO2 uses a development certificate, Unlimited is for testing, and the scoped local administrative automation client remains registered. Production identity propagation, isolation/mTLS, secret management and production rate policies are outside this step. Authentication was never disabled.

For an interview, explain management plane versus gateway, Docker DNS versus localhost, context/version versus backend resource paths, OAuth issuance versus subscription authorization, deployment versus publication, scoped TLS trust, immutable API identity and verifying actual token lifetime. Explain why gateway 404 is different from authenticated backend 404, and why write/read-back proves routing.

Step 3.3 was not started and its exact scope has not been supplied. First resolve the context decision, complete the approved Git checkpoint/push, and retain reproducible evidence without credentials.
