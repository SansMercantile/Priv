$bytes = [System.IO.File]::ReadAllBytes("C:\Users\kpasc\source\repos\priv\scripts\connections_api_new.py")
$b64 = [Convert]::ToBase64String($bytes)
Set-Content -Path "C:\Users\kpasc\source\repos\priv\scripts\connections_api_new.b64" -Value $b64 -NoNewline
Write-Host "LENGTH:" $b64.Length
