# Portfolio release checklist

Prepared locally on `docs/portfolio-release-evidence` from clean application baseline `891a269`. Uncommitted user screenshots were preserved. This is a review-ready limited prototype candidate, not an all-green production release.

## Completed locally

- [x] Inventoried repository/history/branches and fetched remote metadata without reset, merge or push.
- [x] Preserved six prior local documentation/repair commits and the separate unmerged Step 9 branch.
- [x] Validated and visually reviewed all 31 new PNG originals; recorded hashes, dimensions, unknown capture times and provenance.
- [x] Copied 13 safe images byte-for-byte into final-blog; retained all original bytes locally.
- [x] Excluded the bearer-token image, raw-address log and personal-path captures without editing evidence.
- [x] Added a protective root-screenshot ignore and explicit reviewed-image staging workflow.
- [x] Added configurable browser capture output, reusing Step 9's small established approach without merging its whole harness or relaxing assertions.
- [x] Ran host/backend/model/service, real PostgreSQL, Linux/Windows collector, frontend unit/lint/typecheck/build and Chromium checks; retained both Windows failures.
- [x] Reproduced controlled synthetic ML metrics independently of runtime traffic.
- [x] Read current runtime state: healthy monitoring/collector, 99 gateway events, genuine alert/16 links; no live ML artifact/windows.
- [x] Updated README and canonical [technical blog draft](sentinelapi-technical-blog.md) with reviewed relative image paths/captions.
- [x] Documented separate WSO2, bridge, detector, API and frontend processes; left application/runtime configuration intact.
- [x] Scanned baseline reachable Git text for selected credential signatures/current local values and private artifact paths; reviewed new publication files separately.
- [x] Prepared meaningful local commits and a PR body; no remote write authorized or performed.

## Required before public publication/release

- [ ] Owner reviews/revokes the token shown in the excluded authorized screenshot if still active and assesses prior exposure. No value is republished here; credential rotation is not silently performed.
- [ ] Owner reviews the two existing historical collector XML reports containing local paths. No evidence or Git history was rewritten; any history cleanup needs a separately approved plan, never a force-push during this task.
- [ ] Owner reviews the limited-prototype wording and failed Windows tests. Integrate the existing reviewed portability fix through an approved workflow or explicitly accept/document the platform limitation; do not claim an all-green suite.
- [ ] Decide integration order for prior docs/runtime commits and Step 9. A merged harness alone does not establish its live acceptance.
- [ ] Optionally recapture response-only OAuth, rate-limit enforcement, sanitized logs and Screenshot 06 without personal paths/token/address fields. The safe evidence figure already supports the genuine alert narrative.
- [ ] Review captions, layout, alt text and actual image privacy on the publishing platform. Unknown capture times remain unknown.
- [ ] Select a project license/release version if publishing as a reusable release; no tracked LICENSE or new project tag was found/created. API version 1.0.0 is not automatically a project release tag.
- [ ] Approve push explicitly; approve PR creation explicitly. Review draft PR before any merge.
- [ ] Approve blog publication separately; add actual public URL only after it succeeds. No recorded demo video is claimed.

## Known engineering limitations

- Two direct Windows collector fixture failures remain; Linux transport and the deployed host bridge work. Source fix remains on Step 9.
- Only error_rate has a live evidence adapter; other four strategies stay disabled.
- No approved live ML artifact, zero stored ML windows; synthetic metrics do not measure attack accuracy.
- Dashboard screenshots/browser workflows are demo/mocked; full authenticated live rendering is not accepted.
- Loopback backend port 8000 still bypasses gateway enforcement; fixed demo identity is not end-user authentication.
- Gateway log source files can contain addresses; retention, backups/restoration, operational identity/TLS and dependency findings need further work.
- No measured throughput/latency/server-resource benchmark, current vulnerability certification, public deployment or CI success badge.

## Exact next Git commands

Read-only review first:

```powershell
git status --short --branch
git log --oneline origin/main..HEAD
git diff --stat origin/main...HEAD
git diff --check origin/main...HEAD
```

The branch inherits six unpushed commits (four earlier documentation checkpoints and two runtime-repair checkpoints). New release commits add to that ancestry. Do not reset/discard or force-push those commits. Review the full comparison before choosing the final integration order/base. Current origin/main is f931455.

**Only after push approval:**

```powershell
git push -u origin docs/portfolio-release-evidence
```

**Only after separate PR-creation approval**, with an authenticated GitHub CLI (or use the same reviewed body in the web interface):

```powershell
gh pr create --draft --base main --head docs/portfolio-release-evidence --title "docs: prepare SentinelAPI portfolio release and reviewed evidence" --body-file docs/portfolio-release-pr.md
```

No tag/release/merge command is supplied as an automatic next step. Evidence/configuration checkpoint: `2a6106a`. Review the actual commits with `git log --oneline 891a269..HEAD`; the documentation checkpoint resolves through `git log -1 --format=%H -- docs/sentinelapi-technical-blog.md`.

Primary evidence: [current verification](release-verification.md), [all-image audit](release-evidence-audit.md), [actual prior controlled validation](detection-runtime-repair.md). The project can be discussed for an internship as an evidence-based engineering prototype, with its remaining acceptance work visible.
