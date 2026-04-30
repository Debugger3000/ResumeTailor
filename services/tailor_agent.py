import json
import os
from pathlib import Path
from docx import Document
from ollama import AsyncClient
from const.model_prompt import MODEL_PROMPT
import time

ollama_client = AsyncClient(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')


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


#     doc.save(output_path)
async def tailor_resume_in_place(
    input_path: Path,
    output_path: Path,
    paragraphs: list[dict],
    job_description: str,
    approved_skills: list[str] | None = None,
) -> tuple[int, str]:
    user_prompt = json.dumps({
        'job_description': job_description,
        'approved_skills': approved_skills or [],
        'resume_paragraphs': paragraphs,
    })

    print(f"=== Calling model. Input prompt size: {len(user_prompt)} chars ===")
    start = time.time()

    response = await ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=[
            {'role': 'system', 'content': MODEL_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        format='json',
    )

    elapsed = time.time() - start
    raw_content = response['message']['content']
    print(f"=== Model returned in {elapsed:.1f}s. Output size: {len(raw_content)} chars ===")
    print("=== RAW OUTPUT ===")
    print(raw_content[:3000])
    print("=== END RAW OUTPUT ===")

    try:
        parsed = json.loads(raw_content)
        changes = parsed.get('changes', [])
        summary = parsed.get('summary', '')
    except json.JSONDecodeError as e:
        print(f"=== JSON DECODE ERROR: {e} ===")
        changes = []
        summary = '(model returned invalid JSON)'

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
    print(f"tailor_resume_in_place applied {len(changes)} changes")
    print(f"model summary: {summary}")
    return len(changes), summary