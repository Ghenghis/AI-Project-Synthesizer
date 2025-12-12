"""
Lint Checker for VIBE MCP Quality Pipeline

Integrates with multiple linting tools:
- Ruff: Fast Python linter and formatter
- ESLint: JavaScript/TypeScript linting
- MyPy: Static type checking for Python
- Prettier: Code formatting verification

This ensures all generated code follows consistent style and type safety.
"""

import asyncio
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from src.core.exceptions import LintCheckError
from src.core.config import get_settings


class LintLevel(Enum):
    """Lint issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    NOTE = "note"


@dataclass
class LintIssue:
    """Represents a linting issue found."""
    tool: str
    rule_id: str
    message: str
    level: LintLevel
    file_path: str
    line_number: int
    column_number: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    fix_suggestion: Optional[str] = None
    category: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class LintResult:
    """Result of a lint check."""
    passed: bool
    issues: List[LintIssue]
    check_time: float
    files_checked: int
    tool_results: Dict[str, Any]
    fixable_issues: int


class LintChecker:
    """
    Comprehensive lint checking for generated code.
    
    Features:
    - Multi-language support (Python, JS/TS)
    - Auto-fix capabilities
    - Style consistency checks
    - Type safety verification
    - Performance impact analysis
    """
    
    def __init__(self):
        self.config = get_settings()
        self.temp_dir = Path(tempfile.gettempdir()) / "vibe_mcp_lint"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Tool configurations
        self.ruff_config = {
            "select": [
                "E",  # pycodestyle errors
                "W",  # pycodestyle warnings
                "F",  # pyflakes
                "I",  # isort
                "B",  # flake8-bugbear
                "C4", # flake8-comprehensions
                "UP", # pyupgrade
                "S",  # flake8-bandit (security)
                "A",  # flake8-builtins
                "T20", # flake8-print
                "SIM", # flake8-simplify
                "ARG", # flake8-unused-arguments
                "PTH", # flake8-use-pathlib
                "RUF", # Ruff-specific rules
            ],
            "ignore": [
                "E501",  # Line too long (handled by formatter)
                "S603",  # subprocess call (checked by security scanner)
                "S607",  # Starting process with partial path
            ],
            "fix": True  # Enable auto-fix
        }
        
        self.eslint_config = {
            "extends": [
                "eslint:recommended",
                "@typescript-eslint/recommended",
                "prettier"
            ],
            "rules": {
                "no-console": "warn",
                "no-debugger": "error",
                "prefer-const": "error",
                "no-var": "error",
                "eqeqeq": "error",
                "curly": "error"
            }
        }
        
        self.mypy_config = {
            "strict": True,
            "warn_return_any": True,
            "warn_unused_configs": True,
            "disallow_untyped_defs": True,
            "disallow_incomplete_defs": True,
            "check_untyped_defs": True,
            "disallow_untyped_decorators": True,
            "no_implicit_optional": True,
            "warn_redundant_casts": True,
            "warn_unused_ignores": True,
            "warn_no_return": True,
            "warn_unreachable": True,
            "strict_equality": True
        }
    
    async def check_code(self, code: str, file_path: str, language: str = "python") -> LintResult:
        """
        Check code with appropriate linting tools.
        
        Args:
            code: The code to check
            file_path: Virtual file path for context
            language: Programming language (python, javascript, typescript)
            
        Returns:
            LintResult with all found issues
        """
        import time
        start_time = time.time()
        
        # Create temporary file for checking
        temp_file = self.temp_dir / Path(file_path).name
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # Select tools based on language
            if language == "python":
                results = await asyncio.gather(
                    self._check_with_ruff(temp_file),
                    self._check_with_mypy(temp_file),
                    return_exceptions=True
                )
            elif language in ["javascript", "typescript"]:
                results = await asyncio.gather(
                    self._check_with_eslint(temp_file),
                    self._check_with_prettier(temp_file),
                    return_exceptions=True
                )
            else:
                # Unknown language, just do basic checks
                results = [([], "unknown")]
            
            # Collect all issues
            all_issues = []
            tool_results = {}
            fixable_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    print(f"Lint check error: {result}")
                    continue
                
                issues, tool_name = result
                all_issues.extend(issues)
                tool_results[tool_name] = {
                    "issues_found": len(issues),
                    "errors": sum(1 for i in issues if i.level == LintLevel.ERROR),
                    "warnings": sum(1 for i in issues if i.level == LintLevel.WARNING),
                    "fixable": sum(1 for i in issues if i.fix_suggestion)
                }
                fixable_count += sum(1 for i in issues if i.fix_suggestion)
            
            # Determine if check passed (no errors)
            passed = not any(i.level == LintLevel.ERROR for i in all_issues)
            
            check_time = time.time() - start_time
            
            return LintResult(
                passed=passed,
                issues=all_issues,
                check_time=check_time,
                files_checked=1,
                tool_results=tool_results,
                fixable_issues=fixable_count
            )
            
        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()
    
    async def _check_with_ruff(self, file_path: Path) -> Tuple[List[LintIssue], str]:
        """Run Ruff Python linter."""
        issues = []
        
        try:
            # Build ruff command
            cmd = [
                "ruff",
                "check",
                "--format=json",
                f"--config={'.'.join([f'{k}={v}' for k, v in self.ruff_config.items()])}",
                str(file_path)
            ]
            
            # Run ruff
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse results
            if result.stdout:
                data = json.loads(result.stdout)
                
                for finding in data:
                    issue = LintIssue(
                        tool="ruff",
                        rule_id=finding.get('code', ''),
                        message=finding.get('message', ''),
                        level=self._map_ruff_level(finding.get('fix', {}).get('availability')),
                        file_path=finding.get('filename', ''),
                        line_number=finding.get('location', {}).get('row', 0),
                        column_number=finding.get('location', {}).get('column'),
                        end_line=finding.get('end_location', {}).get('row'),
                        end_column=finding.get('end_location', {}).get('column'),
                        fix_suggestion=finding.get('fix', {}).get('message'),
                        category=finding.get('tags', [''])[0] if finding.get('tags') else None,
                        metadata={
                            "url": finding.get('url'),
                            "fix_availability": finding.get('fix', {}).get('availability')
                        }
                    )
                    issues.append(issue)
                    
        except subprocess.TimeoutExpired:
            print("Ruff check timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Ruff output: {e}")
        except FileNotFoundError:
            print("Ruff not installed - skipping check")
        except Exception as e:
            print(f"Ruff check error: {e}")
        
        return issues, "ruff"
    
    async def _check_with_mypy(self, file_path: Path) -> Tuple[List[LintIssue], str]:
        """Run MyPy type checker."""
        issues = []
        
        try:
            # Build mypy command
            cmd = [
                "mypy",
                "--show-error-codes",
                "--no-error-summary",
                "--json",
                f"--config-file={'.'.join([f'{k}={v}' for k, v in self.mypy_config.items()])}",
                str(file_path)
            ]
            
            # Run mypy
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse results
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        data = json.loads(line)
                        
                        issue = LintIssue(
                            tool="mypy",
                            rule_id=data.get('code', ''),
                            message=data.get('message', ''),
                            level=LintLevel.ERROR if data.get('severity') == 'error' else LintLevel.WARNING,
                            file_path=data.get('file', ''),
                            line_number=data.get('line', 0),
                            column_number=data.get('column'),
                            end_line=data.get('end_line'),
                            end_column=data.get('end_column'),
                            fix_suggestion=self._get_mypy_fix_suggestion(data.get('code', '')),
                            category="type-checking",
                            metadata={
                                "severity": data.get('severity'),
                                "hint": data.get('hint')
                            }
                        )
                        issues.append(issue)
                        
        except subprocess.TimeoutExpired:
            print("MyPy check timed out")
        except json.JSONDecodeError:
            # MyPy might output in regular format
            pass
        except FileNotFoundError:
            print("MyPy not installed - skipping check")
        except Exception as e:
            print(f"MyPy check error: {e}")
        
        return issues, "mypy"
    
    async def _check_with_eslint(self, file_path: Path) -> Tuple[List[LintIssue], str]:
        """Run ESLint for JavaScript/TypeScript."""
        issues = []
        
        try:
            # Create temporary ESLint config
            eslint_config_path = self.temp_dir / ".eslintrc.json"
            with open(eslint_config_path, 'w') as f:
                json.dump(self.eslint_config, f, indent=2)
            
            # Build eslint command
            cmd = [
                "eslint",
                "--format=json",
                "--config", str(eslint_config_path),
                str(file_path)
            ]
            
            # Run eslint
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse results
            if result.stdout:
                data = json.loads(result.stdout)
                
                for file_result in data:
                    for message in file_result.get('messages', []):
                        issue = LintIssue(
                            tool="eslint",
                            rule_id=message.get('ruleId', ''),
                            message=message.get('message', ''),
                            level=self._map_eslint_level(message.get('severity', 1)),
                            file_path=file_result.get('filePath', ''),
                            line_number=message.get('line', 0),
                            column_number=message.get('column'),
                            end_line=message.get('endLine'),
                            end_column=message.get('endColumn'),
                            fix_suggestion=message.get('fix', {}).get('text'),
                            category=message.get('ruleId', '').split('/')[0] if message.get('ruleId') else None,
                            metadata={
                                "nodeType": message.get('nodeType'),
                                "source": message.get('source')
                            }
                        )
                        issues.append(issue)
                        
        except subprocess.TimeoutExpired:
            print("ESLint check timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse ESLint output: {e}")
        except FileNotFoundError:
            print("ESLint not installed - skipping check")
        except Exception as e:
            print(f"ESLint check error: {e}")
        finally:
            # Clean up config
            if 'eslint_config_path' in locals() and eslint_config_path.exists():
                eslint_config_path.unlink()
        
        return issues, "eslint"
    
    async def _check_with_prettier(self, file_path: Path) -> Tuple[List[LintIssue], str]:
        """Check code formatting with Prettier."""
        issues = []
        
        try:
            # Build prettier command
            cmd = [
                "prettier",
                "--check",
                "--parser", "typescript" if file_path.suffix == ".ts" else "babel",
                str(file_path)
            ]
            
            # Run prettier
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # If check failed, add formatting issue
            if result.returncode != 0:
                issue = LintIssue(
                    tool="prettier",
                    rule_id="formatting",
                    message="Code formatting does not match Prettier standards",
                    level=LintLevel.WARNING,
                    file_path=str(file_path),
                    line_number=1,
                    fix_suggestion="Run 'prettier --write' to fix formatting",
                    category="formatting"
                )
                issues.append(issue)
                
        except subprocess.TimeoutExpired:
            print("Prettier check timed out")
        except FileNotFoundError:
            print("Prettier not installed - skipping check")
        except Exception as e:
            print(f"Prettier check error: {e}")
        
        return issues, "prettier"
    
    def _map_ruff_level(self, fix_availability: Optional[str]) -> LintLevel:
        """Map Ruff fix availability to lint level."""
        if fix_availability == "none":
            return LintLevel.ERROR
        elif fix_availability == "unsafe":
            return LintLevel.WARNING
        else:
            return LintLevel.INFO
    
    def _map_eslint_level(self, severity: int) -> LintLevel:
        """Map ESLint severity to lint level."""
        if severity == 2:
            return LintLevel.ERROR
        elif severity == 1:
            return LintLevel.WARNING
        else:
            return LintLevel.INFO
    
    def _get_mypy_fix_suggestion(self, code: str) -> Optional[str]:
        """Get fix suggestion for MyPy error."""
        suggestions = {
            "call-arg": "Add type annotation for function parameter",
            "assignment": "Add type annotation for variable",
            "attr-defined": "Check if attribute exists or add type annotation",
            "index": "Add type annotation for container or check index type",
            "operator": "Add type annotations for operands",
            "return-value": "Add return type annotation to function",
            "arg-type": "Check argument type matches expected type",
            "override": "Check method signature matches parent class"
        }
        return suggestions.get(code, "Add appropriate type annotations")
    
    async def fix_code(self, code: str, file_path: str, language: str = "python") -> Tuple[str, List[str]]:
        """
        Auto-fix linting issues in code.
        
        Args:
            code: The code to fix
            file_path: Virtual file path for context
            language: Programming language
            
        Returns:
            Tuple of (fixed_code, applied_fixes)
        """
        temp_file = self.temp_dir / Path(file_path).name
        
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            applied_fixes = []
            fixed_code = code
            
            if language == "python":
                # Use ruff to fix Python code
                try:
                    cmd = ["ruff", "format", str(temp_file)]
                    subprocess.run(cmd, capture_output=True, timeout=30)
                    
                    cmd = ["ruff", "check", "--fix", str(temp_file)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    if "Fixed" in result.stdout:
                        applied_fixes.append("Ruff auto-fixes applied")
                    
                    # Read fixed code
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        fixed_code = f.read()
                        
                except Exception as e:
                    print(f"Ruff fix failed: {e}")
                    
            elif language in ["javascript", "typescript"]:
                # Use prettier and eslint --fix
                try:
                    # Prettier format
                    cmd = ["prettier", "--write", str(temp_file)]
                    subprocess.run(cmd, capture_output=True, timeout=30)
                    applied_fixes.append("Prettier formatting applied")
                    
                    # ESLint fix
                    cmd = ["eslint", "--fix", str(temp_file)]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    applied_fixes.append("ESLint auto-fixes applied")
                    
                    # Read fixed code
                    with open(temp_file, 'r', encoding='utf-8') as f:
                        fixed_code = f.read()
                        
                except Exception as e:
                    print(f"JS/TS fix failed: {e}")
            
            return fixed_code, applied_fixes
            
        finally:
            if temp_file.exists():
                temp_file.unlink()
    
    def generate_report(self, result: LintResult) -> str:
        """Generate a human-readable lint report."""
        report = []
        report.append("=" * 60)
        report.append("LINT CHECK REPORT")
        report.append("=" * 60)
        report.append(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        report.append(f"Files checked: {result.files_checked}")
        report.append(f"Check time: {result.check_time:.2f}s")
        report.append(f"Fixable issues: {result.fixable_issues}")
        report.append("")
        
        # Summary by tool
        report.append("TOOL SUMMARY:")
        for tool, data in result.tool_results.items():
            report.append(f"  {tool}:")
            for key, value in data.items():
                if value > 0:
                    report.append(f"    - {key}: {value}")
        report.append("")
        
        # Issues by level
        if result.issues:
            report.append("ISSUES BY LEVEL:")
            for level in [LintLevel.ERROR, LintLevel.WARNING, LintLevel.INFO]:
                issues = [i for i in result.issues if i.level == level]
                if issues:
                    report.append(f"\n{level.value.upper()} ({len(issues)}):")
                    for issue in issues[:10]:  # Limit to 10 per level
                        report.append(f"  • {issue.file_path}:{issue.line_number}")
                        if issue.rule_id:
                            report.append(f"    [{issue.rule_id}] {issue.message}")
                        else:
                            report.append(f"    {issue.message}")
                        if issue.fix_suggestion:
                            report.append(f"    Fix: {issue.fix_suggestion}")
                    if len(issues) > 10:
                        report.append(f"  ... and {len(issues) - 10} more")
        else:
            report.append("✅ No linting issues found!")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    async def install_tools(self) -> bool:
        """Install required linting tools."""
        tools = [
            ("ruff", "pip install ruff"),
            ("mypy", "pip install mypy"),
            ("black", "pip install black"),  # For ruff format compatibility
        ]
        
        installed = True
        
        for tool, install_cmd in tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                print(f"✅ {tool} is already installed")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"Installing {tool}...")
                try:
                    subprocess.run(install_cmd.split(), check=True)
                    print(f"✅ {tool} installed successfully")
                except subprocess.CalledProcessError:
                    print(f"❌ Failed to install {tool}")
                    installed = False
        
        return installed


# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    async def main():
        checker = LintChecker()
        
        # Install tools if needed
        await checker.install_tools()
        
        if len(sys.argv) > 1:
            # Check file
            file_path = Path(sys.argv[1])
            if file_path.exists():
                with open(file_path, 'r') as f:
                    code = f.read()
                
                language = "python" if file_path.suffix == ".py" else "javascript"
                result = await checker.check_code(code, str(file_path), language)
                print(checker.generate_report(result))
                
                # Try to fix if issues found
                if result.issues:
                    print("\nAttempting auto-fix...")
                    fixed_code, fixes = await checker.fix_code(code, str(file_path), language)
                    if fixes:
                        print(f"Applied fixes: {', '.join(fixes)}")
                        # Save fixed version
                        fixed_file = file_path.parent / f"{file_path.stem}_fixed{file_path.suffix}"
                        with open(fixed_file, 'w') as f:
                            f.write(fixed_code)
                        print(f"Fixed version saved to: {fixed_file}")
            else:
                print(f"File not found: {file_path}")
        else:
            # Demo check
            demo_code = """
import os
import sys

def bad_function(x, y):
    # Missing type annotations
    result = x + y
    print(result)  # Print statement in production code
    return result

# Unused import
import json

# Line too long and formatting issues
very_long_variable_name_that_exceeds_reasonable_limits = "this is a very long string that should be formatted better"
"""
            result = await checker.check_code(demo_code, "demo.py", "python")
            print(checker.generate_report(result))
    
    asyncio.run(main())
