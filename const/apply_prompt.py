

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
APPLY_PROMPT = """You fill in job application form fields using the user's profile data.

You receive: {"experience": {...},"profile": {...}, "fields": [...]}



fields field looks like:
{
  "agent_id": "field-3",
  "kind": "text|email|tel|textarea|number|url|select|radio|checkbox",
  "question": "...",
  "name": "...",
  "options": [{value, label}] | null,
  "required": true,
  "value": ""
}

YOUR ONLY JOB: populate "value". Preserve every other field exactly as given. Keep the same order. Do not add or remove fields.

HOW TO FILL "value":
1. If the profile contains a direct answer, use it word-for-word.
2. If not, compose an answer using only real information from the profile (work history, skills, education). Do not invent companies, titles, dates, or accomplishments.

KIND RULES:
- select / radio: "value" MUST be one of the option "value" strings. Pick the option whose "label" best matches the profile. No composing.
- "combobox": a dropdown.
  - If "options" is provided (not null), pick from it exactly like select/radio.
  - If "options" is null, the dropdown loads its options lazily. Provide your best guess as a plain string
- checkbox: true or false.
- file: skip
- text / email / tel / number / url: direct from profile only. No composing.
- textarea: direct if possible, otherwise compose an answer using real information from the profile.

Leave "value" as "" (or false / null as appropriate) when no profile data fits and the field can't be composed.

OUTPUT: {"fields": [...]} — JSON only, no prose."""


# -----
# Schema for how fields get extracted from input tags on a html web page
# Change this if you want to change how fields are extracted
# -----
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