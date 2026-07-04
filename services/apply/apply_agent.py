import json
import os
import time
from ollama import AsyncClient

from const.apply_prompt import APPLY_PROMPT, POPULATE_FIELDS_SCHEMA
from const.ai_models import ModelType
#from const.personal_info import PROFILE  # adjust import to wherever your profile lives
from services.ai_model_control.ollama_client import ollama_client
from services.apply.apply_helpers import get_full_user_data
from services.ai_model_control.helpers import run_model

async def populate_field_values(fields: list[dict], model_type: ModelType) -> tuple[list[dict], float]:
    """
    Given the extracted form fields, ask the model to populate an array of lean answers, 
    then stitch the values straight back into the original HTML kind metadata blocks.
    """
    user_prompt = json.dumps({
        'profile': get_full_user_data(), 
        'fields': fields,
    })

    try:
        parsed, elapsed = await run_model(APPLY_PROMPT, user_prompt, POPULATE_FIELDS_SCHEMA, model_type)
        
    except json.JSONDecodeError as e:
        print(f"=== run_model call: POPULATE FIELDS JSON DECODE ERROR: {e} ===")
        return fields, 0.0          

    print(f"=== populate_field_values returned in {elapsed:.1f}s ===")

    # Convert the returned array into a local Python lookup dictionary
    raw_answers = parsed.get('answers', []) if isinstance(parsed, dict) else []
    answers_map = {item["agent_id"]: item["value"] for item in raw_answers if "agent_id" in item}
    
    # Merge values programmatically straight into your original field configurations
    merged = []
    for original in fields:
        aid = original.get("agent_id")
        kind = original.get("kind", "text")
        
        if aid and aid in answers_map:
            raw_val = answers_map[aid]
            
            # Map values correctly depending on field types
            if kind in ("checkbox", "ashby_toggle"):
                if str(raw_val).lower() in ("true", "yes", "on", "checked", "1"):
                    value_to_assign = True
                elif str(raw_val).lower() in ("false", "no", "off", "0"):
                    value_to_assign = False
                else:
                    value_to_assign = raw_val
            else:
                value_to_assign = str(raw_val)
        else:
            value_to_assign = False if kind in ("checkbox", "ashby_toggle") else ""
            
        merged.append({**original, "value": value_to_assign})

    print(merged)
    print(f"=== Populated {sum(1 for f in merged if f.get('value') not in (None, '', False))} of {len(merged)} fields ===")
    return merged, elapsed