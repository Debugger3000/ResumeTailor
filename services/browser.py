
# import asyncio
# import uuid
# from dataclasses import dataclass, field
# from pathlib import Path
# from playwright.async_api import async_playwright, BrowserContext, Page, Playwright


# USER_DATA_DIR = Path.home() / ".resumetailor" / "chrome-profile"


# @dataclass
# class Session:
#     id: str
#     page: Page
#     job_description: str | None = None
#     resume_path: str | None = None
#     history: list = field(default_factory=list)


# class BrowserManager:
#     def __init__(self):
#         self._playwright: Playwright | None = None
#         self._context: BrowserContext | None = None
#         self._sessions: dict[str, Session] = {}
#         self._lock = asyncio.Lock()

#     async def _ensure_browser(self):
#         async with self._lock:
#             if self._context is None:
#                 USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
#                 self._playwright = await async_playwright().start()
#                 self._context = await self._playwright.chromium.launch_persistent_context(
#                     user_data_dir=str(USER_DATA_DIR),
#                     headless=False,
#                     channel="chrome",  # <-- uses installed Chrome, not bundled Chromium
#                     viewport={"width": 1280, "height": 800},
#                     args=["--disable-blink-features=AutomationControlled"],
#                 )

#     async def create_session(self, url: str, **kwargs) -> Session:
#         # Close any existing session first — single-session model
#         for sid in list(self._sessions):
#             await self.close_session(sid)
        
#         await self._ensure_browser()
#         page = await self._context.new_page()
#         await page.goto(url)

#         session = Session(
#             id=str(uuid.uuid4()),
#             page=page,
#             **kwargs,
#         )
#         self._sessions[session.id] = session
#         return session
    

#     @property
#     def current(self) -> Session | None:
#         """Return the currently active session, if any."""
#         if not self._sessions:
#             return None
#         # There's only ever one, but pick deterministically
#         return next(iter(self._sessions.values()))

#     def get(self, session_id: str) -> Session | None:
#         return self._sessions.get(session_id)

#     async def close_session(self, session_id: str):
#         session = self._sessions.pop(session_id, None)
#         if session:
#             await session.page.close()  # close the tab, not the whole context

#     async def shutdown(self):
#         for sid in list(self._sessions):
#             await self.close_session(sid)
#         if self._context:
#             await self._context.close()
#         if self._playwright:
#             await self._playwright.stop()


# manager = BrowserManager()



import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from playwright.async_api import async_playwright, BrowserContext, Page, Playwright


USER_DATA_DIR = Path.home() / ".resumetailor" / "chrome-profile"


@dataclass
class Session:
    id: str
    context: BrowserContext              # the durable thing
    last_known_page: Page                 # hint, kept fresh by listener
    job_description: str | None = None
    resume_path: str | None = None
    history: list = field(default_factory=list)
    
    @property
    def page(self) -> Page:
        """Backwards-compat: existing code that reads session.page still works."""
        return self.last_known_page
    
    @page.setter
    def page(self, value: Page) -> None:
        self.last_known_page = value


class BrowserManager:
    def __init__(self):
        self._playwright: Playwright | None = None
        self._context: BrowserContext | None = None
        self._sessions: dict[str, Session] = {}
        self._lock = asyncio.Lock()

    async def _ensure_browser(self):
        async with self._lock:
            if self._context is None:
                USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
                self._playwright = await async_playwright().start()
                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(USER_DATA_DIR),
                    headless=False,
                    channel="chrome",
                    viewport={"width": 1280, "height": 800},
                    args=["--disable-blink-features=AutomationControlled"],
                )

                

    async def create_session(self, url: str, **kwargs) -> Session:
        # Single-session model: close any existing session first
        for sid in list(self._sessions):
            await self.close_session(sid)
        
        await self._ensure_browser()
        page = await self._context.new_page()

        # Close it so it doesn't pollute resolve_active_page later.
        # for p in list(self._context.pages):
        #     if p.url in ("about:blank", "", "chrome://newtab/"):
        #         try:
        #             await p.close()
        #         except Exception:
        #             pass        
        
        session = Session(
            id=str(uuid.uuid4()),
            context=self._context,
            last_known_page=page,
            **kwargs,
        )
        
        # Track new tabs as they open. Keeps last_known_page fresh
        # so resolve_active_page has a good fallback.
        def on_new_page(new_page: Page) -> None:
            print(f"[session {session.id}] new tab opened: {new_page.url}")
            session.last_known_page = new_page
            session.history.append({"event": "new_tab", "url": new_page.url})
        
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
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        # Close all pages belonging to this session's context.
        # In single-session mode this is essentially every open tab.
        for p in list(session.context.pages):
            if not p.is_closed():
                try:
                    await p.close()
                except Exception:
                    pass

    async def shutdown(self):
        for sid in list(self._sessions):
            await self.close_session(sid)
        if self._context:
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()


manager = BrowserManager()