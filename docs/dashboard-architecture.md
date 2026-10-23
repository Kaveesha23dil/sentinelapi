# Step 8 dashboard architecture

## Scope and design

The inspected frontend folder was empty. Step 7 PR #3 is merged into main at
c8fad4a, the clean feature/security-dashboard starting point after fetch. The
explicit Step 8 request supersedes AGENTS.md's historical milestone marker.
Step 7 remains experimental with outstanding live PostgreSQL acceptance.

React/TypeScript/Vite source is in frontend/. Exact top-level dependency versions
and package-lock.json are retained: React 19.3.1, Router 7.18.4, TanStack Query
5.104.5, Vite 8.3.5, TypeScript 6.0.3, Tailwind 4.3.3, Recharts 3.10.1, Zod 4.6.7,
Lucide 1.61.0, Vitest 5.0.5, Playwright 1.64.1. The official shadcn CLI generated
button/badge/card/skeleton/input sources; cn imports use the local clsx/tailwind-merge
utility. Radix is pinned. Inter Variable is self-hosted. Verification host: Windows,
Node 26.7.0/npm 11.19.0 and Python 3.12.14.

The dark operations workspace uses the requested background/surface/blue/semantic
colors, restrained borders, 8px-based layout spacing, compact metrics and readable
tables. Shared panels, pills, skeletons, pagination, safe endpoint displays and data
states keep behavior consistent. No decorative AI imagery or excessive glow.

Routes: / overview; /traffic; /alerts; /alerts/:id; /rules; /ml; /services.
The desktop sidebar becomes an icon rail on tablets, then a toggleable document-flow
navigation on small screens. Icon links retain accessible names. Skip link, native
labeled controls/dialog focus, keyboard indicators and reduced-motion styles are
included. Tables scroll within panels. Seven desktop screens passed axe A/AA smoke
scans; this is not full accessibility certification. Charts include textual labels.
React.lazy/Suspense splits pages, charts and demo data. Unknown routes/error boundaries
offer recovery without disclosing exception details or credentials.

## Implemented API dependencies

These are actual FastAPI routes, not hypothetical response fields. Database-dependent
routes were tested with mocks here; deployed SQL/grants remain pending. Runtime Zod
validation strips unneeded fields such as client_identifier, converts Decimal strings
explicitly, and rejects incompatible responses.

| Feature | Backend route | Support |
| --- | --- | --- |
| Monitoring capabilities | GET /api/v1/monitoring/session | New authenticated route, no DB call |
| Metrics/status | GET /api/v1/monitoring/overview | Existing counts and status distribution |
| Traffic log | GET /api/v1/monitoring/events | Existing pagination/API/time; new server method/status filters |
| API inventory | GET /api/v1/monitoring/services | New paginated registrations + interval event counts |
| Traffic chart | GET /api/v1/monitoring/timeseries | New bounded SQL UTC minute/hour aggregates |
| Endpoint rankings | GET /api/v1/monitoring/endpoints | New bounded sanitized endpoint/method aggregate |
| Security capabilities | GET /api/v1/security/session | New role/capabilities; never returns tokens |
| Alerts | GET /api/v1/security/alerts and /summary | Existing server filtering/pagination |
| Incident | GET /api/v1/security/alerts/{id} | Existing safe explanation/evidence plus safe title |
| Incident extensions | GET /api/v1/security/alerts/{id}/events and /history | New bounded safe events and sanitized status audit history |
| Status updates | PATCH /api/v1/security/alerts/{id} | Existing analyst/admin transitions and audit |
| Rules | GET /api/v1/security/rules; PATCH /rules/{id} | Existing admin-only configuration controls |
| ML | GET /api/v1/ml/model, /evaluation, /anomalies | Existing readiness, actual report provenance, paginated scores |

Active signals mean open + investigating in the interval, not confirmed attacks.
Registered API count does not establish health/full coverage. Requests/minute is an
interval average. Missing/error data is unavailable, not zero; ratios without
requests are unavailable. Timeseries never fills unobserved buckets with invented
zeroes. No source establishes trustworthy latency, client identity, service health
or exposed gateway correlation IDs; these are omitted/unavailable. Event UUIDs are
labeled collector references. Endpoints omit unsafe query/IP/host displays.

