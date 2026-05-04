

EXTRACT_INDEXES_PROMPT = """You scan resume paragraphs and identify which ones contain job titles or technology/skill terms. Return JSON only.

INPUT (in user message):
- resume_paragraphs: list of {index, text} objects

YOUR TASK:
For each paragraph, decide if it contains either:
- A job title (e.g., "Backend Developer", "Senior Software Engineer", "Full Stack Developer - Internship")
- One or more technology or skill names (e.g., "Python", "React", "PostgreSQL", "AWS", "Docker")

Include the paragraph's index in the output if EITHER is true.

WHAT COUNTS AS A JOB TITLE:
- Role names like "Developer", "Engineer", "Architect", "Manager", "Analyst", "Designer", "Consultant", "Specialist", "Lead", "Director", "Intern"
- Often paired with seniority words: "Senior", "Junior", "Principal", "Staff", "Associate"
- Usually a short line, not a full sentence

WHAT COUNTS AS A TECHNOLOGY/SKILL:
- Programming languages: Python, JavaScript, TypeScript, Java, Go, Rust, C++, etc.
- Frameworks/libraries: React, Vue, Django, FastAPI, Express, Spring, etc.
- Databases: PostgreSQL, MySQL, MongoDB, Redis, etc.
- Tools/platforms: Docker, Kubernetes, AWS, Azure, Git, Jenkins, etc.
- Concepts that map to skills: REST, GraphQL, CI/CD, Agile, etc.

WHAT DOES NOT COUNT:
- Names of people
- Email addresses, phone numbers, URLs
- Company names
- Dates
- Section headers like "Skills", "Experience", "Education" (the header itself is not a skill)
- Generic words like "team", "project", "code" without a specific technology

OUTPUT (JSON only, no prose):
{
  "indexes": [<int>, <int>, ...]
}

Return only the indexes of paragraphs that contain a job title or skill mention. Sort indexes ascending. If a paragraph contains neither, omit it.

EXAMPLE INPUT:
resume_paragraphs: [
  {"index": 0, "text": "Jane Smith"},
  {"index": 1, "text": "jane@email.com | 555-1234"},
  {"index": 2, "text": "Backend Developer with 5 years building services in JavaScript and MySQL."},
  {"index": 3, "text": "Skills"},
  {"index": 4, "text": "Languages: JavaScript, MySQL, Docker, Git"},
  {"index": 5, "text": "Work Experience"},
  {"index": 6, "text": "Acme Corp | 2020 - 2023"},
  {"index": 7, "text": "Senior Backend Engineer"},
  {"index": 8, "text": "Built REST APIs serving 1M requests per day"}
]

EXAMPLE OUTPUT:
{"indexes": [2, 4, 7, 8]}
"""











MODEL_PROMPT = """You rewrite specific parts of a resume to match a job description (JD). You adding / changing skills and swapping job titles to the resume from the JD. You return JSON only.

INPUT (in user message):
- job_description: text of the JD
- approved_skills: list of skills allowed to be added
- paragraphs: list of {index, text} objects
- applicable_paragraphs: {"indexes": [2, 4, 7, 8]}

You are too only edit indexes contained within applicable_paragraphs
You are to swap or add skills from list of approved_skills that match ones in the JD
You are too swap job titles with one found in the JD

Input Example:
approved_skills: ["TypeScript", "PostgreSQL", "AWS"]
job_description
paragraphs: [
  {"index": 3, "text": "Backend Developer with 5 years building services in JavaScript and MySQL."},
  {"index": 7, "text": "Skills: JavaScript, MySQL, Docker"}
]
applicable_paragraphs: {"indexes": [2, 6, 9, 11, 14, 16, 19, 29, 30, 31]}

Output Summary Rule:
- Briefly state the sections that were changed (e.g., "Summary", "Experience", "Skills"...) and add no extra information

Output Example (JSON only)
{
  "changes": [
    {"index": 3, "new_text": "Senior Backend Engineer with 5 years building services in TypeScript and PostgreSQL."},
    {"index": 7, "new_text": "Skills: TypeScript, PostgreSQL, Docker"}
  ],
  "summary": "Swapped JavaScript for TypeScript and MySQL for PostgreSQL in Summary and Skills per JD. Updated Summary title to 'Senior Backend Engineer'. Did not add AWS since the JD did not mention it."
}

FORBIDDEN (never do these):
- Never add new bullets, paragraphs, lines, or sections
- Writing comments, notes, or explanations inside any rewritten text
- Change formatting
"""

