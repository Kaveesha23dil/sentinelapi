# WSO2 support draft — not submitted

Subject: SentinelAPI Monitoring API build submission returns HTTP 500 without build record

- Product: WSO2 Developer Platform (Choreo)
- Component display name: SentinelAPI Monitoring API
- Organization/project/component IDs, deployment track, region: obtain from console
- Repository: https://github.com/Kaveesha23dil/sentinelapi
- Branch: feature/choreo-deployment
- Verified remote SHA: aae898ea421833fa41ca1a24991410dfdfcccc69
- Docker context: backend; Dockerfile: backend/Dockerfile.choreo
- Container port: 8001; explicit USER: 10002
- User-reported response correlation ID: 09415394-0f98-4140-9579-4b11d6595145
- Failure request UTC timestamp: **unknown; obtain from original DevTools request**
- Investigation timestamp: 2026-10-24 15:31:01 UTC (not failure time)

User-reported reproduction:
1. Open existing component and click Build Latest.
2. Console displays “Failed to build component SentinelAPI Monitoring API.”
3. Builds table remains “No Builds Available.”
4. Chrome DevTools shows a GraphQL HTTP 500 with the correlation ID above.

Expected: build ID/status/logs, or an actionable source-configuration error.
Actual: no build record or cloud build logs available.

Local checks: original pushed Dockerfile builds and FastAPI imports as UID 10002.
No source endpoint manifest existed; schema 1.2 manifests are prepared locally,
not pushed or retried in Choreo. Please trace the correlation ID and distinguish
source access, configuration, authorization and orchestration failure. Confirm
saved source branch/context/Dockerfile and whether a build was internally queued.
This report does not assert a confirmed infrastructure outage.

Before submission add exact UTC failure time, console identifiers/region and
sanitized response error text/operation name if available. Do not include cookies,
Authorization headers, browser tokens, environment values, raw HAR files,
DB credentials, private keys or unreviewed screenshots.