Severity sorting is explicitly limited to the returned page; global server order
stays newest-first. Rule names come from actual definitions. Null rule IDs stay
unassigned rather than being presumed ML. Incident changes require review/confirm,
verified capability and backend validation; success invalidates related queries.
Rule editing is admin-only, with unsupported adapter enablement still rejected.

ML model/report versions and provenance are separate, with a mismatch warning.
Demo imports the actual executed Step 7 synthetic evaluation JSON; deployment and
anomaly fixtures are illustrative, not live predictions. The histogram shows only
the returned anomaly page, raw negative decision scores and 0.05-width bins. It is
neither a probability nor a full normal/anomaly population distribution. Artifact
health does not establish worker freshness. No unsafe training/loading controls.

## Authentication, modes and data flow

Browser -> same-origin proxy -> FastAPI role checks -> existing services -> PostgreSQL.
The browser cannot access the database, collector spools or WSO2 credentials.

Live mode starts disconnected. Monitoring and/or security credentials are verified
against their respective /session endpoints. Server-derived capabilities govern
queries/controls; backend authorization remains the enforcement boundary. Tokens
remain only in React memory, never localStorage, sessionStorage, URLs, query keys,
.env or source. Disconnect cancels queries and clears caches; session epochs prevent
cross-session cache reuse. Reload requires reauthentication; backend state remains
independent. No user-selected role or development bypass grants permissions.

This is a local-development adaptation of existing service bearer authentication,
not production SSO. Use trusted local access or a TLS/identity gateway. A future
BFF/OIDC design and expiry/logout/security review are recommended before internet use.

Demo is an explicit action with a persistent amber DEMO DATA banner, deterministic
read-only fixtures and a fixed historical anchor. Live failures never switch modes.
The production Docker config disables demo entry. Operator-enabled demo still cannot
authenticate or write to backend APIs. Mocked browser integration tests are labeled
as such and do not substitute for live WSO2/PostgreSQL evidence.

HTTP uses AbortSignal, no-store, relative runtime-configured proxy paths, header-only
credentials, no redirects/cookies, safe errors and Zod validation. Unauthorized,
forbidden, missing, incompatible and unavailable responses have bounded retries.
Loading, empty, missing permissions, unavailable, partial, historical fixture and
experimental states are represented separately.

No SSE/WebSocket infrastructure exists. Live active observers poll every 30s;
background intervals are disabled, inactive views have no polling observers, and
the rolling time anchor advances only while visible. Focus/reconnect refetch safely.
Demo does not pretend to update. Time filters cover 1h/6h/24h/7d; filter changes reset
pagination and inventory links open API-filtered traffic.

## Backend and deployment

Step 8 needs no schema migration. Security role provisioning adds SELECT on only
event_id/timestamp/method/endpoint/status columns of traffic_events and selected
audit columns. Responses omit client identifiers and arbitrary audit metadata.
Owner-run grants and deliberate backend rollout remain pending on the real host.

Development: npm ci; npm run dev; open http://127.0.0.1:5173. Server-side proxy targets
default to monitoring 8010/security 8020, configurable via DASHBOARD_ values in a
private frontend/.env.local based on .env.example. No VITE_TOKEN. Public config.js
contains only validated relative proxy paths and allowDemo. No credentials belong
there. npm run preview is static-only; it does not provide live API proxies.

The Dockerfile uses npm ci and unprivileged Nginx on 8080 with same-origin proxies,
CSP, no access logs, no-store API responses and local fonts. compose.step8.yaml adds
only a dashboard on monitoring-network, loopback 127.0.0.1:8080, never database-network.
No wildcard CORS or PostgreSQL/collector exposure is added. Runtime settings can be
replaced with an operator-reviewed read-only config.js mount; production disables demo.

After approved backend rollout, build the new dashboard and create only that service
using existing appropriate Compose overlays plus compose.step8.yaml and
`up -d --no-deps --no-recreate dashboard`. Docker was unavailable here: no Compose
deployment/validation was performed. Review private variables first and never use
unrestricted compose up/down to bypass persistent-service recreation approval.
