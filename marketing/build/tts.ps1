param([string]$InFile,[string]$Out,[string]$Voice = "Microsoft David Desktop",[int]$Rate = 0)
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
try { $s.SelectVoice($Voice) } catch { }
$s.Rate = $Rate
$s.SetOutputToWaveFile($Out)
$s.Speak((Get-Content -Raw -LiteralPath $InFile))
$s.Dispose()
