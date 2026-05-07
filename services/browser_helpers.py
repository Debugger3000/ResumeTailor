from playwright.async_api import Page, Frame


async def resolve_active_page(session) -> Page:
    """
    Find the page the user (or browser) is actually on right now.
    Source of truth — call at the start of any handler before extracting/filling.
    """
    pages = [p for p in session.context.pages if not p.is_closed()]
    if not pages:
        raise RuntimeError("no open pages in session")
    if len(pages) == 1:
        return pages[0]
    

    # Fallback: prefer last_known if it's still open
    last = session.last_known_page
    if last in pages and not last.is_closed():
        return last
    
    # Try focused/visible first
    for p in pages:
        try:
            is_focused = await p.evaluate(
                "() => document.hasFocus() && document.visibilityState === 'visible'"
            )
            if is_focused:
                return p
        except Exception:
            continue
    
    
    
    # Last resort: most recently opened
    return pages[-1]


async def wait_for_page_ready(page: Page, timeout: int = 15000) -> None:
    """
    Wait until a page is past loading screens and has form content (or has clearly settled).
    Call after navigation, before extraction.
    """
    try:
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception as e:
        print(f"[wait_for_page_ready] domcontentloaded timeout: {e}")
    
    # Wait for at least one interactable element. Don't fail if none appears —
    # confirmation pages have no form controls and that's a valid terminal state.
    try:
        await page.wait_for_selector(
            'input:not([type=hidden]):not([type=submit]):not([type=button]),'
            ' select, textarea, button[type="submit"]',
            timeout=timeout,
        )
    except Exception:
        print(f"[wait_for_page_ready] no form controls appeared on {page.url}")
    
    # Settle network — short timeout, ok if it doesn't fully idle
    try:
        await page.wait_for_load_state("networkidle", timeout=5000)
    except Exception:
        pass


async def find_form_target(page: Page):
    """
    Return the Page or Frame that actually contains the form.
    Many ATS/Apply forms are in iframes. This picks the best target.
    """
    # Apply-frame heuristic for known hosts
    apply_hosts = ("smartapply.indeed.com", "indeedapply", "greenhouse.io", "lever.co", "workday")
    for frame in page.frames:
        if frame == page.main_frame:
            continue
        if any(host in (frame.url or "") for host in apply_hosts):
            return frame
    
    # Fallback: pick whichever frame has the most non-trivial form controls
    candidates = [page.main_frame] + [f for f in page.frames if f != page.main_frame]
    best = page.main_frame
    best_count = 0
    
    for frame in candidates:
        try:
            count = await frame.evaluate("""
                () => document.querySelectorAll(
                    'input:not([type=hidden]):not([type=submit]):not([type=button])'
                    + ':not([name="q"]):not([name="l"]),'
                    + ' select, textarea'
                ).length
            """)
        except Exception:
            count = 0
        if count > best_count:
            best_count = count
            best = frame
    
    return best


async def click_continue(page: Page) -> bool:
    """
    Click the Continue/Submit/Next button and wait for the result.
    Returns True if a button was clicked, False if no advance button found
    (i.e., we're at a terminal page).
    """
    button_texts = [
        "Continue",
        "Next",
        "Review your application",
        "Submit application",
        "Submit",
        "Apply",
    ]
    
    for text in button_texts:
        btn = page.get_by_role("button", name=text, exact=False)
        try:
            count = await btn.count()
        except Exception:
            count = 0
        
        if count == 0:
            continue
        
        try:
            async with page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
                await btn.first.click()
            return True
        except Exception:
            # SPA forms don't navigate — click and let the next step's wait sort it out
            try:
                await btn.first.click()
                await page.wait_for_load_state("networkidle", timeout=5000)
                return True
            except Exception:
                continue
    
    return False