from quart import Blueprint, request, jsonify
from services.browser import manager
import uuid
from services.apply import get_page_html

apply_bp = Blueprint('apply', __name__)



# Browser Action Lifecycle

# Give url, agent first opens the page, and then asks for clarification to begin applying
# Once permission given, agent grabs form fields and fills in data
# Agent notifies user


@apply_bp.route('/start', methods=['POST'])
async def apply_start():
    data = await request.get_json()
    url = data.get('url')
    resume_path = data.get('resume_path')
    job_description = data.get('job_description')

    # make sure a url value is given
    if not url:
        return jsonify({'error': 'url is required'}), 400
    
    session = await manager.create_session(
        url=url,
        job_description=job_description,
        resume_path=resume_path,
    )
    

    # Open url with playwright driven browser
    # try:
    #     await open_url(session_id, url)
    # except:
    #     print("Opening URL for apply process failed.")

    return jsonify({
        'message': 'Agent session started.',
        'session_id': session.id,
    })

# Begin applying with agent
@apply_bp.route('/apply/begin', methods=['POST'])
async def apply_begin():
    print("begin hit")
    data = await request.get_json()
    session = manager.get(data['session_id'])
    if not session:
        return jsonify({'error': 'unknown session'}), 404

    html = get_page_html(session)

    return jsonify({
        'html': html,    
    })


@apply_bp.route('/continue', methods=['POST'])
async def apply_continue():
    data = await request.get_json()
    session = manager.get(data['session_id'])
    if not session:
        return jsonify({'error': 'unknown session'}), 404

    # session.page is a live Page — agent can interact with it
    # e.g. await session.page.click(...), await session.page.fill(...)
    # await agent.step(session)

    return jsonify({'status': 'ok'})


@apply_bp.route('/stop', methods=['POST'])
async def apply_stop():
    data = await request.get_json()
    await manager.close_session(data['session_id'])
    return jsonify({'status': 'stopped'})