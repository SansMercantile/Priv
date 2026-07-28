$ProgressPreference = 'SilentlyContinue'
$base = 'http://54.80.228.144:8000'
$eps = @(
  '/api/v1/connections/brokers',
  '/api/v1/analytics/portfolio/performance',
  '/api/v1/analytics/risk/metrics',
  '/api/v1/system/status',
  '/api/v1/live-prices?symbols=EURUSD,BTCUSD',
  '/api/v1/agents/status'
)
foreach ($e in $eps) {
  Write-Host "=== $e ==="
  try {
    $r = Invoke-RestMethod -Uri "$base$e" -TimeoutSec 8
    $r | ConvertTo-Json -Depth 5
  } catch {
    Write-Host "REQUEST FAILED"
  }
  Write-Host ""
}
