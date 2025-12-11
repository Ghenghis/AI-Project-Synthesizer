#!/usr/bin/env python3
"""
Validate documentation links and version consistency.

This script checks:
1. All doc links in README.md point to existing files
2. Version is consistent across all files
3. URLs in pyproject.toml are correct
"""

import re
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get project root directory."""
    return Path(__file__).parent.parent


def check_doc_links() -> list[str]:
    """Check all documentation links in README.md exist."""
    errors = []
    root = get_project_root()
    readme = root / "README.md"
    
    if not readme.exists():
        errors.append("README.md not found")
        return errors
    
    content = readme.read_text(encoding="utf-8")
    
    # Find all markdown links to docs
    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    links = re.findall(link_pattern, content)
    
    for text, url in links:
        # Skip external URLs
        if url.startswith(('http://', 'https://', '#')):
            continue
        
        # Check if file exists
        target = root / url
        if not target.exists():
            errors.append(f"Broken link: [{text}]({url}) - file not found")
    
    return errors


def check_version_consistency() -> list[str]:
    """Check version is consistent across all files."""
    errors = []
    root = get_project_root()
    
    versions = {}
    
    # Check pyproject.toml
    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8")
        match = re.search(r'version\s*=\s*"([^"]+)"', content)
        if match:
            versions["pyproject.toml"] = match.group(1)
    
    # Check src/core/version.py
    version_py = root / "src" / "core" / "version.py"
    if version_py.exists():
        content = version_py.read_text(encoding="utf-8")
        match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
        if match:
            versions["src/core/version.py"] = match.group(1)
    
    # Check README.md
    readme = root / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8")
        match = re.search(r'Version[:\s]+(\d+\.\d+\.\d+)', content)
        if match:
            versions["README.md"] = match.group(1)
    
    # Check PROJECT_STATUS.md
    status = root / "PROJECT_STATUS.md"
    if status.exists():
        content = status.read_text(encoding="utf-8")
        match = re.search(r'Version[:\s|]+(\d+\.\d+\.\d+)', content)
        if match:
            versions["PROJECT_STATUS.md"] = match.group(1)
    
    # Check CHANGELOG.md
    changelog = root / "CHANGELOG.md"
    if changelog.exists():
        content = changelog.read_text(encoding="utf-8")
        match = re.search(r'## \[(\d+\.\d+\.\d+)\]', content)
        if match:
            versions["CHANGELOG.md (latest)"] = match.group(1)
    
    # Compare versions
    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        errors.append(f"Version mismatch detected:")
        for file, version in versions.items():
            errors.append(f"  - {file}: {version}")
    
    return errors


def check_urls() -> list[str]:
    """Check URLs in pyproject.toml are correct."""
    errors = []
    root = get_project_root()
    
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return errors
    
    content = pyproject.read_text(encoding="utf-8")
    
    # Check for placeholder URLs
    if "yourusername" in content:
        errors.append("pyproject.toml contains placeholder 'yourusername' in URLs")
    
    if "example.com" in content:
        errors.append("pyproject.toml contains placeholder 'example.com' in email")
    
    return errors


def check_required_files() -> list[str]:
    """Check required documentation files exist."""
    errors = []
    root = get_project_root()
    
    required_files = [
        "README.md",
        "CHANGELOG.md",
        "FEATURES.md",
        "LICENSE",
        "docs/API_REFERENCE.md",
        "docs/architecture/ARCHITECTURE.md",
        "docs/diagrams/DIAGRAMS.md",
        "docs/guides/QUICK_START.md",
        "docs/guides/USER_GUIDE.md",
        "docs/guides/CONFIGURATION.md",
        "docs/guides/CLI_REFERENCE.md",
        "docs/guides/TROUBLESHOOTING.md",
    ]
    
    for file in required_files:
        path = root / file
        if not path.exists():
            errors.append(f"Required file missing: {file}")
        elif path.stat().st_size == 0:
            errors.append(f"Required file is empty: {file}")
    
    return errors


def main():
    """Run all validation checks."""
    print("=" * 60)
    print("Documentation Validation")
    print("=" * 60)
    
    all_errors = []
    
    # Check doc links
    print("\n📄 Checking documentation links...")
    errors = check_doc_links()
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All documentation links valid")
    
    # Check version consistency
    print("\n🔢 Checking version consistency...")
    errors = check_version_consistency()
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ Version consistent across all files")
    
    # Check URLs
    print("\n🔗 Checking URLs...")
    errors = check_urls()
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All URLs valid")
    
    # Check required files
    print("\n📁 Checking required files...")
    errors = check_required_files()
    if errors:
        all_errors.extend(errors)
        for e in errors:
            print(f"  ❌ {e}")
    else:
        print("  ✅ All required files present")
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ Validation FAILED - {len(all_errors)} issue(s) found")
        sys.exit(1)
    else:
        print("✅ Validation PASSED - All checks passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
