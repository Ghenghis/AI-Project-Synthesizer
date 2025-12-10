#!/usr/bin/env python3
"""
AI Project Synthesizer - Edge Case Testing

Tests error handling and robustness of all MCP tools with invalid inputs.
"""

import asyncio
import tempfile
from pathlib import Path

from src.mcp.tools import (
    handle_search_repositories,
    handle_analyze_repository,
    handle_check_compatibility,
    handle_resolve_dependencies,
    handle_synthesize_project,
    handle_generate_documentation,
    handle_get_synthesis_status,
)


async def test_search_repositories_edge_cases():
    """Test search tool with edge cases."""
    print("\n🧪 Testing search_repositories edge cases...")
    
    tests = [
        # Empty query
        ({}, "Query is required"),
        # Invalid platforms
        ({"query": "test", "platforms": ["invalid"]}, "No platforms available"),
        # Negative max_results
        ({"query": "test", "max_results": -1}, "success"),  # Should handle gracefully
        # Very long query
        ({"query": "x" * 1000}, "success"),  # Should handle gracefully
    ]
    
    passed = 0
    for args, expected in tests:
        try:
            result = await handle_search_repositories(args)
            if expected == "success":
                if not result.get("error"):
                    passed += 1
                    print(f"   ✅ Handled gracefully: {args}")
                else:
                    print(f"   ❌ Unexpected error: {result.get('message')}")
            else:
                if expected in result.get("message", ""):
                    passed += 1
                    print(f"   ✅ Correct error: {expected}")
                else:
                    print(f"   ❌ Expected '{expected}', got: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return passed, len(tests)


async def test_analyze_repository_edge_cases():
    """Test analyze tool with edge cases."""
    print("\n🧪 Testing analyze_repository edge cases...")
    
    tests = [
        # Missing URL
        ({}, "Repository URL is required"),
        # Invalid URL
        ({"repo_url": "invalid-url"}, "Invalid repository URL"),
        # Non-existent GitHub repo
        ({"repo_url": "https://github.com/nonexistent/repo"}, "success"),  # Should fail gracefully
        # Empty components list
        ({"repo_url": "https://github.com/octocat/Hello-World", "extract_components": False}, "success"),
    ]
    
    passed = 0
    for args, expected in tests:
        try:
            result = await handle_analyze_repository(args)
            if expected == "success":
                if not result.get("error"):
                    passed += 1
                    print(f"   ✅ Handled gracefully: {args.get('repo_url', 'no URL')}")
                else:
                    print(f"   ❌ Unexpected error: {result.get('message')}")
            else:
                if expected in result.get("message", ""):
                    passed += 1
                    print(f"   ✅ Correct error: {expected}")
                else:
                    print(f"   ❌ Expected '{expected}', got: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return passed, len(tests)


async def test_synthesize_project_edge_cases():
    """Test synthesis tool with edge cases."""
    print("\n🧪 Testing synthesize_project edge cases...")
    
    tests = [
        # Missing repos
        ({}, "At least one repository is required"),
        # Empty repos list
        ({"repositories": [], "project_name": "test", "output_path": "/tmp"}, "At least one repository is required"),
        # Missing project name
        ({"repositories": [{"repo_url": "https://github.com/octocat/Hello-World"}]}, "Project name is required"),
        # Invalid URL
        ({"repositories": [{"repo_url": "invalid"}], "project_name": "test", "output_path": "/tmp"}, "Invalid repository URL"),
        # Valid but non-existent repo
        ({"repositories": [{"repo_url": "https://github.com/nonexistent/repo"}], "project_name": "test", "output_path": "/tmp"}, "success"),  # Should fail gracefully
    ]
    
    passed = 0
    for args, expected in tests:
        try:
            result = await handle_synthesize_project(args)
            if expected == "success":
                # Should either succeed or fail with proper error, not crash
                if "error" in result or "status" in result:
                    passed += 1
                    print(f"   ✅ Handled gracefully: {args.get('repositories', [{}])[0].get('repo_url', 'no URL')}")
                else:
                    print(f"   ❌ Unexpected response: {result}")
            else:
                if expected in result.get("message", ""):
                    passed += 1
                    print(f"   ✅ Correct error: {expected}")
                else:
                    print(f"   ❌ Expected '{expected}', got: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return passed, len(tests)


async def test_documentation_edge_cases():
    """Test documentation generation with edge cases."""
    print("\n🧪 Testing generate_documentation edge cases...")
    
    tests = [
        # Missing path
        ({}, "Project path is required"),
        # Invalid path
        ({"project_path": "/nonexistent/path"}, "success"),  # Should fail gracefully
        # Valid path with no project
        ({"project_path": "/tmp"}, "success"),  # Should handle gracefully
    ]
    
    passed = 0
    for args, expected in tests:
        try:
            result = await handle_generate_documentation(args)
            if expected == "success":
                # Should either succeed or fail with proper error
                if "error" in result or "status" in result or "documentation" in result:
                    passed += 1
                    print(f"   ✅ Handled gracefully: {args.get('project_path', 'no path')}")
                else:
                    print(f"   ❌ Unexpected response: {result}")
            else:
                if expected in result.get("message", ""):
                    passed += 1
                    print(f"   ✅ Correct error: {expected}")
                else:
                    print(f"   ❌ Expected '{expected}', got: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return passed, len(tests)


async def test_status_edge_cases():
    """Test status checking with edge cases."""
    print("\n🧪 Testing get_synthesis_status edge cases...")
    
    tests = [
        # Missing ID
        ({}, "Synthesis ID is required"),
        # Invalid ID (non-existent)
        ({"synthesis_id": "invalid-id"}, "success"),  # Should return not found
        # Valid UUID format
        ({"synthesis_id": "00000000-0000-0000-0000-000000000000"}, "success"),
    ]
    
    passed = 0
    for args, expected in tests:
        try:
            result = await handle_get_synthesis_status(args)
            if expected == "success":
                # Should either return status or error, not crash
                if "status" in result or "error" in result:
                    passed += 1
                    print(f"   ✅ Handled gracefully")
                else:
                    print(f"   ❌ Unexpected response: {result}")
            else:
                if expected in result.get("message", ""):
                    passed += 1
                    print(f"   ✅ Correct error: {expected}")
                else:
                    print(f"   ❌ Expected '{expected}', got: {result.get('message')}")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    return passed, len(tests)


async def main():
    """Run all edge case tests."""
    print("=" * 60)
    print("AI Project Synthesizer - Edge Case Testing")
    print("=" * 60)
    
    test_results = []
    
    # Run all tests
    test_results.append(await test_search_repositories_edge_cases())
    test_results.append(await test_analyze_repository_edge_cases())
    test_results.append(await test_synthesize_project_edge_cases())
    test_results.append(await test_documentation_edge_cases())
    test_results.append(await test_status_edge_cases())
    
    # Summary
    print("\n" + "=" * 60)
    print("EDGE CASE TEST RESULTS")
    print("=" * 60)
    
    total_passed = sum(result[0] for result in test_results)
    total_tests = sum(result[1] for result in test_results)
    
    print(f"Overall: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n✅ All edge cases handled correctly!")
        print("The system is robust against invalid inputs.")
        return 0
    else:
        print(f"\n⚠️  {total_tests - total_passed} edge cases need attention.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
