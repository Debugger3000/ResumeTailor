TOOL_DEFS = [
    {
        "name": "fill_field",
        "description": "Fill a single form field with a value from the user's profile.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "The agent_id of the field to fill, from get_fields()."},
                "value": {"description": "The value to fill. String for text/email/select/radio, bool for checkbox, file path for file."},
            },
            "required": ["agent_id", "value"],
        },
    },
    {
        "name": "get_fields",
        "description": "Re-extract the form fields on the current page. Call this after the page changes (e.g., after clicking Continue, or if a field reveals new fields when filled).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "click",
        "description": "Click an element (typically a Continue or Submit button) by its agent_id.",
        "input_schema": {
            "type": "object",
            "properties": {"agent_id": {"type": "string"}},
            "required": ["agent_id"],
        },
    },
    {
        "name": "skip_field",
        "description": "Record that you cannot fill a field because the user's profile lacks the information. Use sparingly — try to infer reasonable values first.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["agent_id", "reason"],
        },
    },
]