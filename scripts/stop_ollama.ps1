

param(
    [Parameter(Mandatory=$false)]
    [string]$OllamaHost = "http://localhost:11434"
)

Write-Host "Stopping all Ollama processes..." -ForegroundColor Cyan

$procs = Get-Process ollama -ErrorAction SilentlyContinue

if (-not $procs) {
    Write-Host "No Ollama processes running" -ForegroundColor Yellow
    exit 0
}

$stopped = 0
$failed  = 0

foreach ($p in $procs) {
    try {
        Stop-Process -Id $p.Id -Force -ErrorAction Stop
        Write-Host "Stopped ollama PID $($p.Id)" -ForegroundColor Green
        $stopped++
    } catch {
        Write-Host "Failed to stop PID $($p.Id): $($_.Exception.Message)" -ForegroundColor Red
        $failed++
    }
}

# Verify nothing's left
Start-Sleep -Milliseconds 500
$still = Get-Process ollama -ErrorAction SilentlyContinue
if ($still) {
    Write-Host "Some ollama processes still alive: $($still.Id -join ', ')" -ForegroundColor Red
    exit 1
}

Write-Host "All Ollama processes stopped ($stopped killed)" -ForegroundColor Green
exit 0