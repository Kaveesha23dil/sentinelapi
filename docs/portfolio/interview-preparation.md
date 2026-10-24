# SentinelAPI interview preparation

Answers describe the actual source baseline and its verification limits. They are technical preparation, not claims of unrecorded personal accomplishments. See the [audit](../final-project-audit.md) and [architecture](../final-architecture.md).

## 1. Why use WSO2 API Manager?

It supplies a concrete API lifecycle, subscription and OAuth gateway around DemoCommerce. SentinelAPI can study gateway-originated observations while leaving access enforcement with WSO2. The project uses actual 4.5.0 integration tooling; it does not replace WSO2's authorization with its own ML model.

## 2. How does an OAuth request reach DemoCommerce?

A subscribed application's client-credentials token accompanies HTTPS requests to gateway port 8243 at `/democommerceapi/1.0.0`. The gateway enforces the configured API security/subscription and forwards the resource to `http://democommerce:8000` through Docker DNS. Historical checks observed 401 without a token and successful subscribed routing. Current TLS trust blocks fresh gateway assertions; decoded JWT timestamps alone are not signature verification.

## 3. How do publication and deployment differ?

Publisher manages API definitions and lifecycle; a revision is deployed to the actual gateway environment/vhost. Developer Portal exposes the API for subscriptions and application keys. A PUBLISHED state alone is not evidence that a gateway revision routes correctly, so retained tests include actual backend write/read-back. Supported updates preserved the existing context; the requested alternative remains unresolved.

## 4. Why is gateway authentication different from backend isolation?

DemoCommerce itself does not authenticate requests and still publishes loopback 8000. A local caller can bypass WSO2. Gateway-only access requires a deliberate networking/deployment change and proof of host refusal while internal routing still succeeds. That change was not silently applied because persistent service replacement requires approval.

## 5. What throttling is verified?

The project discovered WSO2's 10PerMin application policy and provides a bounded dedicated-client test. It has no retained observed 429 result. Application-level and subscription-level policies are different configuration boundaries; the normal Unlimited configuration cannot prove a low-quota limit. Tests must use the intended dedicated app, quota window and actual HTTP outcomes without disabling protection.

## 6. Why BASIC API Logs instead of FULL logs?

Observed BASIC records contain the method, target, correlation, flow and response status needed for this pipeline. STANDARD/FULL introduce headers/payloads the project does not need. The adapter drops source addresses and unknown fields before spooling. Raw WSO2 files still need protection; downstream redaction does not sanitize the gateway's original log history.

## 7. Why collect only RESPONSE_OUT?

One request can generate four flow records. Counting each would inflate volume. The retained live run had 22 flows but six completed responses, including a gateway-rejected request without backend flows. Completion-based collection also has a boundary: requests with no observed final response are not reconstructed or claimed as covered.

## 8. How does correlation and deduplication work?

UUID5 uses the configured API UUID as namespace and combines the source correlation UUID, completion timestamp, method and normalized endpoint. Replayed identical completions get the same event ID, even across source rotation. The database unique constraint and content comparison reject conflicting reuse rather than overwrite. Dashboard event references are these collector IDs, not exposed gateway correlation IDs.

## 9. What is the database design?

Services link to traffic events, rules/alerts/evidence support investigations, audit records retain controlled changes, detection checkpoints track progress and ML windows retain versioned scores. UUID keys, TIMESTAMPTZ, foreign keys, bounded queries and JSONB support structured evidence. Business orders remain in memory; this is monitoring persistence. Later migrations/grants still need live validation.

## 10. How are migrations and tests kept away from project data?

Alembic upgrades are explicit and reviewed. Downgrades/integration fixtures guard the `sentinelapi_test_*` namespace. Runtime uses scoped roles while owner credentials perform migrations/provisioning. Current audit collected 32 DB tests without running them against the project DB. Historical disposable migration/persistence results do not prove the newest live schema.

## 11. What makes collector retry safe?

