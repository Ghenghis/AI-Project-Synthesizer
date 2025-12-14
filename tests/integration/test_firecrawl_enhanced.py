"""
Integration tests for Enhanced Firecrawl component.

Tests enhanced web scraping functionality including:
- Multi-level caching
- Rate limiting
- Content extraction with AI
- Browser automation fallback
- Priority-based batch processing
"""

import asyncio
import tempfile
from pathlib import Path

import pytest

from src.discovery.firecrawl_client import FirecrawlFormat
from src.discovery.firecrawl_enhanced import (
    CacheStrategy,
    ContentExtractionConfig,
    ContentPriority,
    RateLimitConfig,
    RateLimitStrategy,
    create_firecrawl_enhanced,
)


class TestFirecrawlEnhanced:
    """Test suite for FirecrawlEnhanced."""

    @pytest.fixture
    async def client(self):
        """Create Firecrawl enhanced client for testing."""
        client = await create_firecrawl_enhanced(
            cache_strategy=CacheStrategy.MEMORY,
        )
        yield client
        await client.close()

    @pytest.mark.asyncio
    async def test_basic_scraping_with_cache(self, client):
        """Test basic scraping with caching."""
        # First scrape - should hit the source
        content1 = await client.scrape_url_enhanced(
            "https://example.com",
            ttl=timedelta(minutes=5),
        )

        assert content1.url == "https://example.com"
        assert content1.title == "Example Domain"
        assert len(content1.content) > 0

        # Second scrape - should hit cache
        content2 = await client.scrape_url_enhanced("https://example.com")
        assert content1.content == content2.content

        # Check cache stats
        stats = await client.get_cache_stats()
        assert stats["memory_entries"] >= 1

    @pytest.mark.asyncio
    async def test_content_extraction(self, client):
        """Test AI-enhanced content extraction."""
        config = ContentExtractionConfig(
            extract_tables=True,
            extract_code=True,
            language_detection=True,
            summarize_content=False,  # Skip to avoid API calls in tests
        )

        content = await client.scrape_url_enhanced(
            "https://httpbin.org/html",
            config=config,
        )

        assert content.url == "https://httpbin.org/html"
        assert "Herman Melville" in content.content

        # Check metadata
        assert "language" in content.metadata
        assert content.metadata["language"] != "unknown"

    @pytest.mark.asyncio
    async def test_browser_fallback(self, client):
        """Test browser automation fallback."""
        # Use a page that might need JavaScript
        content = await client.scrape_url_enhanced(
            "https://httpbin.org/forms/post",
            use_browser_fallback=True,
        )

        assert content.url == "https://httpbin.org/forms/post"
        assert len(content.content) > 0
        assert "form" in content.content.lower()

    @pytest.mark.asyncio
    async def test_priority_batch_scraping(self, client):
        """Test priority-based batch processing."""
        urls = [
            "https://example.com",
            "https://httpbin.org/json",
            "https://httpbin.org/html",
        ]
        priorities = [
            ContentPriority.HIGH,
            ContentPriority.NORMAL,
            ContentPriority.LOW,
        ]

        results = await client.batch_scrape_priority(
            urls,
            priorities=priorities,
            concurrency=2,
        )

        assert len(results) == 3
        for result in results:
            assert result is not None
            assert len(result.content) > 0

    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        config = RateLimitConfig(
            requests_per_second=2.0,
            strategy=RateLimitStrategy.FIXED,
        )

        client = await create_firecrawl_enhanced(
            rate_limit_config=config,
            cache_strategy=CacheStrategy.NONE,  # Disable cache to test rate limiting
        )

        try:
            start_time = time.time()

            # Make multiple requests
            await client.scrape_url_enhanced("https://httpbin.org/delay/0")
            await client.scrape_url_enhanced("https://httpbin.org/delay/0")

            elapsed = time.time() - start_time
            # Should take at least 0.5 seconds due to rate limiting
            assert elapsed >= 0.5

        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_disk_cache(self):
        """Test disk-based caching."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "firecrawl"

            client = await create_firecrawl_enhanced(
                cache_strategy=CacheStrategy.DISK,
                cache_dir=cache_dir,
            )

            try:
                # Scrape and cache
                content1 = await client.scrape_url_enhanced(
                    "https://example.com",
                    ttl=timedelta(minutes=5),
                )

                # Check disk cache
                stats = await client.get_cache_stats()
                assert stats["disk_entries"] >= 1
                assert stats["disk_size_mb"] > 0

                # Create new client and verify cache persists
                client2 = await create_firecrawl_enhanced(
                    cache_strategy=CacheStrategy.DISK,
                    cache_dir=cache_dir,
                )

                try:
                    content2 = await client2.scrape_url_enhanced("https://example.com")
                    assert content1.content == content2.content
                finally:
                    await client2.close()

            finally:
                await client.close()

    @pytest.mark.asyncio
    async def test_cache_invalidation(self, client):
        """Test cache invalidation with TTL."""
        # Cache with short TTL
        content1 = await client.scrape_url_enhanced(
            "https://httpbin.org/uuid",
            ttl=timedelta(seconds=1),
        )

        # Wait for cache to expire
        await asyncio.sleep(2)

        # Should fetch fresh content
        content2 = await client.scrape_url_enhanced("https://httpbin.org/uuid")

        # UUID should be different (fresh request)
        assert content1.content != content2.content

    @pytest.mark.asyncio
    async def test_multiple_formats(self, client):
        """Test scraping with multiple output formats."""
        content = await client.scrape_url_enhanced(
            "https://example.com",
            formats=[FirecrawlFormat.MARKDOWN, FirecrawlFormat.TEXT],
        )

        assert content.format == FirecrawlFormat.MARKDOWN
        assert len(content.content) > 0

    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling for invalid URLs."""
        with pytest.raises(Exception):
            await client.scrape_url_enhanced("https://invalid-domain-12345.com")

        # Test with browser fallback disabled
        with pytest.raises(Exception):
            await client.scrape_url_enhanced(
                "https://invalid-domain-12345.com",
                use_browser_fallback=False,
            )

    @pytest.mark.asyncio
    async def test_cache_management(self, client):
        """Test cache clearing and management."""
        # Add some cached content
        await client.scrape_url_enhanced("https://example.com")
        await client.scrape_url_enhanced("https://httpbin.org/json")

        # Verify cache has entries
        stats = await client.get_cache_stats()
        assert stats["memory_entries"] >= 2

        # Clear cache
        await client.clear_cache()

        # Verify cache is empty
        stats = await client.get_cache_stats()
        assert stats["memory_entries"] == 0


