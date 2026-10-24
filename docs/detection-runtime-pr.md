SentinelAPI had no deployed detector or detector/security DB roles. Monitoring's
authenticated readiness correctly failed on stale collector input, while its
image was also behind source and could not be built by its own service name.

Make monitoring buildable from the established image, provision scoped roles
without implicit existing-password rotation, and support graceful detector stop.
Add sanitized authenticated probe diagnostics and focused regressions. Preserve
the existing evaluator, thresholds, schema, telemetry and checkpoints.

Verified controlled local WSO2 validation: 24 actual requests (4 HTTP 200, 20 HTTP
404) matched 24 BASIC completions and persisted events. Original 75 events are
preserved (99 total). The worker created one medium/open risk-50 error-rate alert
with 16 unique linked gateway error events, using the normal 120-second lateness
allowance. Monitoring/collector are healthy; authenticated security API returns
the same evidence. Detector stopped with exit 0 and resumed without a duplicate.

Tests: 122 host passes plus four subtests; 21 guarded PostgreSQL passes; 48 Linux
collector/monitoring/startup passes. Groups overlap; no failures/skips. Existing
AnyIO warning remains. Actual results and remaining limits are in
docs/detection-runtime-repair.md and infrastructure/detection-runtime/verification.json.

PostgreSQL/WSO2/collector containers and volumes were not recreated. Only stateless
monitoring was updated; detector/security were new services. No existing password
was rotated. Screenshot 06's actual read-only query is ready; manual PNG capture
is pending. No live ML, real-world attack or production-readiness claim.

Ancestry: this branch also contains the four prior local documentation commits
from docs/final-release-and-blog. Review the dependency/base before opening the PR.
No push or merge is included in the local repair.
