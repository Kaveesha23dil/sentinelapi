# Reviewed portfolio release evidence

Application baseline: 891a269. All JSON is a sanitized summary of actual inspection
or execution; private raw logs/XML/traces/identity state remain ignored.

- evidence-inventory.json: all 31 user PNGs, image validation, SHA256/dimensions,
  visual decisions, unknown capture timestamps and 13 exact-copy destinations.
- git-secret-audit.json: baseline reachable text/blob scan, known local credential
  matching/signatures and forbidden artifact paths. Values are never emitted;
  this is not a guarantee against arbitrary historical secrets or binary-image leaks.
- test-summary.json: actual current JUnit/browser reconciliation and frontend
  outcomes, including the two Windows failures and two unexecuted ML/DB cases.
- synthetic-ml-metrics.json: actual experiment output, synthetic-controlled only.
- runtime-observations.json: actual read-only project/container snapshot; no private
  checkpoint state, event IDs, addresses, headers or credentials included.
- api-observations.json: authenticated/unauthenticated status checks and allowlisted
  alert fields/evidence counts using container-held credentials.

The source request-correlation proof and clean restart evidence belong to the prior
detection repair, not a workload repeated in this release audit. See
[verification](../../docs/release-verification.md) and
[all-image audit](../../docs/release-evidence-audit.md).
