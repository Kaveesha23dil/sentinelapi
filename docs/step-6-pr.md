# Prepared PR text (not published)

Title: feat: add explainable API threat detection and alert management

Base: main. Head: feature/rule-based-threat-detection.

Observed gateway HTTP errors can now be evaluated by a separate deterministic
worker. The change adds five configurable strategies, persistent incident metadata,
event-linked evidence, bounded replay/checkpoints and authenticated alert/rule APIs.
Only API-level error rate is eligible for live execution with the current BASIC
schema. Client flood, enumeration, authentication-failure and baseline rules remain
disabled until trusted telemetry adapters exist.

Validation and limitations: see step-6-verification.md for exact executed commands
and results. PostgreSQL migration/runtime permission checks and genuine WSO2 alert
validation remain blocked by the unavailable Docker runtime. Existing Linux-only
collector transport tests fail on Windows; they must be rerun in their Linux image.
Screenshots remain pending. Do not represent this draft as ready for merge.

No gateway configuration, existing persistent containers, volumes or alerts were
deleted or recreated. No push/remote PR/merge is authorized by this draft.
