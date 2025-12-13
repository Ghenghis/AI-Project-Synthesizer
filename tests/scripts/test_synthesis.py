#!/usr/bin/env python3
"""
Simple end-to-end test of the AI Project Synthesizer.
Tests the complete synthesis pipeline with a tiny repository.
"""

import asyncio
import tempfile
from pathlib import Path

from src.synthesis.project_builder import (
    ExtractionSpec,
    ProjectBuilder,
    SynthesisRequest,
)


async def test_synthesis():
    """Test the complete synthesis pipeline."""

    print("🚀 Starting AI Project Synthesizer end-to-end test")

    # Create temporary output directory
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_project"
        output_path.mkdir()

        # Create project builder
        builder = ProjectBuilder()

        # Create synthesis request with a simple Python repo
        request = SynthesisRequest(
            project_name="test-synthesis",
            repositories=[
                ExtractionSpec(
                    repo_url="https://github.com/octocat/Hello-World",
                    components=["README.md"],
                    destination="src",
                    rename_map={}
                )
            ],
            output_path=str(output_path),
            template="python-default",
            generate_docs=True,
        )

        print(f"📁 Output directory: {output_path}")

        try:
            # Run synthesis
            result = await builder.synthesize(request)

            print(f"✅ Synthesis completed with status: {result.status.value}")
            print(f"📊 Files generated: {result.files_generated}")
            print(f"📄 Documentation: {result.documentation_generated}")
            print(f"⚠️  Warnings: {len(result.warnings)}")

            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")

            # Check output files
            print("\n📋 Generated files:")
            for file_path in output_path.rglob("*"):
                if file_path.is_file():
                    rel_path = file_path.relative_to(output_path)
                    size = file_path.stat().st_size
                    print(f"  {rel_path} ({size} bytes)")

            # Verify README was generated
            readme_path = output_path / "README.md"
            if readme_path.exists():
                print("\n📖 README.md preview:")
                content = readme_path.read_text()
                print(content[:300] + "..." if len(content) > 300 else content)

            return result.status.value == "complete"

        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_build_method():
    """Test the build method used by MCP tools."""

    print("\n🔧 Testing build() method (MCP entry point)")

    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_build"
        output_path.mkdir()

        builder = ProjectBuilder()

        # Test with dict configs (as MCP would provide)
        result = await builder.build(
            repositories=[
                {
                    "repo_url": "https://github.com/octocat/Hello-World",
                    "components": ["README.md"],
                    "destination": "src",
                    "rename_map": {}
                }
            ],
            project_name="test-build",
            output_path=output_path,
            template="python-default"
        )

        print("✅ Build completed")
        print(f"📁 Project path: {result.project_path}")
        print(f"📊 Repos processed: {result.repos_processed}")
        print(f"📄 Files created: {result.files_created}")

        return result.files_created > 0


async def main():
    """Run all tests."""
    print("=" * 60)
    print("AI Project Synthesizer - End-to-End Test Suite")
    print("=" * 60)

    # Test synthesis pipeline
    synthesis_ok = await test_synthesis()

    # Test build method
    build_ok = await test_build_method()

    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Synthesis Pipeline: {'✅ PASS' if synthesis_ok else '❌ FAIL'}")
    print(f"Build Method: {'✅ PASS' if build_ok else '❌ FAIL'}")

    if synthesis_ok and build_ok:
        print("\n🎉 All tests passed! The AI Project Synthesizer is working.")
        return 0
    else:
        print("\n💥 Some tests failed. Check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
