import json
import os
import time
from ollama import AsyncClient


from database.queries.get_user_data_apply import get_user_profile, get_user_skills, get_work_experience
from const.apply_input import POPULATE_FIELDS_PROMPT
from const.personal_info import PROFILE  # adjust import to wherever your profile lives

ollama_client = AsyncClient(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')


POPULATE_FIELDS_SCHEMA = {
    'type': 'object',
    'properties': {
        'fields': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'agent_id': {'type': 'string'},
                    'kind': {'type': 'string'},
                    'question': {'type': 'string'},
                    'options': {
                        # Either null or an array of {value, label}
                        'type': ['array', 'null'],
                        'items': {
                            'type': 'object',
                            'properties': {
                                'value': {'type': 'string'},
                                'label': {'type': 'string'},
                            },
                            'required': ['value', 'label'],
                        },
                    },
                    'required': {'type': 'boolean'},
                    'value': {
                        # Strings, bools, or empty — keep permissive
                        'type': ['string', 'boolean', 'null'],
                    },
                },
                'required': ['agent_id', 'kind', 'question', 'required', 'value'],
                'additionalProperties': True,
            },
        },
    },
    'required': ['fields'],
    'additionalProperties': False,
}


def get_full_user_data() -> dict:
    """
    Aggregate user data from all sources into a single flat-ish dict
    suitable for passing to the model.
    """
    return {
        "profile": get_user_profile(),         # spread profile keys at top level
        "experience": get_work_experience(),
        "skills": get_user_skills(),
    }


async def populate_field_values(fields: list[dict]) -> tuple[list[dict], float]:
    """
    Given the extracted form fields, ask the model to populate each field's
    `value` based on the user's profile. Returns the fields list with values filled.
    """
    user_prompt = json.dumps({
        'profile': get_full_user_data(), # grab all user data needed to populate forms
        'fields': fields,
    })

    print(f"=== populate_field_values: input size {len(user_prompt)} chars, {len(fields)} fields ===")
    start = time.time()

    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {'role': 'system', 'content': POPULATE_FIELDS_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        format=POPULATE_FIELDS_SCHEMA,
        options={'temperature': 0.0},
    )

    elapsed = time.time() - start
    raw_content = response['message']['content']
    print(f"=== populate_field_values returned in {elapsed:.1f}s ===")
    print(f"=== RAW OUTPUT: {raw_content[:2000]} ===")


    try:
        parsed = json.loads(raw_content)
        populated = parsed.get('fields', [])
    except json.JSONDecodeError as e:
        print(f"=== POPULATE FIELDS JSON DECODE ERROR: {e} ===")
        # Fall back to the original fields with no values populated
        return fields
    
    # Merge model values back into the original field objects.
    # This guarantees agent_id, name, options, etc. are always correct.
    by_id = {f["agent_id"]: f for f in fields}
    merged = []
    for p in populated:
        original = by_id.get(p.get("agent_id"))
        if not original:
            continue
        merged.append({**original, "value": p.get("value", "")})

    # Sanity check: ensure agent_ids match the input
    # input_ids = {f['agent_id'] for f in fields}
    # output_ids = {f.get('agent_id') for f in populated}
    # if input_ids != output_ids:
    #     missing = input_ids - output_ids
    #     extra = output_ids - input_ids
    #     print(f"=== WARNING: agent_id mismatch. missing={missing} extra={extra} ===")

    print(f"=== Populated {sum(1 for f in merged if f.get('value'))} of {len(merged)} fields ===")
    return merged, elapsed