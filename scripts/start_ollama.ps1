


param(
    [Parameter(Mandatory=$true)]
    [string]$Model,

    [Parameter(Mandatory=$false)]
    [string]$OllamaHost = "http://localhost:11434"
)

# Set Ollama env vars from params (sourced from DB)
$env:OLLAMA_HOST = $OllamaHost

Write-Host "Starting Ollama with model: $Model"
Write-Host "Host: $OllamaHost"


# Parse host for the health check URL
$healthUrl = "$($OllamaHost.TrimEnd('/'))/api/tags"
Write-Host "Health check URL: $healthUrl" -ForegroundColor DarkGray

# Check if Ollama is already running
function Test-OllamaRunning {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url `
            -UseBasicParsing `
            -TimeoutSec 5 `
            -ErrorAction Stop
        return $response.StatusCode -eq 200
    } catch {
        Write-Host "Health check failed: $($_.Exception.Message)" -ForegroundColor DarkGray
        return $false
    }
}

$running = Test-OllamaRunning -Url $healthUrl

if ($running) {
    Write-Host "Ollama is already running - skipping startup" -ForegroundColor Yellow
} else {
    Write-Host "Ollama not running - starting server..." -ForegroundColor Cyan
    Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "Ollama server started" -ForegroundColor Green
}

Write-Host "Running model (if its not already in memory...): $model" -ForegroundColor Cyan
ollama run $Model "" *> $null
# ollama run $model ""

Write-Host "Ollama ready" -ForegroundColor Green