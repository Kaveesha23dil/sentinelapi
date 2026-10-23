# Detection rule catalog

All thresholds are validated PostgreSQL configuration, versioned on API updates.
Windows are UTC `(end-duration, end]`. All fixture results are offline only.

| Rule | Default condition | Grouping | Live eligibility |
| --- | --- | --- | --- |
| request_flood | >100 requests /60s | verified client + API | Pending verified identity adapter |
| error_rate | >=20 requests /300s and errors/requests >0.5 | API | Supported by stored BASIC fields; Step 6 live verification pending |
| enumeration | >=15 distinct trusted unknown routes /120s | verified client + API | Pending identity and route verdicts; 404/unmapped is insufficient |
| auth_failures | >=10 confirmed failures /120s | verified client + API | Pending explicit auth-failure evidence; 401 alone is insufficient |
| unusual_activity | volume / established average >3 /300s | verified client + API | Pending identity and baseline adapter/materialization |

HTTP errors include 400 through 599. Equality at flood/ratio/unusual thresholds
does not trigger; equality at enumeration/authentication counts does. Missing
identity suppresses client rules. Baselines must contain at least 12 complete,
equally sized historical windows, have positive mean and end before the current
window starts. The pure evaluator checks readiness/count/end; the trusted adapter
must establish window completeness, equal duration and provenance. No such live
baseline adapter exists yet. Unready baselines produce no alert.

Configuration fields: version (positive integer), window_seconds (1..300), threshold
(finite positive number; error ratio <=1), minimum_requests (1..100000),
baseline_windows (12..288). Unknown fields are rejected. Default severity is medium,
with fixed policy risk score 50. This is not a probability of compromise.

Bootstrap inserts all five definitions without overwriting existing settings;
only error_rate defaults enabled. Disabled rules are excluded from evaluation.
Rule updates require admin, increment version, and create an audit record.
Unsupported rules cannot be enabled through the management API.
