param([switch]$SkipRestart)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repository = Split-Path -Parent $PSScriptRoot
Push-Location $repository
try {
    function Invoke-ComposeChecked {
        param([string[]]$Arguments)
        & docker compose @Arguments
        if ($LASTEXITCODE -ne 0) { throw 'Database check failed. Review the preceding safe output; no volumes were removed.' }
    }
    $evidence = Join-Path $repository 'infrastructure/database'
    New-Item -ItemType Directory -Force -Path $evidence | Out-Null
    Invoke-ComposeChecked -Arguments @('config', '--quiet')
    Invoke-ComposeChecked -Arguments @('build', 'persistence')
    # Refuse to recreate a persistent service if config changed. Inspect and
    # migrate existing deployments deliberately rather than resetting data.
    Invoke-ComposeChecked -Arguments @('up', '-d', '--no-deps', '--no-recreate', '--wait', 'postgres')
    $runner = @('run', '--rm', '--no-deps', '--volume', "${repository}/backend:/app",
                '--volume', "${evidence}:/evidence", 'persistence')
    Invoke-ComposeChecked -Arguments ($runner + @('alembic', 'upgrade', 'head'))
    Invoke-ComposeChecked -Arguments ($runner + @('alembic', 'upgrade', 'head'))
    Invoke-ComposeChecked -Arguments ($runner + @('alembic', 'check'))
    Invoke-ComposeChecked -Arguments ($runner + @('python', '-m', 'sentinelapi.db.verify', 'prepare'))
    if ($SkipRestart) {
        Write-Output 'PENDING: container restart verification explicitly skipped.'
    } else {
        Invoke-ComposeChecked -Arguments @('restart', 'postgres')
        # Dependency health condition waits for PostgreSQL before the new process.
        $restartRunner = @('run', '--rm', '--volume', "${repository}/backend:/app",
                          '--volume', "${evidence}:/evidence", 'persistence')
        Invoke-ComposeChecked -Arguments ($restartRunner + @('python', '-m', 'sentinelapi.db.verify', 'restart-check'))
    }
} finally {
    Pop-Location
}
