"""
Mock browser automation for testing.
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime


class MockBrowserAutomation:
    """Mock browser automation for testing."""
    
    def __init__(self):
        self.browser = MagicMock()
        self.context = MagicMock()
        self.page = MagicMock()
        self.pages = []
        self.screenshots = []
        self.navigated_urls = []
        self.clicked_selectors = []
        self.typed_texts = []
        
    async def start(self, browser_type: str = "chromium", headless: bool = True):
        """Mock start browser."""
        self.browser_type = browser_type
        self.headless = headless
        return True
        
    async def stop(self):
        """Mock stop browser."""
        self.browser = None
        self.context = None
        self.page = None
        
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Mock navigate to URL."""
        self.navigated_urls.append(url)
        return {
            "url": url,
            "title": f"Mock Page for {url}",
            "load_time": 0.5
        }
        
    async def click(self, selector: str):
        """Mock click element."""
        self.clicked_selectors.append(selector)
        return {"success": True}
        
    async def type_text(self, selector: str, text: str):
        """Mock type text."""
        self.typed_texts.append((selector, text))
        return {"success": True}
        
    async def screenshot(self, path: Optional[Path] = None) -> bytes:
        """Mock screenshot."""
        screenshot_data = b"mock_screenshot_data"
        self.screenshots.append(screenshot_data)
        return screenshot_data
        
    async def wait_for_selector(self, selector: str, timeout: int = 5000):
        """Mock wait for selector."""
        return MagicMock()
        
    async def wait_for_load_state(self, state: str = "domcontentloaded"):
        """Mock wait for load state."""
        return None
        
    async def evaluate(self, script: str) -> Any:
        """Mock evaluate JavaScript."""
        if "document.title" in script:
            return "Mock Page Title"
        return None


class MockBrowserClient:
    """Mock browser client for testing."""
    
    def __init__(self):
        self.browser = MockBrowserAutomation()
        self.sessions = {}
        self.current_session_id = None
        self.navigation_history = []
        
    @property
    def clicked_selectors(self):
        """Delegate to browser's clicked_selectors."""
        return self.browser.clicked_selectors
        
    async def start_browser(self, browser_type: str = "chromium", headless: bool = True):
        """Mock start browser."""
        await self.browser.start(browser_type, headless)
        return {"success": True}
        
    async def stop_browser(self):
        """Mock stop browser."""
        await self.browser.stop()
        return {"success": True}
        
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Mock navigate."""
        result = await self.browser.navigate(url)
        self.navigation_history.append(url)
        return result
        
    async def create_session(self, name: str) -> Dict[str, Any]:
        """Mock create session."""
        session_id = f"session_{len(self.sessions)}"
        self.sessions[session_id] = {
            "name": name,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        self.current_session_id = session_id
        return {"session_id": session_id}
        
    async def click(self, selector: str, wait_for: Optional[str] = None) -> Dict[str, Any]:
        """Mock click."""
        result = await self.browser.click(selector)
        if wait_for:
            await self.browser.wait_for_selector(wait_for)
        return result
        
    async def type_text(self, selector: str, text: str) -> Dict[str, Any]:
        """Mock type text."""
        return await self.browser.type_text(selector, text)
        
    async def screenshot(self, path: Optional[str] = None) -> Dict[str, Any]:
        """Mock screenshot."""
        screenshot_data = await self.browser.screenshot()
        return {
            "success": True,
            "data": screenshot_data,
            "path": path
        }
