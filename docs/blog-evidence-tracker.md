# Authentic development evidence inventory

No final blog is being written here. Screenshot inventory was inspected with
`rg --files screenshots`: only checklist READMEs existed, with no captured images.

| Milestone | Screenshots captured | Remaining evidence |
| --- | --- | --- |
| Step 3.2 API integration | 0/9 | screenshots/03-api-integration/README.md |
| Step 3.3 security | 0/8 | screenshots/03-security/README.md; isolation and actual 429 still unverified |
| Step 4 database | 0/7 | screenshots/04-database/README.md |
| Step 5 traffic collection | 0/8 | screenshots/05-traffic-collection/README.md |

Step 5 genuine non-image evidence under infrastructure/telemetry:

- logging-configuration.json: supported DevOps OFF → BASIC, scoped to DemoCommerce.
- log-format-observations.json: field names and sanitized real record metadata.
- gateway-precheck.json: real OAuth routing smoke results, separately from older milestones.
- prerequisite-verification.json: retained Step 4 test marker and actual migration revision.
- runtime-privileges.json: authenticated collector/monitor role permission checks.
- test-results.json: 57 executed tests, migration cycle and separate demo restart marker.
- e2e-verification.json: six real completed gateway requests matched to DB/API;
  checkpointed collector restart/replay kept both scoped counts at six.
- outage-verification.json: real gateway 200, monitoring 503 during PostgreSQL outage,
  unchanged collector checkpoint, one real event recovered exactly once.
- runtime-status.json: bounded current-log/DB/API matching and current service health.

JSON reports are evidence files, not screenshots. Fabricated test data is labeled
and isolated in test databases. It must never illustrate real WSO2 traffic.
Before any screenshot is marked captured, verify file existence, open it, inspect
redaction and confirm the actual service/test window. Do not generate or rebuild UI.

Git provenance: feature/api-traffic-collector, persistence 090d129, collector
7345a5e, monitoring 48d141f. Resolve the final evidence commit via
`git log -1 --format=%H -- docs/step-5-verification.md`. GitHub PR evidence remains
pending until approved feature push and actual PR creation. Step 3.3 remains
incomplete independently of the verified Step 5 collection path.
