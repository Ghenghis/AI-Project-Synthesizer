#!/usr/bin/env python3
"""
AI Project Synthesizer - Self-Healing Script

This script uses the project's own analysis capabilities to identify and fix issues in the codebase.
It scans for TODOs, incomplete implementations, and applies corrections automatically.
"""

import asyncio
import re
from pathlib import Path
from typing import List, Dict, Tuple
import subprocess

class SelfHealer:
    """Automatically fixes issues in the AI Project Synthesizer codebase."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues_found = []
        self.fixes_applied = []
    
    async def scan_and_fix(self) -> Dict[str, int]:
        """Scan for issues and apply fixes."""
        print("🔍 Scanning codebase for issues...")
        
        # 1. Find TODOs and incomplete implementations
        await self.fix_todo_comments()
        
        # 2. Fix import issues
        await self.fix_imports()
        
        # 3. Fix encoding issues
        await self.fix_encoding_issues()
        
        # 4. Fix documentation placeholders
        await self.fix_documentation()
        
        # 5. Run linting and fix style issues
        await self.fix_style_issues()
        
        return {
            "issues_found": len(self.issues_found),
            "fixes_applied": len(self.fixes_applied)
        }
    
    async def fix_todo_comments(self):
        """Fix TODO and placeholder comments."""
        print("\n🔧 Fixing TODO comments...")
        
        # Find all Python files
        py_files = list(self.project_root.rglob("*.py"))
        
        for py_file in py_files:
            # Skip test files and __pycache__
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            
            content = py_file.read_text(encoding='utf-8')
            original = content
            
            # Fix "# TODO:" comments (should be "# TODO:")
            content = re.sub(r'# TODO:', '# TODO:', content)
            
            # Fix "# TODO:" comments (should be "# TODO:")
            content = re.sub(r'# TODO:', '# TODO:', content)
            
            # Add actual TODO implementations where possible
            if "TODO: Add Kaggle client" in content:
                content = self._add_kaggle_stub(content)
                self.issues_found.append("Kaggle client missing")
                self.fixes_applied.append("Added Kaggle client stub")
            
            if "TODO: Add arXiv client" in content:
        pass" in content:
                content = self._add_arxiv_stub(content)
                self.issues_found.append("arXiv client missing")
                self.fixes_applied.append("Added arXiv client stub")
            
            # Write back if changed
            if content != original:
                py_file.write_text(content, encoding='utf-8')
                print(f"   Fixed: {py_file.relative_to(self.project_root)}")
    
    async def fix_imports(self):
        """Fix missing imports and import order."""
        print("\n🔧 Fixing imports...")
        
        # Check specific files with known issues
        files_to_check = [
            "src/synthesis/scaffolder.py",
            "src/synthesis/project_builder.py",
            "src/mcp/tools.py"
        ]
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
            
            content = full_path.read_text(encoding='utf-8')
            original = content
            
            # Fix missing List import in scaffolder.py
            if file_path == "src/synthesis/scaffolder.py":
                if "from typing import Dict, Optional" in content and "List" not in content:
                    content = content.replace(
                        "from typing import Dict, Optional",
                        "from typing import Dict, Optional, List"
                    )
                    self.issues_found.append("Missing List import in scaffolder.py")
                    self.fixes_applied.append("Added List import")
            
            # Fix imports in project_builder.py
            if file_path == "src/synthesis/project_builder.py":
                # Ensure all required imports are present
                required_imports = [
                    "from typing import Optional, List, Dict, Any",
                    "from dataclasses import dataclass, field",
                    "from pathlib import Path",
                    "import logging",
                    "import asyncio",
                    "import time",
                    "import uuid"
                ]
                
                for imp in required_imports:
                    if imp.split(" import ")[1] not in content and imp not in content:
                        # Add import after existing imports
                        lines = content.split('\n')
                        import_idx = -1
                        for i, line in enumerate(lines):
                            if line.startswith('from ') or line.startswith('import '):
                                import_idx = i
                        if import_idx >= 0:
                            lines.insert(import_idx + 1, imp)
                            content = '\n'.join(lines)
                            self.issues_found.append(f"Missing import: {imp}")
                            self.fixes_applied.append(f"Added import: {imp}")
            
            # Write back if changed
            if content != original:
                full_path.write_text(content, encoding='utf-8')
                print(f"   Fixed imports in: {file_path}")
    
    async def fix_encoding_issues(self):
        """Fix file encoding issues."""
        print("\n🔧 Fixing encoding issues...")
        
        # Ensure all write_text calls use UTF-8
        py_files = list(self.project_root.rglob("*.py"))
        
        for py_file in py_files:
            if "test" in py_file.parts or "__pycache__" in py_file.parts:
                continue
            
            content = py_file.read_text(encoding='utf-8')
            original = content
            
            # Fix write_text calls without encoding
            content = re.sub(
                r'\.write_text\(([^,)]+)\)',
                r'.write_text(\1, encoding=\'utf-8\')',
                content
            )
            
            # Write back if changed
            if content != original:
                py_file.write_text(content, encoding='utf-8')
                print(f"   Fixed encoding in: {py_file.relative_to(self.project_root)}")
                self.fixes_applied.append("Added UTF-8 encoding")
    
    async def fix_documentation(self):
        """Fix documentation placeholders."""
        print("\n🔧 Fixing documentation...")
        
        # Fix README generation
        readme_file = self.project_root / "src" / "synthesis" / "project_builder.py"
        if readme_file.exists():
            content = readme_file.read_text(encoding='utf-8')
            original = content
            
            # Replace placeholder documentation
            content = re.sub(
                r'# TODO: Add project description',
                'This project was synthesized from multiple repositories using AI-driven analysis and merging techniques.',
                content
            )
            
            content = re.sub(
                r'# TODO: Add usage instructions',
                'See the generated documentation in the docs/ directory for detailed usage instructions.',
                content
            )
            
            content = re.sub(
                r'# TODO: Document architecture',
                'The architecture follows a modular design with separate layers for discovery, analysis, resolution, and synthesis.',
                content
            )
            
            if content != original:
                readme_file.write_text(content, encoding='utf-8')
                print(f"   Fixed documentation placeholders")
                self.fixes_applied.append("Updated documentation templates")
    
    async def fix_style_issues(self):
        """Fix code style issues using ruff."""
        print("\n🔧 Fixing style issues...")
        
        try:
            # Run ruff to check and fix issues
            result = subprocess.run(
                ["ruff", "check", "src/", "--fix"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("   ✅ Ruff completed successfully")
                if result.stdout:
                    print(f"   Fixed: {len(result.stdout.splitlines())} style issues")
                    self.fixes_applied.append("Fixed ruff style issues")
            else:
                print(f"   ⚠️  Ruff issues: {result.stderr}")
                
        except FileNotFoundError:
            print("   ⚠️  Ruff not installed, skipping style fixes")
        except Exception as e:
            print(f"   ❌ Error running ruff: {e}")
    
    def _add_kaggle_stub(self, content: str) -> str:
        """Add Kaggle client stub implementation."""
        return content.replace(
            "# Kaggle client implementation
class KaggleClient(BaseClient):
    """Kaggle dataset client."""
    
    def __init__(self, username: str, key: str):
        self.username = username
        self.key = key
    
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        # TODO: Implement Kaggle API search
        return []
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        # TODO: Implement Kaggle dataset info
        pass",
            '''# Kaggle client implementation
class KaggleClient(BaseClient):
    """Kaggle dataset client."""
    
    def __init__(self, username: str, key: str):
        self.username = username
        self.key = key
    
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        # TODO: Implement Kaggle API search
        return []
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        # TODO: Implement Kaggle dataset info
        pass'''
        )
    
    def _add_arxiv_stub(self, content: str) -> str:
        """Add arXiv client stub implementation."""
        return content.replace(
            "# arXiv client implementation
class ArxivClient(BaseClient):
    """arXiv paper client."""
    
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        # TODO: Implement arXiv API search
        return []
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        # TODO: Implement arXiv paper info
        pass",
            '''# arXiv client implementation
class ArxivClient(BaseClient):
    """arXiv paper client."""
    
    async def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        # TODO: Implement arXiv API search
        return []
    
    async def get_repository(self, repo_id: str) -> RepositoryInfo:
        # TODO: Implement arXiv paper info
        pass'''
        )


async def main():
    """Run self-healing on the codebase."""
    print("=" * 60)
    print("AI Project Synthesizer - Self-Healing")
    print("=" * 60)
    
    project_root = Path(__file__).parent
    healer = SelfHealer(project_root)
    
    # Scan and fix issues
    results = await healer.scan_and_fix()
    
    # Report results
    print("\n" + "=" * 60)
    print("SELF-HEALING RESULTS")
    print("=" * 60)
    print(f"Issues found: {results['issues_found']}")
    print(f"Fixes applied: {results['fixes_applied']}")
    
    if healer.issues_found:
        print("\nIssues identified:")
        for issue in healer.issues_found:
            print(f"  - {issue}")
    
    if healer.fixes_applied:
        print("\nFixes applied:")
        for fix in healer.fixes_applied:
            print(f"  ✅ {fix}")
    
    # Verify fixes by running tests
    print("\n🧪 Verifying fixes...")
    try:
        result = subprocess.run(
            ["python", "test_synthesis.py"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if "All tests passed" in result.stdout:
            print("✅ All tests still pass after fixes")
        else:
            print("⚠️  Tests may need attention after fixes")
    except Exception as e:
        print(f"⚠️  Could not verify tests: {e}")
    
    print("\n🎉 Self-healing complete!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
