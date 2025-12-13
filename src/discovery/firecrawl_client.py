"""
VIBE MCP - Firecrawl Client Integration

Web scraping client using Firecrawl API for intelligent content extraction.
Implements Phase 5.2 of the VIBE MCP roadmap.

Features:
- Web page scraping and content extraction
- Site mapping and crawling
- Text cleaning and processing
- Async batch processing
- Rate limiting and caching
"""

import asyncio
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
import markdownify
from bs4 import BeautifulSoup, Comment

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class FirecrawlFormat(Enum):
    """Output format options."""
    MARKDOWN = "markdown"
    HTML = "html"
    RAW = "raw"
    TEXT = "text"


class FirecrawlMode(Enum):
    """Scraping modes."""
    SCRAPE = "scrape"  # Single page
    CRAWL = "crawl"    # Entire site
    MAP = "map"        # Site map only


@dataclass
class ScrapedContent:
    """Scraped content representation."""
    url: str
    title: str
    description: str
    content: str
    format: FirecrawlFormat
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    links: list[str] = field(default_factory=list)
    images: list[str] = field(default_factory=list)
    word_count: int = 0
    reading_time: int = 0  # in minutes


@dataclass
class SiteMap:
    """Site map representation."""
    base_url: str
    pages: list[dict[str, Any]]
    total_pages: int
    crawled_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


