"""
VIBE MCP - Browser Automation Client

Browser automation client using Playwright for intelligent web interactions.
Implements Phase 5.3 of the VIBE MCP roadmap.

Features:
- Browser automation with Playwright
- Page interaction and navigation
- Form filling and submission
- Screenshot capture
- JavaScript execution
- Multi-browser support
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from playwright.async_api import Browser, BrowserContext, Page, async_playwright
from playwright.async_api import Error as PlaywrightError

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class BrowserType(Enum):
    """Supported browser types."""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class ViewportSize(Enum):
    """Common viewport sizes."""
    DESKTOP = (1920, 1080)
    TABLET = (768, 1024)
    MOBILE = (375, 667)


@dataclass
class BrowserAction:
    """Browser action representation."""
    type: str
    selector: str | None = None
    value: str | None = None
    wait_for: str | None = None
    screenshot: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserSession:
    """Browser session information."""
    session_id: str
    browser_type: BrowserType
    url: str
    title: str
    created_at: datetime
    last_activity: datetime
    pages: list[str] = field(default_factory=list)


class BrowserClient:
    """
    Browser automation client using Playwright.

    Provides intelligent browser automation with support for
    multiple browsers, page interactions, and visual testing.
    """

    def __init__(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
        viewport: ViewportSize = ViewportSize.DESKTOP,
        timeout: int = 30000,
        user_agent: str | None = None,
    ):
        """
        Initialize browser client.

        Args:
            browser_type: Browser to use
            headless: Run in headless mode
            viewport: Viewport size
            timeout: Default timeout in milliseconds
            user_agent: Custom user agent
        """
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout
        self.user_agent = user_agent

        # Playwright instances
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

        # Session tracking
        self._sessions: dict[str, BrowserSession] = {}
        self._current_session_id: str | None = None

        secure_logger.info(f"Browser client initialized with {browser_type.value}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()

    async def start(self) -> None:
        """Start the browser."""
        try:
            self._playwright = await async_playwright().start()

            # Launch browser
            launch_options = {
                "headless": self.headless,
            }

            if self.browser_type == BrowserType.CHROMIUM:
                self._browser = await self._playwright.chromium.launch(**launch_options)
            elif self.browser_type == BrowserType.FIREFOX:
                self._browser = await self._playwright.firefox.launch(**launch_options)
            elif self.browser_type == BrowserType.WEBKIT:
                self._browser = await self._playwright.webkit.launch(**launch_options)

            # Create context
            context_options = {
                "viewport": {"width": self.viewport.value[0], "height": self.viewport.value[1]},
                "timeout": self.timeout,
            }

            if self.user_agent:
                context_options["user_agent"] = self.user_agent

            self._context = await self._browser.new_context(**context_options)

            # Create page
            self._page = await self._context.new_page()

            # Create session
            session_id = f"session_{datetime.now().timestamp()}"
            self._current_session_id = session_id

            self._sessions[session_id] = BrowserSession(
                session_id=session_id,
                browser_type=self.browser_type,
                url="about:blank",
                title="New Tab",
                created_at=datetime.now(),
                last_activity=datetime.now(),
            )

            secure_logger.info(f"Browser started with session {session_id}")

        except Exception as e:
            secure_logger.error(f"Failed to start browser: {e}")
            raise

    async def stop(self) -> None:
        """Stop the browser."""
        try:
            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            secure_logger.info("Browser stopped")

        except Exception as e:
            secure_logger.error(f"Error stopping browser: {e}")

    # ========================================================================
    # NAVIGATION METHODS
    # ========================================================================

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete

        Returns:
            Navigation result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            response = await self._page.goto(url, wait_until=wait_until)

            # Update session
            if self._current_session_id:
                session = self._sessions[self._current_session_id]
                session.url = url
                session.title = await self._page.title()
                session.last_activity = datetime.now()

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Navigation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
            }

    async def reload(self, wait_until: str = "domcontentloaded") -> dict[str, Any]:
        """
        Reload the current page.

        Args:
            wait_until: When to consider reload complete

        Returns:
            Reload result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            response = await self._page.reload(wait_until=wait_until)

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "status": response.status if response else None,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Reload failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def go_back(self) -> dict[str, Any]:
        """Go back in browser history."""
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.go_back()

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Go back failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def go_forward(self) -> dict[str, Any]:
        """Go forward in browser history."""
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.go_forward()

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Go forward failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ========================================================================
    # ELEMENT INTERACTION
    # ========================================================================

    async def click(self, selector: str, wait_for: str | None = None) -> dict[str, Any]:
        """
        Click an element.

        Args:
            selector: CSS selector for element
            wait_for: Selector to wait for after click

        Returns:
            Click result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.click(selector)

            if wait_for:
                await self._page.wait_for_selector(wait_for)

            # Update session activity
            if self._current_session_id:
                self._sessions[self._current_session_id].last_activity = datetime.now()

            return {
                "success": True,
                "selector": selector,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Click failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def type_text(self, selector: str, text: str, clear: bool = True) -> dict[str, Any]:
        """
        Type text into an element.

        Args:
            selector: CSS selector for element
            text: Text to type
            clear: Clear field before typing

        Returns:
            Type result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            if clear:
                await self._page.fill(selector, "")

            await self._page.type(selector, text)

            # Update session activity
            if self._current_session_id:
                self._sessions[self._current_session_id].last_activity = datetime.now()

            return {
                "success": True,
                "selector": selector,
                "text_length": len(text),
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Type failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def fill_form(self, form_data: dict[str, str]) -> dict[str, Any]:
        """
        Fill a form with data.

        Args:
            form_data: Dictionary of selector -> value pairs

        Returns:
            Fill result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        results = {}

        for selector, value in form_data.items():
            try:
                await self._page.fill(selector, value)
                results[selector] = {"success": True, "value": value}
            except PlaywrightError as e:
                results[selector] = {"success": False, "error": str(e)}

        # Update session activity
        if self._current_session_id:
            self._sessions[self._current_session_id].last_activity = datetime.now()

        return {
            "success": all(r.get("success", False) for r in results.values()),
            "fields": results,
            "timestamp": datetime.now().isoformat(),
        }

    async def select_option(self, selector: str, value: str) -> dict[str, Any]:
        """
        Select an option from a dropdown.

        Args:
            selector: CSS selector for select element
            value: Option value to select

        Returns:
            Select result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.select_option(selector, value)

            # Update session activity
            if self._current_session_id:
                self._sessions[self._current_session_id].last_activity = datetime.now()

            return {
                "success": True,
                "selector": selector,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Select option failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def upload_file(self, selector: str, file_path: str) -> dict[str, Any]:
        """
        Upload a file through an input element.

        Args:
            selector: CSS selector for file input
            file_path: Path to file to upload

        Returns:
            Upload result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            file_path = Path(file_path).resolve()
            await self._page.set_input_files(selector, str(file_path))

            # Update session activity
            if self._current_session_id:
                self._sessions[self._current_session_id].last_activity = datetime.now()

            return {
                "success": True,
                "selector": selector,
                "file_path": str(file_path),
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"File upload failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    # ========================================================================
    # INFORMATION EXTRACTION
    # ========================================================================

    async def get_text(self, selector: str) -> dict[str, Any]:
        """
        Get text content of an element.

        Args:
            selector: CSS selector for element

        Returns:
            Text content
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            element = await self._page.query_selector(selector)
            if not element:
                return {
                    "success": False,
                    "error": "Element not found",
                    "selector": selector,
                }

            text = await element.text_content()

            return {
                "success": True,
                "selector": selector,
                "text": text,
                "length": len(text) if text else 0,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Get text failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def get_attribute(self, selector: str, attribute: str) -> dict[str, Any]:
        """
        Get attribute value of an element.

        Args:
            selector: CSS selector for element
            attribute: Attribute name

        Returns:
            Attribute value
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            element = await self._page.query_selector(selector)
            if not element:
                return {
                    "success": False,
                    "error": "Element not found",
                    "selector": selector,
                }

            value = await element.get_attribute(attribute)

            return {
                "success": True,
                "selector": selector,
                "attribute": attribute,
                "value": value,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Get attribute failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def evaluate(self, javascript: str) -> dict[str, Any]:
        """
        Execute JavaScript in the page.

        Args:
            javascript: JavaScript code to execute

        Returns:
            Execution result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            result = await self._page.evaluate(javascript)

            # Update session activity
            if self._current_session_id:
                self._sessions[self._current_session_id].last_activity = datetime.now()

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"JavaScript evaluation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "javascript": javascript,
            }

    async def get_page_content(self, content_type: str = "html") -> dict[str, Any]:
        """
        Get page content.

        Args:
            content_type: Type of content (html, text, markdown)

        Returns:
            Page content
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            if content_type == "html":
                content = await self._page.content()
            elif content_type == "text":
                content = await self._page.evaluate("() => document.body.innerText")
            elif content_type == "markdown":
                # Convert HTML to markdown (simplified)
                html = await self._page.content()
                import markdownify
                content = markdownify.markdownify(html, heading_style="ATX")
            else:
                raise ValueError(f"Unsupported content type: {content_type}")

            return {
                "success": True,
                "type": content_type,
                "content": content,
                "length": len(content),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            secure_logger.error(f"Get page content failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": content_type,
            }

    # ========================================================================
    # SCREENSHOTS AND VISUAL TESTING
    # ========================================================================

    async def screenshot(
        self,
        full_page: bool = False,
        selector: str | None = None,
        file_path: str | None = None,
    ) -> dict[str, Any]:
        """
        Take a screenshot.

        Args:
            full_page: Capture full page
            selector: Capture specific element
            file_path: Save screenshot to file

        Returns:
            Screenshot result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            screenshot_options = {
                "type": "png",
                "full_page": full_page,
            }

            if selector:
                element = await self._page.query_selector(selector)
                if not element:
                    return {
                        "success": False,
                        "error": "Element not found",
                        "selector": selector,
                    }
                screenshot_options["clip"] = await element.bounding_box()

            if file_path:
                file_path = Path(file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                await self._page.screenshot(path=str(file_path), **screenshot_options)

                return {
                    "success": True,
                    "file_path": str(file_path),
                    "size": file_path.stat().st_size,
                    "timestamp": datetime.now().isoformat(),
                }
            else:
                # Return base64 encoded screenshot
                screenshot = await self._page.screenshot(**screenshot_options)
                import base64

                return {
                    "success": True,
                    "data": base64.b64encode(screenshot).decode(),
                    "size": len(screenshot),
                    "timestamp": datetime.now().isoformat(),
                }

        except PlaywrightError as e:
            secure_logger.error(f"Screenshot failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ========================================================================
    # WAITING AND CONDITIONS
    # ========================================================================

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int | None = None,
        state: str = "visible",
    ) -> dict[str, Any]:
        """
        Wait for an element to appear.

        Args:
            selector: CSS selector to wait for
            timeout: Custom timeout
            state: Element state (visible, hidden, attached, detached)

        Returns:
            Wait result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.wait_for_selector(
                selector,
                timeout=timeout or self.timeout,
                state=state,
            )

            return {
                "success": True,
                "selector": selector,
                "state": state,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Wait for selector failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "selector": selector,
            }

    async def wait_for_navigation(self, timeout: int | None = None) -> dict[str, Any]:
        """
        Wait for navigation to complete.

        Args:
            timeout: Custom timeout

        Returns:
            Wait result
        """
        if not self._page:
            raise RuntimeError("Browser not started")

        try:
            await self._page.wait_for_load_state("networkidle", timeout=timeout or self.timeout)

            return {
                "success": True,
                "url": self._page.url,
                "title": await self._page.title(),
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"Wait for navigation failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def get_sessions(self) -> list[BrowserSession]:
        """Get all browser sessions."""
        return list(self._sessions.values())

    async def get_current_session(self) -> BrowserSession | None:
        """Get current browser session."""
        if self._current_session_id:
            return self._sessions.get(self._current_session_id)
        return None

    async def new_tab(self) -> dict[str, Any]:
        """Open a new browser tab."""
        if not self._context:
            raise RuntimeError("Browser context not available")

        try:
            await self._context.new_page()

            # Create new session
            session_id = f"session_{datetime.now().timestamp()}"

            session = BrowserSession(
                session_id=session_id,
                browser_type=self.browser_type,
                url="about:blank",
                title="New Tab",
                created_at=datetime.now(),
                last_activity=datetime.now(),
            )

            self._sessions[session_id] = session

            return {
                "success": True,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }

        except PlaywrightError as e:
            secure_logger.error(f"New tab failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def get_browser_info(self) -> dict[str, Any]:
        """Get browser information."""
        return {
            "browser_type": self.browser_type.value,
            "headless": self.headless,
            "viewport": {
                "width": self.viewport.value[0],
                "height": self.viewport.value[1],
            },
            "timeout": self.timeout,
            "user_agent": self.user_agent,
            "sessions": len(self._sessions),
            "current_session": self._current_session_id,
        }

    async def test_connection(self) -> bool:
        """Test browser functionality."""
        try:
            await self.goto("https://example.com")
            title = await self._page.title()
            return "Example Domain" in title
        except Exception as e:
            secure_logger.error(f"Browser test failed: {e}")
            return False


# Factory function
async def create_browser_client(
    browser_type: BrowserType = BrowserType.CHROMIUM,
    headless: bool = True,
    viewport: ViewportSize = ViewportSize.DESKTOP,
) -> BrowserClient:
    """
    Create and initialize browser client.

    Args:
        browser_type: Browser to use
        headless: Run in headless mode
        viewport: Viewport size

    Returns:
        Initialized browser client
    """
    client = BrowserClient(
        browser_type=browser_type,
        headless=headless,
        viewport=viewport,
    )

    await client.start()

    # Test connection
    if await client.test_connection():
        secure_logger.info("Browser client created and tested successfully")
        return client
    else:
        raise RuntimeError("Browser client failed basic test")


# CLI interface for testing
async def main():
    """Test the browser client."""
    import argparse

    parser = argparse.ArgumentParser(description="Browser Client Test")
    parser.add_argument("--browser", default="chromium", help="Browser type (chromium, firefox, webkit)")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--url", default="https://example.com", help="URL to navigate to")
    parser.add_argument("--screenshot", help="Take screenshot and save to file")
    parser.add_argument("--selector", help="CSS selector to interact with")
    parser.add_argument("--text", help="Text to type into selector")

    args = parser.parse_args()

    # Parse browser type
    try:
        browser_type = BrowserType(args.browser)
    except ValueError:
        print(f"Invalid browser type: {args.browser}")
        return

    # Create client
    try:
        client = await create_browser_client(
            browser_type=browser_type,
            headless=args.headless,
        )
    except RuntimeError as e:
        print(f"Failed to create browser client: {e}")
        return

    async with client:
        # Navigate to URL
        print(f"\nNavigating to: {args.url}")
        result = await client.goto(args.url)
        print(f"  Title: {result.get('title', 'N/A')}")
        print(f"  Status: {result.get('status', 'N/A')}")

        # Get browser info
        info = await client.get_browser_info()
        print("\nBrowser Info:")
        print(f"  Type: {info['browser_type']}")
        print(f"  Headless: {info['headless']}")
        print(f"  Viewport: {info['viewport']['width']}x{info['viewport']['height']}")

        # Take screenshot if requested
        if args.screenshot:
            print("\nTaking screenshot...")
            result = await client.screenshot(file_path=args.screenshot)
            if result["success"]:
                print(f"  Saved to: {result['file_path']}")
                print(f"  Size: {result['size']} bytes")

        # Interact with element if specified
        if args.selector:
            print(f"\nInteracting with: {args.selector}")

            # Get text first
            text_result = await client.get_text(args.selector)
            if text_result["success"]:
                print(f"  Current text: {text_result['text'][:100]}...")

            # Type new text if provided
            if args.text:
                type_result = await client.type_text(args.selector, args.text)
                if type_result["success"]:
                    print(f"  Typed {len(args.text)} characters")

        # Get page content
        content = await client.get_page_content("text")
        if content["success"]:
            print(f"\nPage content length: {content['length']} characters")
            print(f"  Preview: {content['content'][:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
