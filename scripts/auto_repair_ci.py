#!/usr/bin/env python3
"""
AI Project Synthesizer - CI Auto-Repair Script

Automatically detects and fixes common CI/CD issues:
- Import errors
- Linting violations
- Type errors
- Missing dependencies
- Configuration issues

Usage:
    python scripts/auto_repair_ci.py [--fix] [--check] [--report]
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Issue:
    """Detected issue."""
    category: str
    file: str
    line: int | None
    message: str
    fix_available: bool = False
    fix_command: str | None = None


@dataclass
class RepairReport:
    """Report of repair operations."""
    issues_found: list[Issue] = field(default_factory=list)
    issues_fixed: list[Issue] = field(default_factory=list)
    issues_remaining: list[Issue] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": {
                "found": len(self.issues_found),
                "fixed": len(self.issues_fixed),
                "remaining": len(self.issues_remaining),
            },
            "issues_fixed": [
                {"category": i.category, "file": i.file, "message": i.message}
                for i in self.issues_fixed
            ],
            "issues_remaining": [
                {"category": i.category, "file": i.file, "message": i.message}
                for i in self.issues_remaining
            ],
        }


class CIAutoRepair:
    """Automated CI repair system."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.report = RepairReport()
    
    def run_command(self, cmd: list[str], capture: bool = True) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=capture,
                text=True,
                timeout=300
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def detect_lint_issues(self) -> list[Issue]:
        """Detect linting issues using ruff."""
        issues = []
        code, stdout, stderr = self.run_command([
            "ruff", "check", "src/", "tests/", "--output-format=json"
        ])
        
        if stdout:
            try:
                violations = json.loads(stdout)
                for v in violations:
                    issues.append(Issue(
                        category="lint",
                        file=v.get("filename", ""),
                        line=v.get("location", {}).get("row"),
                        message=f"{v.get('code')}: {v.get('message')}",
                        fix_available=v.get("fix") is not None,
                        fix_command="ruff check --fix"
                    ))
            except json.JSONDecodeError:
                pass
        
        return issues
    
    def detect_import_issues(self) -> list[Issue]:
        """Detect import issues by running pytest collection."""
        issues = []
        code, stdout, stderr = self.run_command([
            "python", "-m", "pytest", "--collect-only", "-q"
        ])
        
        # Parse import errors from stderr
        import_error_pattern = r"ImportError: (.+)"
        module_not_found_pattern = r"ModuleNotFoundError: No module named '([^']+)'"
        
        for match in re.finditer(import_error_pattern, stderr):
            issues.append(Issue(
                category="import",
                file="",
                line=None,
                message=match.group(1),
                fix_available=False
            ))
        
        for match in re.finditer(module_not_found_pattern, stderr):
            module = match.group(1)
            issues.append(Issue(
                category="import",
                file="",
                line=None,
                message=f"Missing module: {module}",
                fix_available=True,
                fix_command=f"pip install {module}"
            ))
        
        return issues
    
    def detect_type_issues(self) -> list[Issue]:
        """Detect type issues using mypy."""
        issues = []
        code, stdout, stderr = self.run_command([
            "mypy", "src/", "--ignore-missing-imports", "--no-error-summary"
        ])
        
        # Parse mypy output
        error_pattern = r"([^:]+):(\d+): error: (.+)"
        for match in re.finditer(error_pattern, stdout):
            issues.append(Issue(
                category="type",
                file=match.group(1),
                line=int(match.group(2)),
                message=match.group(3),
                fix_available=False
            ))
        
        return issues
    
    def fix_lint_issues(self) -> int:
        """Auto-fix linting issues."""
        print("🔧 Running ruff --fix...")
        code, _, _ = self.run_command([
            "ruff", "check", "src/", "tests/", "--fix", "--unsafe-fixes"
        ])
        
        print("🔧 Running ruff format...")
        self.run_command(["ruff", "format", "src/", "tests/"])
        
        print("🔧 Running isort...")
        self.run_command(["isort", "src/", "tests/", "--profile", "black"])
        
        return code
    
    def fix_import_issues(self, issues: list[Issue]) -> int:
        """Attempt to fix import issues."""
        fixed = 0
        for issue in issues:
            if issue.fix_command and issue.category == "import":
                print(f"🔧 Fixing: {issue.message}")
                code, _, _ = self.run_command(issue.fix_command.split())
                if code == 0:
                    fixed += 1
                    self.report.issues_fixed.append(issue)
                else:
                    self.report.issues_remaining.append(issue)
        return fixed
    
    def add_missing_init_files(self) -> int:
        """Add missing __init__.py files to test directories."""
        added = 0
        for test_dir in (self.project_root / "tests").rglob("*"):
            if test_dir.is_dir() and not test_dir.name.startswith("__"):
                init_file = test_dir / "__init__.py"
                if not init_file.exists():
                    init_file.write_text('"""Test package."""\n')
                    print(f"✅ Created: {init_file.relative_to(self.project_root)}")
                    added += 1
        return added
    
    def check_and_fix_conftest(self) -> bool:
        """Ensure conftest.py has proper path setup."""
        conftest = self.project_root / "tests" / "conftest.py"
        if not conftest.exists():
            return False
        
        content = conftest.read_text()
        
        # Check if sys.path setup exists
        if "sys.path.insert" not in content:
            # Add path setup
            path_setup = '''
import sys
from pathlib import Path

# Ensure project root is in path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))
'''
            # Insert after imports
            lines = content.split('\n')
            insert_pos = 0
            for i, line in enumerate(lines):
                if line.startswith('import') or line.startswith('from'):
                    insert_pos = i + 1
                elif insert_pos > 0 and not line.strip():
                    break
            
            lines.insert(insert_pos, path_setup)
            conftest.write_text('\n'.join(lines))
            print("✅ Added path setup to conftest.py")
            return True
        
        return False
    
    def run_checks(self) -> RepairReport:
        """Run all checks and return report."""
        print("=" * 60)
        print("🔍 AI Project Synthesizer - CI Auto-Repair")
        print("=" * 60)
        
        # Detect issues
        print("\n📋 Detecting issues...")
        
        lint_issues = self.detect_lint_issues()
        print(f"  - Lint issues: {len(lint_issues)}")
        self.report.issues_found.extend(lint_issues)
        
        import_issues = self.detect_import_issues()
        print(f"  - Import issues: {len(import_issues)}")
        self.report.issues_found.extend(import_issues)
        
        type_issues = self.detect_type_issues()
        print(f"  - Type issues: {len(type_issues)}")
        self.report.issues_found.extend(type_issues)
        
        print(f"\n📊 Total issues found: {len(self.report.issues_found)}")
        
        return self.report
    
    def run_fixes(self) -> RepairReport:
        """Run all auto-fixes."""
        print("\n🔧 Applying auto-fixes...")
        
        # Fix lint issues
        self.fix_lint_issues()
        
        # Add missing __init__.py files
        init_added = self.add_missing_init_files()
        if init_added:
            print(f"  - Added {init_added} __init__.py files")
        
        # Fix conftest
        if self.check_and_fix_conftest():
            print("  - Fixed conftest.py path setup")
        
        # Re-check to see what's fixed
        print("\n🔍 Re-checking after fixes...")
        remaining_lint = self.detect_lint_issues()
        remaining_import = self.detect_import_issues()
        
        # Calculate fixed vs remaining
        fixed_count = len(self.report.issues_found) - len(remaining_lint) - len(remaining_import)
        print(f"\n✅ Fixed: {fixed_count} issues")
        print(f"⚠️  Remaining: {len(remaining_lint) + len(remaining_import)} issues")
        
        self.report.issues_remaining = remaining_lint + remaining_import
        
        return self.report
    
    def generate_github_summary(self) -> str:
        """Generate GitHub Actions summary markdown."""
        report = self.report.to_dict()
        
        md = f"""## 🤖 CI Auto-Repair Report

### Summary
| Metric | Count |
|--------|-------|
| Issues Found | {report['summary']['found']} |
| Issues Fixed | {report['summary']['fixed']} |
| Issues Remaining | {report['summary']['remaining']} |

"""
        if report['issues_fixed']:
            md += "### ✅ Fixed Issues\n"
            for issue in report['issues_fixed'][:10]:
                md += f"- **{issue['category']}**: {issue['message'][:80]}\n"
            if len(report['issues_fixed']) > 10:
                md += f"- ... and {len(report['issues_fixed']) - 10} more\n"
        
        if report['issues_remaining']:
            md += "\n### ⚠️ Remaining Issues (Manual Fix Required)\n"
            for issue in report['issues_remaining'][:10]:
                md += f"- **{issue['category']}** in `{issue['file']}`: {issue['message'][:60]}\n"
            if len(report['issues_remaining']) > 10:
                md += f"- ... and {len(report['issues_remaining']) - 10} more\n"
        
        return md


def main():
    parser = argparse.ArgumentParser(description="CI Auto-Repair Script")
    parser.add_argument("--fix", action="store_true", help="Apply auto-fixes")
    parser.add_argument("--check", action="store_true", help="Only check, don't fix")
    parser.add_argument("--report", action="store_true", help="Generate JSON report")
    parser.add_argument("--github-summary", action="store_true", help="Output GitHub summary")
    args = parser.parse_args()
    
    # Find project root
    project_root = Path(__file__).parent.parent
    
    repair = CIAutoRepair(project_root)
    
    if args.check or not args.fix:
        report = repair.run_checks()
    
    if args.fix:
        report = repair.run_fixes()
    
    if args.report:
        print("\n📄 JSON Report:")
        print(json.dumps(report.to_dict(), indent=2))
    
    if args.github_summary:
        summary = repair.generate_github_summary()
        # Write to GitHub step summary if available
        import os
        summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_file:
            with open(summary_file, "a") as f:
                f.write(summary)
        else:
            print(summary)
    
    # Exit with error if issues remain
    if report.issues_remaining:
        sys.exit(1)
    
    print("\n✅ All checks passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()
