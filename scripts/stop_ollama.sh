#!/usr/bin/env bash
set -uo pipefail
# NOTE: not using `set -e` here — we want to keep going even if individual kills fail,
# matching the PS1 script's behavior.

# --- arg parsing (accepted but unused, matches PS1 signature) ---
OLLAMA_HOST_ARG="http://localhost:11434"
while [[ $# -gt 0 ]]; do
    case "$1" in
        -OllamaHost|--host)
            OLLAMA_HOST_ARG="${2:-}"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

echo "Stopping all Ollama processes..."

# Get all ollama PIDs. `pgrep -x` matches exact process name.
mapfile -t PIDS < <(pgrep -x ollama 2>/dev/null || true)

if [[ ${#PIDS[@]} -eq 0 ]]; then
    echo "No Ollama processes running"
    exit 0
fi

stopped=0
failed=0

for pid in "${PIDS[@]}"; do
    if kill -TERM "$pid" 2>/dev/null; then
        echo "Sent TERM to ollama PID $pid"
        stopped=$((stopped + 1))
    else
        echo "Failed to signal PID $pid" >&2
        failed=$((failed + 1))
    fi
done

# Give them a moment to die gracefully, then force-kill stragglers
sleep 1

mapfile -t STILL < <(pgrep -x ollama 2>/dev/null || true)
if [[ ${#STILL[@]} -gt 0 ]]; then
    echo "Force-killing stragglers: ${STILL[*]}"
    for pid in "${STILL[@]}"; do
        kill -KILL "$pid" 2>/dev/null || true
    done
    sleep 0.5
fi

# Verify
mapfile -t REMAINING < <(pgrep -x ollama 2>/dev/null || true)
if [[ ${#REMAINING[@]} -gt 0 ]]; then
    echo "Some ollama processes still alive: ${REMAINING[*]}" >&2
    exit 1
fi

echo "All Ollama processes stopped ($stopped signaled)"
exit 0