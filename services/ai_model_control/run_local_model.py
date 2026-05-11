import subprocess
import sys
from pathlib import Path
from const.ai_models import ModelProvider
from database.queries.ai_models import get_model_config




SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"






def _run_powershell(script_name: str, *args: str) -> tuple[int, str, str]:
    """Run a PowerShell script and return (returncode, stdout, stderr)."""
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"PowerShell script not found: {script_path}")

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script_path),
        *args,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode, result.stdout, result.stderr

# Start local ollama instance
# ---
def start_ollama(model: ModelProvider) -> None:
    """Run Start-Ollama.ps1. Raises RuntimeError on failure."""
    print("[ollama] Starting via PowerShell... hehehehe", flush=True)

    model_name = model.get("model_name")
    host = model.get("host")

    if not model_name:
        raise RuntimeError("model_config.model_name is not set")
    
    args = ["-Model", model_name]
    if host:
        args.extend(["-Ollamahost", host])

    code, stdout, stderr = _run_powershell("start_ollama.ps1", *args)

    if stdout:
        print(stdout, flush=True)
    if stderr:
        print(stderr, file=sys.stderr, flush=True)

    if code != 0:
        raise RuntimeError(f"Start-Ollama.ps1 failed with exit code {code}")


def stop_ollama() -> None:
    """Run Stop-Ollama.ps1. Logs failures but does not raise."""
    print("[ollama] Stopping via PowerShell...", flush=True)
    try:
        code, stdout, stderr = _run_powershell("stop_ollama.ps1")
        if stdout:
            print(stdout, flush=True)
        if stderr:
            print(stderr, file=sys.stderr, flush=True)
        if code != 0:
            print(f"[ollama] Stop script exited with code {code}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ollama] Failed to run stop script: {e}", file=sys.stderr, flush=True)