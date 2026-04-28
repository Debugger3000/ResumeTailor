from quart import Blueprint, request, jsonify

apply_bp = Blueprint('apply', __name__)


@apply_bp.route('/start', methods=['POST'])
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


@apply_bp.route('/continue', methods=['POST'])
async def apply_continue():
    # TODO: advance agent to next step
    return jsonify({'status': 'ok'})


@apply_bp.route('/stop', methods=['POST'])
async def apply_stop():
    # TODO: close Playwright browser, end session
    return jsonify({'status': 'stopped'})