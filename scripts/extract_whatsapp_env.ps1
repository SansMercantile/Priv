Select-String -Path 'C:\Users\kpasc\source\repos\priv\.env' -Pattern '^WHATSAPP_(ACCESS_TOKEN|PHONE_NUMBER_ID)=' | ForEach-Object { $_.Line } | Set-Content -Path 'C:\Users\kpasc\source\repos\priv\scripts\whatsapp_env_lines.txt'
Write-Host "LINES:"
Get-Content 'C:\Users\kpasc\source\repos\priv\scripts\whatsapp_env_lines.txt' | Measure-Object -Line
