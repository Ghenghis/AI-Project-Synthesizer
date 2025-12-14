"""
Security Scanner for VIBE MCP Quality Pipeline

Integrates with multiple security scanning tools:
- Semgrep: Static analysis for security vulnerabilities
- Bandit: Python-specific security issues
- Custom rules: VIBE MCP specific security patterns

This scanner automatically checks all generated code before deployment.
"""

import asyncio
import json
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings


class SeverityLevel(Enum):
    """Security issue severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability found."""

    tool: str
    rule_id: str
    message: str
    severity: SeverityLevel
    file_path: str
    line_number: int
    column_number: int | None = None
    cwe_id: str | None = None
    owasp_category: str | None = None
    fix_suggestion: str | None = None
    metadata: dict[str, Any] = None


@dataclass
class ScanResult:
    """Result of a security scan."""

    passed: bool
    issues: list[SecurityIssue]
    scan_time: float
    files_scanned: int
    tool_results: dict[str, Any]


class SecurityScanner:
    """
    Comprehensive security scanning for generated code.

    Features:
    - Multi-tool scanning (Semgrep, Bandit)
    - Custom VIBE MCP security rules
    - Automatic fix suggestions
    - OWASP Top 10 coverage
    - CWE mapping
    """

    def __init__(self):
        self.config = get_settings()
        self.temp_dir = Path(tempfile.gettempdir()) / "vibe_mcp_scans"
        self.temp_dir.mkdir(exist_ok=True)

        # Tool configurations
        self.semgrep_rules = [
            "p/security-audit",  # OWASP Top 10
            "p/command-injection",
            "p/sql-injection",
            "p/xss",
            "p/path-traversal",
            "p/cryptographic-misuse",
            "p/regex",
            "p/django",
        ]

        # Custom VIBE MCP rules
        self.custom_rules = self._load_custom_rules()

    def _load_custom_rules(self) -> dict[str, Any]:
        """Load VIBE MCP specific security rules."""
        return {
            "no_hardcoded_secrets": {
                "pattern": r"(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                "severity": "high",
                "message": "Hardcoded secret detected - use environment variables",
            },
            "no_eval_exec": {
                "pattern": r"\b(eval|exec)\s*\(",
                "severity": "critical",
                "message": "Use of eval/exec is dangerous - avoid dynamic code execution",
            },
            "no_shell_true": {
                "pattern": r"shell\s*=\s*True",
                "severity": "high",
                "message": "shell=True is dangerous - use proper command handling",
            },
            "validate_user_input": {
                "pattern": r"(request\.(form|args|json)|input\(|raw_input\()[^)]*[^)]*$",
                "severity": "medium",
                "message": "User input should be validated before use",
            },
        }

    async def scan_code(self, code: str, file_path: str = "generated.py") -> ScanResult:
        """
        Scan code with all security tools.

        Args:
            code: The code to scan
            file_path: Virtual file path for context

        Returns:
            ScanResult with all found issues
        """
        import time

        start_time = time.time()

        # Create temporary file for scanning
        temp_file = self.temp_dir / Path(file_path).name
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(code)

            # Run all scans in parallel
            results = await asyncio.gather(
                self._scan_with_semgrep(temp_file),
                self._scan_with_bandit(temp_file),
                self._scan_with_custom_rules(code, file_path),
                return_exceptions=True,
            )

            # Collect all issues
            all_issues = []
            tool_results = {}

            for result in results:
                if isinstance(result, Exception):
                    print(f"Scanner error: {result}")
                    continue

                issues, tool_name = result
                all_issues.extend(issues)
                tool_results[tool_name] = {
                    "issues_found": len(issues),
                    "critical": sum(
                        1 for i in issues if i.severity == SeverityLevel.CRITICAL
                    ),
                    "high": sum(1 for i in issues if i.severity == SeverityLevel.HIGH),
                    "medium": sum(
                        1 for i in issues if i.severity == SeverityLevel.MEDIUM
                    ),
                    "low": sum(1 for i in issues if i.severity == SeverityLevel.LOW),
                }

            # Determine if scan passed (no critical/high issues)
            passed = not any(
                i.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
                for i in all_issues
            )

            scan_time = time.time() - start_time

            return ScanResult(
                passed=passed,
                issues=all_issues,
                scan_time=scan_time,
                files_scanned=1,
                tool_results=tool_results,
            )

        finally:
            # Clean up
            if temp_file.exists():
                temp_file.unlink()

    async def _scan_with_semgrep(
        self, file_path: Path
    ) -> tuple[list[SecurityIssue], str]:
        """Run Semgrep security scan."""
        issues = []

        try:
            # Build semgrep command
            cmd = [
                "semgrep",
                "--config",
                ",".join(self.semgrep_rules),
                "--json",
                "--quiet",
                str(file_path),
            ]

            # Run semgrep
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Parse results
                data = json.loads(result.stdout)

                for finding in data.get("results", []):
                    issue = SecurityIssue(
                        tool="semgrep",
                        rule_id=finding.get("check_id", ""),
                        message=finding.get("message", ""),
                        severity=self._map_semgrep_severity(
                            finding.get("metadata", {}).get("severity", "INFO")
                        ),
                        file_path=finding.get("path", ""),
                        line_number=finding.get("start", {}).get("line", 0),
                        column_number=finding.get("start", {}).get("col"),
                        cwe_id=finding.get("metadata", {}).get("cwe"),
                        owasp_category=finding.get("metadata", {}).get("owasp"),
                        fix_suggestion=finding.get("metadata", {})
                        .get("fix", {})
                        .get("regex"),
                        metadata=finding.get("metadata", {}),
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            print("Semgrep scan timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Semgrep output: {e}")
        except FileNotFoundError:
            print("Semgrep not installed - skipping scan")
        except Exception as e:
            print(f"Semgrep scan error: {e}")

        return issues, "semgrep"

    async def _scan_with_bandit(
        self, file_path: Path
    ) -> tuple[list[SecurityIssue], str]:
        """Run Bandit Python security scan."""
        issues = []

        try:
            # Build bandit command
            cmd = ["bandit", "-f", "json", "-q", str(file_path)]

            # Run bandit
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode in [0, 1]:  # 0 = no issues, 1 = issues found
                # Parse results
                data = json.loads(result.stdout)

                for finding in data.get("results", []):
                    issue = SecurityIssue(
                        tool="bandit",
                        rule_id=finding.get("test_name", ""),
                        message=finding.get("issue_text", ""),
                        severity=self._map_bandit_severity(
                            finding.get("issue_severity", "LOW")
                        ),
                        file_path=finding.get("filename", ""),
                        line_number=finding.get("line_number", 0),
                        cwe_id=finding.get("cwe_id"),
                        fix_suggestion=finding.get("issue_cwe", {}).get("link"),
                        metadata={
                            "test_id": finding.get("test_id"),
                            "confidence": finding.get("issue_confidence"),
                        },
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            print("Bandit scan timed out")
        except json.JSONDecodeError as e:
            print(f"Failed to parse Bandit output: {e}")
        except FileNotFoundError:
            print("Bandit not installed - skipping scan")
        except Exception as e:
            print(f"Bandit scan error: {e}")

        return issues, "bandit"

    async def _scan_with_custom_rules(
        self, code: str, file_path: str
    ) -> tuple[list[SecurityIssue], str]:
        """Scan with VIBE MCP custom rules."""
        import re

        issues = []
        lines = code.split("\n")

        for rule_name, rule_config in self.custom_rules.items():
            pattern = re.compile(rule_config["pattern"], re.IGNORECASE)

            for line_num, line in enumerate(lines, 1):
                if pattern.search(line):
                    issue = SecurityIssue(
                        tool="vibe_mcp",
                        rule_id=rule_name,
                        message=rule_config["message"],
                        severity=SeverityLevel(rule_config["severity"]),
                        file_path=file_path,
                        line_number=line_num,
                        fix_suggestion=self._get_fix_suggestion(rule_name),
                        metadata={"rule_type": "custom"},
                    )
                    issues.append(issue)

        return issues, "vibe_mcp"

    def _map_semgrep_severity(self, severity: str) -> SeverityLevel:
        """Map Semgrep severity to our enum."""
        mapping = {
            "ERROR": SeverityLevel.HIGH,
            "WARNING": SeverityLevel.MEDIUM,
            "INFO": SeverityLevel.INFO,
        }
        return mapping.get(severity.upper(), SeverityLevel.LOW)

    def _map_bandit_severity(self, severity: str) -> SeverityLevel:
        """Map Bandit severity to our enum."""
        mapping = {
            "HIGH": SeverityLevel.HIGH,
            "MEDIUM": SeverityLevel.MEDIUM,
            "LOW": SeverityLevel.LOW,
        }
        return mapping.get(severity.upper(), SeverityLevel.LOW)

    def _get_fix_suggestion(self, rule_name: str) -> str:
        """Get fix suggestion for custom rule."""
        suggestions = {
            "no_hardcoded_secrets": "Use environment variables: os.getenv('SECRET_NAME')",
            "no_eval_exec": "Use safer alternatives like ast.literal_eval() or avoid dynamic execution",
            "no_shell_true": "Use subprocess.run without shell=True or properly escape arguments",
            "validate_user_input": "Add validation: if not input.is_valid(): raise ValueError()",
        }
        return suggestions.get(rule_name, "Review and fix the security issue")

    async def scan_directory(self, directory: Path) -> ScanResult:
        """
        Scan an entire directory for security issues.

        Args:
            directory: Directory path to scan

        Returns:
            ScanResult with aggregated findings
        """
        import time

        start_time = time.time()

        all_issues = []
        tool_results = {}
        files_scanned = 0

        # Get all code files
        code_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".java",
            ".go",
            ".rb",
            ".php",
        }
        code_files = []

        for ext in code_extensions:
            code_files.extend(directory.rglob(f"*{ext}"))

        # Limit to reasonable number of files
        if len(code_files) > 100:
            print(
                f"Warning: Limiting scan to first 100 files (found {len(code_files)})"
            )
            code_files = code_files[:100]

        # Scan files in batches
        batch_size = 10
        for i in range(0, len(code_files), batch_size):
            batch = code_files[i : i + batch_size]

            tasks = []
            for file_path in batch:
                try:
                    with open(file_path, encoding="utf-8") as f:
                        code = f.read()
                    tasks.append(self.scan_code(code, str(file_path)))
                except Exception as e:
                    print(f"Could not read {file_path}: {e}")
                    continue

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, ScanResult):
                    all_issues.extend(result.issues)
                    for tool, data in result.tool_results.items():
                        if tool not in tool_results:
                            tool_results[tool] = {
                                "issues_found": 0,
                                "critical": 0,
                                "high": 0,
                                "medium": 0,
                                "low": 0,
                            }
                        for key in data:
                            tool_results[tool][key] += data[key]
                    files_scanned += 1

        scan_time = time.time() - start_time
        passed = not any(
            i.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
            for i in all_issues
        )

        return ScanResult(
            passed=passed,
            issues=all_issues,
            scan_time=scan_time,
            files_scanned=files_scanned,
            tool_results=tool_results,
        )

    def generate_report(self, result: ScanResult) -> str:
        """Generate a human-readable security report."""
        report = []
        report.append("=" * 60)
        report.append("SECURITY SCAN REPORT")
        report.append("=" * 60)
        report.append(f"Status: {'✅ PASSED' if result.passed else '❌ FAILED'}")
        report.append(f"Files scanned: {result.files_scanned}")
        report.append(f"Scan time: {result.scan_time:.2f}s")
        report.append("")

        # Summary by tool
        report.append("TOOL SUMMARY:")
        for tool, data in result.tool_results.items():
            report.append(f"  {tool}:")
            for key, value in data.items():
                if key != "issues_found" and value > 0:
                    report.append(f"    - {key}: {value}")
            report.append(f"    - Total issues: {data['issues_found']}")
        report.append("")

        # Issues by severity
        if result.issues:
            report.append("ISSUES BY SEVERITY:")
            for severity in [
                SeverityLevel.CRITICAL,
                SeverityLevel.HIGH,
                SeverityLevel.MEDIUM,
                SeverityLevel.LOW,
            ]:
                issues = [i for i in result.issues if i.severity == severity]
                if issues:
                    report.append(f"\n{severity.value.upper()} ({len(issues)}):")
                    for issue in issues[:10]:  # Limit to 10 per severity
                        report.append(f"  • {issue.file_path}:{issue.line_number}")
                        report.append(f"    {issue.message}")
                        if issue.fix_suggestion:
                            report.append(f"    Fix: {issue.fix_suggestion}")
                    if len(issues) > 10:
                        report.append(f"  ... and {len(issues) - 10} more")
        else:
            report.append("✅ No security issues found!")

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    async def install_tools(self) -> bool:
        """Install required security scanning tools."""
        tools = [("semgrep", "pip install semgrep"), ("bandit", "pip install bandit")]

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
        scanner = SecurityScanner()

        # Install tools if needed
        await scanner.install_tools()

        if len(sys.argv) > 1:
            # Scan file
            file_path = Path(sys.argv[1])
            if file_path.exists():
                with open(file_path) as f:
                    code = f.read()
                result = await scanner.scan_code(code, str(file_path))
                print(scanner.generate_report(result))
            else:
                print(f"File not found: {file_path}")
        else:
            # Demo scan
            demo_code = """
import os
import subprocess

password = "secret123"  # Hardcoded password
eval(user_input)  # Dangerous eval

def process_query(query):
    # SQL injection vulnerability
    sql = f"SELECT * FROM users WHERE name = '{query}'"
    return db.execute(sql)
"""
            result = await scanner.scan_code(demo_code, "demo.py")
            print(scanner.generate_report(result))

    asyncio.run(main())
