# Final blog capture 06: genuine security alert

Status: genuine alert verified on 2026-10-24; **manual PNG capture pending**.
No placeholder, generated image or reconstructed terminal screenshot is provided.

Target: `06-security-alerts.png`.

In the existing repository's Docker Desktop host PowerShell:

```powershell
Clear-Host
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/show_security_alerts.ps1
```

This executes `infrastructure/sql/security-alerts.sql` in a READ ONLY transaction,
using real persisted records. The verified row has title “Observed API error-rate
spike”, severity medium, risk 50.00, status open, first detection
2026-10-24 07:52:41.065997+00 and 16 linked gateway evidence records.
If later records exist, capture their actual returned values instead of editing them.

Widen the terminal, press Win+Shift+S, select the actual table and save the PNG here.
Exclude secret-bearing terminal history, personal host paths, notifications and
unrelated windows. The query does not select credentials, client addresses or
full event IDs. Inspect the resulting image before staging it.

Caption: **Controlled local WSO2 error-rate validation: genuine persisted alert
with linked evidence; not a real-world attack.** Retain the title, severity, risk,
status, UTC timestamp and evidence count. Record actual capture time and commit in
a sidecar only after capture. No video or screenshot creation is claimed here.

[Validation and exact commands](../../docs/detection-runtime-repair.md).
