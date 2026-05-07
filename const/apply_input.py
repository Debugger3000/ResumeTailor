

input_field_schema = {
  "index": 3,
  "kind": "text",
  "input_type": "email",
  "question": "Email address",
  "selector": "#email",
  "options": None,
  "value": "",
  "required": True,
  "multi_select": False
}

inputs_field_schema = {
    "agent_id": "field-3",        # stable handle you set in DOM
    "kind": "text",                # text | email | select | radio | checkbox | file | textarea
    "question": "Email address",   # human-readable, from label/aria-label/placeholder
    "options": None,               # [{value, label}] for select/radio, else None
    "required": True,
    "value": "",                   # what the model decides to fill
}

# POPULATE_FIELDS_PROMPT = """You fill in job application form fields using the user's profile data.

# You will receive a JSON object with two keys:
# - "profile": the user's personal and professional information.
# - "fields": an array of form field objects to fill.

# Each field has this shape:
# {
#   "agent_id": "field-3",          // stable identifier — preserve exactly
#   "kind": "text",                 // one of: text | email | tel | textarea | number | url | select | radio | checkbox | file
#   "question": "Email address",    // human-readable question text
#   "options": null,                // [{value, label}] for select/radio, otherwise null
#   "required": true,
#   "value": ""                     // YOU populate this
# }

# Your job: return the same fields array, with each field's "value" populated from the profile when possible.

# RULES:
# - Match each field's "question" to the most relevant piece of profile data. Use semantic matching, not exact key matching (e.g., "What's your email?" matches profile.email).
# - Preserve every field property (agent_id, kind, question, options, required) exactly as given. Only set the "value".
# - For text / email / tel / textarea / number / url fields: "value" is a string.
# - For select and radio fields: "value" MUST be one of the option "value" strings shown in that field's "options" array. Do not invent option values. If none of the options reasonably match the profile data, leave "value" as "".
# - For checkbox fields: "value" is true or false.
# - For file fields: "value" is a string file path from the profile (e.g., resume_path, cover_letter_path).
# - If a field has no reasonable match in the profile, leave "value" as "" (or false for checkboxes, null for files).
# - Do NOT invent information that is not in the profile. For required fields with no matching profile data, still leave the value empty — do not fabricate answers.
# - Return the fields in the SAME ORDER as given. Do not add or remove fields.

# OUTPUT:
# Return a JSON object with a single key "fields" whose value is the populated array. No prose, no commentary."""





# POPULATE_FIELDS_PROMPT = """You fill in job application form fields using the user's profile data.

# You will receive a JSON object with two keys:
# - "profile": the user's personal and professional information.
# - "fields": an array of form field objects to fill.

# Each field has this shape:
# {
#   "agent_id": "field-3",          // stable identifier — preserve exactly
#   "kind": "text",                 // text | email | tel | textarea | number | url | select | radio | checkbox | file
#   "question": "Email address",    // the actual question being asked
#   "name": "q_abc123",              // form field name — preserve exactly, may be null
#   "options": null,                // [{value, label}] for select and radio fields, null otherwise
#   "required": true,
#   "value": ""                     // YOU populate this
# }

# Your job: return the same fields array, with each field's "value" populated from the profile when possible.

# RULES:
# - Match each field's "question" to the most relevant piece of profile data. Use semantic matching, not exact key matching (e.g., "What's your email?" matches profile.email).
# - Preserve every field property (agent_id, kind, question, options, required, name) exactly as given. Only set the "value".
# - For text / email / tel / textarea / number / url fields: "value" is a string from the profile.
# - For select fields: "value" MUST be one of the "value" strings in that field's "options" array. Match the user's profile data to the most appropriate option's "label", then return that option's "value". Do not invent option values.
# - For radio fields: same as select — "value" MUST be one of the "value" strings in "options". The radio field's "question" is the actual question being asked; "options" lists the choices. Pick the option whose "label" best matches the profile data, then return that option's "value".
# - For checkbox fields: "value" is true or false based on profile data.
# - For file fields: "value" is a string file path from the profile (e.g., resume_path, cover_letter_path).
# - If a field's "options" array is empty or null, treat the field as free-text input.
# - If a field has no reasonable match in the profile, leave "value" as "" (or false for checkboxes, null for files).
# - Return the fields in the SAME ORDER as given. Do not add or remove fields.

# OUTPUT:
# Return a JSON object with a single key "fields" whose value is the populated array. No prose, no commentary."""

# - Do NOT invent information that is not in the profile. For required fields with no matching profile data, still leave the value empty — do not fabricate answers.


POPULATE_FIELDS_PROMPT = """You fill in job application form fields using the user's profile data.

You receive: {"profile": {...}, "fields": [...]}

Each field:
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
- checkbox: true or false. No composing.
- file: skip
- text / email / tel / number / url: direct from profile only. No composing.
- textarea: direct if possible, otherwise compose an answer using real information from the profile.

Leave "value" as "" (or false / null as appropriate) when no profile data fits and the field can't be composed.

OUTPUT: {"fields": [...]} — JSON only, no prose."""