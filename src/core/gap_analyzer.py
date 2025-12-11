"""
AI Project Synthesizer - Gap Analyzer & Auto-Repair System

Robust progressive gap filling:
- Identifies missing components
- Auto-repairs issues
- Validates system integrity
- Generates repair reports
"""

import asyncio
import importlib
from typing import Optional, Dict, Any, List, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import traceback

from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class GapSeverity(str, Enum):
    """Severity levels for gaps."""
    CRITICAL = "critical"  # System won't work
    HIGH = "high"          # Major feature broken
    MEDIUM = "medium"      # Feature degraded
    LOW = "low"            # Minor issue
    INFO = "info"          # Suggestion


class GapCategory(str, Enum):
    """Categories of gaps."""
    IMPORT = "import"
    CONFIG = "config"
    FILE = "file"
    DEPENDENCY = "dependency"
    API = "api"
    DATABASE = "database"
    INTEGRATION = "integration"
    TEST = "test"
    DOCUMENTATION = "documentation"


@dataclass
class Gap:
    """Represents a system gap."""
    id: str
    category: GapCategory
    severity: GapSeverity
    description: str
    location: str
    auto_fixable: bool = False
    fix_action: Optional[str] = None
    fix_function: Optional[Callable] = None
    fixed: bool = False
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "category": self.category.value,
            "severity": self.severity.value,
            "description": self.description,
            "location": self.location,
            "auto_fixable": self.auto_fixable,
            "fix_action": self.fix_action,
            "fixed": self.fixed,
            "error": self.error,
        }


@dataclass
class AnalysisReport:
    """Gap analysis report."""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    gaps: List[Gap] = field(default_factory=list)
    fixed_count: int = 0
    failed_count: int = 0

    @property
    def total_gaps(self) -> int:
        return len(self.gaps)

    @property
    def critical_gaps(self) -> List[Gap]:
        return [g for g in self.gaps if g.severity == GapSeverity.CRITICAL]

    @property
    def unfixed_gaps(self) -> List[Gap]:
        return [g for g in self.gaps if not g.fixed]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_gaps": self.total_gaps,
            "fixed_count": self.fixed_count,
            "failed_count": self.failed_count,
            "gaps": [g.to_dict() for g in self.gaps],
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Gap Analysis Report",
            f"\n**Generated:** {self.timestamp}",
            "\n## Summary",
            f"- **Total Gaps:** {self.total_gaps}",
            f"- **Fixed:** {self.fixed_count}",
            f"- **Failed:** {self.failed_count}",
            f"- **Remaining:** {len(self.unfixed_gaps)}",
        ]

        if self.critical_gaps:
            lines.append("\n## ⚠️ Critical Issues")
            for gap in self.critical_gaps:
                status = "✅" if gap.fixed else "❌"
                lines.append(f"- {status} **{gap.description}** ({gap.location})")

        for severity in [GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]:
            gaps = [g for g in self.gaps if g.severity == severity]
            if gaps:
                lines.append(f"\n## {severity.value.title()} Priority")
                for gap in gaps:
                    status = "✅" if gap.fixed else "⬜"
                    lines.append(f"- {status} {gap.description}")

        return "\n".join(lines)


