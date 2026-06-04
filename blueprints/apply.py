from quart import Blueprint, request, jsonify
from services.browser.browser import manager
import uuid
from services.apply.apply_helpers import extract_form_fields, fill_fields, get_focused_page, get_form_frame
from services.apply.apply_agent import populate_field_values
from services.browser.browser_helpers import resolve_active_page, wait_for_page_ready, find_form_target
from services.apply.apply_fields_filter import filter_fields
from services.apply.site_detect import detect_site

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
@apply_bp.route('/fillform', methods=['POST'])
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

    # detect specific job sites
    site = await detect_site(target)
    print(f"detected site: {site.value}")

    fields = await extract_form_fields(target, site=site)



    #html = await get_page_html(session)
    # fields = await extract_form_fields(target)

    filtered_fields = filter_fields(fields)
    print(f"fields returned:\n {fields}")

    # Model populates values of fields
    # -----------------------
    # give model fields data, so it can populate it with user data
    populated_fields, elapsed = await populate_field_values(filtered_fields)


    # pass populated_fields and sessions page to be filled with data
    summary = await fill_fields(target, populated_fields)


    # print("html input fields grabbed from extract_form_fields")
    # print(fields)

    return jsonify({
        'fields': populated_fields,
        'summary': summary,
        'time_elapsed': elapsed,
    })


@apply_bp.route('/scan', methods=['POST'])
async def apply_scan():
    """Re-read the CURRENT page's fields on demand. Reads the live DOM each
    call, so call it AFTER you've revealed/added the fields you want."""
    session = manager.current
    if not session:
        return jsonify({'error': 'no active session — call /start first'}), 400

    page = await resolve_active_page(session)
    session.last_known_page = page

    await wait_for_page_ready(page)
    target = await find_form_target(page)      # re-find every scan, no caching
    fields = await extract_form_fields(target)
    filtered = filter_fields(fields)

    return jsonify({'url': page.url, 'count': len(filtered), 'fields': filtered})