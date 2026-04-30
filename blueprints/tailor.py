import os
import tempfile
from pathlib import Path
from quart import Blueprint, request, jsonify, send_file
import uuid
from const.approved_skills import approved_skills

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

    

    paragraphs = extract_paragraphs(original_path)
    changes_count, model_summary = await tailor_resume_in_place(
        original_path, output_path, paragraphs, job_description, approved_skills,
    )
    score = await score_fit(paragraphs, job_description)

    SESSIONS[session_id] = {
        'original_filename': resume_file.filename,
        'output_path': str(output_path),
        'model_summary': model_summary,
        'changes_count': changes_count,
    }

    print("Returning response from tailor route.")
    return jsonify({
        'session_id': session_id,
        'score': score,
        'changes_count': changes_count,
        'model_summary': model_summary,
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