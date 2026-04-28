import json
import os
from pathlib import Path
from docx import Document
from ollama import AsyncClient

ollama_client = AsyncClient(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')

# System prompt for Tailor
# ---

SYSTEM_PROMPT = """
    You are a resume tailoring assistant. Given a job 
description and a resume, rewrite the resume to better match the job while 
keeping all facts truthful. You have two main goals. The first goal is to match skill sections on the resume with skills listed with the job description.
Your second goal is to tailor job experience and/or project sections bullet points on the resume with language that may more closely resemble what the job description is either using or asking for.
Although you want to keep these bullet points to be as close as possible to what the job description is asking for, you should not change any facts that are already true, and should keep the purpose of each line
the same as it was, but just embellish the language used, to more properly match terms used within the job description. Also remember to keep the length of the bullet points the same. We DO NOT want to increase lines or page length by 
making each line more descriptive or longer. We also DO NOT want to decrease lines or page length. Keep them the same size as they are. For example; if one bullet point is one line, keep it to one line. If a bullet point is two lines keep it to two lines.
The tools you are too use to achieve this is 

Guidelines of action: Leave formatting as it was, do not add anything for formatting, do not add anything for styling, do not add anything for comments, do not add anything for explanations.
Only touch sections like skills, Job experience, and Projects. Everything else should be left as it is.

You have tools to read 
and modify a .docx resume. Your workflow:

1. Call read_resume to see all paragraphs and their indices.
2. Identify paragraphs that are skills lists or job/project bullet points.
3. For each one that should be tailored to the job description, call 
   replace_paragraph_text with the same approximate length and same factual content,
   but with language adjusted to match the job description's terminology.
4. Do NOT change paragraph counts or line lengths significantly.
5. Do NOT invent new facts or experiences.

When you're done editing, respond with a brief summary of what you changed.

    
    
    You receive a job 
description and resume paragraphs (with indices). Rewrite paragraphs that should 
better match the job description.

RULES:
- Only rewrite skill lists and bullet points in experience/projects.
- Keep approximately the same length.
- Never invent facts not in the original.
- Do not modify headers, names, contact info, or dates.
- If a paragraph doesn't need changes, omit it.

Respond ONLY with JSON:
{"changes": [{"index": 5, "new_text": "rewritten text"}]}"""




def extract_paragraphs(file_path: Path) -> list[dict]:
    """Pull all non-empty paragraphs with their indices."""
    doc = Document(file_path)
    return [
        {'index': i, 'text': p.text, 'style': p.style.name}
        for i, p in enumerate(doc.paragraphs)
        if p.text.strip()
    ]


async def score_fit(resume_paragraphs: list[dict], job_description: str) -> int:
    """Get a 0-100 fit score from the model."""
    resume_text = '\n'.join(p['text'] for p in resume_paragraphs)
    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {
                'role': 'system',
                'content': 'Score resume-job fit from 0 to 100. Respond ONLY with the integer.',
            },
            {
                'role': 'user',
                'content': f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}",
            },
        ],
    )
    try:
        return int(''.join(c for c in response['message']['content'] if c.isdigit())[:3])
    except ValueError:
        return 0


def apply_changes(file_path: Path, changes: list[dict], output_path: Path) -> None:
    """Apply approved changes to the .docx, save to output_path."""
    doc = Document(file_path)

    for change in changes:
        idx = change['index']
        new_text = change['after']
        if idx >= len(doc.paragraphs):
            continue

        para = doc.paragraphs[idx]
        if para.runs:
            para.runs[0].text = new_text
            for run in para.runs[1:]:
                run.text = ''
        else:
            para.text = new_text

    doc.save(output_path)


async def tailor_resume_in_place(
    input_path: Path,
    output_path: Path,
    paragraphs: list[dict],
    job_description: str,
) -> int:
    """Have the model rewrite paragraphs and apply changes to a copy of the .docx."""
    
    user_prompt = json.dumps({
        'job_description': job_description,
        'resume_paragraphs': paragraphs,
    })

    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {'role': 'system', 'content': SYSTEM_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        format='json',
    )

    try:
        changes = json.loads(response['message']['content']).get('changes', [])
    except json.JSONDecodeError:
        changes = []

    # Apply to a copy
    doc = Document(input_path)
    for change in changes:
        idx = change.get('index')
        new_text = change.get('new_text', '')
        if idx is None or idx >= len(doc.paragraphs):
            continue
        para = doc.paragraphs[idx]
        if para.runs:
            para.runs[0].text = new_text
            for run in para.runs[1:]:
                run.text = ''
        else:
            para.text = new_text

    doc.save(output_path)
    print("tailor resume in place returning here...")
    return len(changes)