if __name__ == "__main__":
    # Run tests directly
    import sys
    import time
    from datetime import timedelta

    print("Running Firecrawl Enhanced integration tests...")

    async def run_tests():
        test = TestFirecrawlEnhanced()

        try:
            # Test with memory cache
            async with create_firecrawl_enhanced(
                cache_strategy=CacheStrategy.MEMORY,
            ) as client:
                await test.test_basic_scraping_with_cache(client)
                print("✓ Basic scraping with cache test passed")

                await test.test_content_extraction(client)
                print("✓ Content extraction test passed")

                await test.test_browser_fallback(client)
                print("✓ Browser fallback test passed")

                await test.test_priority_batch_scraping(client)
                print("✓ Priority batch scraping test passed")

                await test.test_cache_invalidation(client)
                print("✓ Cache invalidation test passed")

                await test.test_multiple_formats(client)
                print("✓ Multiple formats test passed")

                await test.test_cache_management(client)
                print("✓ Cache management test passed")

            # Test rate limiting
            await test.test_rate_limiting()
            print("✓ Rate limiting test passed")

            # Test disk cache
            await test.test_disk_cache()
            print("✓ Disk cache test passed")

            print("\nAll tests passed! ✓")

        except Exception as e:
            print(f"\nTest failed: {e}")
            import traceback

            traceback.print_exc()
            sys.exit(1)

    asyncio.run(run_tests())
