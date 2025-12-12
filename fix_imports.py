"""
Script to fix all import errors from get_config to get_settings
"""

import os
from pathlib import Path

# List of files to fix
files_to_fix = [
    "src/vibe/architect_agent.py",
    "src/vibe/context_injector.py",
    "src/vibe/auto_rollback.py",
    "src/vibe/context_manager.py",
    "src/vibe/explain_mode.py",
    "src/vibe/project_classifier.py",
    "src/vibe/auto_commit.py",
    "src/vibe/prompt_enhancer.py",
    "src/vibe/rules_engine.py",
    "src/vibe/task_decomposer.py",
    "src/quality/dependency_scanner.py",
    "src/quality/lint_checker.py",
    "src/quality/quality_gate.py",
    "src/quality/security_scanner.py",
    "src/quality/review_agent.py",
    "src/quality/test_generator.py",
]

def fix_imports():
    """Fix import statements in all files"""
    base_path = Path(__file__).parent
    
    for file_path in files_to_fix:
        full_path = base_path / file_path
        
        if not full_path.exists():
            print(f"File not found: {full_path}")
            continue
            
        # Read file
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace import
        old_import = "from src.core.config import get_config"
        new_import = "from src.core.config import get_settings"
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            
            # Also replace get_config() calls with get_settings()
            content = content.replace("get_config()", "get_settings()")
            
            # Write back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"Fixed: {file_path}")
        else:
            print(f"No changes needed: {file_path}")

if __name__ == "__main__":
    fix_imports()
    print("\nImport fix complete!")
