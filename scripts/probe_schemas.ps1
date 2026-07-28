$ProgressPreference = 'SilentlyContinue'
$resp = Invoke-RestMethod -Uri 'http://54.80.228.144:8000/openapi.json' -TimeoutSec 8
$targets = @(
  '/api/v1/risk/portfolio',
  '/api/v1/analytics/portfolio/performance',
  '/api/v1/analytics/risk/metrics',
  '/api/v1/connections/brokers',
  '/api/v1/tax/calculate',
  '/api/v1/tax/supported_countries',
  '/api/v1/market/data',
  '/api/v1/live-prices',
  '/api/v1/system/status'
)
foreach ($t in $targets) {
  Write-Host "=== $t ==="
  $resp.paths.$t | ConvertTo-Json -Depth 6
  Write-Host ""
}
