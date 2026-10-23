# feat: add SentinelAPI security monitoring dashboard

Base main; head feature/security-dashboard. Prepared locally, no remote PR yet.

Adds seven responsive React/TypeScript screens with explicit live/demo separation,
Zod contracts, server-verified capabilities, memory-only credentials, bounded polling,
incident status review and admin rule controls. New authenticated read-only backend
queries supply inventory, timeseries, endpoint ranking, safe incident events/audit
history and server request filters. Adds a standalone loopback-only frontend Compose
service without changing persistent services or WSO2/PostgreSQL state.

Validation: lint/typecheck/production build pass; 32 component/contract tests pass;
five Chromium browser tests pass, including seven desktop axe scans, mobile layout,
fixtures and mocked authorization/update contracts. Backend/tool regressions: 126
passed plus four subtests. Collector/demo: 30 passed, two known Windows O_DIRECTORY
failures. 32 PostgreSQL/monitoring checks collected, not executed. Nine genuine
screenshots captured; application images show DEMO DATA. GitHub capture pending.

Live WSO2-to-dashboard acceptance, SQL/grants on the real host, Docker deployment
and production identity/TLS review remain pending. Step 7 is still experimental.
Mocked APIs and synthetic ML metrics are not production proof. Review as an
implemented dashboard with incomplete live acceptance; no merge authorization given.
