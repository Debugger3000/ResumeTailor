
import asyncio
import uuid
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright


@dataclass
class Session:
    id: str
    context: BrowserContext
    page: Page
    job_description: str | None = None
    resume_path: str | None = None
    # whatever else the agent needs to track
    history: list = field(default_factory=list)


class BrowserManager:
    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if self._browser is None:
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=False)

    async def create_session(self, url: str, **kwargs) -> Session:
        await self._ensure_browser()
        context = await self._browser.new_context()
        page = await context.new_page()
        await page.goto(url)

        session = Session(
            id=str(uuid.uuid4()),
            context=context,
            page=page,
            **kwargs,
        )
        self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str):
        session = self._sessions.pop(session_id, None)
        if session:
            await session.context.close()

    async def shutdown(self):
        for sid in list(self._sessions):
            await self.close_session(sid)
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


# Singleton instance, imported wherever you need it
manager = BrowserManager()