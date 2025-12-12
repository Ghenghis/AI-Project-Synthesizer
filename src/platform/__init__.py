"""
VIBE MCP Platform Integrations

This module implements platform-specific integrations:
- Browser automation with Playwright
- Enhanced GitLab client features
- Improved Firecrawl web scraping
- Additional platform tools

Components:
- BrowserAutomation: Playwright-based browser control
- Enhanced GitLab: MR automation, CI/CD integration
- Enhanced Firecrawl: Better scraping with caching
"""

from .browser_automation import (
    BrowserAutomation,
    BrowserType,
    ViewportSize,
    ScreenshotOptions,
    FormField,
    PageAction,
    BrowserSession,
    create_browser_automation,
)

__version__ = "1.0.0"
__all__ = [
    # Browser Automation
    "BrowserAutomation",
    "BrowserType",
    "ViewportSize",
    "ScreenshotOptions",
    "FormField",
    "PageAction",
    "BrowserSession",
    "create_browser_automation",
]