The bridge advances its source checkpoint only after durable sanitized transport acceptance. The collector acknowledges chunks after DB work; deterministic IDs deduplicate replay. Bounded reads, complete-line handling, rotation checks and spool pressure fail visibly. Offline duration beyond source retention can still lose history. Windows directory fsync currently fails on main; its tested portability fix is unmerged and does not promise POSIX-equivalent power-loss durability.

## 12. Which threat rules work live?

Only error_rate has a live evidence adapter: at least 20 requests and an error ratio >.5 in 300 seconds. Flood, enumeration, authentication failures and unusual activity have tested pure strategies but lack trusted client/route/auth/baseline adapters. HTTP 401/404 alone cannot support those intended classifications. They remain disabled rather than approximate unsupported evidence.

## 13. How are detection windows and duplicate alerts managed?

The worker processes event-time slices with 300-second history, a 120-second lateness allowance and overlap. Transaction-scoped advisory locking serializes work. Alerts and watermarks commit atomically; fingerprints incorporate rule/version/window context to suppress duplicates. Capacity overflow rolls back instead of truncating. Events beyond supported lateness need explicit historical replay.

## 14. Why these ML features?

The seven identity-free minute features can be computed from sanitized observed fields: request count, 4xx/5xx ratios, endpoint count, GET/POST ratios and status diversity. Latency/client features are excluded because the source does not establish them. Partial windows are excluded; sparse/missing-field windows are ineligible. Features detect behavioral differences, not intent.

## 15. How is the Isolation Forest trained and versioned?

A training-only imputer/scaler/Isolation Forest pipeline uses per-API windows. The controlled experiment sets 200 trees, .05 contamination, seed 42 and one worker. Metadata binds feature order/schema, API, training digest, configuration, provenance and dependency versions; artifacts are immutable. A minimum window count is a guard, not statistical adequacy. Real traffic needs separate baseline review and a chronological split.

## 16. What do the evaluation results establish?

Only performance against controlled synthetic labels: 360 training and 180 held-out minutes, with 60 normal and 120 scenario windows. ML matrix is [[56,4],[66,54]], precision .931034, recall .45, F1 .606742 and FPR .066667. The rule comparison uses 300-second history versus ML's 60 seconds. The experiment retains misses/benign bursts; it cannot establish live attack accuracy or universal ML superiority.

## 17. Is an anomaly score an attack probability?

No. Raw decision_function below zero is unusual under the fitted model. It does not establish malicious intent; policy risk 50 is not confidence. Investigation uses model version, features, window and linked events. Joblib also requires a trusted local artifact: matching hashes check integrity but not trusted authorship, and deserialization can execute code.

## 18. How does Docker orchestration preserve existing infrastructure?

Base Compose defines DemoCommerce, PostgreSQL, collector, monitoring and tool profiles. Step 6 adds detector/security, Step 7 optionally supplies an ML image/read-only artifacts, and Step 8 adds Nginx. WSO2 is separately managed on an external network; DB networking is internal. Selected-service `--no-recreate` preserves containers, but also preserves stale images. Builds alone do not update runtime code; approved cutover and readiness checks are still needed.

## 19. How does the dashboard handle security and fixture data?

It uses typed API contracts, independent monitoring/security credentials, server-verified capabilities and in-memory token handling. Disconnect/cancel prevents stale asynchronous verification from restoring credentials. Demo is explicit, read-only and never a failed-request fallback. Real browser checks verify UI/accessibility and mocked authorization flows, not DB durability. Production Nginx/demo behavior and header inheritance still need runtime validation.

## 20. What would you prioritize before release?

Review/integrate Step 9 without losing its work; reconcile stale monitoring/unavailable security services; review dependency findings; establish trusted gateway TLS; execute guarded DB and fresh end-to-end correlation; verify isolation and actual low-quota throttling. Approve a real API model and measure controlled performance only afterward. Current results are 156 Python passes plus four subtests/two known failures, 36 frontend unit passes and seven browser passes; no complete live or production-readiness claim is justified.
