import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright

USER_DATA_DIR = Path.home() / ".resumetailor" / "chrome-profile"


@dataclass
class Session:
    id: str
    context: BrowserContext
    last_known_page: Page
    job_description: str | None = None
    resume_path: str | None = None
    history: list = field(default_factory=list)

    @property
    def page(self) -> Page:
        return self.last_known_page

    @page.setter
    def page(self, value: Page) -> None:
        self.last_known_page = value


class BrowserManager:
    def __init__(self):
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._sessions: dict[str, Session] = {}
        self._page_listener = None
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if self._context is None:
                USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                if self._playwright is None:
                    self._playwright = await async_playwright().start()
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(USER_DATA_DIR),
                    headless=False,
                    channel="chrome",
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"],
                )
                self._context.on("close", self._on_context_close)

    def _on_context_close(self, *_):
        self._context = None
        self._sessions.clear()

    async def create_session(self, url: str, **kwargs) -> Session:
        await self._ensure_browser()

        live = [p for p in self._context.pages if not p.is_closed()]
        if live:
            page = live[0]
            for extra in live[1:]:
                try:
                    await extra.close()
                except Exception:
                    pass
        else:
            page = await self._context.new_page()

        self._sessions.clear()

        session = Session(
            id=str(uuid.uuid4()),
            context=self._context,
            last_known_page=page,
            **kwargs,
        )

        if self._page_listener is not None:
            try:
                self._context.remove_listener("page", self._page_listener)
            except Exception:
                pass

        def on_new_page(new_page: Page) -> None:
            print(f"[session {session.id}] new tab: {new_page.url}")
            session.last_known_page = new_page
            session.history.append({"event": "new_tab", "url": new_page.url})

        self._page_listener = on_new_page
        self._context.on("page", on_new_page)

        await page.goto(url)
        self._sessions[session.id] = session
        return session

    @property
    def current(self) -> Session | None:
        if not self._sessions:
            return None
        return next(iter(self._sessions.values()))

    def get(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def close_session(self, session_id: str):
        # Closes every page in the context, which ENDS the persistent browser.
        # Only call this on shutdown — not when swapping URLs.
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        for p in list(session.context.pages):
            if not p.is_closed():
                try:
                    await p.close()
                except Exception:
                    pass

    async def shutdown(self):
        self._sessions.clear()
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


manager = BrowserManager()