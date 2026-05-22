

# -----
# Prompt for paragraph / docx line extraction
# Change this if you want to change what lines are to be grabbed and changed by the second stage tailoring model call
# -----
EXTRACT_INDEXES_PROMPT = """You scan resume paragraphs and identify which ones contain job titles or technology/skill terms. Return JSON only.

INPUT (in user message):
- resume_paragraphs: list of {index, text} objects

YOUR TASK:
For each paragraph, decide if it contains either:
- A job title (e.g., "Backend Developer", "Senior Software Engineer", "Full Stack Developer")
- One or more technology or skill names (e.g., "Python", "React", "PostgreSQL", "AWS", "Docker")

Include the paragraph's index in the output if EITHER is true.

WHAT COUNTS AS A JOB TITLE:
- Role names like "Developer", "Engineer", "Architect", "Analyst", "Designer", "Consultant", "Specialist", "Lead", "Intern"
- Often paired with seniority words: "Senior", "Junior"
- Usually a short line, not a full sentence

WHAT COUNTS AS A TECHNOLOGY/SKILL:
- Programming languages: Python, JavaScript, TypeScript, Java, Go, Rust, C++, etc.
- Frameworks/libraries: React, Vue, Django, FastAPI, Express, Spring, etc.
- Databases: PostgreSQL, MySQL, MongoDB, Redis, etc.
- Tools/platforms: Docker, Kubernetes, AWS, Azure, Git, Jenkins, etc.
- Concepts that map to skills: REST, GraphQL, CI/CD, Agile, etc.

WHAT DOES NOT COUNT:
- Names of people, Dates, Company names
- Email addresses, phone numbers, URLs
- Section headers like "Skills", "Experience", "Education" (the header itself is not a skill)
- Generic words like "team", "project", "code" without a specific technology

OUTPUT (JSON only, no prose):
{
"applicable_paragraphs": [
  {"index": int, "original_text": "..."}, 
]}

Return only the indexes of paragraphs that contain a job title or skill mention. Sort indexes ascending. If a paragraph contains neither, omit it.

EXAMPLE INPUT:
resume_paragraphs: [
  {"index": 2, "text": "Backend Developer with 5 years building services in JavaScript and MySQL."},
  {"index": 4, "text": "Languages: JavaScript, MySQL, Docker, Git"},
  {"index": 7, "text": "Full Stack Developer"},
]
"""

# EXAMPLE OUTPUT:
# {"applicable_paragraphs": [
#   {"index": 2, "original_text": "Full Stack Developer(3+ years xp) - Typescript, C#, Python and Linux environments."}, 
#   {"index": 6, "original_text": "Full Stack Developer - Internship"}, 
# ]}



# -----
# Prompt for tailoring
# Change this if you want to change how your resume is tailored
# -----
TAILOR_PROMPT = """You rewrite specific parts of a resume to match a job description (JD). You return JSON only.

Input Example:
approved_skills: ["TypeScript", "PostgreSQL", "AWS"]
job_description
applicable_paragraphs: [
  {"index": 3, "original_text": "Backend Developer with 5 years building services in JavaScript and MySQL."},
  {"index": 7, "original_text": "Skills: JavaScript, MySQL, Docker"}
]

You are too only edit indexes contained within applicable_paragraphs.

Rules:
You are too:
Add or swap skills found in applicable_paragraphs with skills from list of approved_skills that match ones in the JD.
Remove skills found in applicable_paragraphs when they are not found in the JD.
Swap job titles with one found in the JD.
Leave all formatting alone.

Output Summary Rule:
- Briefly state the sections that were changed (e.g., "Summary", "Experience", "Skills"...) and add no extra information

Output Example (JSON only)
{
  "changes": [
    {"index": 3, "new_text": "Backend Engineer with 5 years building services in TypeScript and PostgreSQL."},
    {"index": 7, "new_text": "Skills: TypeScript, PostgreSQL, Docker"}
  ],
  "summary": "Swapped JavaScript for TypeScript and MySQL for PostgreSQL in Summary and Skills per JD. Updated Summary title to 'Backend Engineer'."
}

FORBIDDEN (never do these):
- Never add new bullets, paragraphs, lines, or sections
- Writing comments, notes, or explanations inside any rewritten text
"""

# SCHEMAS for tailor model calls
# Extract applicable paragraphs
# Replace paragraphs 

TAILOR_REPLACE_INDEX_SCHEMA = {
        'type': 'object',
        'properties': {
            'changes': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'index': {'type': 'integer'},
                        'new_text': {'type': 'string'},
                    },
                    'required': ['index', 'new_text'],
                    'additionalProperties': False,
                },
            },
            'summary': {'type': 'string'},
        },
        'required': ['changes', 'summary'],
        'additionalProperties': False,
    }


# TAILOR_EXTRACT_PARAGRAPHS_INDEXES_SCHEMA = {
#     'type': 'object',
#     'properties': {
#         'indexes': {
#             'type': 'array',
#             'items': {'type': 'integer'},
#         },
#     },
#     'required': ['indexes'],
#     'additionalProperties': False,
# }

TAILOR_EXTRACT_PARAGRAPHS_INDEXES_SCHEMA = {
    'type': 'object',
    'properties': {
        'applicable_paragraphs': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'index': {'type': 'integer'},
                    'original_text': {'type': 'string'},
                },
                'required': ['index', 'original_text'],
                'additionalProperties': False,
            },
        },
    },
    'required': ['applicable_paragraphs'],
    'additionalProperties': False,
}