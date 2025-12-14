"""
Quick end-to-end test of synthesis functionality.
"""

import asyncio
import tempfile
from pathlib import Path
from src.synthesis.project_assembler import ProjectAssembler, AssemblerConfig

async def test_synthesis_e2e():
    """Test synthesis with real API calls."""
    print("Starting end-to-end synthesis test...")
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config = AssemblerConfig(
            base_output_dir=Path(temp_dir),
            create_github_repo=False,  # Skip GitHub for testing
            download_code=False,  # Skip actual downloads for speed
        )
        
        assembler = ProjectAssembler(config)
        
        # Test with a simple idea
        project = await assembler.assemble(
            idea="Simple Python calculator with basic operations",
            name="Test Calculator"
        )
        
        # Verify project was created
        assert project.name == "Test Calculator"
        assert project.base_path.exists()
        
        # Check generated files
        assert (project.base_path / "README.md").exists()
        assert (project.base_path / ".gitignore").exists()
        
        # Check README content
        readme = (project.base_path / "README.md").read_text(encoding="utf-8")
        assert "Test Calculator" in readme
        
        print(f"✅ Project created at: {project.base_path}")
        print(f"✅ README generated with {len(readme)} characters")
        print(f"✅ Ready for Windsurf: {project.ready_for_windsurf}")
        
        return True

if __name__ == "__main__":
    asyncio.run(test_synthesis_e2e())
    print("\n✅ End-to-end test passed!")
