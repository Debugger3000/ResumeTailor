from quart import Quart, render_template, request, jsonify, send_file


# Run Devleopment
# hypercorn app:app -c hypercorn.toml

app = Quart(__name__)

@app.route('/')
async def index():
    return await render_template('index.html')

# ===== TAILOR =====
@app.route('/api/tailor', methods=['POST'])
async def tailor():
    form = await request.form
    files = await request.files
    job_description = form.get('job_description')
    resume_file = files.get('resume')

    # TODO:
    # 1. Save resume_file to temp path
    # 2. Parse .docx with python-docx
    # 3. Call Ollama with tailor system prompt
    # 4. Modify .docx in-place preserving formatting
    # 5. Call Ollama for fit score
    # 6. Return paths + score

    return jsonify({
        'score': 0,
        'preview_text': 'Tailored resume preview will appear here.',
        'download_url': '/api/download/placeholder.docx',
        'resume_path': 'placeholder.docx',
    })

@app.route('/api/download/<filename>')
async def download(filename):
    # TODO: serve tailored .docx from output dir
    return 'Not implemented yet', 501

# ===== APPLY =====
@app.route('/api/apply/start', methods=['POST'])
async def apply_start():
    data = await request.get_json()
    url = data.get('url')
    resume_path = data.get('resume_path')
    job_description = data.get('job_description')

    # TODO:
    # 1. Launch Playwright browser (headed mode)
    # 2. Navigate to url
    # 3. Initialize agent session with job_description + user profile + resume_path
    # 4. Return session ID so frontend can poll/stream next steps

    return jsonify({'message': 'Agent session started (stub).', 'session_id': 'stub'})

@app.route('/api/apply/continue', methods=['POST'])
async def apply_continue():
    # TODO: advance agent to next step
    return jsonify({'status': 'ok'})

@app.route('/api/apply/stop', methods=['POST'])
async def apply_stop():
    # TODO: close Playwright browser, end session
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    # Run with: hypercorn app:app --reload --bind 127.0.0.1:8000
    pass