import os
import tempfile
from pathlib import Path
from quart import Blueprint, request, jsonify, send_file
import uuid

from ollama import AsyncClient
# from services.docx_tools import TOOL_SCHEMAS, TOOL_REGISTRY
from services.tailor_agent import (
    extract_paragraphs,
    tailor_resume_in_place,  # new — does everything internally
    score_fit,
)

# blueprint - route name is 'tailor'
tailor_bp = Blueprint('tailor', __name__)

UPLOAD_DIR = Path(tempfile.gettempdir()) / 'resume_uploads'
OUTPUT_DIR = Path(tempfile.gettempdir()) / 'resume_outputs'
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

SESSIONS: dict[str, dict] = {}

# ---
# Model prompt for Tailor mode

TAILOR_SYSTEM_PROMPT = """You are a resume tailoring assistant. Given a job 
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


"""

# max iterations of tool calls

MAX_TOOL_ITERATIONS = 10

ollama_client = AsyncClient(host=os.getenv('OLLAMA_HOST', 'http://localhost:11434'))
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.1:8b')

# Main Endpoint for Tailor process 
# ---
@tailor_bp.route('/tailor', methods=['POST'])
async def tailor():
    print("Tailor route hit.")
    form = await request.form
    files = await request.files
    job_description = form.get('job_description')
    resume_file = files.get('resume')

    if not job_description or not resume_file:
        return jsonify({'error': 'Missing job_description or resume'}), 400

    session_id = uuid.uuid4().hex
    original_path = UPLOAD_DIR / f"{session_id}_{resume_file.filename}"
    output_path = OUTPUT_DIR / f"{session_id}_tailored_{resume_file.filename}"
    await resume_file.save(original_path)

    # Tailor the resume — model makes changes, writes to output_path
    paragraphs = extract_paragraphs(original_path)
    await tailor_resume_in_place(original_path, output_path, paragraphs, job_description)
    score = await score_fit(paragraphs, job_description)

    SESSIONS[session_id] = {
        'original_filename': resume_file.filename,
        'output_path': str(output_path),
    }
    print("Returning response from tailor route.")
    return jsonify({
        'session_id': session_id,
        'score': score,
        'preview_url': f'/api/tailor/preview/{session_id}',
        'download_url': f'/api/download/{session_id}',
    })


@tailor_bp.route('/tailor/preview/<session_id>')
async def preview(session_id):
    """Serve the tailored .docx bytes for in-browser rendering."""
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    output_path = Path(session['output_path'])
    if not output_path.exists():
        return jsonify({'error': 'Tailored file not found'}), 404

    return await send_file(
        output_path,
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    )


@tailor_bp.route('/download/<session_id>')
async def download(session_id):
    session = SESSIONS.get(session_id)
    if not session:
        return jsonify({'error': 'Session not found'}), 404

    output_path = Path(session['output_path'])
    if not output_path.exists():
        return jsonify({'error': 'File not generated'}), 404

    return await send_file(
        output_path,
        as_attachment=True,
        attachment_filename=f"tailored_{session['original_filename']}",
    )

# Test route
# ---
@tailor_bp.route('/test-ollama', methods=['GET'])
async def test_ollama():
    """Quick sanity check that the app can reach Ollama and get a response."""
    try:
        response = await ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant. Reply briefly.'},
                {'role': 'user', 'content': 'Tell me a quick joke!'},
            ],
        )
        return jsonify({
            'ok': True,
            'model': OLLAMA_MODEL,
            'reply': response['message']['content'],
        })
    except Exception as e:
        return jsonify({
            'ok': False,
            'error': str(e),
            'error_type': type(e).__name__,
        }), 500