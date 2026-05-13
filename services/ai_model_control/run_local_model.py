
import platform, os, subprocess, sys
from pathlib import Path
from const.ai_models import ModelProvider
from database.queries.ai_models import get_model_config




SCRIPTS_DIR = Path(__file__).parent.parent.parent / "scripts"


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _build_command(script_basename: str, *args: str) -> tuple[list[str], Path]:
    """
    Resolve the right script for the current OS and build the subprocess command.
    `script_basename` is the name without extension, e.g. 'start_ollama'.
    Returns (cmd, script_path).
    """
    if _is_windows():
        script_path = SCRIPTS_DIR / f"{script_basename}.ps1"
        if not script_path.exists():
            raise FileNotFoundError(f"PowerShell script not found: {script_path}")
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-File", str(script_path),
            *args,
        ]
    else:
        script_path = SCRIPTS_DIR / f"{script_basename}.sh"
        if not script_path.exists():
            raise FileNotFoundError(f"Shell script not found: {script_path}")
        # Ensure executable; harmless if already set
        try:
            os.chmod(script_path, 0o755)
        except OSError:
            pass
        cmd = ["bash", str(script_path), *args]

    return cmd, script_path

def _run_script(script_basename: str, *args: str) -> tuple[int, str, str]:
    """Run a platform-appropriate script and return (returncode, stdout, stderr)."""
    cmd, _ = _build_command(script_basename, *args)
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return result.returncode, result.stdout, result.stderr

# def _run_powershell(script_name: str, *args: str) -> tuple[int, str, str]:
#     """Run a PowerShell script and return (returncode, stdout, stderr)."""
#     script_path = SCRIPTS_DIR / script_name

#     if not script_path.exists():
#         raise FileNotFoundError(f"PowerShell script not found: {script_path}")

#     cmd = [
#         "powershell.exe",
#         "-NoProfile",
#         "-ExecutionPolicy", "Bypass",
#         "-File", str(script_path),
#         *args,
#     ]

#     result = subprocess.run(
#         cmd,
#         capture_output=True,
#         text=True,
#         timeout=120,
#     )
#     return result.returncode, result.stdout, result.stderr

# Start local ollama instance
# ---
# def start_ollama(model: ModelProvider) -> None:
#     """Run Start-Ollama.ps1. Raises RuntimeError on failure."""
#     print("[ollama] Starting via PowerShell... hehehehe", flush=True)

#     model_name = model.get("model_name")
#     host = model.get("host")

#     if not model_name:
#         raise RuntimeError("model_config.model_name is not set")
    
#     args = ["-Model", model_name]
#     if host:
#         args.extend(["-Ollamahost", host])

#     code, stdout, stderr = _run_powershell("start_ollama.ps1", *args)

#     if stdout:
#         print(stdout, flush=True)
#     if stderr:
#         print(stderr, file=sys.stderr, flush=True)

#     if code != 0:
#         raise RuntimeError(f"Start-Ollama.ps1 failed with exit code {code}")


# def stop_ollama() -> None:
#     """Run Stop-Ollama.ps1. Logs failures but does not raise."""
#     print("[ollama] Stopping via PowerShell...", flush=True)
#     try:
#         code, stdout, stderr = _run_powershell("stop_ollama.ps1")
#         if stdout:
#             print(stdout, flush=True)
#         if stderr:
#             print(stderr, file=sys.stderr, flush=True)
#         if code != 0:
#             print(f"[ollama] Stop script exited with code {code}", file=sys.stderr, flush=True)
#     except Exception as e:
#         print(f"[ollama] Failed to run stop script: {e}", file=sys.stderr, flush=True)



def start_ollama(model: ModelProvider) -> None:
    """Run start_ollama script. Raises RuntimeError on failure."""
    print(f"[ollama] Starting via {'PowerShell' if _is_windows() else 'bash'}...", flush=True)

    model_name = model.get("model_name")
    host = model.get("host")

    if not model_name:
        raise RuntimeError("model_config.model_name is not set")

    # Use long-form flags that both scripts accept
    args = ["--model", model_name]
    if host:
        args.extend(["-Ollamahost", host])
        # args.extend(["--host", host])

    code, stdout, stderr = _run_script("start_ollama", *args)

    if stdout:
        print(stdout, flush=True)
    if stderr:
        print(stderr, file=sys.stderr, flush=True)

    if code != 0:
        raise RuntimeError(f"start_ollama script failed with exit code {code}")


def stop_ollama() -> None:
    """Run stop_ollama script. Logs failures but does not raise."""
    print("[ollama] Stopping...", flush=True)
    try:
        code, stdout, stderr = _run_script("stop_ollama")
        if stdout:
            print(stdout, flush=True)
        if stderr:
            print(stderr, file=sys.stderr, flush=True)
        if code != 0:
            print(f"[ollama] Stop script exited with code {code}", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"[ollama] Failed to run stop script: {e}", file=sys.stderr, flush=True)