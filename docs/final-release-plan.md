# Release and PR review plan

This file prepares a review, not a release announcement. No tag, GitHub release, push, remote Step 10 PR, merge, published blog, recorded video or public deployment is claimed.

## Branch gate

Initial clean checkout already named `docs/final-release-and-blog` at `f931455`, matching fetched main. Step 9 (`test/end-to-end-validation`, `d832c25` and `b9f6098`) is unmerged. Preserve it. The requested condition for creating the release branch from updated main has not passed; no new branch was created or reset. Current documentation is a local review draft on the existing branch.

Safest next action: review Step 9's tested portability fix and guarded harness, its failing live acceptance and known risks; obtain explicit approval before pushing that branch and creating its PR. Merging needs separate approval. If accepted, fetch the resulting main and integrate it into this docs branch with an ordinary reviewed merge, preserving both histories. Reconcile journal conflicts manually. Re-run documentation links, relevant tests and deployment acceptance. Do not force-push or discard either branch. A merged harness is not proof that live release gates passed.

## Proposed Step 10 PR

Title: `docs: prepare SentinelAPI portfolio documentation and release evidence`

Base: `main`. Head: `docs/final-release-and-blog`. Keep draft while Step 9/live acceptance gates remain unresolved.

Body:

> SentinelAPI's previous README did not explain safe multi-service startup or distinguish historical live ingestion from synthetic ML and dashboard fixtures. This change adds an evidence-based audit, editable architecture diagrams, deployment runbook, verification/evidence inventory, an unpublished WSO2 engineering article, a demo recording plan and internship materials.
>
> The source baseline remains f931455. Step 9 is unmerged; the current Windows collector tests still have two known failures. Current verification: 156 Python passes plus four subtests, two failures; 36 frontend unit passes; seven browser passes; lint/typecheck/build pass; 32 DB checks collected only. Synthetic ML metrics reproduced. Live security API is unavailable, monitoring is stale/drifted and gateway checks lack trusted TLS. No full live acceptance or performance result is claimed.
>
> No persistent container, WSO2 config or database was changed. Review the release gates in final-project-audit.md before approving publication claims. The blog remains a draft and the video is a plan.

## Local checkpoints and approval

Documentation is split into architecture/setup, audit/evidence, blog/demo and portfolio checkpoints. Their relevant checks are document links, evidence hashes/provenance, whitespace and credential review; existing runtime failures are documented, not silently fixed on this branch. Resolve exact hashes with:

```powershell
git log --oneline main..HEAD
git log -1 --format=%H -- docs/final-architecture.md
git log -1 --format=%H -- docs/final-project-audit.md
git log -1 --format=%H -- docs/blog/sentinelapi-wso2-technical-blog.md
git log -1 --format=%H -- docs/portfolio/project-summary.md
```

Push and PR creation remain pending approval. After authorization, push only the named branch; create a **draft** PR targeting main using this reviewed body. Do not push main or merge. No GitHub release tag/version is assigned before readiness and owner approval.

## Publication checklist

1. Decide whether to publish an explicitly limited prototype article now or wait for live acceptance. Preserve all provenance qualifications either way.
2. Resolve Step 9 integration and highest engineering risks; update counts only from actual executions.
3. Capture missing live WSO2/DB/detection evidence using the inventory's instructions, or retain explicit editorial TODOs.
4. Review wording, screenshots and public repository links for secrets/personal data. Add alt text and final image captions on the publishing platform.
5. Recheck official references, choose platform and approve final title/author text. Publish only after owner approval; then add the actual blog URL to README/portfolio.
6. Record the planned video only after validating its selected screens. Review the real file for secrets; then add its genuine link.
7. Approve any tag/release separately, with release notes that state remaining limitations. Never label this prototype production ready.
