"""Test the MCP tool handler."""
import asyncio
from src.mcp_server.tools import handle_search_repositories

async def test():
    print("Testing MCP search_repositories tool...")
    
    result = await handle_search_repositories({
        'query': 'machine learning',
        'platforms': ['github'],
        'max_results': 5
    })
    
    if result.get('success'):
        print(f"SUCCESS! Found {len(result['repositories'])} repositories:")
        for repo in result['repositories']:
            print(f"  - {repo['full_name']}: {repo['stars']} stars")
    else:
        print(f"ERROR: {result.get('message')}")

if __name__ == "__main__":
    asyncio.run(test())
