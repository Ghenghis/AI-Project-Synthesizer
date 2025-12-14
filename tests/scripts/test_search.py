"""Test the search functionality."""

import asyncio

from src.discovery.unified_search import create_unified_search


async def test():
    s = create_unified_search()
    print("Available platforms:", s.available_platforms)

    # Test GitHub search
    print("\n=== GitHub Search ===")
    r = await s.search("machine learning python", platforms=["github"], max_results=5)
    print(f"Results: {len(r.repositories)}")
    print(f"Errors: {r.errors}")
    for repo in r.repositories[:5]:
        print(f"  - {repo.full_name}: {repo.stars} stars")

    # Test HuggingFace search
    print("\n=== HuggingFace Search ===")
    r = await s.search("text generation", platforms=["huggingface"], max_results=5)
    print(f"Results: {len(r.repositories)}")
    print(f"Errors: {r.errors}")
    for repo in r.repositories[:5]:
        print(f"  - {repo.full_name}: {repo.stars} likes")

    # Test Kaggle search
    print("\n=== Kaggle Search (Datasets) ===")
    r = await s.search("machine learning", platforms=["kaggle"], max_results=5)
    print(f"Results: {len(r.repositories)}")
    print(f"Errors: {r.errors}")
    for repo in r.repositories[:5]:
        print(f"  - {repo.full_name}: {repo.stars} votes, {repo.watchers} downloads")


if __name__ == "__main__":
    asyncio.run(test())
