"""
Enhanced Firecrawl Client for VIBE MCP

Extended web scraping with advanced features:
- Intelligent caching with TTL and invalidation
- Advanced rate limiting with backoff
- Content extraction with AI enhancement
- Batch processing with prioritization
- Integration with browser automation

Builds on the existing FirecrawlClient with additional capabilities.
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Tuple

import tiktoken
from bs4 import BeautifulSoup

from src.llm.litellm_router import LiteLLMRouter
from src.platform.browser_automation import (
    BrowserAutomation,
    BrowserType,
    create_browser_automation,
)

from .firecrawl_client import FirecrawlClient, FirecrawlFormat, ScrapedContent

secure_logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """Caching strategies."""
    NONE = "none"
    MEMORY = "memory"
    DISK = "disk"
    HYBRID = "hybrid"


class RateLimitStrategy(Enum):
    """Rate limiting strategies."""
    FIXED = "fixed"
    EXPONENTIAL_BACKOFF = "exponential"
    ADAPTIVE = "adaptive"
    TOKEN_BUCKET = "token_bucket"


class ContentPriority(Enum):
    """Content processing priority."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    content: ScrapedContent
    timestamp: datetime
    ttl: timedelta
    hits: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)

    @property
    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > self.ttl

    @property
    def age_seconds(self) -> float:
        return (datetime.now() - self.timestamp).total_seconds()


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 1.0
    burst_limit: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE
    max_retries: int = 3
    backoff_factor: float = 2.0


@dataclass
class ContentExtractionConfig:
    """Content extraction configuration."""
    extract_images: bool = True
    extract_tables: bool = True
    extract_code: bool = True
    extract_links: bool = True
    summarize_content: bool = False
    max_summary_tokens: int = 500
    language_detection: bool = True


