$ProgressPreference = 'SilentlyContinue'
$r = Invoke-RestMethod -Uri 'http://54.80.228.144:8000/api/v1/connections/brokers' -TimeoutSec 8
$r | ConvertTo-Json -Depth 6
