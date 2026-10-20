param(
    [string]$OutputPath = 'infrastructure/wso2/environment-verification.json'
)
$ErrorActionPreference = 'Stop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI unavailable. Run in a host PowerShell with Docker Desktop on PATH.'
}
function Invoke-DockerChecked {
    param([string[]]$Arguments)
    $result = & docker @Arguments
    if ($LASTEXITCODE -ne 0) { throw 'Docker verification command failed.' }
    return $result
}
$containers = @()
foreach ($name in @('sentinelapi-democommerce', 'sentinelapi-wso2')) {
    # Inspect only selected fields; never persist container environment variables.
    $raw = Invoke-DockerChecked -Arguments @('inspect', $name, '--format', '{{json .State}}')
    $state = $raw | ConvertFrom-Json
    $image = Invoke-DockerChecked -Arguments @('inspect', $name, '--format', '{{.Config.Image}}')
    $raw = Invoke-DockerChecked -Arguments @('inspect', $name, '--format', '{{json .NetworkSettings.Networks}}')
    $networks = $raw | ConvertFrom-Json
    if (-not $state.Running) { throw "$name is not running" }
    if (-not $networks.PSObject.Properties['sentinelapi-network']) {
        throw "$name is not attached to sentinelapi-network"
    }
    $containers += [ordered]@{
        name = $name
        image = "$image"
        running = $state.Running
        docker_health = $(if ($state.Health) { $state.Health.Status } else { 'not configured' })
        network = 'sentinelapi-network'
    }
}
$health = Invoke-RestMethod -Uri 'http://localhost:8000/health' -TimeoutSec 15
if ($health.status -ne 'healthy') { throw 'Backend health endpoint failed' }
$networkHealth = Invoke-DockerChecked -Arguments @('exec', 'sentinelapi-wso2', 'curl',
    '--fail', '--silent', '--show-error', '--max-time', '15', 'http://democommerce:8000/health')
if (($networkHealth | ConvertFrom-Json).status -ne 'healthy') {
    throw 'Backend health check from WSO2 failed'
}
$report = [ordered]@{
    checked_at_utc = (Get-Date).ToUniversalTime().ToString('o')
    containers = $containers
    host_backend_health = $health
    wso2_to_backend_health = ($networkHealth | ConvertFrom-Json)
}
$report | ConvertTo-Json -Depth 8 | Set-Content -Encoding UTF8 -LiteralPath $OutputPath
Write-Output 'PASS: both containers running on sentinelapi-network; host and WSO2 backend health checks passed.'
Write-Output "Redacted evidence saved to $OutputPath"