class FirecrawlEnhanced(FirecrawlClient):
    """
    Enhanced Firecrawl client with advanced features.

    Extends FirecrawlClient with:
    - Multi-level caching
    - Intelligent rate limiting
    - AI-enhanced content extraction
    - Browser automation fallback
    - Content prioritization
    """

    def __init__(
        self,
        cache_strategy: CacheStrategy = CacheStrategy.HYBRID,
        cache_dir: Path | None = None,
        rate_limit_config: RateLimitConfig | None = None,
        **kwargs,
    ):
        """Initialize enhanced Firecrawl client."""
        super().__init__(**kwargs)

        # Caching
        self.cache_strategy = cache_strategy
        self.cache_dir = cache_dir or Path.home() / ".cache" / "firecrawl"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Memory cache
        self._memory_cache: dict[str, CacheEntry] = {}
        self._memory_cache_size = 100

        # Disk cache (SQLite)
        self._db_path = self.cache_dir / "cache.db"
        self._init_disk_cache()

        # Rate limiting
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self._rate_limiter = RateLimiter(self.rate_limit_config)

        # AI enhancement
        self.llm_router = LiteLLMRouter()
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

        # Browser automation fallback
        self.browser: BrowserAutomation | None = None

        # Content queue for prioritized processing
        self._content_queue: list[Tuple[ContentPriority, dict[str, Any]]] = []
        self._queue_lock = asyncio.Lock()

        secure_logger.info(f"Enhanced Firecrawl client initialized with {cache_strategy.value} caching")

    def _init_disk_cache(self):
        """Initialize SQLite disk cache."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                hits INTEGER DEFAULT 0,
                last_accessed TEXT NOT NULL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
        conn.commit()
        conn.close()

    async def _get_from_cache(self, key: str) -> ScrapedContent | None:
        """Get content from cache."""
        if self.cache_strategy == CacheStrategy.NONE:
            return None

        # Try memory cache first
        if self.cache_strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID]:
            if key in self._memory_cache:
                entry = self._memory_cache[key]
                if not entry.is_expired:
                    entry.hits += 1
                    entry.last_accessed = datetime.now()
                    return entry.content
                else:
                    # Remove expired entry
                    del self._memory_cache[key]

        # Try disk cache
        if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.execute(
                "SELECT content, timestamp, ttl_seconds, hits FROM cache WHERE key = ?",
                (key,),
            )
            row = cursor.fetchone()

            if row:
                content_json, timestamp_str, ttl_seconds, hits = row
                timestamp = datetime.fromisoformat(timestamp_str)
                ttl = timedelta(seconds=ttl_seconds)

                if datetime.now() - timestamp <= ttl:
                    # Update access info
                    conn.execute(
                        "UPDATE cache SET hits = hits + 1, last_accessed = ? WHERE key = ?",
                        (datetime.now().isoformat(), key),
                    )
                    conn.commit()
                    conn.close()

                    # Parse content
                    try:
                        content_data = json.loads(content_json)
                        content = ScrapedContent(
                            url=content_data["url"],
                            title=content_data["title"],
                            description=content_data["description"],
                            content=content_data["content"],
                            format=FirecrawlFormat(content_data["format"]),
                            timestamp=datetime.fromisoformat(content_data["timestamp"]),
                            metadata=content_data.get("metadata", {}),
                            links=content_data.get("links", []),
                            images=content_data.get("images", []),
                            word_count=content_data.get("word_count", 0),
                            reading_time=content_data.get("reading_time", 0),
                        )

                        # Add to memory cache if using hybrid
                        if self.cache_strategy == CacheStrategy.HYBRID:
                            self._add_to_memory_cache(key, content, ttl)

                        return content
                    except Exception as e:
                        secure_logger.error(f"Failed to parse cached content: {e}")
                else:
                    # Remove expired entry
                    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                    conn.commit()

            conn.close()

        return None

    async def _set_cache(self, key: str, content: ScrapedContent, ttl: timedelta):
        """Store content in cache."""
        if self.cache_strategy == CacheStrategy.NONE:
            return

        # Store in memory cache
        if self.cache_strategy in [CacheStrategy.MEMORY, CacheStrategy.HYBRID]:
            self._add_to_memory_cache(key, content, ttl)

        # Store in disk cache
        if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            content_data = {
                "url": content.url,
                "title": content.title,
                "description": content.description,
                "content": content.content,
                "format": content.format.value,
                "timestamp": content.timestamp.isoformat(),
                "metadata": content.metadata,
                "links": content.links,
                "images": content.images,
                "word_count": content.word_count,
                "reading_time": content.reading_time,
            }

            conn = sqlite3.connect(str(self._db_path))
            conn.execute(
                """
                INSERT OR REPLACE INTO cache
                (key, content, timestamp, ttl_seconds, hits, last_accessed)
                VALUES (?, ?, ?, ?, 1, ?)
                """,
                (
                    key,
                    json.dumps(content_data),
                    datetime.now().isoformat(),
                    int(ttl.total_seconds()),
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()
            conn.close()

    def _add_to_memory_cache(self, key: str, content: ScrapedContent, ttl: timedelta):
        """Add to memory cache with LRU eviction."""
        # Evict if necessary
        while len(self._memory_cache) >= self._memory_cache_size:
            # Find least recently used
            oldest_key = min(
                self._memory_cache.keys(),
                key=lambda k: self._memory_cache[k].last_accessed,
            )
            del self._memory_cache[oldest_key]

        # Add new entry
        self._memory_cache[key] = CacheEntry(
            key=key,
            content=content,
            timestamp=datetime.now(),
            ttl=ttl,
        )

    def _get_cache_key(self, url: str, options: dict[str, Any]) -> str:
        """Generate cache key for URL and options."""
        key_data = {
            "url": url,
            "formats": [f.value for f in options.get("formats", [FirecrawlFormat.MARKDOWN])],
            "only_main_content": options.get("only_main_content", True),
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    # ========================================================================
    # ENHANCED SCRAPING OPERATIONS
    # ========================================================================

    async def scrape_url_enhanced(
        self,
        url: str,
        formats: list[FirecrawlFormat] | None = None,
        config: ContentExtractionConfig | None = None,
        ttl: timedelta = timedelta(hours=1),
        priority: ContentPriority = ContentPriority.NORMAL,
        use_browser_fallback: bool = True,
    ) -> ScrapedContent:
        """
        Enhanced URL scraping with caching and rate limiting.

        Args:
            url: URL to scrape
            formats: Output formats
            config: Content extraction config
            ttl: Cache TTL
            priority: Processing priority
            use_browser_fallback: Use browser automation if API fails

        Returns:
            Enhanced scraped content
        """
        options = {
            "formats": formats or [FirecrawlFormat.MARKDOWN],
            "only_main_content": True,
        }

        # Check cache first
        cache_key = self._get_cache_key(url, options)
        cached = await self._get_from_cache(cache_key)
        if cached:
            secure_logger.debug(f"Cache hit for {url}")
            return cached

        # Apply rate limiting
        await self._rate_limiter.acquire()

        # Scrape with fallback chain
        content = None

        # Try Firecrawl API
        if self.api_key:
            try:
                content = await self.scrape_url(url, formats=formats)
            except Exception as e:
                secure_logger.warning(f"Firecrawl API failed: {e}")

        # Try browser automation fallback
        if not content and use_browser_fallback:
            content = await self._scrape_with_browser(url, formats)

        # Try basic fallback
        if not content:
            content = await self._fallback_scrape(url)

        if not content:
            raise RuntimeError(f"All scraping methods failed for {url}")

        # Enhance content
        if config:
            content = await self._enhance_content(content, config)

        # Cache result
        await self._set_cache(cache_key, content, ttl)

        return content

    async def _scrape_with_browser(
        self,
        url: str,
        formats: list[FirecrawlFormat],
    ) -> ScrapedContent | None:
        """Scrape using browser automation."""
        if not self.browser:
            self.browser = await create_browser_automation(
                browser_type=BrowserType.CHROMIUM,
                headless=True,
            )

        try:
            # Navigate to page
            await self.browser.navigate(url)
            await self.browser.wait_for_load_state("networkidle")

            # Get page content
            html = await self.browser.get_page_content()

            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")

            # Extract metadata
            title = soup.find("title")
            title = title.get_text().strip() if title else ""

            description = soup.find("meta", attrs={"name": "description"})
            description = description.get("content", "") if description else ""

            # Extract content based on format
            if FirecrawlFormat.MARKDOWN in formats:
                import markdownify
                content = markdownify.markdownify(str(soup), heading_style="ATX")
            else:
                # Clean text
                for script in soup(["script", "style"]):
                    script.decompose()
                content = soup.get_text(separator="\n", strip=True)

            # Extract links and images
            links = []
            images = []

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http"):
                    links.append(href)

            for img in soup.find_all("img", src=True):
                src = img["src"]
                if src.startswith("http"):
                    images.append(src)

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
                links=links,
                images=images,
                word_count=word_count,
                reading_time=reading_time,
            )

        except Exception as e:
            secure_logger.error(f"Browser scraping failed: {e}")
            return None

    async def _enhance_content(
        self,
        content: ScrapedContent,
        config: ContentExtractionConfig,
    ) -> ScrapedContent:
        """Enhance content with AI processing."""
        enhanced = content

        # Extract and enhance tables
        if config.extract_tables:
            enhanced = await self._extract_tables(enhanced)

        # Extract and format code blocks
        if config.extract_code:
            enhanced = await self._extract_code_blocks(enhanced)

        # Detect language
        if config.language_detection:
            enhanced.metadata["language"] = await self._detect_language(enhanced.content)

        # Generate summary
        if config.summarize_content and len(enhanced.content) > 500:
            summary = await self._generate_summary(
                enhanced.content,
                config.max_summary_tokens,
            )
            enhanced.metadata["summary"] = summary

        return enhanced

    async def _extract_tables(self, content: ScrapedContent) -> ScrapedContent:
        """Extract and format tables from content."""
        soup = BeautifulSoup(content.content, "html.parser")
        tables = []

        for table in soup.find_all("table"):
            # Convert table to markdown
            rows = []
            for tr in table.find_all("tr"):
                cells = [td.get_text().strip() for td in tr.find_all(["td", "th"])]
                if cells:
                    rows.append(" | ".join(cells))

            if rows:
                # Add header separator
                if len(rows) > 1:
                    rows.insert(1, " | ".join(["---"] * len(rows[0].split(" | "))))
                tables.append("\n".join(rows))

        if tables:
            content.metadata["tables"] = tables

        return content

    async def _extract_code_blocks(self, content: ScrapedContent) -> ScrapedContent:
        """Extract code blocks with language detection."""
        soup = BeautifulSoup(content.content, "html.parser")
        code_blocks = []

        for pre in soup.find_all("pre"):
            code = pre.get_text()
            # Try to detect language from class
            code_class = pre.get("class", [])
            language = "unknown"

            for cls in code_class:
                if cls.startswith("language-"):
                    language = cls[9:]
                    break
                elif cls in ["python", "javascript", "java", "cpp", "c"]:
                    language = cls
                    break

            code_blocks.append({
                "code": code,
                "language": language,
            })

        if code_blocks:
            content.metadata["code_blocks"] = code_blocks

        return content

    async def _detect_language(self, text: str) -> str:
        """Detect content language using simple heuristics."""
        # Simple keyword-based detection
        common_words = {
            "en": ["the", "and", "or", "but", "in", "on", "at", "to", "for"],
            "es": ["el", "la", "y", "o", "pero", "en", "para", "con", "por"],
            "fr": ["le", "la", "et", "ou", "mais", "dans", "pour", "avec", "par"],
            "de": ["der", "die", "das", "und", "oder", "aber", "in", "zu", "für"],
        }

        text_lower = text.lower()[:1000]  # Sample first 1000 chars
        scores = {}

        for lang, words in common_words.items():
            score = sum(1 for word in words if word in text_lower)
            scores[lang] = score

        if scores:
            detected = max(scores, key=scores.get)
            if scores[detected] > 2:  # Threshold
                return detected

        return "unknown"

    async def _generate_summary(self, content: str, max_tokens: int) -> str:
        """Generate content summary using AI."""
        # Truncate content if too long
        tokens = self.tokenizer.encode(content)
        if len(tokens) > 4000:
            content = self.tokenizer.decode(tokens[:4000])

        prompt = f"""
