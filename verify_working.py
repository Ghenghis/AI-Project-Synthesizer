#!/usr/bin/env python3
"""
Verify AI Project Synthesizer is ACTUALLY working.
This test checks if the system can really clone and extract from GitHub.
"""

import os
import asyncio
import tempfile
from pathlib import Path

from src.discovery.unified_search import UnifiedSearch
from src.synthesis.project_builder import ProjectBuilder, SynthesisRequest, ExtractionSpec


async def verify_github_client():
    """Verify GitHub client can actually connect."""
    print("🔍 Verifying GitHub client...")
    
    search = UnifiedSearch()
    
    # Check if GitHub client is initialized
    github_client = search._clients.get("github")
    
    if not github_client:
        print("❌ GitHub client NOT initialized")
        print("   Check your GITHUB_TOKEN in .env file")
        return False
    
    print("✅ GitHub client initialized")
    
    # Test a simple search
    try:
        result = await search.search(
            query="hello world",
            platforms=["github"],
            max_results=1
        )
        
        if result.repositories:
            print(f"✅ GitHub search working: found {len(result.repositories)} repos")
            return True
        else:
            print("⚠️  GitHub search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ GitHub search failed: {e}")
        return False


async def verify_actual_cloning():
    """Verify we can actually clone a repository."""
    print("\n🔍 Verifying repository cloning...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_path = Path(temp_dir) / "test_clone"
        output_path.mkdir()
        
        # Use a very small, simple public repo
        request = SynthesisRequest(
            project_name="clone-test",
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
            generate_docs=False,  # Skip docs to focus on cloning
        )
        
        builder = ProjectBuilder()
        
        try:
            result = await builder.synthesize(request)
            
            # Check if README.md was actually extracted
            readme_path = output_path / "src" / "README.md"
            
            if readme_path.exists():
                content = readme_path.read_text(encoding='utf-8')
                if len(content) > 10:  # Should have actual content
                    print(f"✅ Repository cloned successfully")
                    print(f"   README.md size: {len(content)} bytes")
                    print(f"   First 100 chars: {content[:100]}...")
                    return True
                else:
                    print("❌ README.md exists but appears empty")
                    return False
            else:
                print("❌ README.md was not extracted")
                print(f"   Expected at: {readme_path}")
                
                # Show what was actually created
                print("\n📁 Files created:")
                for file_path in output_path.rglob("*"):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(output_path)
                        size = file_path.stat().st_size
                        print(f"   {rel_path} ({size} bytes)")
                
                return False
                
        except Exception as e:
            print(f"❌ Synthesis failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def verify_mcp_tools():
    """Verify MCP tools can be imported and listed."""
    print("\n🔍 Verifying MCP server...")
    
    try:
        from src.mcp_server.server import server
        
        # List tools
        tools = await server.list_tools()
        
        print(f"✅ MCP server has {len(tools)} tools:")
        for tool in tools:
            print(f"   - {tool.name}: {tool.description[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ MCP server error: {e}")
        return False


async def main():
    """Run all verification checks."""
    print("=" * 60)
    print("AI Project Synthesizer - Working Verification")
    print("=" * 60)
    
    # Check environment
    print("\n📋 Environment Check:")
    github_token = os.getenv("GITHUB_TOKEN", "")
    if github_token and github_token != "your_github_token_here":
        print(f"✅ GITHUB_TOKEN is set (length: {len(github_token)})")
    else:
        print("❌ GITHUB_TOKEN is not set or is still placeholder")
        print("   Edit .env file and add a real GitHub token")
        return 1
    
    # Run checks
    checks = [
        ("GitHub Client", verify_github_client()),
        ("Repository Cloning", verify_actual_cloning()),
        ("MCP Server", verify_mcp_tools()),
    ]
    
    results = []
    for name, check in checks:
        try:
            result = await check
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION RESULTS")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All checks passed! The AI Project Synthesizer is working correctly.")
        return 0
    else:
        print("\n💥 Some checks failed. The system needs fixes before it's fully functional.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
