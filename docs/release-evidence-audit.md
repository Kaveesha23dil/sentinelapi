# Portfolio release evidence audit

Source baseline: `891a269`; release branch: `docs/portfolio-release-evidence`. Audit performed on 2026-10-24.

At the start, `screenshots/final-blog/` contained **README.md only, zero images**. The 31 newly supplied captures were untracked PNGs directly under `screenshots/`. All 31 were opened visually, checked with Pillow `verify()` and fully decoded with `load()`. All are valid PNG images. Metadata contains only dpi/gamma/srgb fields; no capture timestamp is available. Displayed request/record dates are not asserted to be capture dates.

**13 safe images were copied byte-for-byte** into final-blog; no original was renamed, moved, cropped, blurred, regenerated or modified. SHA256, dimensions, original/destination mapping and provenance are in [evidence-inventory.json](../infrastructure/portfolio-release/evidence-inventory.json). Root originals remain local and are now ignored to prevent accidental publication; exclusion also covers safe redundant originals. No original was deleted.

## Privacy findings and decisions

- The authorized OAuth capture visibly contains a bearer token. It is excluded unchanged. Do not share it; revoke the affected token if still active and review any prior exposure. No value is transcribed here.
- The BASIC-log capture contains raw source addresses, correlation references and a personal workspace path. It is excluded unchanged.
- Several terminal images expose personal workspace paths; these are excluded for clean recapture, including the otherwise genuine Screenshot 06. A safe joined alert/evidence image supplies the blog’s live alert illustration instead.
- No password or private key was visually identified in the selected copies. Generic local admin labels, demo observer labels, route templates and documented Docker DNS names are not represented as credentials or real client identities.
- A screenshot of an OpenAPI Example Value is not an executed HTTP 201 result; a 404 at the wrong context is not an OAuth rejection. A PUBLISHED lifecycle screen is not proof of a deployed gateway revision. Misleading source filenames are explicitly corrected in copied names/captions.

## Every supplied capture

