#!/usr/bin/env bash
set -euo pipefail

# --- arg parsing ---
MODEL=""
OLLAMA_HOST_ARG=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -Model|--model)
            MODEL="${2:-}"
            shift 2
            ;;
        -OllamaHost|--host)
            OLLAMA_HOST_ARG="${2:-}"
            shift 2
            ;;
        *)
            echo "Unknown argument: $1" >&2
            exit 2
            ;;
    esac
done

if [[ -z "$MODEL" ]]; then
    echo "Error: -Model/--model is required" >&2
    exit 2
fi

# Set OLLAMA_HOST env var from param (sourced from DB)
if [[ -n "$OLLAMA_HOST_ARG" ]]; then
    export OLLAMA_HOST="$OLLAMA_HOST_ARG"
fi

# Default for health check URL construction if host wasn't passed
HOST_FOR_URL="${OLLAMA_HOST_ARG:-http://localhost:11434}"

echo "Starting Ollama with model: $MODEL"
echo "Host: $HOST_FOR_URL"

# Build health check URL (strip trailing slash)
HEALTH_URL="${HOST_FOR_URL%/}/api/tags"
echo "Health check URL: $HEALTH_URL"

# --- health check ---
test_ollama_running() {
    local url="$1"
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        --max-time 5 \
        "$url" 2>/dev/null || echo "000")

    if [[ "$http_code" == "200" ]]; then
        return 0
    else
        echo "Health check failed: HTTP $http_code"
        return 1
    fi
}

# --- ensure ollama binary exists ---
if ! command -v ollama >/dev/null 2>&1; then
    echo "Error: 'ollama' is not installed or not on PATH." >&2
    echo "Install from https://ollama.com/download" >&2
    exit 127
fi

# --- start server if not running ---
if test_ollama_running "$HEALTH_URL"; then
    echo "Ollama is already running - skipping startup"
else
    echo "Ollama not running - starting server..."
    LOG_DIR="${TMPDIR:-/tmp}"
    nohup ollama serve >"$LOG_DIR/ollama.log" 2>&1 &
    disown || true
    sleep 2
    echo "Ollama server started (log: $LOG_DIR/ollama.log)"
fi

# --- warm the model into memory ---
echo "Running model (if it's not already in memory...): $MODEL"
ollama run "$MODEL" "" >/dev/null 2>&1 || true

echo "Ollama ready"