class FirecrawlClient:
    """
    Firecrawl API client for web scraping.

    Provides intelligent web scraping with content extraction,
    site mapping, and batch processing capabilities.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = "https://api.firecrawl.dev/v1",
        timeout: int = 30,
    ):
        """
        Initialize Firecrawl client.

        Args:
            api_key: Firecrawl API key
            base_url: Firecrawl API base URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)

        # Rate limiting
        self.rate_limit_remaining = 1000
        self.rate_limit_reset = datetime.now()

        # Cache
        self._cache: dict[str, dict[str, Any]] = {}
        self._cache_ttl = timedelta(hours=1)

        # Session
        self._session: aiohttp.ClientSession | None = None

        if not self.api_key:
            secure_logger.warning("No Firecrawl API key provided. Using fallback scraping.")

        secure_logger.info("Firecrawl client initialized")

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self._session:
            headers = {
                "User-Agent": "VIBE-MCP/1.0",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=self.timeout,
                trust_env=True,
            )

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """
        Make request to Firecrawl API.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            use_cache: Whether to use cache

        Returns:
            Response data
        """
        await self._ensure_session()

        # Check cache
        if method.upper() == "POST" and use_cache and data:
            cache_key = f"{endpoint}:{json.dumps(data, sort_keys=True)}"
            if cache_key in self._cache:
                cached = self._cache[cache_key]
                if datetime.now() - cached["timestamp"] < self._cache_ttl:
                    secure_logger.debug(f"Cache hit for {endpoint}")
                    return cached["data"]

        # Apply rate limiting
        await self._check_rate_limit()

        url = urljoin(f"{self.base_url}/", endpoint.lstrip("/"))

        try:
            async with self._session.request(method, url, json=data) as response:
                response.raise_for_status()
                result = await response.json()

                # Cache successful responses
                if method.upper() == "POST" and use_cache and data:
                    self._cache[cache_key] = {
                        "data": result,
                        "timestamp": datetime.now(),
                    }

                return result

        except aiohttp.ClientError as e:
            secure_logger.error(f"Firecrawl API request failed: {e}")
            raise

    async def _check_rate_limit(self):
        """Check and respect rate limits."""
        if self.rate_limit_remaining < 10:
            wait_time = (self.rate_limit_reset - datetime.now()).total_seconds()
            if wait_time > 0:
                secure_logger.warning(f"Rate limit approaching. Waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)

    async def _fallback_scrape(self, url: str) -> ScrapedContent:
        """
        Fallback scraping without Firecrawl API.

        Args:
            url: URL to scrape

        Returns:
            Scraped content
        """
        secure_logger.info(f"Using fallback scraping for {url}")

        try:
            async with self._session.get(url) as response:
                response.raise_for_status()
                html = await response.text()

                # Parse with BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")

                # Extract metadata
                title = soup.find("title")
                title = title.get_text().strip() if title else ""

                description = soup.find("meta", attrs={"name": "description"})
                description = description.get("content", "") if description else ""

                # Clean content
                for script in soup(["script", "style", "nav", "footer"]):
                    script.decompose()

                # Remove comments
                for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                    comment.extract()

                # Extract links
                links = []
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("http"):
                        links.append(href)
                    elif href.startswith("/"):
                        parsed = urlparse(url)
                        links.append(f"{parsed.scheme}://{parsed.netloc}{href}")

                # Extract images
                images = []
                for img in soup.find_all("img", src=True):
                    src = img["src"]
                    if src.startswith("http"):
                        images.append(src)
                    elif src.startswith("/"):
                        parsed = urlparse(url)
                        images.append(f"{parsed.scheme}://{parsed.netloc}{src}")

                # Convert to markdown
                content = markdownify.markdownify(str(soup), heading_style="ATX")

                # Clean markdown
                content = re.sub(r"\n{3,}", "\n\n", content)
                content = content.strip()

                # Calculate metrics
                word_count = len(content.split())
                reading_time = max(1, word_count // 200)  # 200 words per minute

                return ScrapedContent(
                    url=url,
                    title=title,
                    description=description,
                    content=content,
                    format=FirecrawlFormat.MARKDOWN,
                    timestamp=datetime.now(),
                    links=links,
                    images=images,
                    word_count=word_count,
                    reading_time=reading_time,
                )

        except Exception as e:
            secure_logger.error(f"Fallback scraping failed: {e}")
            raise

    # ========================================================================
    # SCRAPING OPERATIONS
    # ========================================================================

    async def scrape_url(
        self,
        url: str,
        formats: list[FirecrawlFormat] | None = None,
        include_tags: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        only_main_content: bool = True,
        timeout: int | None = None,
    ) -> ScrapedContent:
        """
        Scrape a single URL.

        Args:
            url: URL to scrape
            formats: Output formats to generate
            include_tags: HTML tags to include
            exclude_tags: HTML tags to exclude
            only_main_content: Extract only main content
            timeout: Custom timeout

        Returns:
            Scraped content
        """
        if not formats:
            formats = [FirecrawlFormat.MARKDOWN]

        # Use Firecrawl API if available
        if self.api_key:
            data = {
                "url": url,
                "formats": [f.value for f in formats],
                "onlyMainContent": only_main_content,
            }

            if include_tags:
                data["includeTags"] = include_tags

            if exclude_tags:
                data["excludeTags"] = exclude_tags

            if timeout:
                data["timeout"] = timeout

            try:
                result = await self._request("POST", "/scrape", data=data)

                # Parse response
                content = result.get("data", {}).get("content", "")
                title = result.get("data", {}).get("metadata", {}).get("title", "")
                description = result.get("data", {}).get("metadata", {}).get("description", "")

                # Calculate metrics
                word_count = len(content.split())
                reading_time = max(1, word_count // 200)

                return ScrapedContent(
                    url=url,
                    title=title,
                    description=description,
                    content=content,
                    format=formats[0],
                    timestamp=datetime.now(),
                    metadata=result.get("data", {}).get("metadata", {}),
                    word_count=word_count,
                    reading_time=reading_time,
                )

            except Exception as e:
                secure_logger.warning(f"Firecrawl API failed, using fallback: {e}")

        # Fallback scraping
        return await self._fallback_scrape(url)

    async def crawl_site(
        self,
        url: str,
        limit: int = 10,
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
        formats: list[FirecrawlFormat] | None = None,
        max_depth: int = 2,
    ) -> list[ScrapedContent]:
        """
        Crawl an entire site.

        Args:
            url: Starting URL
            limit: Maximum pages to crawl
            include_paths: URL patterns to include
            exclude_paths: URL patterns to exclude
            formats: Output formats
            max_depth: Maximum crawl depth

        Returns:
            List of scraped content
        """
        if not formats:
            formats = [FirecrawlFormat.MARKDOWN]

        # Use Firecrawl API if available
        if self.api_key:
            data = {
                "url": url,
                "limit": limit,
                "scrapeOptions": {
                    "formats": [f.value for f in formats],
                    "onlyMainContent": True,
                },
            }

            if include_paths:
                data["includePaths"] = include_paths

            if exclude_paths:
                data["excludePaths"] = exclude_paths

            if max_depth:
                data["maxDepth"] = max_depth

            try:
                # Start crawl job
                result = await self._request("POST", "/crawl", data=data)
                job_id = result.get("jobId")

                if not job_id:
                    raise RuntimeError("No job ID returned")

                # Monitor job
                contents = []
                while len(contents) < limit:
                    status = await self._request("GET", f"/crawl/status/{job_id}")

                    if status.get("status") == "completed":
                        break

                    if status.get("status") == "failed":
                        raise RuntimeError("Crawl job failed")

                    # Get current data
                    data = status.get("data", [])
                    for item in data:
                        if len(contents) >= limit:
                            break

                        content = ScrapedContent(
                            url=item.get("url", ""),
                            title=item.get("metadata", {}).get("title", ""),
                            description=item.get("metadata", {}).get("description", ""),
                            content=item.get("content", ""),
                            format=formats[0],
                            timestamp=datetime.now(),
                            metadata=item.get("metadata", {}),
                        )

                        # Calculate metrics
                        content.word_count = len(content.content.split())
                        content.reading_time = max(1, content.word_count // 200)

                        contents.append(content)

                    await asyncio.sleep(2)  # Poll interval

                return contents

            except Exception as e:
                secure_logger.warning(f"Firecrawl crawl failed, scraping single page: {e}")

        # Fallback: just scrape the main page
        return [await self.scrape_url(url, formats=formats)]

    async def map_site(
        self,
        url: str,
        limit: int = 100,
        include_paths: list[str] | None = None,
        exclude_paths: list[str] | None = None,
    ) -> SiteMap:
        """
        Generate a site map.

        Args:
            url: Site URL
            limit: Maximum pages to map
            include_paths: URL patterns to include
            exclude_paths: URL patterns to exclude

        Returns:
            Site map
        """
        # Use Firecrawl API if available
        if self.api_key:
            data = {
                "url": url,
                "limit": limit,
            }

            if include_paths:
                data["includePaths"] = include_paths

            if exclude_paths:
                data["excludePaths"] = exclude_paths

            try:
                result = await self._request("POST", "/map", data=data)

                pages = result.get("links", [])

                return SiteMap(
                    base_url=url,
                    pages=pages[:limit],
                    total_pages=len(pages),
                    crawled_at=datetime.now(),
                )

            except Exception as e:
                secure_logger.warning(f"Firecrawl map failed: {e}")

        # Fallback: return single page
        return SiteMap(
            base_url=url,
            pages=[{"url": url, "title": "Main Page"}],
            total_pages=1,
            crawled_at=datetime.now(),
        )

    # ========================================================================
    # BATCH OPERATIONS
    # ========================================================================

    async def batch_scrape(
        self,
        urls: list[str],
        formats: list[FirecrawlFormat] | None = None,
        concurrency: int = 5,
    ) -> list[ScrapedContent]:
        """
        Scrape multiple URLs concurrently.

        Args:
            urls: List of URLs to scrape
            formats: Output formats
            concurrency: Maximum concurrent requests

        Returns:
            List of scraped content
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def scrape_with_semaphore(url: str) -> ScrapedContent:
            async with semaphore:
                return await self.scrape_url(url, formats=formats)

        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter exceptions
        contents = []
        for result in results:
            if isinstance(result, Exception):
                secure_logger.error(f"Batch scrape error: {result}")
            else:
                contents.append(result)

        return contents

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def test_connection(self) -> bool:
        """Test connection to Firecrawl API."""
        if not self.api_key:
            secure_logger.info("No API key, using fallback mode")
            return True

        try:
            # Try to scrape a simple page
            await self.scrape_url("https://example.com")
            secure_logger.info("Firecrawl API connection successful")
            return True
        except Exception as e:
            secure_logger.error(f"Firecrawl API connection failed: {e}")
            return False

    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        secure_logger.info("Cache cleared")

    async def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status."""
        return {
            "remaining": self.rate_limit_remaining,
            "reset_at": self.rate_limit_reset.isoformat(),
            "reset_in_seconds": max(0, (self.rate_limit_reset - datetime.now()).total_seconds()),
        }

    def clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove non-printable characters
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # Normalize line breaks
        text = re.sub(r"\r\n|\r", "\n", text)

        return text.strip()

    def extract_links(self, content: str, base_url: str) -> list[str]:
        """
        Extract links from content.

        Args:
            content: HTML or markdown content
            base_url: Base URL for relative links

        Returns:
            List of absolute URLs
        """
        links = []

        # Extract markdown links
        md_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        for _, url in md_links:
            if url.startswith("http"):
                links.append(url)
            elif url.startswith("/"):
                links.append(urljoin(base_url, url))

        # Extract HTML links if it's HTML
        if "<a href=" in content:
            soup = BeautifulSoup(content, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http"):
                    links.append(href)
                elif href.startswith("/"):
                    links.append(urljoin(base_url, href))

        # Remove duplicates
        return list(set(links))


# Factory function
async def create_firecrawl_client(
    api_key: str | None = None,
    base_url: str = "https://api.firecrawl.dev/v1",
) -> FirecrawlClient:
    """
    Create and initialize Firecrawl client.

    Args:
        api_key: Firecrawl API key
        base_url: Firecrawl API base URL

    Returns:
        Initialized Firecrawl client
    """
    client = FirecrawlClient(api_key=api_key, base_url=base_url)

    # Test connection
    if await client.test_connection():
        return client
    else:
        secure_logger.warning("Firecrawl client initialized in fallback mode")
        return client


# CLI interface for testing
async def main():
    """Test the Firecrawl client."""
    import argparse

    parser = argparse.ArgumentParser(description="Firecrawl Client Test")
    parser.add_argument("--api-key", help="Firecrawl API key")
    parser.add_argument("--url", required=True, help="URL to scrape")
    parser.add_argument("--crawl", action="store_true", help="Crawl entire site")
    parser.add_argument("--map", action="store_true", help="Generate site map")
    parser.add_argument("--limit", type=int, default=10, help="Page limit for crawl/map")
    parser.add_argument("--format", default="markdown", help="Output format")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    # Create client
    client = await create_firecrawl_client(api_key=args.api_key)

    async with client:
        if args.map:
            # Generate site map
            print(f"\nMapping site: {args.url}")
            site_map = await client.map_site(args.url, limit=args.limit)

            print(f"\nFound {site_map.total_pages} pages:")
            for page in site_map.pages[:20]:
                print(f"  - {page.get('url', '')}")
                if page.get("title"):
                    print(f"    {page['title']}")

        elif args.crawl:
            # Crawl site
            print(f"\nCrawling site: {args.url} (limit: {args.limit})")
            contents = await client.crawl_site(args.url, limit=args.limit)

            print(f"\nScraped {len(contents)} pages:")
            for content in contents:
                print(f"\n  {content.title}")
                print(f"  URL: {content.url}")
                print(f"  Words: {content.word_count} | Reading time: {content.reading_time} min")
                print(f"  Preview: {content.content[:200]}...")

        else:
            # Scrape single page
            print(f"\nScraping: {args.url}")
            content = await client.scrape_url(args.url)

            print(f"\n  Title: {content.title}")
            print(f"  Description: {content.description}")
            print(f"  Words: {content.word_count} | Reading time: {content.reading_time} min")
            print(f"  Links found: {len(content.links)}")
            print(f"  Images found: {len(content.images)}")

            # Save to file if requested
            if args.output:
                output_path = Path(args.output)
                output_path.write_text(content.content, encoding="utf-8")
                print(f"\n  Saved to: {output_path}")
            else:
                print("\n  Content preview:")
                print(f"  {content.content[:500]}...")


if __name__ == "__main__":
    asyncio.run(main())
