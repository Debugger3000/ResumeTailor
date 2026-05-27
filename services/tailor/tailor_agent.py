import json
import os
from pathlib import Path
from docx import Document
from ollama import AsyncClient
from const.tailor_prompt import TAILOR_PROMPT, EXTRACT_INDEXES_PROMPT, TAILOR_EXTRACT_PARAGRAPHS_INDEXES_SCHEMA, TAILOR_REPLACE_INDEX_SCHEMA
import time
from services.ai_model_control.ollama_client import ollama_client

# ollama_client = AsyncClient(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
# OLLAMA_MODEL = os.getenv('OLLAMA_MODEL')

async def extract_applicable_paragraphs(
    paragraphs: list[dict],
) -> list[dict]:
    """
    Stage 1: Identify which paragraphs contain job titles or tech/skill mentions.
    Returns [{'index': int, 'original_text': str}, ...] for stage 2.
    """
    user_prompt = json.dumps({
        'resume_paragraphs': [
            {'index': p['index'], 'text': p['text']} for p in paragraphs
        ],
    })

    print(f"=== Stage 1: extracting applicable indexes. Input size: {len(user_prompt)} chars ===")
    start = time.time()

    response = await ollama_client.chat(
        model=ollama_client.model,
        messages=[
            {'role': 'system', 'content': EXTRACT_INDEXES_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        format=TAILOR_EXTRACT_PARAGRAPHS_INDEXES_SCHEMA,
        options={'temperature': 0.0},
    )

    elapsed = time.time() - start
    print(f"=== Stage 1 returned in {elapsed:.1f}s ===")
    print(f"=== RAW STAGE 1 OUTPUT: {response} ===")

    try:
        parsed = json.loads(response)
        items = parsed.get('applicable_paragraphs', [])
    except json.JSONDecodeError as e:
        print(f"=== STAGE 1 JSON DECODE ERROR: {e} ===")
        items = []

    # Build an index -> text map from the source of truth (not the model's echo)
    paragraph_lookup = {p['index']: p['text'] for p in paragraphs}

    # Keep only indexes that actually exist; rebuild original_text from source
    applicable = [
        {'index': item['index'], 'original_text': paragraph_lookup[item['index']]}
        for item in items
        if item.get('index') in paragraph_lookup
    ]

    print(f"=== Stage 1 selected {len(applicable)} of {len(paragraphs)} paragraphs ===")
    print(f"=== Selected indexes: {sorted(a['index'] for a in applicable)} ===")
    print(f"=== Stage 1 applicable_paragraphs returned: {applicable}===")

    return applicable



# async def extract_applicable_paragraphs(
#     paragraphs: list[dict],
# ) -> list[dict]:
#     """
#     Stage 1: Ask the model to identify which paragraphs contain job titles
#     or technology/skill mentions. Returns the filtered list of paragraphs
#     that stage 2 should consider editing.
#     """
#     user_prompt = json.dumps({
#         'resume_paragraphs': [
#             {'index': p['index'], 'text': p['text']} for p in paragraphs
#         ],
#     })

#     print(f"=== Stage 1: extracting applicable indexes. Input size: {len(user_prompt)} chars ===")
#     start = time.time()

#     response = await ollama_client.chat(
#         model=ollama_client.model,
#         messages=[
#             {'role': 'system', 'content': EXTRACT_INDEXES_PROMPT},
#             {'role': 'user', 'content': user_prompt},
#         ],
#         format=TAILOR_EXTRACT_PARAGRAPHS_INDEXES_SCHEMA,
#         options={'temperature': 0.0},
#     )

#     elapsed = time.time() - start
#     #raw_content = response['message']['content']
#     print(f"=== Stage 1 returned in {elapsed:.1f}s ===")
#     print(f"=== RAW STAGE 1 OUTPUT: {response} ===")

#     try:
#         parsed = json.loads(response)
#         indexes = parsed.get('indexes', [])
#     except json.JSONDecodeError as e:
#         print(f"=== STAGE 1 JSON DECODE ERROR: {e} ===")
#         indexes = []

#     # Sanity check: drop any indexes the model hallucinated
#     valid_indexes = {p['index'] for p in paragraphs}
#     indexes = [i for i in indexes if i in valid_indexes]

#     # Filter the original paragraph list down to only the flagged indexes
#     index_set = set(indexes)
#     filtered = [p for p in paragraphs if p['index'] in index_set]

#     print(f"=== Stage 1 selected {len(filtered)} of {len(paragraphs)} paragraphs ===")
#     print(f"=== Selected indexes: {sorted(index_set)} ===")

#     return filtered



def extract_paragraphs(file_path: Path) -> list[dict]:
    """Pull all non-empty paragraphs with their indices."""
    doc = Document(file_path)
    return [
        {'index': i, 'text': p.text, 'style': p.style.name}
        for i, p in enumerate(doc.paragraphs)
        if p.text.strip()
    ]





#     doc.save(output_path)
async def tailor_resume_in_place(
    input_path: Path,
    output_path: Path,
    applicable_paragraphs: list[dict],
    job_description: str,
    approved_skills: list[str] | None = None,
) -> tuple[int, str]:
    
    # Group input for model
    user_prompt = json.dumps({
        'job_description': job_description,
        'approved_skills': approved_skills or [],
        'applicable_paragraphs': applicable_paragraphs,
    })

    print(f"=== Calling model. Input prompt size: {len(user_prompt)} chars ===")
    print(f"Input prompt: {user_prompt}")
    print(f"Input prompt: {job_description}")
    start = time.time()

    # get running ollama client and give list of paragraphs to change...
    response = await ollama_client.chat(
        model=ollama_client.model,
        messages=[
            {'role': 'system', 'content': TAILOR_PROMPT},
            {'role': 'user', 'content': user_prompt},
        ],
        format=TAILOR_REPLACE_INDEX_SCHEMA,
        options={'temperature': 0.0},
    )

    elapsed = time.time() - start
    #raw_content = response['message']['content']
    print(f"=== Model returned in {elapsed:.1f}s. Output size: {len(response)} chars ===")
    print("=== RAW OUTPUT ===")
    print(response[:3000])
    print("=== END RAW OUTPUT ===")

    try:
        parsed = json.loads(response)
        changes = parsed.get('changes', [])
        summary = parsed.get('summary', '')
    except json.JSONDecodeError as e:
        print(f"=== JSON DECODE ERROR: {e} ===")
        changes = []
        summary = '(model returned invalid JSON)'

    allowed_indexes = {p['index'] for p in applicable_paragraphs}

    # Apply to a copy
    # if indexes in changes list match then change that line / paragraph with new one.
    doc = Document(input_path)
    applied = 0
    for change in changes:
        idx = change.get('index')
        new_text = change.get('new_text', '')
        if idx is None or idx not in allowed_indexes or idx >= len(doc.paragraphs):
            continue
        para = doc.paragraphs[idx]
        if para.runs:
            para.runs[0].text = new_text
            for run in para.runs[1:]:
                run.text = ''
        else:
            para.text = new_text
        applied += 1

    doc.save(output_path)
    print(f"tailor_resume_in_place applied {len(changes)} changes")
    print(f"model summary: {summary}")
    return len(changes), summary












# async def score_fit(resume_paragraphs: list[dict], job_description: str) -> int:
#     """Get a 0-100 fit score from the model."""
#     resume_text = '\n'.join(p['text'] for p in resume_paragraphs)
#     response = await ollama_client.chat(
#         model=ollama_client.model,
#         messages=[
#             {
#                 'role': 'system',
#                 'content': 'Score resume-job fit from 0 to 100. Respond ONLY with the integer.',
#             },
#             {
#                 'role': 'user',
#                 'content': f"JOB:\n{job_description}\n\nRESUME:\n{resume_text}",
#             },
#         ],
#     )
#     try:
#         return int(''.join(c for c in response['message']['content'] if c.isdigit())[:3])
#     except ValueError:
#         return 0
