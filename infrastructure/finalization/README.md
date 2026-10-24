# Reviewed finalization evidence

Audit 2026-10-24, application source baseline f931455. These sanitized files are
derived from actual executions, not fabricated reports:

- `test-summary.json`: current Pytest JUnit and Playwright JSON reconciliation;
  frontend command outcomes; DB collection count; separately labeled historical
  Step 9 local XML totals. Four subtests are XML cases, not extra console tests.
- `synthetic-ml-metrics.json`: actual rerun output at its recorded UTC evaluation
  time. Every event/label is controlled synthetic; production_ready is false.
- `runtime-observations.json`: read-only monitoring HTTP observations using the
  existing private token in memory. Only allowlisted status/count/health fields
  are retained; this is not independent SQL verification.
- `image-inventory.json`: actual image dimensions and byte hashes, classification
  and pre-checkpoint last committed revision. It does not infer capture times from
  Git timestamps or file modification times.

Raw XML, traces, local paths, model binaries and private configuration remain
ignored under .runtime or frontend output directories. Reproduction commands and
limits are in [final verification](../../docs/final-verification.md); image review
and missing captures are in [evidence inventory](../../docs/final-evidence-inventory.md).
No full live acceptance, benchmark, new vulnerability scan or production deployment
is established by these files.
