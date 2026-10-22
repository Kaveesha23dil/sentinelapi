# PR title

Collect real WSO2 BASIC gateway traffic into PostgreSQL and expose monitoring

Base: main. Head: feature/api-traffic-collector. Proposed as a draft pending
review of the existing Step 3.3 security gaps. Do not merge without approval.

## Summary

Enable BASIC logs only for the existing DemoCommerceAPI through supported DevOps
operations. A bounded host bridge sanitizes real log records into a read-only
collector spool without recreating WSO2 or exposing Docker access to containers.
Only completed RESPONSE_OUT records become events; PostgreSQL uniqueness and
post-commit checkpoints protect replay/restart recovery. Missing duration and
client measurements remain NULL through a data-preserving migration.

Add authenticated loopback monitoring overview/events/API stats/health routes,
bounded UTC filtering/pagination, dedicated database roles and hardened Docker
services. Preserve DemoCommerce behavior, gateway security and all existing volumes.

## Verification

- 57 database/collector/monitoring tests passed; one AnyIO deprecation warning.
- 23 host WSO2 tooling/bridge tests passed.
- 12 existing DemoCommerce tests passed; one existing deprecation warning.
- Alembic upgrade/idempotence/drift and disposable downgrade/upgrade passed;
  retained Step 4 marker survived and runtime grants were verified.
- Real proof: gateway 200×4, 404, 401; 22 flows → six unique completed requests
  → six PostgreSQL rows → six API events. Collector restart/replay kept counts six.
- Real PostgreSQL outage: gateway 200, monitoring 503, checkpoint unchanged,
  then one queued real event recovered after restart.
- Sanitized evidence and exact commands: docs/step-5-verification.md.

## Review and limitations

Step 3.3 remains incomplete: backend host port 8000 still published and no observed
429 enforcement. This PR does not close those gaps. The host bridge must be
started/supervised on Windows and can only recover logs still retained by WSO2.
Correlation identity relies on the inspected BASIC format and source timestamp
precision. No threat detection, dashboard or final blog is included.

Screenshots: 0/8; no capture surfaces available. Exact checklist supplied. No
screenshots or performance measurements were fabricated. Feature push and remote
PR creation await approval; this file is prepared PR text, not an existing PR.
