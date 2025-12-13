"""
Browser Automation for VIBE MCP

Comprehensive browser automation using Playwright:
- Page navigation and interaction
- Screenshot capture and comparison
- Form filling and submission
- Web scraping with JavaScript execution
- Testing and validation
- Performance monitoring

Integrates with GitLab (MR testing) and Firecrawl (enhanced scraping).
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from playwright.async_api import (
    Browser,
    BrowserContext,
    Error,
    Locator,
    Page,
    Request,
    Response,
    async_playwright,
)

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
    WIDE = (2560, 1440)


@dataclass
class ScreenshotOptions:
    """Screenshot capture options."""
    full_page: bool = True
    quality: int = 80  # For JPEG
    type: str = "png"  # png, jpeg
    omit_background: bool = False
    clip: dict[str, int] | None = None
    scale: str = "css"  # css, device


@dataclass
class FormField:
    """Form field definition."""
    selector: str
    value: str
    field_type: str = "input"  # input, select, textarea, checkbox, radio
    wait_for_selector: bool = True


@dataclass
class PageAction:
    """Page action definition."""
    action: str  # click, fill, type, press, screenshot, evaluate
    selector: str | None = None
    value: str | None = None
    options: dict[str, Any] = field(default_factory=dict)
    wait_for: str | None = None


@dataclass
class BrowserSession:
    """Browser session information."""
    id: str
    browser_type: BrowserType
    started_at: datetime
    pages: list[str] = field(default_factory=list)
    cookies: list[dict[str, Any]] = field(default_factory=list)
    storage: dict[str, Any] = field(default_factory=dict)


class BrowserAutomation:
    """
    Advanced browser automation with Playwright.

    Features:
    - Multi-browser support (Chromium, Firefox, WebKit)
    - Screenshot capture and comparison
    - Form automation
    - Network interception
    - Performance monitoring
    - Headless and headed modes
    """

    def __init__(
        self,
        browser_type: BrowserType = BrowserType.CHROMIUM,
        headless: bool = True,
        viewport: tuple[int, int] = ViewportSize.DESKTOP.value,
        timeout: int = 30000,
        slow_mo: int = 0,
    ):
        """
        Initialize browser automation.

        Args:
            browser_type: Browser to use
            headless: Run in headless mode
            viewport: Default viewport size
            timeout: Default timeout in milliseconds
            slow_mo: Slow down operations by milliseconds
        """
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout
        self.slow_mo = slow_mo

        # Playwright instances
        self.playwright = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

        # Session tracking
        self.sessions: dict[str, BrowserSession] = {}
        self.current_session_id: str | None = None

        # Network monitoring
        self.network_requests: list[dict[str, Any]] = []
        self.network_responses: list[dict[str, Any]] = []

        # Performance metrics
        self.performance_metrics: dict[str, Any] = {}

        secure_logger.info(f"Browser automation initialized: {browser_type.value}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def start(self) -> str:
        """
        Start the browser and create a new session.

        Returns:
            Session ID
        """
        if not self.playwright:
            self.playwright = await async_playwright().start()

        # Launch browser
        launch_options = {
            "headless": self.headless,
            "slow_mo": self.slow_mo,
        }

        # Add browser-specific options
        if self.browser_type == BrowserType.CHROMIUM:
            launch_options.update({
                "args": [
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor",
                ]
            })

        self.browser = await getattr(
            self.playwright,
            self.browser_type.value
        ).launch(**launch_options)

        # Create context
        context_options = {
            "viewport": {"width": self.viewport[0], "height": self.viewport[1]},
            "ignore_https_errors": True,
            "java_script_enabled": True,
        }

        self.context = await self.browser.new_context(**context_options)

        # Set default timeout
        self.context.set_default_timeout(self.timeout)

        # Create page
        self.page = await self.context.new_page()

        # Setup monitoring
        await self._setup_monitoring()

        # Create session
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_id = session_id
        self.sessions[session_id] = BrowserSession(
            id=session_id,
            browser_type=self.browser_type,
            started_at=datetime.now(),
        )

        secure_logger.info(f"Browser started with session: {session_id}")
        return session_id

    async def close(self):
        """Close the browser and cleanup."""
        if self.page:
            await self.page.close()
            self.page = None

        if self.context:
            await self.context.close()
            self.context = None

        if self.browser:
            await self.browser.close()
            self.browser = None

        if self.playwright:
            await self.playwright.stop()
            self.playwright = None

        secure_logger.info("Browser closed")

    async def _setup_monitoring(self):
        """Setup network and performance monitoring."""
        if not self.page:
            return

        # Monitor requests
        async def on_request(request: Request):
            self.network_requests.append({
                "url": request.url,
                "method": request.method,
                "headers": dict(request.headers),
                "timestamp": datetime.now(),
            })

        # Monitor responses
        async def on_response(response: Response):
            self.network_responses.append({
                "url": response.url,
                "status": response.status,
                "headers": dict(response.headers),
                "timestamp": datetime.now(),
            })

        self.page.on("request", on_request)
        self.page.on("response", on_response)

    # ========================================================================
    # NAVIGATION OPERATIONS
    # ========================================================================

    async def navigate(
        self,
        url: str,
        wait_until: str = "domcontentloaded",
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
            wait_until: When to consider navigation complete
            timeout: Custom timeout

        Returns:
            Navigation metrics
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        start_time = datetime.now()

        try:
            response = await self.page.goto(
                url,
                wait_until=wait_until,
                timeout=timeout or self.timeout,
            )

            # Update session
            if self.current_session_id:
                session = self.sessions[self.current_session_id]
                if url not in session.pages:
                    session.pages.append(url)

            # Calculate metrics
            load_time = (datetime.now() - start_time).total_seconds()

            metrics = {
                "url": url,
                "status": response.status if response else None,
                "load_time": load_time,
                "timestamp": datetime.now(),
            }

            # Get page title
            try:
                metrics["title"] = await self.page.title()
            except:
                metrics["title"] = ""

            secure_logger.info(f"Navigated to {url} in {load_time:.2f}s")
            return metrics

        except Error as e:
            secure_logger.error(f"Navigation failed: {e}")
            raise

    async def wait_for_load_state(self, state: str = "domcontentloaded"):
        """
        Wait for specific load state.

        Args:
            state: Load state to wait for
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        await self.page.wait_for_load_state(state)

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int | None = None,
        state: str = "attached",
    ) -> Locator:
        """
        Wait for element to appear.

        Args:
            selector: CSS selector
            timeout: Custom timeout
            state: Element state

        Returns:
            Element locator
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        return await self.page.wait_for_selector(
            selector,
            timeout=timeout or self.timeout,
            state=state,
        )

    # ========================================================================
    # SCREENSHOT OPERATIONS
    # ========================================================================

    async def screenshot(
        self,
        options: ScreenshotOptions | None = None,
        file_path: Path | None = None,
    ) -> str | bytes:
        """
        Capture screenshot.

        Args:
            options: Screenshot options
            file_path: Save to file if provided

        Returns:
            Base64 string or bytes
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        opts = options or ScreenshotOptions()

        screenshot_opts = {
            "full_page": opts.full_page,
            "type": opts.type,
            "omit_background": opts.omit_background,
        }

        if opts.type == "jpeg":
            screenshot_opts["quality"] = opts.quality

        if opts.clip:
            screenshot_opts["clip"] = opts.clip

        if file_path:
            await self.page.screenshot(path=str(file_path), **screenshot_opts)
            return str(file_path)
        else:
            return await self.page.screenshot(**screenshot_opts)

    async def screenshot_element(
        self,
        selector: str,
        options: ScreenshotOptions | None = None,
        file_path: Path | None = None,
    ) -> str | bytes:
        """
        Capture screenshot of specific element.

        Args:
            selector: Element selector
            options: Screenshot options
            file_path: Save to file if provided

        Returns:
            Base64 string or bytes
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        element = await self.page.wait_for_selector(selector)

        opts = options or ScreenshotOptions()

        screenshot_opts = {
            "type": opts.type,
        }

        if opts.type == "jpeg":
            screenshot_opts["quality"] = opts.quality

        if file_path:
            await element.screenshot(path=str(file_path), **screenshot_opts)
            return str(file_path)
        else:
            return await element.screenshot(**screenshot_opts)

    # ========================================================================
    # FORM OPERATIONS
    # ========================================================================

    async def fill_form(self, fields: list[FormField], submit: bool = True):
        """
        Fill a form with multiple fields.

        Args:
            fields: List of form fields
            submit: Whether to submit the form
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        for field in fields:
            if field.wait_for_selector:
                await self.wait_for_selector(field.selector)

            if field.field_type in ["input", "textarea"]:
                await self.page.fill(field.selector, field.value)
            elif field.field_type == "select":
                await self.page.select_option(field.selector, field.value)
            elif field.field_type == "checkbox":
                if field.value.lower() in ["true", "1", "checked"]:
                    await self.page.check(field.selector)
                else:
                    await self.page.uncheck(field.selector)
            elif field.field_type == "radio":
                await self.page.click(field.selector)

        if submit:
            # Find submit button or form
            submit_selector = "input[type='submit'], button[type='submit'], button:not([type])"
            try:
                await self.page.click(submit_selector)
            except:
                # Try to submit form directly
                await self.page.evaluate("document.querySelector('form').submit()")

    # ========================================================================
    # INTERACTION OPERATIONS
    # ========================================================================

    async def click(
        self,
        selector: str,
        modifiers: list[str] | None = None,
        position: tuple[int, int] | None = None,
        timeout: int | None = None,
    ):
        """
        Click on an element.

        Args:
            selector: Element selector
            modifiers: Keyboard modifiers
            position: Click position
            timeout: Custom timeout
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        click_opts = {
            "timeout": timeout or self.timeout,
        }

        if modifiers:
            click_opts["modifiers"] = modifiers

        if position:
            click_opts["position"] = {"x": position[0], "y": position[1]}

        await self.page.click(selector, **click_opts)

    async def type_text(
        self,
        selector: str,
        text: str,
        delay: int = 50,
        clear: bool = True,
    ):
        """
        Type text into an element.

        Args:
            selector: Element selector
            text: Text to type
            delay: Delay between keystrokes
            clear: Clear field before typing
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        if clear:
            await self.page.fill(selector, "")

        await self.page.type(selector, text, delay=delay)

    async def press_key(self, key: str, selector: str | None = None):
        """
        Press a keyboard key.

        Args:
            key: Key to press
            selector: Element to focus (optional)
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        if selector:
            await self.page.focus(selector)

        await self.page.keyboard.press(key)

    async def scroll_to(self, x: int = 0, y: int = 0):
        """
        Scroll the page.

        Args:
            x: Horizontal scroll position
            y: Vertical scroll position
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        await self.page.evaluate(f"window.scrollTo({x}, {y})")

    async def scroll_to_element(self, selector: str):
        """
        Scroll to specific element.

        Args:
            selector: Element selector
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        element = await self.page.wait_for_selector(selector)
        await element.scroll_into_view_if_needed()

    # ========================================================================
    # EXECUTION OPERATIONS
    # ========================================================================

    async def evaluate_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in page context.

        Args:
            script: JavaScript code
            *args: Arguments to pass

        Returns:
            Script result
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        return await self.page.evaluate(script, *args)

    async def get_element_text(self, selector: str) -> str:
        """
        Get text content of element.

        Args:
            selector: Element selector

        Returns:
            Text content
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        element = await self.page.wait_for_selector(selector)
        return await element.text_content()

    async def get_element_attribute(
        self,
        selector: str,
        attribute: str,
    ) -> str | None:
        """
        Get attribute value of element.

        Args:
            selector: Element selector
            attribute: Attribute name

        Returns:
            Attribute value
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        element = await self.page.wait_for_selector(selector)
        return await element.get_attribute(attribute)

    async def get_page_content(self) -> str:
        """
        Get the full page HTML content.

        Returns:
            Page HTML
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        return await self.page.content()

    # ========================================================================
    # PERFORMANCE MONITORING
    # ========================================================================

    async def get_performance_metrics(self) -> dict[str, Any]:
        """
        Get performance metrics for the current page.

        Returns:
            Performance metrics
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        # Get navigation timing
        timing = await self.page.evaluate("""
            () => {
                const timing = performance.timing;
                return {
                    domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
                    loadComplete: timing.loadEventEnd - timing.navigationStart,
                    firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                    firstContentfulPaint: performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
                };
            }
        """)

        # Get resource metrics
        resources = await self.page.evaluate("""
            () => {
                const entries = performance.getEntriesByType('resource');
                return {
                    total: entries.length,
                    totalSize: entries.reduce((sum, e) => sum + (e.transferSize || 0), 0),
                    types: {}
                };
            }
        """)

        return {
            "timing": timing,
            "resources": resources,
            "network_requests": len(self.network_requests),
            "network_responses": len(self.network_responses),
        }

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def wait_for_network_idle(self, timeout: int = 5000):
        """
        Wait for network to be idle.

        Args:
            timeout: Time to wait with no requests
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        await self.page.wait_for_load_state("networkidle", timeout=timeout)

    async def set_user_agent(self, user_agent: str):
        """
        Set custom user agent.

        Args:
            user_agent: User agent string
        """
        if not self.context:
            raise RuntimeError("Browser context not created")

        # Create new context with user agent
        pages = self.context.pages
        await self.context.close()

        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": self.viewport[0], "height": self.viewport[1]},
        )

        # Recreate pages
        for _page in pages:
            await self.context.new_page()

    async def set_cookies(self, cookies: list[dict[str, Any]]):
        """
        Set cookies for the current context.

        Args:
            cookies: List of cookies
        """
        if not self.context:
            raise RuntimeError("Browser context not created")

        await self.context.add_cookies(cookies)

    async def get_cookies(self) -> list[dict[str, Any]]:
        """
        Get all cookies.

        Returns:
            List of cookies
        """
        if not self.context:
            raise RuntimeError("Browser context not created")

        return await self.context.cookies()

    def clear_network_logs(self):
        """Clear network request/response logs."""
        self.network_requests.clear()
        self.network_responses.clear()