| Original filename under screenshots/ | Provenance and visual finding | Publication decision |
|---|---|---|
| `01dashboardoverview.png` | demo-fixture: Visible DEMO DATA; illustrative counts, not live metrics. | 07-dashboard-overview-demo.png |
| `01fastapiswagger.png` | application-documentation: Actual Swagger operation list; no execution result implied. | 01-democommerce-openapi.png |
| `01wso2apipublisher.png` | runtime-configuration: PUBLISHED API, OAuth2, actual context; generic admin label, no secret. | 02-wso2-publisher.png |
| `02aoauthunauthorized.png` | runtime-http: Exclude: personal workspace path and full correlation reference; curl uses TLS bypass. HTTP 401 is visible. | Excluded / retained locally |
| `02apitraffic.png` | demo-fixture: Visible DEMO DATA and fixture event references. | 08-api-traffic-demo.png |
| `02boauthauthorized.png` | runtime-http: EXCLUDE: visible Authorization bearer token. Do not publish or transcribe; revoke affected token and review exposure. | Excluded / retained locally |
| `02createorderresponse.png` | openapi-example: Safe but omit: schema Example Value, not an executed HTTP 201 response. | Excluded / retained locally |
| `02wso2startup.png` | historical-runtime: Exclude: personal workspace paths; startup/redirect transcript is not API routing proof. | Excluded / retained locally |
| `03apiintegration04dockercontainers.png` | historical-runtime: Safe but omit: narrow WSO2 container row, not whole-stack readiness; CPU is an instantaneous display. | Excluded / retained locally |
| `03aratelimitpolicy.png` | runtime-configuration: Safe alternate policy catalog; omitted to avoid redundant figures. | Excluded / retained locally |
| `03bratelimitenforcemen3t.png` | runtime-http: Exclude: personal workspace path. Shows 10 HTTP 200 then 5 HTTP 429; not a timestamped benchmark. | Excluded / retained locally |
| `03bratelimitenforcement.png` | runtime-http: Exclude: personal workspace path and TLS-bypass command. Shows 11 HTTP 200 then 4 HTTP 429; separate capture, not proof of exact quota timing. | Excluded / retained locally |
| `03pytestresults.png` | historical-tests: Exclude: personal paths; 12 individual passes visible, not the current release suite summary. | Excluded / retained locally |
| `03security03unauthorizedrequest.png` | historical-failure: Exclude: personal path/correlation reference; wrong context returns 404, not authentication rejection. | Excluded / retained locally |
| `03security05ratelimitpolicy.png` | runtime-configuration: Safe alternate 10/20/50-per-minute catalog, not enforcement evidence; redundant. | Excluded / retained locally |
| `03threatalerts.png` | demo-fixture: Visible DEMO DATA; fixture high severity is not the actual medium live alert. | 09-alert-queue-demo.png |
| `04incidentdetails.png` | demo-fixture: Original filename is misleading: actual screen is Detection rules, not Incident details. | 10-detection-rules-demo.png |
| `04wso2apitrafficlogs.png` | runtime-raw-log: EXCLUDE: raw source addresses, correlation IDs and personal workspace path. No edited substitute provided. | Excluded / retained locally |
| `05postgresqltelemet5ryevents.png` | controlled-local-runtime: Sanitized SQL rows include actual 200/429 gateway events; visible record timestamps are not capture time. | 04-postgresql-gateway-events.png |
| `05postgresqltelemetryevents.png` | historical-runtime: Safe older SQL observation: 21-row aggregate, NULL latency; omitted in favor of later gateway rows. | Excluded / retained locally |
| `06mlmonitoring.png` | demo-fixture-and-synthetic-report: Visible demo banner; actual retained synthetic evaluation metrics, not a live deployed model. | 11-ml-monitoring-synthetic-demo.png |
| `06securityalerts.png` | controlled-local-runtime: Genuine stored alert with 16 evidence links, but exclude for personal workspace path. Clean recapture needed for named Screenshot 06. | Excluded / retained locally |
| `07alertevidencedetails.png` | controlled-local-runtime: Safe joined alert/evidence rows; LIMIT page shows 12 rows, not all 16 evidence links. | 05-alert-evidence-details.png |
| `07apiservices.png` | demo-fixture: Visible demo banner; three fixture services do not mean three deployed business APIs. | 12-api-services-demo.png |
| `07wso2-apioverview.png` | configuration-form: Safe but omit: pre-creation OpenAPI form, not a published API overview. | Excluded / retained locally |
| `08wso2backendendpoint.png` | historical-configuration: Safe but omit: CREATED-state overview; filename does not prove a deployed endpoint. | Excluded / retained locally |
| `09wso2gatewaydeployment.png` | runtime-configuration: Safe lifecycle PUBLISHED screen; not gateway revision-deployment proof. | 13-published-lifecycle.png |
| `10wso2developerportal.png` | runtime-configuration: Safe published catalog entry; no keys/token details visible. | 14-developer-portal.png |
| `environment-versions.png` | historical-environment: Safe but omit: terminal versions are historical, not this test environment; no personal username shown. | Excluded / retained locally |
| `finalblog03aratelimitpolicy.png` | runtime-configuration: Safe dedicated application overview showing configured 10PerMin policy and approved state; not a measured 429 result. | 03-application-rate-policy.png |
| `WSO2Dockerimage.png` | historical-installation: Exclude: personal workspace path; pull completion does not establish service readiness. | Excluded / retained locally |

## Every image now in final-blog

