from quart import Blueprint, request, jsonify
from services.browser import manager
import uuid
from services.apply import extract_form_fields, fill_fields, get_focused_page
from services.apply_agent import populate_field_values
from services.browser_helpers import resolve_active_page, wait_for_page_ready, find_form_target, click_continue
from services.apply_fields_filter import filter_fields

apply_bp = Blueprint('apply', __name__)



# Browser Action Lifecycle

# Give url, agent first opens the page, and then asks for clarification to begin applying
# Once permission given, agent grabs form fields and fills in data
# Agent notifies user

# Start the browser session
# -----
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
@apply_bp.route('/begin', methods=['POST'])
async def apply_begin():
    print("begin hit")

    session = manager.current
    if not session:
        return jsonify({'error': 'no active session — call /start first'}), 400


    page = await resolve_active_page(session)
    session.last_known_page = page
    print(f"active page: {page.url}")

    await wait_for_page_ready(page)

    target = await find_form_target(page)
    print(f"form target: {target.url if hasattr(target, 'url') else 'main frame'}")


    #html = await get_page_html(session)
    fields = await extract_form_fields(target)

    filtered_fields = filter_fields(fields)
    print(f"fields returned:\n {fields}")
    # give model fields data, so it can populate it with user data
    populated_fields = await populate_field_values(filtered_fields)
    # pass populated_fields and sessions page to be filled with data
    summary = await fill_fields(page, populated_fields)


    # print("html input fields grabbed from extract_form_fields")
    # print(fields)

    return jsonify({
        'fields': populated_fields,
        'summary': summary,
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



@apply_bp.route('/advance', methods=['POST'])
async def apply_advance():
    """Click Continue/Submit on the current page and report what happened."""
    session = manager.current
    if not session:
        return jsonify({'error': 'no active session'}), 400
    
    page = await resolve_active_page(session)
    advanced = await click_continue(page)
    
    if advanced:
        # Re-resolve in case the click opened a new tab
        page = await resolve_active_page(session)
        await wait_for_page_ready(page)
        session.last_known_page = page
    
    return jsonify({
        'advanced': advanced,
        'url': page.url,
    })