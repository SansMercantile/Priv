$b = Get-Content 'C:\Users\kpasc\source\repos\priv\scripts\connections_api_new.b64' -Raw
$len = $b.Length
$chunkSize = 3000
$n = [Math]::Ceiling($len / $chunkSize)
for ($i = 0; $i -lt $n; $i++) {
    $start = $i * $chunkSize
    $size = [Math]::Min($chunkSize, $len - $start)
    $chunk = $b.Substring($start, $size)
    Set-Content -Path "C:\Users\kpasc\source\repos\priv\scripts\chunk_$i.txt" -Value $chunk -NoNewline
}
Write-Host "CHUNKS:" $n