| File | Evidence meaning |
|---|---|
| [01-democommerce-openapi.png](../screenshots/final-blog/01-democommerce-openapi.png) | Actual Swagger operation list; no execution result implied. |
| [02-wso2-publisher.png](../screenshots/final-blog/02-wso2-publisher.png) | PUBLISHED API, OAuth2, actual context; generic admin label, no secret. |
| [03-application-rate-policy.png](../screenshots/final-blog/03-application-rate-policy.png) | Safe dedicated application overview showing configured 10PerMin policy and approved state; not a measured 429 result. |
| [04-postgresql-gateway-events.png](../screenshots/final-blog/04-postgresql-gateway-events.png) | Sanitized SQL rows include actual 200/429 gateway events; visible record timestamps are not capture time. |
| [05-alert-evidence-details.png](../screenshots/final-blog/05-alert-evidence-details.png) | Safe joined alert/evidence rows; LIMIT page shows 12 rows, not all 16 evidence links. |
| [07-dashboard-overview-demo.png](../screenshots/final-blog/07-dashboard-overview-demo.png) | Visible DEMO DATA; illustrative counts, not live metrics. |
| [08-api-traffic-demo.png](../screenshots/final-blog/08-api-traffic-demo.png) | Visible DEMO DATA and fixture event references. |
| [09-alert-queue-demo.png](../screenshots/final-blog/09-alert-queue-demo.png) | Visible DEMO DATA; fixture high severity is not the actual medium live alert. |
| [10-detection-rules-demo.png](../screenshots/final-blog/10-detection-rules-demo.png) | Original filename is misleading: actual screen is Detection rules, not Incident details. |
| [11-ml-monitoring-synthetic-demo.png](../screenshots/final-blog/11-ml-monitoring-synthetic-demo.png) | Visible demo banner; actual retained synthetic evaluation metrics, not a live deployed model. |
| [12-api-services-demo.png](../screenshots/final-blog/12-api-services-demo.png) | Visible demo banner; three fixture services do not mean three deployed business APIs. |
| [13-published-lifecycle.png](../screenshots/final-blog/13-published-lifecycle.png) | Safe lifecycle PUBLISHED screen; not gateway revision-deployment proof. |
| [14-developer-portal.png](../screenshots/final-blog/14-developer-portal.png) | Safe published catalog entry; no keys/token details visible. |

## Missing or withheld evidence

| Evidence | Status |
|---|---|
| Clean OAuth 401 and authenticated 200 captures | Supplied images contain personal paths/token; clean recapture needed. Retained gateway JSON provides historical checks. |
| Clean rate-limit enforcement terminal | Supplied captures show 200→429 but expose workspace paths; no TLS trust proof from curl -k. Curated policy configuration and actual persisted 429 rows are available. |
| Clean BASIC log view | Raw source-address image excluded. Recapture a legitimate sanitized observation, not an edited/reconstructed result. |
| 06-security-alerts.png | Captured original exists locally but contains a personal path. Not copied under this name. Clean recapture pending; 05-alert-evidence-details.png safely shows the genuine alert and linked 404 events. |
| Gateway revision-deployment view | Lifecycle image is available; actual revision view is not supplied. Historical machine report retains deployment evidence. |
| Live authenticated dashboard | All supplied dashboard images visibly show DEMO DATA; none proves a live dashboard connection. |
| Live Isolation Forest inference | No approved artifact configured; zero stored ML windows in current observation. Only synthetic evaluation is verified. |
| Performance/throughput/latency | No executed benchmark samples; no performance image or claim supported. |
| Current clean test summary screenshot | Terminal test capture is historical/personal-path-bearing. Actual current JSON/JUnit summaries are retained instead. |

## Provenance rules for publication

Use original live configuration screenshots as configuration observations; controlled gateway/SQL captures as controlled local runtime evidence; and all DEMO DATA screens as fixtures. The ML screen combines fixture UI with the retained controlled synthetic report. Its metrics do not prove a live model. The joined alert screenshot shows 12 rows of a limited query, while independently verified SQL/API counts show 16 links. Do not relabel the 12 displayed rows as the full evidence set.

The previous [Step 10 inventory](final-evidence-inventory.md) remains a historical record of earlier reviewed charts/UI images. Those tracked bytes were not changed by this release audit. Current browser checks save new captures only under ignored `.runtime/portfolio-release/browser-captures/` via SENTINEL_SCREENSHOT_DIR; existing evidence is not overwritten.

## Clean recapture instructions

Use the actual app or actual read-only SQL output. In a clean host terminal, hide the prompt before capturing, close unrelated history/notifications, and keep credential forms/Authorization headers off-screen. Run `scripts/show_security_alerts.ps1`; capture only the actual returned table with Win+Shift+S, without editing its values, then save 06-security-alerts.png under final-blog. For OAuth capture only the response/status area after privately supplying credentials; do not include generated curl token headers. For log evidence avoid raw source addresses and full identifiers by using an actual authorized sanitized view. Retain DEMO DATA banners for fixtures.

Inspect each new image before staging it and record its actual capture time/command/code revision in a sidecar only after capture. Add it explicitly after review; never force-add the excluded root originals. This audit does not fabricate missing screenshots or claim the blog has been published.
