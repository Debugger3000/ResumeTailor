

# app/services/page_reader.py

# return page html from playwright session
async def get_page_html(session):
    """Return the full rendered HTML of the current page."""
    return await session.page.content()