
from database.queries.ai_models import get_model_config
from const.ai_models import ModelProvider, OllamaStatus
import requests

def is_model_listed() -> bool:
    model = get_model_config()

    # if empty return false
    if model == None:
        return False
    else:
        return True
    


def is_model_local(model: str) -> bool:
    model_lower = model.lower()

    if model_lower == ModelProvider.OLLAMA:
        return True
    else:
        return False
    



def ollama_status(model: ModelProvider) -> OllamaStatus:
    """Check if Ollama is running and which models are loaded."""
   
    host = (model or {}).get("host") or "http://localhost:11434"
    model_name = model.get("model_name")
    provider   = model.get("provider", "ollama")

    base = {
        "provider": provider,
        "model_name": model_name,
        "host": host,
    }

    try:
        resp = requests.get(f"{host.rstrip('/')}/api/ps", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            loaded = [m.get("name", m.get("model", "")) for m in data.get("models", [])]
            return {**base, "running": True, "loaded_models": loaded, "error": None}

        return {**base, "running": False, "loaded_models": [], "error": f"HTTP {resp.status_code}"}

    except requests.exceptions.ConnectionError:
        return {**base, "running": False, "loaded_models": [], "error": None}
    except Exception as e:
        return {**base, "running": False, "loaded_models": [], "error": str(e)}