Summarize the following content in a concise paragraph:

{content}

Summary:
"""

        try:
            response = await self.llm_router.complete(
                prompt=prompt,
                model="gpt-3.5-turbo",
                max_tokens=max_tokens,
            )
            return response.strip()
        except Exception as e:
            secure_logger.error(f"Failed to generate summary: {e}")
            return ""

    # ========================================================================
    # BATCH PROCESSING WITH PRIORITY
    # ========================================================================

    async def batch_scrape_priority(
        self,
        urls: list[str],
        priorities: list[ContentPriority] | None = None,
        concurrency: int = 3,
    ) -> list[ScrapedContent]:
        """
        Batch scrape with priority queue.

        Args:
            urls: List of URLs to scrape
            priorities: Priority for each URL
            concurrency: Max concurrent requests

        Returns:
            List of scraped content
        """
        if priorities is None:
            priorities = [ContentPriority.NORMAL] * len(urls)

        # Add to priority queue
        async with self._queue_lock:
            for url, priority in zip(urls, priorities, strict=False):
                self._content_queue.append((priority, {"url": url}))

            # Sort by priority (descending)
            self._content_queue.sort(key=lambda x: x[0].value, reverse=True)

        # Process queue
        results = []
        semaphore = asyncio.Semaphore(concurrency)

        async def process_item():
            async with semaphore:
                async with self._queue_lock:
                    if not self._content_queue:
                        return None
                    priority, item = self._content_queue.pop(0)

                try:
                    content = await self.scrape_url_enhanced(
                        item["url"],
                        priority=priority,
                    )
                    return content
                except Exception as e:
                    secure_logger.error(f"Failed to scrape {item['url']}: {e}")
                    return None

        # Run tasks
        tasks = [process_item() for _ in range(min(len(urls), concurrency * 2))]
        results = await asyncio.gather(*tasks)

        # Filter None results
        return [r for r in results if r is not None]

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    async def clear_cache(self, strategy: CacheStrategy | None = None):
        """Clear cache."""
        if strategy is None or strategy == CacheStrategy.MEMORY:
            self._memory_cache.clear()

        if strategy is None or strategy == CacheStrategy.DISK:
            conn = sqlite3.connect(str(self._db_path))
            conn.execute("DELETE FROM cache")
            conn.commit()
            conn.close()

        secure_logger.info(f"Cache cleared: {strategy or 'all'}")

    async def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "memory_entries": len(self._memory_cache),
            "memory_size_mb": sum(
                len(str(entry.content.__dict__))
                for entry in self._memory_cache.values()
            ) / (1024 * 1024),
        }

        if self.cache_strategy in [CacheStrategy.DISK, CacheStrategy.HYBRID]:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.execute(
                "SELECT COUNT(*), SUM(LENGTH(content)) FROM cache",
            )
            count, size = cursor.fetchone()
            stats["disk_entries"] = count
            stats["disk_size_mb"] = (size or 0) / (1024 * 1024)
            conn.close()

        return stats

    async def close(self):
        """Cleanup resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None

        await super().__aexit__(None, None, None)


