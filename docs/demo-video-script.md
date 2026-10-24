# SentinelAPI demo video script

Plan only: no actual video file is available and no recording/upload is claimed. Target 4 minutes 20 seconds. The default version below remains truthful with current blockers; live alternatives require the listed acceptance first. Use actual application views, code and reports. Keep captions saying LIVE HISTORICAL EVIDENCE, CONTROLLED SYNTHETIC or DEMO FIXTURES as appropriate.

## Before recording

Use [deployment instructions](final-deployment.md), verify selected screens and review the [evidence inventory](final-evidence-inventory.md). Start the React app and test Explore demo. Open the architecture, retained gateway/telemetry report, synthetic charts and actual current test report. Close secret-bearing tabs/terminals and notifications. Use hidden credential prompts off-camera. Never expose Authorization headers, `.env`, DB credentials, raw IPs or real client identifiers. Do not run load/restart tests during recording. Record only after checking screen resolution and audio.

## 00:00–00:20 — Introduction

- **Screen:** actual React Overview with DEMO DATA banner.
- **Action:** hold overview; point to provenance banner before request cards.
- **Narration:** “SentinelAPI is my API security monitoring prototype built around WSO2 API Manager. I explored how to turn gateway activity into investigation evidence using a collector, PostgreSQL, rules and an experimental anomaly model. This dashboard currently shows labeled fixtures.”
- **Evidence:** actual app rendering, not live request counts.
- **Hide:** personal browser profile, unrelated tabs and notifications.

## 00:20–00:50 — Architecture and WSO2

- **Screen:** rendered Mermaid from final-architecture.md and source links.
- **Action:** trace Client → Gateway → DemoCommerce, then the separate log-to-monitoring path.
- **Narration:** “WSO2 handles OAuth, subscriptions and gateway routing. SentinelAPI reads BASIC logs out of band, sanitizes completed responses and stores them. Detection never runs in the request path and does not automatically block traffic.”
- **Evidence:** versioned architecture and actual implementation modules.
- **Hide:** editor workspace paths containing personal information; enlarge the diagram.

## 00:50–01:25 — Protected API

- **Screen now:** retained gateway-verification.json, display only test names/statuses and context; keep historical caption.
- **Action:** show 401 without token, 200 with subscribed token, 201 creation and matching read-back.
- **Narration:** “The retained local gateway run verified OAuth rejection and routing, including a write read back through the backend. The actual context is democommerceapi. Fresh acceptance is currently blocked by certificate trust. I have not verified low-quota 429 enforcement or gateway-only backend isolation.”
- **Live alternative:** after trust/application checks pass, show existing Publisher and privately authorized bounded calls, with new timestamp and results. Add a throttling screen only after actual 429.
- **Evidence:** historical genuine report; no claim of a fresh call.
- **Hide:** tokens, app credentials/IDs, response identities and unrelated configuration.

## 01:25–02:00 — Telemetry and PostgreSQL

- **Screen now:** sanitized e2e-verification.json count/status section plus normalizer/identity source.
- **Action:** show six source completions → six stored/monitoring events and unchanged replay count.
- **Narration:** “A previous controlled live run correlated six actual gateway responses with six persisted events. Only RESPONSE_OUT creates an event. IDs are deterministic for replay. I drop source addresses and preserve latency and client identity as unavailable because the observed logs cannot establish them. The current collector is stale, so this report is historical.”
- **Live alternative:** after restored ingestion, show read-only sanitized DB counts over a matching fresh UTC interval.
- **Evidence:** historical report, actual code; DB screen is not currently available.
- **Hide:** raw logs, sourceIP, connection strings and full event/client identifiers.

## 02:00–02:35 — Rules and investigation

- **Screen:** actual demo Detection Rules → fixture Incident Details, retain DEMO DATA.
- **Action:** show error_rate threshold .5/300s and disabled adapter-dependent rules; open example evidence.
- **Narration:** “Five rule strategies are implemented and tested, but only error-rate has a live evidence adapter. It requires at least 20 requests and more than half errors in five minutes. The worker commits alerts with checkpoints and uses incident fingerprints for duplicate suppression. This example incident is a read-only fixture; genuine live alert acceptance remains pending.”
- **Evidence:** code/rule catalog plus real fixture UI, not actual attack detection.
- **Hide:** credential dialog; do not present fixture high severity as the live worker's fixed medium policy.

## 02:35–03:10 — ML and provenance

- **Screen:** genuine confusion matrix/score chart and current synthetic metric JSON.
- **Action:** point to 54 true positives, 66 misses and four false positives; show synthetic label.
- **Narration:** “I evaluated Isolation Forest on 360 synthetic training minutes and 180 held-out minutes. Precision was about .931 and recall .45. These are controlled-label results, not production attack accuracy. Rule history is 300 seconds while ML uses 60-second windows. An unusual window does not establish malicious intent. A live model requires trusted artifact approval and a real API baseline.”
- **Evidence:** reproduced controlled experiment; no live model claim.
- **Hide:** artifact directory's personal host path; no joblib loading from untrusted sources.

## 03:10–03:45 — React dashboard

- **Screen:** actual Traffic filters → Alerts → ML Monitoring → mobile viewport if time permits.
- **Action:** filter method, paginate, show experimental provenance and read-only fixtures.
- **Narration:** “The dashboard provides seven investigation views. Real connections use authenticated APIs with separate monitoring and security capabilities. Credentials stay in memory; demo mode is explicit and never a fallback for failed authentication. Browser tests cover rendering, accessibility, filtering and mocked authorization flows. They do not prove the full live backend.”
- **Evidence:** real app interaction; fixture/mock classification stays visible.
- **Hide:** connection form and browser storage/headers; do not show unverified live controls as successful writes.

## 03:45–04:20 — Results and closing

- **Screen:** final-verification.md table, current actual report, then repository README.
- **Action:** show counts and blockers together; end on architecture/source links.
- **Narration:** “This audit passed 156 Python tests and four subtests, with two known Windows collector failures on main. The fix is on unmerged Step 9. Thirty-six frontend unit tests and seven browser tests passed; 32 database checks were only collected. There is no measured throughput or live inference latency. My next work is integrating the reviewed fix, reconciling deployed services and completing genuine end-to-end acceptance. The repository documents both the implementation and its limits.”
- **Evidence:** exact current counts, no passing-build badge or invented benchmark.
- **Hide:** local paths and account details; show the public repository URL only.

## After recording

Review the actual video frame-by-frame around credentials and terminal transitions. Confirm narration matches the selected live/historical/fixture path. Record file name, duration and actual recording date only after the file exists. Obtain approval to publish; then add the real video URL. If a required live step is still unavailable, keep the limited-prototype narration rather than editing in a fabricated success screen.
