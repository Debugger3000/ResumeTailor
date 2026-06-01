

# input_field_schema = {
#   "index": 3,
#   "kind": "text",
#   "input_type": "email",
#   "question": "Email address",
#   "selector": "#email",
#   "options": None,
#   "value": "",
#   "required": True,
#   "multi_select": False
# }

# inputs_field_schema = {
#     "agent_id": "field-3",        # stable handle you set in DOM
#     "kind": "text",                # text | email | select | radio | checkbox | file | textarea
#     "question": "Email address",   # human-readable, from label/aria-label/placeholder
#     "options": None,               # [{value, label}] for select/radio, else None
#     "required": True,
#     "value": "",                   # what the model decides to fill
# }

# -----
# Prompt for form completion
# Change this if you want to change how forms are completed
# -----
# APPLY_PROMPT = """You fill in job application form fields using the user's profile data.

# You receive: {"experience": {...},"profile": {...}, "fields": [...]}



# fields field looks like:
# {
#   "agent_id": "field-3",
#   "kind": "text|email|tel|textarea|number|url|select|radio|checkbox",
#   "question": "...",
#   "name": "...",
#   "options": [{value, label}] | null,
#   "required": true,
#   "value": ""
# }

# YOUR ONLY JOB: populate "value". Preserve every other field exactly as given. Keep the same order. Do not add or remove fields.

# HOW TO FILL "value":
# 1. Map common semantic synonyms from the profile or experience data to the form questions. For example:
#    - "Legal Name", "First Name + Last Name", or "Full Name" should map to the profile's "name".
#    - "LinkedIn Profile", "Github / Website" should map to the matching URLs in the profile links.
#    - "Phone", "Phone Number", "Mobile" should map to the profile's phone fields.
# 2. If the profile contains a direct answer for a specific custom question, use it word-for-word.
# 3. If not, compose an answer using only real information from the profile (work history, skills, education). Do not invent information.

# KIND RULES:
# - select / radio: "value" MUST be one of the option "value" strings. Pick the option whose "label" best matches the profile. No composing.
# - "combobox": a dropdown.
#   - If "options" is provided (not null), pick from it exactly like select/radio.
#   - If "options" is null, the dropdown loads its options lazily. Provide your best guess as a plain string
# - checkbox: true or false.
# - file: skip
# - text / email / tel / number / url: direct from profile only. No composing.
# - textarea: direct if possible, otherwise compose an answer using real information from the profile.

# Leave "value" as "" (or false / null as appropriate) when no profile data fits and the field can't be composed.

# OUTPUT: {"fields": [...]} — JSON only, no prose."""
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

# Replace your old multi-nested array Pydantic/Dict schema with this flat dictionary setup:
# POPULATE_FIELDS_SCHEMA = {
#     "type": "object",
#     "properties": {
#         "answers": {
#             "type": "object",
#             "description": "A flat dictionary mapping field agent_ids (keys) directly to their populated text values (values).",
#             "properties": {}, # Empty properties allows free-form additional properties string values
#         }
#     },
#     "required": ["answers"]
# }

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



# POPULATE_FIELDS_SCHEMA = {
#     'type': 'object',
#     'properties': {
#         'fields': {
#             'type': 'array',
#             'items': {
#                 'type': 'object',
#                 'properties': {
#                     'agent_id': {'type': 'string'},
#                     'kind': {'type': 'string'},
#                     'question': {'type': 'string'},
#                     'options': {
#                         # Either null or an array of {value, label}
#                         'type': ['array', 'null'],
#                         'items': {
#                             'type': 'object',
#                             'properties': {
#                                 'value': {'type': 'string'},
#                                 'label': {'type': 'string'},
#                             },
#                             'required': ['value', 'label'],
#                         },
#                     },
#                     'required': {'type': 'boolean'},
#                     'value': {
#                         # Strings, bools, or empty — keep permissive
#                         'type': ['string', 'boolean', 'null'],
#                     },
#                 },
#                 'required': ['agent_id', 'kind', 'question', 'required', 'value'],
#                 'additionalProperties': True,
#             },
#         },
#     },
#     'required': ['fields'],
#     'additionalProperties': False,
# }