# Factory function
async def create_browser_automation(
    browser_type: BrowserType = BrowserType.CHROMIUM,
    headless: bool = True,
    viewport: tuple[int, int] = ViewportSize.DESKTOP.value,
) -> BrowserAutomation:
    """
    Create and initialize browser automation.

    Args:
        browser_type: Browser to use
        headless: Run in headless mode
        viewport: Default viewport size

    Returns:
        Initialized browser automation
    """
    browser = BrowserAutomation(
        browser_type=browser_type,
        headless=headless,
        viewport=viewport,
    )

    await browser.start()
    return browser


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    import asyncio

    async def main():
        parser = argparse.ArgumentParser(description="Browser Automation Test")
        parser.add_argument("--url", default="https://example.com", help="URL to visit")
        parser.add_argument("--browser", default="chromium", help="Browser type")
        parser.add_argument("--headed", action="store_true", help="Run in headed mode")
        parser.add_argument("--screenshot", help="Screenshot file path")
        parser.add_argument("--evaluate", help="JavaScript to evaluate")

        args = parser.parse_args()

        # Create browser
        browser_type = BrowserType(args.browser)
        async with BrowserAutomation(
            browser_type=browser_type,
            headless=not args.headed,
        ) as browser:

            # Navigate
            print(f"\nNavigating to: {args.url}")
            metrics = await browser.navigate(args.url)
            print(f"  Title: {metrics.get('title', '')}")
            print(f"  Status: {metrics.get('status', '')}")
            print(f"  Load time: {metrics.get('load_time', 0):.2f}s")

            # Take screenshot
            if args.screenshot:
                print(f"\nTaking screenshot: {args.screenshot}")
                await browser.screenshot(file_path=Path(args.screenshot))

            # Evaluate script
            if args.evaluate:
                print(f"\nEvaluating: {args.evaluate}")
                result = await browser.evaluate_script(args.evaluate)
                print(f"  Result: {result}")

            # Get performance metrics
            perf = await browser.get_performance_metrics()
            print("\nPerformance metrics:")
            print(f"  DOM loaded: {perf['timing']['domContentLoaded']:.2f}ms")
            print(f"  Load complete: {perf['timing']['loadComplete']:.2f}ms")
            print(f"  Network requests: {perf['network_requests']}")

    asyncio.run(main())
