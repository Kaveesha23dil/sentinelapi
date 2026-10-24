# SentinelAPI portfolio summary

## One sentence

SentinelAPI is a WSO2-based API monitoring prototype that turns sanitized gateway completions into persisted traffic evidence, rule observations and experimental anomaly signals for a React investigation dashboard.

## 100-word description

SentinelAPI is an API security monitoring prototype built around WSO2 API Manager, FastAPI, PostgreSQL, and React. It collects sanitized gateway completion logs, deduplicates persisted events, and implements evidence-linked rule detection and experimental Isolation Forest inference. Historical verification correlated six gateway responses with database and monitoring records. Controlled synthetic evaluation reproduced model metrics, while browser tests verified dashboard fixtures and mocked authorization workflows. The project documents missing telemetry fields, deployment drift, Windows collector failures, and incomplete live acceptance. It demonstrates API management, persistence, testing, and provenance design without claiming production readiness, confirmed attack detection, measured throughput, or a fully verified deployment.

## Engineering features

- Deterministic completion-event IDs, transactional persistence, durable spool/checkpoint design and bounded reads.
- PostgreSQL constraints, migration guards, scoped roles and evidence-linked alert records.
- Five pure rule evaluators; only the error-rate adapter is eligible for live execution.
- Per-API minute features, chronological controlled evaluation and immutable, digest-reviewed ML artifacts.
- Seven dashboard views, typed contracts, server capability checks, memory-only tokens and explicit read-only demo fixtures.
- Unit/contract/browser tests and an unmerged guarded live harness; failures remain visible.

## WSO2-specific work

OpenAPI import/validation; inspection of existing API context/backend/security; revision deployment; OAuth application/subscription tooling; short-lived token verification; BASIC API Logs configuration and normalization. Historical live gateway write/read-back and source-to-DB correlation are retained. Dedicated low-quota enforcement and backend isolation are not verified outcomes.

## Stack

WSO2 API Manager 4.5.0, Python 3.12, FastAPI, PostgreSQL, SQLAlchemy, Alembic, Docker Compose, scikit-learn, React, TypeScript, Vite, Pytest, Vitest, Playwright and GitHub.

## Verified outcomes and boundaries

Current audit: 156 Python tests passed plus four subtests, two existing Windows failures; 36 frontend unit tests and seven Chromium tests passed; lint/typecheck/build passed. Thirty-two real DB checks were collected only. Historical live evidence correlated six responses/events and later observed 21 matches; it does not establish current health.

Controlled synthetic Isolation Forest results: precision .931034, recall .45, F1 .606742 and FPR .066667 across 180 held-out minutes. These are not production attack metrics. Full live rule/ML/dashboard acceptance, dependency remediation and performance measurements remain pending. Step 9 and its Windows fix are unmerged.

Repository: [SentinelAPI](https://github.com/Kaveesha23dil/sentinelapi). Blog: [unpublished technical draft](../blog/sentinelapi-wso2-technical-blog.md); public URL pending. Video: [recording plan](../demo-video-script.md), not recorded. [Audit](../final-project-audit.md) and [actual verification](../final-verification.md).

Application wording should present this as an evidence-conscious engineering prototype and discuss its tradeoffs. Do not describe it as deployed production security, proven attack prevention or a benchmarked system.