class GapAnalyzer:
    """
    Comprehensive gap analyzer and auto-repair system.
    
    Features:
    - Progressive gap detection
    - Auto-repair capabilities
    - Validation checks
    - Report generation
    """

    def __init__(self):
        self._gaps: List[Gap] = []
        self._checks: List[Tuple[str, Callable]] = []
        self._setup_checks()

    def _setup_checks(self):
        """Set up all gap checks."""
        # Import checks
        self._checks.extend([
            ("core_imports", self._check_core_imports),
            ("agent_imports", self._check_agent_imports),
            ("dashboard_imports", self._check_dashboard_imports),
            ("workflow_imports", self._check_workflow_imports),
        ])

        # Config checks
        self._checks.extend([
            ("env_file", self._check_env_file),
            ("settings_file", self._check_settings_file),
            ("api_keys", self._check_api_keys),
        ])

        # File checks
        self._checks.extend([
            ("directories", self._check_directories),
            ("n8n_workflows", self._check_n8n_workflows),
            ("init_files", self._check_init_files),
        ])

        # Integration checks
        self._checks.extend([
            ("database", self._check_database),
            ("llm_connection", self._check_llm_connection),
            ("voice_system", self._check_voice_system),
        ])

        # Test checks
        self._checks.extend([
            ("test_coverage", self._check_test_coverage),
        ])

    def add_gap(self, gap: Gap):
        """Add a gap to the list."""
        self._gaps.append(gap)

    async def analyze(self, auto_fix: bool = True) -> AnalysisReport:
        """
        Run full gap analysis.
        
        Args:
            auto_fix: Automatically fix auto-fixable gaps
            
        Returns:
            AnalysisReport with all findings
        """
        self._gaps = []

        secure_logger.info("Starting gap analysis...")

        # Run all checks
        for check_name, check_func in self._checks:
            try:
                await self._run_check(check_name, check_func)
            except Exception as e:
                self.add_gap(Gap(
                    id=f"check_error_{check_name}",
                    category=GapCategory.INTEGRATION,
                    severity=GapSeverity.HIGH,
                    description=f"Check '{check_name}' failed: {str(e)}",
                    location=check_name,
                    error=traceback.format_exc(),
                ))

        # Auto-fix if enabled
        report = AnalysisReport(gaps=self._gaps)

        if auto_fix:
            await self._auto_fix_gaps(report)

        secure_logger.info(f"Gap analysis complete: {report.total_gaps} gaps found, {report.fixed_count} fixed")

        return report

    async def _run_check(self, name: str, func: Callable):
        """Run a single check."""
        if asyncio.iscoroutinefunction(func):
            await func()
        else:
            func()

    async def _auto_fix_gaps(self, report: AnalysisReport):
        """Auto-fix all fixable gaps."""
        for gap in report.gaps:
            if gap.auto_fixable and gap.fix_function:
                try:
                    if asyncio.iscoroutinefunction(gap.fix_function):
                        await gap.fix_function()
                    else:
                        gap.fix_function()
                    gap.fixed = True
                    report.fixed_count += 1
                    secure_logger.info(f"Fixed gap: {gap.description}")
                except Exception as e:
                    gap.error = str(e)
                    report.failed_count += 1
                    secure_logger.error(f"Failed to fix gap: {gap.description} - {e}")

    # ============================================
    # Import Checks
    # ============================================

    def _check_core_imports(self):
        """Check core module imports."""
        modules = [
            ("src.core.config", "get_settings"),
            ("src.core.cache", "get_cache"),
            ("src.core.health", "check_health"),
            ("src.core.memory", "get_memory_store"),
            ("src.core.realtime", "get_event_bus"),
            ("src.core.settings_manager", "get_settings_manager"),
            ("src.core.hotkey_manager", "get_hotkey_manager"),
            ("src.core.plugins", "get_plugin_manager"),
        ]

        for module_name, attr_name in modules:
            try:
                module = importlib.import_module(module_name)
                if not hasattr(module, attr_name):
                    self.add_gap(Gap(
                        id=f"missing_attr_{module_name}_{attr_name}",
                        category=GapCategory.IMPORT,
                        severity=GapSeverity.HIGH,
                        description=f"Missing {attr_name} in {module_name}",
                        location=module_name,
                    ))
            except ImportError as e:
                self.add_gap(Gap(
                    id=f"import_error_{module_name}",
                    category=GapCategory.IMPORT,
                    severity=GapSeverity.CRITICAL,
                    description=f"Cannot import {module_name}: {e}",
                    location=module_name,
                ))

    def _check_agent_imports(self):
        """Check agent imports."""
        agents = [
            "ResearchAgent",
            "SynthesisAgent",
            "VoiceAgent",
            "AutomationAgent",
            "CodeAgent",
        ]

        try:
            from src import agents as agents_module
            for agent_name in agents:
                if not hasattr(agents_module, agent_name):
                    self.add_gap(Gap(
                        id=f"missing_agent_{agent_name}",
                        category=GapCategory.IMPORT,
                        severity=GapSeverity.HIGH,
                        description=f"Missing agent: {agent_name}",
                        location="src.agents",
                    ))
        except ImportError as e:
            self.add_gap(Gap(
                id="agents_import_error",
                category=GapCategory.IMPORT,
                severity=GapSeverity.CRITICAL,
                description=f"Cannot import agents module: {e}",
                location="src.agents",
            ))

    def _check_dashboard_imports(self):
        """Check dashboard imports."""
        try:
            from src.dashboard.app import create_app
            from src.dashboard.settings_routes import router as settings_router
            from src.dashboard.agent_routes import router as agent_router
            from src.dashboard.memory_routes import router as memory_router
            from src.dashboard.webhook_routes import router as webhook_router
        except ImportError as e:
            self.add_gap(Gap(
                id="dashboard_import_error",
                category=GapCategory.IMPORT,
                severity=GapSeverity.HIGH,
                description=f"Dashboard import error: {e}",
                location="src.dashboard",
            ))

    def _check_workflow_imports(self):
        """Check workflow imports."""
        try:
            from src.workflows import N8NClient, WorkflowOrchestrator, get_orchestrator
        except ImportError as e:
            self.add_gap(Gap(
                id="workflow_import_error",
                category=GapCategory.IMPORT,
                severity=GapSeverity.MEDIUM,
                description=f"Workflow import error: {e}",
                location="src.workflows",
            ))

    # ============================================
    # Config Checks
    # ============================================

    def _check_env_file(self):
        """Check .env file exists and has required keys."""
        env_path = Path(".env")

        if not env_path.exists():
            self.add_gap(Gap(
                id="missing_env_file",
                category=GapCategory.CONFIG,
                severity=GapSeverity.CRITICAL,
                description=".env file is missing",
                location=".env",
                auto_fixable=True,
                fix_action="Create .env from .env.example",
                fix_function=self._fix_create_env,
            ))
            return

        content = env_path.read_text()
        required_keys = ["GITHUB_TOKEN"]

        for key in required_keys:
            if key not in content:
                self.add_gap(Gap(
                    id=f"missing_env_key_{key}",
                    category=GapCategory.CONFIG,
                    severity=GapSeverity.HIGH,
                    description=f"Missing {key} in .env",
                    location=".env",
                ))

    def _fix_create_env(self):
        """Create .env from .env.example."""
        example_path = Path(".env.example")
        env_path = Path(".env")

        if example_path.exists():
            env_path.write_text(example_path.read_text())
        else:
            env_path.write_text("# AI Project Synthesizer Environment\nGITHUB_TOKEN=\n")

    def _check_settings_file(self):
        """Check settings file exists."""
        settings_path = Path("config/settings.json")

        if not settings_path.exists():
            self.add_gap(Gap(
                id="missing_settings_file",
                category=GapCategory.CONFIG,
                severity=GapSeverity.LOW,
                description="Settings file missing (will use defaults)",
                location="config/settings.json",
                auto_fixable=True,
                fix_action="Create default settings",
                fix_function=self._fix_create_settings,
            ))

    def _fix_create_settings(self):
        """Create default settings file."""
        from src.core.settings_manager import get_settings_manager
        manager = get_settings_manager()
        manager.save()

    def _check_api_keys(self):
        """Check API keys are configured."""
        import os
        from dotenv import load_dotenv

        # Load .env file
        load_dotenv()

        keys = {
            "GITHUB_TOKEN": GapSeverity.HIGH,
            "ELEVENLABS_API_KEY": GapSeverity.MEDIUM,
            "OPENAI_API_KEY": GapSeverity.LOW,
            "ANTHROPIC_API_KEY": GapSeverity.LOW,
        }

        for key, severity in keys.items():
            value = os.environ.get(key, "")
            if not value or value == "your_token_here" or value.startswith("your_"):
                self.add_gap(Gap(
                    id=f"missing_api_key_{key}",
                    category=GapCategory.CONFIG,
                    severity=severity,
                    description=f"API key {key} not configured",
                    location=".env",
                ))

    # ============================================
    # File Checks
    # ============================================

    def _check_directories(self):
        """Check required directories exist."""
        dirs = [
            ("data", "Data storage"),
            ("config", "Configuration"),
            ("logs", "Log files"),
            ("cache", "Cache storage"),
        ]

        for dir_name, description in dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                self.add_gap(Gap(
                    id=f"missing_dir_{dir_name}",
                    category=GapCategory.FILE,
                    severity=GapSeverity.LOW,
                    description=f"Missing directory: {dir_name} ({description})",
                    location=dir_name,
                    auto_fixable=True,
                    fix_action=f"Create {dir_name} directory",
                    fix_function=lambda d=dir_name: Path(d).mkdir(exist_ok=True),
                ))

    def _check_n8n_workflows(self):
        """Check n8n workflow files exist."""
        workflow_dir = Path("src/automation/n8n_workflows")

        if not workflow_dir.exists():
            self.add_gap(Gap(
                id="missing_n8n_workflows_dir",
                category=GapCategory.FILE,
                severity=GapSeverity.MEDIUM,
                description="n8n workflows directory missing",
                location="src/automation/n8n_workflows",
            ))
            return

        workflows = list(workflow_dir.glob("*.json"))
        if len(workflows) < 5:
            self.add_gap(Gap(
                id="insufficient_n8n_workflows",
                category=GapCategory.FILE,
                severity=GapSeverity.LOW,
                description=f"Only {len(workflows)} n8n workflows found",
                location="src/automation/n8n_workflows",
            ))

    def _check_init_files(self):
        """Check __init__.py files exist in all packages."""
        src_path = Path("src")

        for dir_path in src_path.rglob("*"):
            if dir_path.is_dir() and not dir_path.name.startswith("__"):
                init_file = dir_path / "__init__.py"
                if not init_file.exists():
                    # Check if there are .py files in the directory
                    py_files = list(dir_path.glob("*.py"))
                    if py_files:
                        self.add_gap(Gap(
                            id=f"missing_init_{dir_path.name}",
                            category=GapCategory.FILE,
                            severity=GapSeverity.MEDIUM,
                            description=f"Missing __init__.py in {dir_path}",
                            location=str(dir_path),
                            auto_fixable=True,
                            fix_action="Create __init__.py",
                            fix_function=lambda p=init_file: p.write_text('"""Package."""\n'),
                        ))

    # ============================================
    # Integration Checks
    # ============================================

    async def _check_database(self):
        """Check database connectivity."""
        try:
            from src.core.memory import get_memory_store
            store = get_memory_store()
            # Try a simple operation
            store.get_search_history(limit=1)
        except Exception as e:
            self.add_gap(Gap(
                id="database_error",
                category=GapCategory.DATABASE,
                severity=GapSeverity.HIGH,
                description=f"Database error: {e}",
                location="data/memory.db",
            ))

    async def _check_llm_connection(self):
        """Check LLM connectivity."""
        try:
            from src.llm import LMStudioClient
            client = LMStudioClient()
            # Don't actually call, just check import
        except Exception as e:
            self.add_gap(Gap(
                id="llm_connection_error",
                category=GapCategory.INTEGRATION,
                severity=GapSeverity.MEDIUM,
                description=f"LLM connection issue: {e}",
                location="src.llm",
            ))

    async def _check_voice_system(self):
        """Check voice system."""
        try:
            from src.voice import get_voice_manager
            manager = get_voice_manager()
            voices = manager.list_voices()
            if not voices:
                self.add_gap(Gap(
                    id="no_voices_available",
                    category=GapCategory.INTEGRATION,
                    severity=GapSeverity.LOW,
                    description="No voices available in voice manager",
                    location="src.voice",
                ))
        except Exception as e:
            self.add_gap(Gap(
                id="voice_system_error",
                category=GapCategory.INTEGRATION,
                severity=GapSeverity.MEDIUM,
                description=f"Voice system error: {e}",
                location="src.voice",
            ))

    # ============================================
    # Test Checks
    # ============================================

    def _check_test_coverage(self):
        """Check test coverage."""
        test_dir = Path("tests")

        if not test_dir.exists():
            self.add_gap(Gap(
                id="missing_tests_dir",
                category=GapCategory.TEST,
                severity=GapSeverity.HIGH,
                description="Tests directory missing",
                location="tests/",
            ))
            return

        test_files = list(test_dir.glob("test_*.py"))
        if len(test_files) < 5:
            self.add_gap(Gap(
                id="insufficient_tests",
                category=GapCategory.TEST,
                severity=GapSeverity.MEDIUM,
                description=f"Only {len(test_files)} test files found",
                location="tests/",
            ))

        # Check for key test files
        required_tests = [
            "test_core_memory.py",
            "test_settings_manager.py",
            "test_agents.py",
        ]

        for test_file in required_tests:
            if not (test_dir / test_file).exists():
                self.add_gap(Gap(
                    id=f"missing_test_{test_file}",
                    category=GapCategory.TEST,
                    severity=GapSeverity.LOW,
                    description=f"Missing test file: {test_file}",
                    location=f"tests/{test_file}",
                ))


# Global analyzer
_analyzer: Optional[GapAnalyzer] = None


def get_gap_analyzer() -> GapAnalyzer:
    """Get or create gap analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = GapAnalyzer()
    return _analyzer


async def run_gap_analysis(auto_fix: bool = True) -> AnalysisReport:
    """Run gap analysis and return report."""
    analyzer = get_gap_analyzer()
    return await analyzer.analyze(auto_fix=auto_fix)