class RateLimiter:
    """Adaptive rate limiter with multiple strategies."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._tokens = config.burst_limit
        self._last_refill = time.time()
        self._failures = 0
        self._last_request_time = 0
        self._adaptive_delay = 1.0 / config.requests_per_second

    async def acquire(self):
        """Acquire permission to make a request."""
        if self.config.strategy == RateLimitStrategy.FIXED:
            await self._fixed_wait()
        elif self.config.strategy == RateLimitStrategy.EXPONENTIAL_BACKOFF:
            await self._exponential_backoff_wait()
        elif self.config.strategy == RateLimitStrategy.ADAPTIVE:
            await self._adaptive_wait()
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            await self._token_bucket_wait()

    async def _fixed_wait(self):
        """Fixed delay between requests."""
        elapsed = time.time() - self._last_request_time
        delay = 1.0 / self.config.requests_per_second - elapsed

        if delay > 0:
            await asyncio.sleep(delay)

        self._last_request_time = time.time()

    async def _exponential_backoff_wait(self):
        """Exponential backoff after failures."""
        if self._failures > 0:
            delay = self.config.backoff_factor ** self._failures
            await asyncio.sleep(min(delay, 60))  # Cap at 60 seconds
        else:
            await self._fixed_wait()

    async def _adaptive_wait(self):
        """Adaptive delay based on response times."""
        # Simple adaptive strategy
        if self._failures > 0:
            self._adaptive_delay *= 1.5
        else:
            self._adaptive_delay *= 0.95

        self._adaptive_delay = max(
            self._adaptive_delay,
            1.0 / (self.config.requests_per_second * 2),
        )
        self._adaptive_delay = min(
            self._adaptive_delay,
            5.0,
        )

        await asyncio.sleep(self._adaptive_delay)

    async def _token_bucket_wait(self):
        """Token bucket algorithm."""
        now = time.time()
        elapsed = now - self._last_refill

        # Refill tokens
        if elapsed > 0:
            refill_rate = self.config.requests_per_second
            self._tokens = min(
                self.config.burst_limit,
                self._tokens + elapsed * refill_rate,
            )
            self._last_refill = now

        # Wait for token
        if self._tokens < 1:
            wait_time = (1 - self._tokens) / self.config.requests_per_second
            await asyncio.sleep(wait_time)
            self._tokens = 1

        self._tokens -= 1

    def record_success(self):
        """Record successful request."""
        self._failures = 0

    def record_failure(self):
        """Record failed request."""
        self._failures = min(self._failures + 1, self.config.max_retries)


# Factory function
async def create_firecrawl_enhanced(**kwargs) -> FirecrawlEnhanced:
    """
    Create and initialize enhanced Firecrawl client.

    Args:
        **kwargs: Arguments for FirecrawlEnhanced

    Returns:
        Initialized enhanced Firecrawl client
    """
    client = FirecrawlEnhanced(**kwargs)

    # Test connection
    if await client.test_connection():
        return client
    else:
        secure_logger.warning("Firecrawl client initialized in fallback mode")
        return client


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    import asyncio

    async def main():
        parser = argparse.ArgumentParser(description="Enhanced Firecrawl Client Test")
        parser.add_argument("--url", required=True, help="URL to scrape")
        parser.add_argument("--cache", choices=["none", "memory", "disk", "hybrid"], default="hybrid")
        parser.add_argument("--summarize", action="store_true", help="Generate summary")
        parser.add_argument("--extract-tables", action="store_true", help="Extract tables")
        parser.add_argument("--extract-code", action="store_true", help="Extract code blocks")
        parser.add_argument("--priority", choices=["low", "normal", "high", "critical"], default="normal")

        args = parser.parse_args()

        # Create client
        client = await create_firecrawl_enhanced(
            cache_strategy=CacheStrategy(args.cache),
        )

        async with client:
            # Configure extraction
            config = ContentExtractionConfig(
                extract_tables=args.extract_tables,
                extract_code=args.extract_code,
                summarize_content=args.summarize,
            )

            # Scrape
            print(f"\nScraping: {args.url}")
            content = await client.scrape_url_enhanced(
                url=args.url,
                config=config,
                priority=ContentPriority[args.priority.upper()],
            )

            print(f"\n  Title: {content.title}")
            print(f"  Description: {content.description}")
            print(f"  Words: {content.word_count} | Reading time: {content.reading_time} min")

            # Show extracted content
            if content.metadata.get("tables"):
                print(f"\n  Tables found: {len(content.metadata['tables'])}")

            if content.metadata.get("code_blocks"):
                print(f"  Code blocks: {len(content.metadata['code_blocks'])}")

            if content.metadata.get("summary"):
                print(f"\n  Summary: {content.metadata['summary']}")

            # Cache stats
            stats = await client.get_cache_stats()
            print(f"\n  Cache stats: {stats}")

    asyncio.run(main())
