

APPLY_PROMPT = """
You fill in job application form fields using the user's profile data.

Input:
- profile: {
    name: "...",
    experience: [...],
    skills: [...],
}
- fields: A variable array of form field objects extracted from the page.

Rules:
1. Perform a semantic cross-mapping between the user profile attributes and the input field metadata. Identify fields where the contextual meaning of the input descriptors aligns with elements of the user profile, and resolve the correct data payload into the "value" property.
2. Value Resolution Rules:
   - For open-ended structural elements (e.g., standard text entries), extract and normalize the corresponding literal string value from the profile dataset.
   - For closed-choice or constrained UI elements (e.g., toggles, selects, radios), you must exclusively evaluate the provided option arrays. Select and return the exact string token that matches the contextually correct option.
3. Fallback Integrity: If an input element has no direct or implicit semantic relationship to any attribute within the provided user profile, preserve structural alignment by assigning an empty string ("") or a literal boolean false for checkboxes. Do not omit the index.


CRITICAL REQUIREMENT:
- You MUST loop through and generate a corresponding answer object for EVERY SINGLE field provided in the input data.
- Do not add or invent fields not present in the input.

Output layout schema:
{"answers": [{"agent_id": "ID_FROM_INPUT", "value": "MAPPED_VALUE_OR_EMPTY_STRING"}]}
"""


# -----
# Schema for how fields get extracted from input tags on a html web page
# Change this if you want to change how fields are extracted
# -----


POPULATE_FIELDS_SCHEMA = {
    "type": "object",
    "properties": {
        "answers": {
            "type": "array",
            "description": "List of populated answers for the form fields.",
            "items": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "The unique field identifier (e.g. field-0)"},
                    "value": {"type": "string", "description": "The exact value to fill or choice string selection (e.g., 'Yes', 'No', 'Carter McCauley')"}
                },
                "required": ["agent_id", "value"]
            }
        }
    },
    "required": ["answers"]
}