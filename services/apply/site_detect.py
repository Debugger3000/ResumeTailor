from enum import Enum


class Site(str, Enum):
    WORKDAY = "workday"
    GREENHOUSE = "greenhouse"
    ASHBY = "ashby"
    LEVER = "lever"
    GENERIC = "generic"


# Host fragment -> Site. Cheapest, most reliable signal when present.
_HOST_MARKERS = {
    "myworkdayjobs.com": Site.WORKDAY,
    "workday.com": Site.WORKDAY,
    "greenhouse.io": Site.GREENHOUSE,
    "ashbyhq.com": Site.ASHBY,
    "lever.co": Site.LEVER,
}


async def detect_site(page_or_frame) -> Site:
    # 1) URL host — works on both Page and Frame (both expose .url)
    url = getattr(page_or_frame, "url", "") or ""
    for fragment, site in _HOST_MARKERS.items():
        if fragment in url:
            return site

    # 2) Fallback: probe the DOM for platform-specific markers
    try:
        marker = await page_or_frame.evaluate("""
            () => {
              if (document.querySelector('[data-automation-id="applyFlowPage"], [data-fkit-id], [data-automation-id^="formField-"]')) return 'workday';
              if (document.querySelector('#grnhse_app')) return 'greenhouse';
              if (document.querySelector('[class*="ashby" i]')) return 'ashby';
              return 'generic';
            }
        """)
        return Site(marker)
    except Exception:
        return Site.GENERIC