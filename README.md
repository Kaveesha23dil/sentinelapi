# SentinelAPI

API security monitoring with WSO2 API Manager 4.5.0, FastAPI, PostgreSQL,
rule-based detection, experimental Isolation Forest models, and React.

## Security dashboard (Step 8)

```powershell
cd frontend
npm ci
npm run dev
```

Open **http://127.0.0.1:5173**. Node 26.7.0/npm 11.19.0 were used for verification.
The interface starts disconnected. Choose **Explore demo** for clearly labeled,
read-only fixtures, or **Connect backend** with existing monitoring and security
service credentials. Credentials stay in memory; reconnect after a browser reload.
Never put credentials in Vite environment variables, URLs, source files or screenshots.

Live development proxies use `frontend/.env.example`: monitoring on loopback 8010,
security/ML on 8020. Updated backend code must be running for the new inventory,
timeseries, filtering, capabilities and investigation routes. Demo mode never acts
as a fallback for a failed live request. Production Docker configuration disables
the demo entry point and uses same-origin proxies with loopback-only browser access.

Screens: Overview, API Traffic, Threat Alerts, Incident Details, Detection Rules,
ML Monitoring and API Services. ML provenance is explicit; anomalous behavior is not
treated as established malicious intent.

```powershell
npm run lint
npm run typecheck
npm test
npm run build
npx playwright install chromium
npm run test:browser
```

Step 8 has a verified frontend and contract-level tests; live WSO2/PostgreSQL
acceptance is pending. Step 7 models remain experimental. Existing Windows collector
tests have two known `os.O_DIRECTORY` failures. No persistent services/data were changed.

See [dashboard architecture](docs/dashboard-architecture.md),
[Step 8 verification](docs/step-8-verification.md),
[ML model card](docs/ml-model-card.md), and the [development journal](docs/development-journal.md).
