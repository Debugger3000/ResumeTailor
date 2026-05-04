# Load .env if present
$envFile = Join-Path $PSScriptRoot "..\.env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+?)\s*=\s*(.+?)\s*$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
        }
    }
}

$model = if ($env:OLLAMA_MODEL) { $env:OLLAMA_MODEL } else { "qwen3:8b" }

Write-Host "Checking if Ollama is already running..." -ForegroundColor Cyan

$running = try {
    (Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200
} catch {
    $false
}

if ($running) {
    Write-Host "Ollama is already running - skipping startup" -ForegroundColor Yellow
} else {
    Write-Host "Ollama not running - starting server..." -ForegroundColor Cyan
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "Ollama server started" -ForegroundColor Green
}

Write-Host "Loading model: $model" -ForegroundColor Cyan
ollama run $model "" *> $null
# ollama run $model ""

Write-Host "Ollama ready" -ForegroundColor Green