
from database.queries.ai_models import get_model_config
from const.ai_models import ModelProvider, OllamaStatus, ModelType
import requests
from services.ai_model_control.claude_client import claude_client
from services.ai_model_control.ollama_client import ollama_client
from services.ai_model_control.gemini_client import gemini_client
import json
import time
from database.queries.ai_models import get_model_config
import re

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
        "configured": True,
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



# Call current model for use 
# return structured json data
# ai/inference.py
async def run_model(system_prompt: str, user_content: str, schema: dict, model_type: ModelType) -> tuple[dict, float]:

    print("model type in run_model:")
    print(model_type)

    models = get_model_config()
    if not models:
        raise RuntimeError("No model configured")

    messages = [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user',   'content': user_content},
    ]

    # print(f"=== run_structured: provider={model.get('provider')}, "
    #       f"input {len(user_content)} chars ===")
    start = time.time()

    if is_model_listed():
        # if no model config exists, it doesnt start any...
        #cloud_model = next((m for m in models if not is_model_local(m.get('provider'))),None,)

        if model_type == ModelType.LOCAL:
            response = await ollama_client.chat(
                model=ollama_client.model,
                messages=messages,
                #format=schema,
                options={
                'temperature': 0.0,
                },
            )

            if isinstance(response, str):
                raw_text = response
            else:
                raw_text = getattr(response, 'message', response).content if hasattr(response, 'message') else str(response)

            raw_text = raw_text.strip()

            print(f"--- DEBUG: Raw model text received ({len(raw_text)} chars) ---")
            
            # Regex extraction to grab whatever is inside curly or straight brackets if it added fluff
            json_match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)
            if json_match:
                raw_text = json_match.group(1)

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON Parse failed on text:\n{raw_text}")
                # Return an empty answers structure matching your schema type so the loop doesn't blow up
                parsed = {"answers": []}
        # cloud model is current selection so run gemini...
        else:
            # parsed = await claude_client.chat(messages=messages, schema=schema)  # returns dict
            # print(f"=== run_model parsed: {model.get('api_key_env')} ===")
            parsed = await gemini_client.chat(messages=messages, schema=schema)  # returns dict


    elapsed = time.time() - start
    print(f"=== run_structured returned in {elapsed:.1f}s ===")
    print(f"=== run_model parsed: {parsed} ===")
    return parsed, elapsed