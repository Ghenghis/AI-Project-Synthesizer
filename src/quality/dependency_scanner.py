"""
Dependency Scanner for VIBE MCP

Scans project dependencies for security vulnerabilities:
- Multiple package manager support (pip, npm, yarn, poetry, etc.)
- CVE database integration
- Vulnerability severity assessment
- Auto-fix suggestions
- Integration with QualityGate

Provides comprehensive dependency security analysis.
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from src.core.config import get_settings
from src.core.security_utils import safe_subprocess_run, validate_path


class PackageManager(Enum):
    """Supported package managers."""
    PIP = "pip"
    POETRY = "poetry"
    NPM = "npm"
    YARN = "yarn"
    PIPENV = "pipenv"
    GRADLE = "gradle"
    MAVEN = "maven"
    CARGO = "cargo"
    GO_MOD = "go_mod"
    COMPOSER = "composer"
    UNKNOWN = "unknown"


class SeverityLevel(Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


@dataclass
class Vulnerability:
    """Represents a security vulnerability."""
    id: str
    package: str
    installed_version: str
    fixed_version: Optional[str]
    severity: SeverityLevel
    description: str
    cve_id: Optional[str]
    references: List[str]
    advisory_data: Dict[str, Any]


@dataclass
class DependencyReport:
    """Report of dependency scan results."""
    package_manager: PackageManager
    total_packages: int
    vulnerabilities: List[Vulnerability]
    summary: Dict[str, int]
    scan_duration: float
    recommendations: List[str]


class DependencyScanner:
    """
    Scans project dependencies for vulnerabilities.
    
    Features:
    - Multi-language support
    - CVE database integration
    - Auto-fix suggestions
    - Detailed reporting
    - QualityGate integration
    """
    
    def __init__(self):
        self.config = get_settings()
        
        # Scanner configurations
        self.scanners = {
            PackageManager.PIP: self._scan_pip,
            PackageManager.POETRY: self._scan_poetry,
            PackageManager.NPM: self._scan_npm,
            PackageManager.YARN: self._scan_yarn,
            PackageManager.PIPENV: self._scan_pipenv,
            PackageManager.GRADLE: self._scan_gradle,
            PackageManager.MAVEN: self._scan_maven,
            PackageManager.CARGO: self._scan_cargo,
            PackageManager.GO_MOD: self._scan_go_mod,
            PackageManager.COMPOSER: self._scan_composer,
        }
        
        # Severity weights for scoring
        self.severity_weights = {
            SeverityLevel.CRITICAL: 10,
            SeverityLevel.HIGH: 7,
            SeverityLevel.MEDIUM: 4,
            SeverityLevel.LOW: 1,
            SeverityLevel.NONE: 0,
        }
    
    async def scan(self, project_path: str = ".") -> List[DependencyReport]:
        """
        Scan all dependencies in the project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of reports for each package manager found
        """
        project_path = Path(project_path).resolve()
        reports = []
        
        # Detect package managers
        managers = self._detect_package_managers(project_path)
        
        if not managers:
            return [DependencyReport(
                package_manager=PackageManager.UNKNOWN,
                total_packages=0,
                vulnerabilities=[],
                summary={},
                scan_duration=0,
                recommendations=["No supported package manager detected"]
            )]
        
        # Scan each package manager
        for manager in managers:
            try:
                report = await self.scanners[manager](project_path)
                reports.append(report)
            except Exception as e:
                reports.append(DependencyReport(
                    package_manager=manager,
                    total_packages=0,
                    vulnerabilities=[],
                    summary={},
                    scan_duration=0,
                    recommendations=[f"Scan failed: {str(e)}"]
                ))
        
        return reports
    
    def _detect_package_managers(self, path: Path) -> List[PackageManager]:
        """Detect which package managers are used in the project."""
        managers = []
        
        # Check for lock files and config files
        indicators = {
            PackageManager.PIP: ["requirements.txt", "setup.py", "pyproject.toml"],
            PackageManager.POETRY: ["poetry.lock", "pyproject.toml"],
            PackageManager.NPM: ["package.json", "package-lock.json"],
            PackageManager.YARN: ["package.json", "yarn.lock"],
            PackageManager.PIPENV: ["Pipfile", "Pipfile.lock"],
            PackageManager.GRADLE: ["build.gradle", "build.gradle.kts"],
            PackageManager.MAVEN: ["pom.xml"],
            PackageManager.CARGO: ["Cargo.toml", "Cargo.lock"],
            PackageManager.GO_MOD: ["go.mod", "go.sum"],
            PackageManager.COMPOSER: ["composer.json", "composer.lock"],
        }
        
        for manager, files in indicators.items():
            if any((path / f).exists() for f in files):
                managers.append(manager)
        
        return managers
    
    async def _scan_pip(self, path: Path) -> DependencyReport:
        """Scan Python pip dependencies."""
        import time
        start = time.time()
        
        vulnerabilities = []
        
        # Try pip-audit first
        try:
            result = safe_subprocess_run(
                ["pip-audit", "--format", "json", "--requirement", "requirements.txt"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for vuln in data.get("dependencies", []):
                    for vuln_info in vuln.get("vulnerabilities", []):
                        vulnerabilities.append(Vulnerability(
                            id=vuln_info.get("id", ""),
                            package=vuln.get("name", ""),
                            installed_version=vuln.get("version", ""),
                            fixed_version=vuln_info.get("fix_versions", [None])[0],
                            severity=self._parse_severity(vuln_info.get("severity", "unknown")),
                            description=vuln_info.get("description", ""),
                            cve_id=vuln_info.get("id", "").replace("PYSEC-", ""),
                            references=vuln_info.get("references", []),
                            advisory_data=vuln_info
                        ))
        except FileNotFoundError:
            # Fallback to safety
            try:
                result = safe_subprocess_run(
                    ["safety", "check", "--json", "--short-report"],
                    capture_output=True,
                    text=True,
                    cwd=validate_path(path),
                    timeout=30
                )
                
                if result.stdout:
                    data = json.loads(result.stdout)
                    for vuln in data:
                        vulnerabilities.append(Vulnerability(
                            id=vuln.get("id", ""),
                            package=vuln.get("package", ""),
                            installed_version=vuln.get("installed_version", ""),
                            fixed_version=vuln.get("analyzed_version"),
                            severity=self._parse_severity(vuln.get("vulnerability", "").split()[0]),
                            description=vuln.get("advisory", ""),
                            cve_id=vuln.get("cve", ""),
                            references=[],
                            advisory_data=vuln
                        ))
            except FileNotFoundError:
                pass
        
        # Count total packages
        total_packages = 0
        if (path / "requirements.txt").exists():
            with open(path / "requirements.txt") as f:
                total_packages = len([l for l in f if l.strip() and not l.startswith("#")])
        
        # Generate summary
        summary = self._generate_summary(vulnerabilities)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(vulnerabilities, PackageManager.PIP)
        
        return DependencyReport(
            package_manager=PackageManager.PIP,
            total_packages=total_packages,
            vulnerabilities=vulnerabilities,
            summary=summary,
            scan_duration=time.time() - start,
            recommendations=recommendations
        )
    
    async def _scan_poetry(self, path: Path) -> DependencyReport:
        """Scan Python Poetry dependencies."""
        import time
        start = time.time()
        
        vulnerabilities = []
        
        try:
            # Use poetry to show dependencies
            result = safe_subprocess_run(
                ["poetry", "show", "--tree", "--no-dev"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            
            if result.returncode == 0:
                # Parse poetry output and check with pip-audit
                packages = []
                for line in result.stdout.split('\n'):
                    if line and not line.startswith(' ') and '├' not in line and '└' not in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            packages.append(f"{parts[0]}=={parts[1]}")
                
                # Create temporary requirements file
                temp_req = path / "temp_poetry_deps.txt"
                with open(temp_req, 'w') as f:
                    f.write('\n'.join(packages))
                
                # Scan with pip-audit
                try:
                    result = subprocess.run(
                        ["pip-audit", "--format", "json", "--requirement", str(temp_req)],
                        capture_output=True,
                        text=True,
                        cwd=path
                    )
                    
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        for vuln in data.get("dependencies", []):
                            for vuln_info in vuln.get("vulnerabilities", []):
                                vulnerabilities.append(Vulnerability(
                                    id=vuln_info.get("id", ""),
                                    package=vuln.get("name", ""),
                                    installed_version=vuln.get("version", ""),
                                    fixed_version=vuln_info.get("fix_versions", [None])[0],
                                    severity=self._parse_severity(vuln_info.get("severity", "unknown")),
                                    description=vuln_info.get("description", ""),
                                    cve_id=vuln_info.get("id", "").replace("PYSEC-", ""),
                                    references=vuln_info.get("references", []),
                                    advisory_data=vuln_info
                                ))
                finally:
                    temp_req.unlink(missing_ok=True)
                    
        except FileNotFoundError:
            pass
        
        # Get total packages from poetry
        total_packages = 0
        try:
            result = safe_subprocess_run(
                ["poetry", "show", "--no-dev"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            if result.returncode == 0:
                total_packages = len([l for l in result.stdout.split('\n') if l.strip()])
        except:
            pass
        
        summary = self._generate_summary(vulnerabilities)
        recommendations = self._generate_recommendations(vulnerabilities, PackageManager.POETRY)
        
        return DependencyReport(
            package_manager=PackageManager.POETRY,
            total_packages=total_packages,
            vulnerabilities=vulnerabilities,
            summary=summary,
            scan_duration=time.time() - start,
            recommendations=recommendations
        )
    
    async def _scan_npm(self, path: Path) -> DependencyReport:
        """Scan Node.js npm dependencies."""
        import time
        start = time.time()
        
        vulnerabilities = []
        
        try:
            # Use npm audit
            result = safe_subprocess_run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                # Process vulnerabilities
                for vuln_id, vuln_data in data.get("vulnerabilities", {}).items():
                    vulnerabilities.append(Vulnerability(
                        id=vuln_id,
                        package=vuln_data.get("name", ""),
                        installed_version=vuln_data.get("via", [{}])[0].get("version", ""),
                        fixed_version=vuln_data.get("fixAvailable", {}).get("version"),
                        severity=self._parse_severity(vuln_data.get("severity", "unknown")),
                        description=vuln_data.get("title", ""),
                        cve_id=vuln_data.get("url", "").split("/")[-1] if vuln_data.get("url") else None,
                        references=[vuln_data.get("url", "")],
                        advisory_data=vuln_data
                    ))
                    
        except FileNotFoundError:
            pass
        
        # Get total packages
        total_packages = 0
        if (path / "package.json").exists():
            try:
                with open(path / "package.json") as f:
                    data = json.load(f)
                    total_packages = len(data.get("dependencies", {})) + len(data.get("devDependencies", {}))
            except:
                pass
        
        summary = self._generate_summary(vulnerabilities)
        recommendations = self._generate_recommendations(vulnerabilities, PackageManager.NPM)
        
        return DependencyReport(
            package_manager=PackageManager.NPM,
            total_packages=total_packages,
            vulnerabilities=vulnerabilities,
            summary=summary,
            scan_duration=time.time() - start,
            recommendations=recommendations
        )
    
    async def _scan_yarn(self, path: Path) -> DependencyReport:
        """Scan Node.js Yarn dependencies."""
        import time
        start = time.time()
        
        vulnerabilities = []
        
        try:
            # Use yarn audit
            result = safe_subprocess_run(
                ["yarn", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            
            # Parse yarn audit JSON output
            for line in result.stdout.split('\n'):
                if line.strip() and line.startswith('{'):
                    try:
                        data = json.loads(line)
                        if data.get("type") == "auditAdvisory":
                            advisory = data.get("data", {})
                            vulnerabilities.append(Vulnerability(
                                id=advisory.get("id", ""),
                                package=advisory.get("module_name", ""),
                                installed_version=advisory.get("findings", [{}])[0].get("version", ""),
                                fixed_version=advisory.get("patched_versions", [None])[0],
                                severity=self._parse_severity(advisory.get("severity", "unknown")),
                                description=advisory.get("title", ""),
                                cve_id=advisory.get("cve", ""),
                                references=advisory.get("url", []),
                                advisory_data=advisory
                            ))
                    except json.JSONDecodeError:
                        continue
                        
        except FileNotFoundError:
            pass
        
        # Get total packages from yarn
        total_packages = 0
        try:
            result = safe_subprocess_run(
                ["yarn", "list", "--json"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            if result.stdout:
                data = json.loads(result.stdout)
                total_packages = len(data.get("trees", []))
        except:
            pass
        
        summary = self._generate_summary(vulnerabilities)
        recommendations = self._generate_recommendations(vulnerabilities, PackageManager.YARN)
        
        return DependencyReport(
            package_manager=PackageManager.YARN,
            total_packages=total_packages,
            vulnerabilities=vulnerabilities,
            summary=summary,
            scan_duration=time.time() - start,
            recommendations=recommendations
        )
    
    async def _scan_pipenv(self, path: Path) -> DependencyReport:
        """Scan Pipenv dependencies."""
        import time
        start = time.time()
        
        vulnerabilities = []
        
        try:
            # Export requirements from Pipenv
            result = safe_subprocess_run(
                ["pipenv", "requirements"],
                capture_output=True,
                text=True,
                cwd=validate_path(path)
            , timeout=30)
            
            if result.returncode == 0:
                # Create temp file and scan with pip-audit
                temp_req = path / "temp_pipenv_deps.txt"
                with open(temp_req, 'w') as f:
                    f.write(result.stdout)
                
                try:
                    result = subprocess.run(
                        ["pip-audit", "--format", "json", "--requirement", str(temp_req)],
                        capture_output=True,
                        text=True,
                        cwd=path
                    )
                    
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        for vuln in data.get("dependencies", []):
                            for vuln_info in vuln.get("vulnerabilities", []):
                                vulnerabilities.append(Vulnerability(
                                    id=vuln_info.get("id", ""),
                                    package=vuln.get("name", ""),
                                    installed_version=vuln.get("version", ""),
                                    fixed_version=vuln_info.get("fix_versions", [None])[0],
                                    severity=self._parse_severity(vuln_info.get("severity", "unknown")),
                                    description=vuln_info.get("description", ""),
                                    cve_id=vuln_info.get("id", "").replace("PYSEC-", ""),
                                    references=vuln_info.get("references", []),
                                    advisory_data=vuln_info
                                ))
                finally:
                    temp_req.unlink(missing_ok=True)
                    
        except FileNotFoundError:
            pass
        
        # Get total packages from Pipfile
        total_packages = 0
        if (path / "Pipfile").exists():
            try:
                with open(path / "Pipfile") as f:
                    content = f.read()
                    total_packages = len([l for l in content.split('\n') 
                                        if l.strip() and '=' in l and not l.startswith('#')])
            except:
                pass
        
        summary = self._generate_summary(vulnerabilities)
        recommendations = self._generate_recommendations(vulnerabilities, PackageManager.PIPENV)
        
        return DependencyReport(
            package_manager=PackageManager.PIPENV,
            total_packages=total_packages,
            vulnerabilities=vulnerabilities,
            summary=summary,
            scan_duration=time.time() - start,
            recommendations=recommendations
        )
    
    async def _scan_gradle(self, path: Path) -> DependencyReport:
        """Scan Gradle dependencies."""
        # Placeholder for Gradle scanning
        return DependencyReport(
            package_manager=PackageManager.GRADLE,
            total_packages=0,
            vulnerabilities=[],
            summary={},
            scan_duration=0,
            recommendations=["Gradle scanning not yet implemented"]
        )
    
    async def _scan_maven(self, path: Path) -> DependencyReport:
        """Scan Maven dependencies."""
        # Placeholder for Maven scanning
        return DependencyReport(
            package_manager=PackageManager.MAVEN,
            total_packages=0,
            vulnerabilities=[],
            summary={},
            scan_duration=0,
            recommendations=["Maven scanning not yet implemented"]
        )
    
    async def _scan_cargo(self, path: Path) -> DependencyReport:
        """Scan Rust Cargo dependencies."""
        # Placeholder for Cargo scanning
        return DependencyReport(
            package_manager=PackageManager.CARGO,
            total_packages=0,
            vulnerabilities=[],
            summary={},
            scan_duration=0,
            recommendations=["Cargo scanning not yet implemented"]
        )
    
    async def _scan_go_mod(self, path: Path) -> DependencyReport:
        """Scan Go modules dependencies."""
        # Placeholder for Go modules scanning
        return DependencyReport(
            package_manager=PackageManager.GO_MOD,
            total_packages=0,
            vulnerabilities=[],
            summary={},
            scan_duration=0,
            recommendations=["Go modules scanning not yet implemented"]
        )
    
    async def _scan_composer(self, path: Path) -> DependencyReport:
        """Scan PHP Composer dependencies."""
        # Placeholder for Composer scanning
        return DependencyReport(
            package_manager=PackageManager.COMPOSER,
            total_packages=0,
            vulnerabilities=[],
            summary={},
            scan_duration=0,
            recommendations=["Composer scanning not yet implemented"]
        )
    
    def _parse_severity(self, severity_str: str) -> SeverityLevel:
        """Parse severity string to enum."""
        severity_str = severity_str.lower()
        
        if "critical" in severity_str:
            return SeverityLevel.CRITICAL
        elif "high" in severity_str:
            return SeverityLevel.HIGH
        elif "medium" in severity_str or "moderate" in severity_str:
            return SeverityLevel.MEDIUM
        elif "low" in severity_str:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.NONE
    
    def _generate_summary(self, vulnerabilities: List[Vulnerability]) -> Dict[str, int]:
        """Generate vulnerability summary."""
        summary = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": len(vulnerabilities)
        }
        
        for vuln in vulnerabilities:
            if vuln.severity == SeverityLevel.CRITICAL:
                summary["critical"] += 1
            elif vuln.severity == SeverityLevel.HIGH:
                summary["high"] += 1
            elif vuln.severity == SeverityLevel.MEDIUM:
                summary["medium"] += 1
            elif vuln.severity == SeverityLevel.LOW:
                summary["low"] += 1
        
        return summary
    
    def _generate_recommendations(self, vulnerabilities: List[Vulnerability], 
                                 manager: PackageManager) -> List[str]:
        """Generate fix recommendations."""
        recommendations = []
        
        if not vulnerabilities:
            recommendations.append("No vulnerabilities found! ✅")
            return recommendations
        
        # Count fixable vulnerabilities
        fixable = sum(1 for v in vulnerabilities if v.fixed_version)
        
        if fixable > 0:
            recommendations.append(f"Update {fixable} packages to fix vulnerabilities")
            
            if manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                recommendations.append("Run: pip install --upgrade <package>")
            elif manager in [PackageManager.NPM, PackageManager.YARN]:
                recommendations.append("Run: npm update <package>")
        
        # Critical vulnerabilities
        critical = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.CRITICAL)
        if critical > 0:
            recommendations.append(f"URGENT: Fix {critical} critical vulnerabilities immediately")
        
        # High vulnerabilities
        high = sum(1 for v in vulnerabilities if v.severity == SeverityLevel.HIGH)
        if high > 0:
            recommendations.append(f"Fix {high} high severity vulnerabilities soon")
        
        # General recommendations
        recommendations.append("Enable automated dependency scanning in CI/CD")
        recommendations.append("Use lock files to ensure consistent dependencies")
        recommendations.append("Review dependencies regularly")
        
        return recommendations
    
    def calculate_risk_score(self, reports: List[DependencyReport]) -> float:
        """Calculate overall risk score from all reports."""
        total_score = 0
        max_score = 0
        
        for report in reports:
            for vuln in report.vulnerabilities:
                total_score += self.severity_weights[vuln.severity]
                max_score += self.severity_weights[SeverityLevel.CRITICAL]
        
        if max_score == 0:
            return 0.0
        
        # Return score as percentage (0-100)
        return (total_score / max_score) * 100
    
    def get_most_critical(self, reports: List[DependencyReport], limit: int = 5) -> List[Vulnerability]:
        """Get the most critical vulnerabilities across all reports."""
        all_vulns = []
        
        for report in reports:
            all_vulns.extend(report.vulnerabilities)
        
        # Sort by severity weight
        all_vulns.sort(
            key=lambda v: self.severity_weights[v.severity],
            reverse=True
        )
        
        return all_vulns[:limit]


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    
    async def main():
        scanner = DependencyScanner()
        
        print("Scanning dependencies...")
        reports = await scanner.scan(".")
        
        for report in reports:
            print(f"\n=== {report.package_manager.value.upper()} ===")
            print(f"Total packages: {report.total_packages}")
            print(f"Vulnerabilities: {report.summary['total']}")
            
            if report.vulnerabilities:
                print(f"\nCritical: {report.summary['critical']}")
                print(f"High: {report.summary['high']}")
                print(f"Medium: {report.summary['medium']}")
                print(f"Low: {report.summary['low']}")
                
                print("\nTop vulnerabilities:")
                for vuln in report.vulnerabilities[:3]:
                    print(f"  - {vuln.package}@{vuln.installed_version} ({vuln.severity.value})")
                    print(f"    {vuln.description[:100]}...")
            
            print("\nRecommendations:")
            for rec in report.recommendations:
                print(f"  - {rec}")
        
        # Overall risk score
        risk_score = scanner.calculate_risk_score(reports)
        print(f"\nOverall Risk Score: {risk_score:.1f}/100")
    
    asyncio.run(main())
