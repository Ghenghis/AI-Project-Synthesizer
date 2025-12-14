"""
VIBE MCP - LM Studio Connectivity Test

Tests connection to LM Studio and local model availability.
Replaces test-lmstudio.js from windsurf-vibe-setup.

Usage:
    python tests/tools/test_lmstudio.py
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.llm.lmstudio_client import LMStudioClient

logger = logging.getLogger(__name__)


class LMStudioConnectivityTest:
    """Test LM Studio connectivity and basic functionality."""

    def __init__(self):
        """Initialize test with default LM Studio settings."""
        self.lmstudio_client = LMStudioClient()
        self.test_results = {
            "lmstudio_connection": False,
            "simple_completion": False,
            "direct_http": False,
        }

    async def test_lmstudio_connection(self) -> bool:
        """Test basic connection to LM Studio."""
        print("🔗 Testing LM Studio connection...")

        try:
            # Try a simple model list - if this works, LM Studio is running
            models = await self.lmstudio_client.list_models()

            if models:
                print("✅ LM Studio is running and responsive")
                print(f"   Found {len(models)} models available")
                self.test_results["lmstudio_connection"] = True
                return True
            else:
                print("⚠️ LM Studio responded but no models found")
                return False

        except Exception as e:
            print(f"❌ LM Studio connection failed: {e}")
            logger.exception("LM Studio connection error")
            return False

    async def test_simple_completion(self) -> bool:
        """Test a simple completion with LM Studio."""
        print("\n✍️ Testing simple completion...")

        try:
            # Try a simple completion
            result = await self.lmstudio_client.complete(
                prompt="Say 'Hello from LM Studio!'",
                max_tokens=10,
                temperature=0.1,
            )

            if result and result.content:
                print("✅ Completion successful:")
                print(f"   Response: {result.content.strip()}")
                self.test_results["simple_completion"] = True
                return True
            else:
                print("❌ Completion returned empty result")
                return False

        except Exception as e:
            print(f"❌ Simple completion failed: {e}")
            logger.exception("Completion error")
            return False

    async def test_direct_http(self) -> bool:
        """Test direct HTTP connection to LM Studio API (simplified)."""
        print("\n🌐 Testing direct HTTP connection...")

        try:
            # Use the client's built-in connection test
            models = await self.lmstudio_client.list_models()
            if models:
                print("✅ Direct HTTP connection successful")
                return True
            else:
                print("❌ No response from HTTP endpoint")
                return False

        except Exception as e:
            print(f"❌ Direct HTTP connection failed: {e}")
            return False

    async def run_all_tests(self) -> dict:
        """Run all LM Studio connectivity tests."""
        print("=" * 60)
        print("VIBE MCP - LM Studio Connectivity Test")
        print("=" * 60)

        # Run tests in sequence
        await self.test_lmstudio_connection()
        await self.test_simple_completion()
        await self.test_direct_http()

        # Calculate results
        passed = sum(self.test_results.values())
        total = len(self.test_results)

        print("\n" + "=" * 60)
        print("TEST RESULTS")
        print("=" * 60)

        for test, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test.replace('_', ' ').title():<25} {status}")

        print(f"\nOverall: {passed}/{total} tests passed")

        if passed == total:
            print("🎉 LM Studio is fully configured!")
        elif passed >= 2:
            print("✅ LM Studio is usable for basic operations")
        else:
            print("⚠️ LM Studio has limited connectivity")
            print("\n💡 Suggestions:")
            print("   1. Make sure LM Studio is running")
            print("   2. Load a model in LM Studio")
            print("   3. Check that port 1234 is available")

        return {
            "passed": passed,
            "total": total,
            "results": self.test_results,
            "success_rate": passed / total * 100,
        }

    async def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self.lmstudio_client, "close"):
                await self.lmstudio_client.close()
        except:
            pass


async def main():
    """Main test runner."""
    test = LMStudioConnectivityTest()

    try:
        results = await test.run_all_tests()

        # Exit with appropriate code
        sys.exit(0 if results["success_rate"] >= 60 else 1)

    finally:
        await test.cleanup()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run tests
    asyncio.run(main())
