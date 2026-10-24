# Render actual read-only SQL output for the controlled local validation capture.
# No credentials, raw traffic, client addresses or full event IDs are selected.
$ErrorActionPreference = 'Stop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI unavailable. Use the existing Docker Desktop host terminal.'
}
$queryPath = Join-Path $PSScriptRoot '../infrastructure/sql/security-alerts.sql'
Get-Content -LiteralPath $queryPath -Raw | docker exec -i sentinelapi-postgres psql -X `
    -U sentinelapi_owner -d sentinelapi -v ON_ERROR_STOP=1 -P pager=off -f -
if ($LASTEXITCODE -ne 0) {
    throw 'Read-only alert query failed. Verify the existing PostgreSQL service and owner identity.'
}
