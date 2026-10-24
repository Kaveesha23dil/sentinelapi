# SentinelAPI final project audit

Audit date: 2026-10-24. Source baseline: `f931455`. This is a portfolio prototype audit, not production certification. User's Step 10 request supersedes AGENTS.md's historical Step 3.2 scope for documentation; infrastructure preservation rules still apply.

## Repository and method

Initial worktree was clean on already-existing `docs/final-release-and-blog`, identical to local main and origin/main at `f931455`. Approved `git fetch origin` succeeded and did not change that baseline. All 233 tracked paths were inventoried; implementation review covered Compose/Dockerfiles, application modules, migrations, test suites, evidence reports, journal and milestone documents. Dependencies, ignored runtime state and private secrets are not publication inputs. No claim is made to have manually read every lockfile entry or audited third-party binaries.

Local branches retained: main, docs/final-release-and-blog, feature/api-traffic-collector, feature/rule-based-threat-detection, feature/ml-anomaly-detection, feature/security-dashboard, fix/dashboard-issues and test/end-to-end-validation. No branch reset, discard or merge occurred.

GitHub REST PR metadata was read during this audit: PRs [1](https://github.com/Kaveesha23dil/sentinelapi/pull/1) (collector), [2](https://github.com/Kaveesha23dil/sentinelapi/pull/2) (rules), [3](https://github.com/Kaveesha23dil/sentinelapi/pull/3) (ML), [4](https://github.com/Kaveesha23dil/sentinelapi/pull/4) (dashboard) and [5](https://github.com/Kaveesha23dil/sentinelapi/pull/5) (dashboard fixes) are closed and merged into main. No Step 9 PR was returned. `test/end-to-end-validation` has two commits outside main: `d832c25` and `b9f6098`; `git merge-base --is-ancestor test/end-to-end-validation main` returned 1. Step 9 is not merged. The existing docs branch is retained for review drafts; it is not recreated under the false assumption that the requested prerequisite passed.

## Steps 1–9

| Step | Actual implementation/evidence | Completion boundary |
|---|---|---|
| 1 foundation | `f0d8705` repository initialization | Historical setup, not a public deployment |
| 2 DemoCommerce | `ce04982`; FastAPI and 12 service tests | In-memory demo business data; simulated payments |
| 3 WSO2 | `c7f4aa4`, `e2532f3`, `dc6df2f`; real gateway OAuth/routing reports | Context mismatch, host bypass and observed throttling remain unresolved despite commit titles |
| 4 database | `cf9abb8`; actual migrations, 26 tests and restart marker report | Historical initial-schema evidence; does not verify later detection/ML migrations live |
| 5 telemetry | `090d129` through `b3c4903`, merged PR 1 | Actual six-response correlation/replay and later 21-row observation; current collector stale |
| 6 rules | `4cc8368` through `e2b4010`, merged PR 2 | Five pure evaluators; only error_rate live adapter; no full live alert acceptance |
| 7 ML | `33c1d76` through `f089a8d`, merged PR 3 | Controlled synthetic experiment and source integration; real approved model/live scoring pending |
| 8 dashboard | `48ef53b` through `04b3852`, PRs 4–5 | Seven screens and fixture/mocked workflows tested; complete live acceptance pending |
| 9 final testing | `d832c25`, `b9f6098` on separate local branch | Unmerged, explicitly incomplete; recorded live suite 2 passed / 10 failed / 5 skipped |

## Implemented and verified

- Current offline source run: 156 Python passes, two known Windows collector failures, four passing subtests. Passing scope includes DemoCommerce, rule evaluators, ML feature/model/inference logic, HTTP/SQL contracts and WSO2 tooling fixtures; it is not live database proof.
- Current frontend lint/typecheck/build, 36 unit tests and seven Chromium tests passed. Browser checks include real rendering/accessibility and explicit mock API workflows.
- Current synthetic experiment reproduced `iforest-a51ad3e496475a8d` and the retained confusion matrices. No real attack dataset is implied.
- Historical real gateway report: six checks including OAuth rejection, subscribed access, gateway write and matching backend read-back. The requested context was still unmet.
- Historical initial-schema DB verification: 26 passes, migrations/repeat upgrade/schema comparison and restart durability on a disposable test database.
- Historical Step 5: six unique completed source responses matched six persisted/monitoring events, with unchanged count after replay; later runtime report matched 21 completions. These are bounded observations from 2026-10-22, not current end-to-end status.
- Current read-only HTTP observations: DemoCommerce health 200; monitoring no-token 401; authenticated overview 200 with zero recent requests; monitoring health 503 reporting DB available/collector stale. DB availability is the service's report, not independent SQL verification.

## Implemented but not end-to-end verified

Detection worker transactions, advisory locks, watermarks, evidence links, incident lifecycle/audit, scoped grants, ML windows, model validation and authenticated dashboard routes exist in source. The current DB has not been independently checked against the latest migrations/grants. The optional ML and Nginx Compose deployments have not been validated on this host. All 32 current DB-dependent tests were only collected. Genuine rule/ML alert-to-dashboard persistence and replay are not proven.

## Synthetic demonstration only

The Isolation Forest experiment generates 25,953 events over 540 minutes: 360 training and 180 held-out minutes, including 60 normal/120 scenario windows. ML precision 0.931034, recall 0.45, F1 0.606742 and FPR 0.066667 describe those labels only. The rule comparison uses different temporal history. Both detectors miss scenarios. Unsupervised anomalies are not confirmed attacks.

React screenshots contain explicitly labeled fixtures: 86 illustrative records, three fixture services, example alerts and anomaly scores. These are not three deployed APIs or observed live attacks. Simulated payments do not move money. Mocks establishing UI state changes do not establish database durability.

## Incomplete or blocked

| Priority | Defect/gap | Evidence and safest action |
|---|---|---|
| High engineering release risk | Complete live chain absent | Restore existing Docker control, reconcile deployment and run correlated acceptance before release claims |
| High | Security/ML API unavailable | Current 8020 connection failure; inspect existing deployment without recreation |
| High | Source/runtime drift | Monitoring session 404, invalid status filter 200; source contracts expect session/422; deploy reviewed code through approved update |
| High | Runtime dependency findings unresolved | Step 9 installed audit recorded 12 advisories in three packages, including Starlette; review compatible upgrades and retest, not exploit claims |
| Medium | Collector stale | Current authenticated health 503; restore bridge/collector and correlate real source rows |
| Medium | Windows collector portability | Two reproduced O_DIRECTORY failures; tested fix is unmerged in `d832c25` |
| Medium | Gateway-only isolation absent | Source publishes unauthenticated backend on loopback 8000; current health 200; approved network/deployment change required |
| Medium | Gateway trust/authorization acceptance incomplete | Current no-token attempt fails certificate verification; no bypass used; expired/unsubscribed and bounded 429 checks still pending |
| Medium | Latest DB migrations/reliability unverified | 32 tests collected only; provision guarded separate test DB, preserve project data |
| Medium | No approved real-API ML baseline | Synthetic artifact is experimental and API-scoped; collect sufficient actual history before promotion |
| Medium | No performance measurements | Step 9 wrapper recorded NOT RUN; do not publish throughput or latency figures |
| Low/configuration | API context decision unresolved | Deployed `/democommerceapi` differs from requested `/democommerce`; accept/document or plan a separate migration |
| Editorial | Missing live screenshots/video/blog publication | Capture actual evidence after prerequisites; retain honest placeholders |

Priorities describe project/release risk, not CVSS scores. No production readiness claim is supported.

## Known security limitations

- Gateway authentication does not isolate an unauthenticated backend reachable from the host. Internal HTTP and loopback binding are not transport encryption or zero-trust design.
- No trusted stable client identity/latency in observed BASIC data; request-flood/auth/enumeration/baseline adapters remain unavailable. Unknown-route mapping and status codes cannot establish attack intent.
- Static bearer tokens and in-memory browser handling are local-development controls, not a complete production identity/session/TLS design.
- Raw WSO2 logs can contain sourceIP even though downstream events omit it. No verified retention, backup restore, audit immutability or disaster recovery exists.
- Joblib deserialization requires trusted artifacts. Hashes detect byte changes but do not authenticate authorship.
- Finite replay allowance and gateway log retention permit missed history. NULL measurements and empty buckets must remain explicit.
- Step 9 reported four medium/47 low Bandit findings and dependency advisories; source review is not a penetration test. Container/WSO2 deployed dependencies were not audited. Nginx location-level header inheritance also needs runtime review.

## Release decision

Suitable for an internship discussion as an honestly scoped engineering prototype with reproducible fixture/synthetic demonstrations. Not ready for claims of full live completion, production deployment or measured performance. Preserve Step 9's two commits and review its PR first. An approved merge alone would not clear its live failures. Documentation is prepared locally while those gates remain visible. [Verification](final-verification.md), [evidence](final-evidence-inventory.md), [release plan](final-release-plan.md).
