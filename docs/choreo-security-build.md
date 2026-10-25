# Choreo build 20001150621: critical Debian package findings

The user-supplied report and screenshot show Docker Build passed and the Trivy
gate failed on commit `3e155459e`. This supersedes the earlier context-path error.
Seven critical findings are listed in Debian packages; scanned Python packages
have zero findings in this report. No cloud deployment has succeeded.

The report lists fixed package versions:

| Package | Reported installed | Minimum fixed in report |
| --- | --- | --- |
| libgnutls30 | 3.7.9-2+deb12u6 | 3.7.9-2+deb12u7 |
| libssl3, openssl | 3.0.18-1~deb12u2 | 3.0.19-1~deb12u2 |
| perl-base | 5.36.0-7+deb12u3 | 5.36.0-7+deb12u4 |

Changed only the cloud backend Dockerfile to update APT indexes, upgrade available
Debian packages, and remove index files in the same layer before installing Python
requirements. This keeps Python/app startup, numeric UID 10002 and local Compose
unchanged. No CVE suppression or scan bypass was added.

Verification command:

```powershell
docker build --pull --no-cache -f backend/Dockerfile.choreo -t sentinelapi/monitoring:choreo-security-check backend
```

Local package version checks cannot replace Choreo's own current Trivy scan.
After reviewed changes are committed and an explicitly approved push completes,
Auto Build on Commit may immediately trigger a cloud build. Otherwise choose
Build Latest and confirm the new SHA. Require a successful vulnerability scan
before proceeding. Do not deploy until compromised secrets are rotated and
cloud runtime configuration is verified.

Docker may cache RUN upgrade layers on later builds. Future security refreshes
need cache invalidation or an updated base digest, followed by rebuild/rescan.

Sources: [Docker cache rules](https://docs.docker.com/reference/dockerfile/#cache-invalidation-for-run-instructions),
[WSO2 critical-CVE build gate](https://wso2.com/engineering-platform/developer-platform/docs/develop-components/deploy-a-containerized-application/).

Base commit: `3e15545`. Proposed commit: `fix: apply Debian security updates in Choreo image`.
No commit, push, cloud build trigger or deployment performed by this repair.

## Actual local results

Fresh `--pull --no-cache` build passed, including fresh Python dependency downloads.
Disposable network-isolated image checks confirmed UID 10002, successful FastAPI
import, `/healthz` HTTP 200, and Debian version comparisons at or above all four
reported package thresholds. Installed: libgnutls30 `3.7.9-2+deb12u7`, libssl3 and
openssl `3.0.22-1~deb12u1`, perl-base `5.36.0-7+deb12u4`.

The focused backend suite documented in choreo-deployment.md was rerun against
`sentinelapi/monitoring:choreo-security-check`: **106 passed**, one existing
Starlette/AnyIO deprecation warning. `git diff --check` passed. Trivy was not
installed locally; no full local scan or Choreo scan pass is claimed.