# System prompt for Tailor
# ---
# SYSTEM_PROMPT = """You rewrite specific parts of a resume to match a job description (JD). You return JSON only.

# # Hard rules (these matter most)

# RULE 1 — SKILLS MUST BE SPECIFIC NAMED TECHNOLOGIES ONLY.
# Each entry in a skills list must be a proper noun: a specific language, framework, library, tool, platform, protocol, or service. No descriptive phrases, no categories, no parenthetical clarifications, no JD prose copied verbatim.
#   WRONG: "various data visualization tools"  → too vague, not a named technology
#   WRONG: "modern frameworks (SvelteKit)"     → keep only "SvelteKit"
#   WRONG: "state management solutions"        → too vague
#   WRONG: "RESTful services"                  → category, use "REST" or specific tool
#   RIGHT: "SvelteKit", "Svelte 5", "Tailwind", "D3.js", "Chart.js", "Redux"

# When the JD describes a category (e.g. "data visualization tools", "state management solutions"), you must NOT copy that phrase. Either:
#   (a) replace it with a specific named technology the candidate already lists elsewhere on the resume, OR
#   (b) leave the original skill in place.
# Never invent a specific tool the candidate doesn't have.


# RULE 2 — EVERY EXPERIENCE JOB TITLE BECOMES THE JD'S JOB TITLE.
# Find the JD's job title (e.g. "UI Developer"). Replace every job title in the candidate's Experience section with that exact title. No exceptions, no synonyms — use the JD's title verbatim.
#   JD title: "UI Developer"
#   Original: "Full Stack Developer at Acme Corp"
#   Output:   "UI Developer at Acme Corp"

# RULE 3 — REWRITE THE SUMMARY.
# The Summary is the one-line (or two-line) blurb near the top that states a job title + years of experience + a few skills. It is NOT a section header. It usually sits in the first 3-6 non-empty paragraphs.
# You MUST rewrite it. Replace the candidate's stated title with the JD's title. Replace the listed skills with the top 4 most-emphasized skills from the JD. Keep the same line count and roughly the same character count.
#   Original: "Full Stack Developer with 5 years of experience in React, Node.js, and Python."
#   JD wants: UI Developer, SvelteKit, Tailwind, accessibility, responsive design
#   Output:   "UI Developer with 5 years of experience in SvelteKit, Tailwind, and responsive design."

# RULE 4 — BULLETS KEEP THEIR LENGTH.
# Every rewritten bullet must match the original character count within ±10%. A one-line bullet stays one line. Swap tech terms to match the JD (JS→TypeScript, React→SvelteKit if the candidate's work supports it), but never expand the sentence.

# RULE 5 — DO NOT INVENT FACTS.
# Only resurface skills/tech the candidate already demonstrates. Don't add new bullets, new skill lines, new paragraphs, or new blank lines.

# # What you may edit

# - The Summary blurb (Rule 3).
# - Skill list lines (Rule 1).
# - Job titles in Experience (Rule 2).
# - Bullet points in Experience and Projects (Rule 4).

# # What you must NOT touch

# Section headers, the candidate's name, contact info, dates, company names, locations, education, certifications, formatting. Never change paragraph counts.

# # Output format

# Respond with JSON only. No prose, no markdown fences. Omit any paragraph you didn't change.

# {"changes": [{"index": <int>, "new_text": "<rewritten text>"}]}

# Before you finalize your JSON, verify:
# - Did you include a change for the Summary blurb? (Rule 3 — required if a summary exists.)
# - Did you include changes for every Experience job title? (Rule 2 — required for each one.)
# - Do any skill lines contain "Skilled in", "Proficient in", "Experience with", or "Familiar with"? If yes, remove those words.
# """
