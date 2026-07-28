$ProgressPreference = 'SilentlyContinue'
try {
    $resp = Invoke-RestMethod -Uri 'http://54.80.228.144:8000/openapi.json' -TimeoutSec 8
    $resp.paths.PSObject.Properties.Name | Sort-Object
} catch {
    Write-Host "FAILED: $($_.Exception.Message)"
}
