"""
Rules Engine for VIBE MCP

Manages and injects rules automatically:
- Security rules: Prevent vulnerabilities
- Style rules: Enforce coding standards
- Project rules: Project-specific conventions
- Priority handling: Security > Project > Style

Rules are loaded from YAML configuration files and can be
dynamically applied based on context.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from src.core.config import get_settings


class RuleCategory(Enum):
    """Categories of rules."""
    SECURITY = "security"
    STYLE = "style"
    PROJECT = "project"
    PATTERN = "pattern"
    PERFORMANCE = "performance"


class RulePriority(Enum):
    """Priority levels for rules."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class Rule:
    """Represents a single rule."""
    id: str
    name: str
    description: str
    category: RuleCategory
    priority: RulePriority
    pattern: str | None = None  # Regex pattern to match
    conditions: dict[str, Any] | None = None
    action: str | None = None  # What to do when rule matches
    examples: list[str] = None
    tags: set[str] = None

    def __post_init__(self):
        if self.examples is None:
            self.examples = []
        if self.tags is None:
            self.tags = set()


@dataclass
class RuleSet:
    """A collection of rules for a specific context."""
    name: str
    description: str
    rules: list[Rule]
    context: dict[str, Any]


class RulesEngine:
    """
    Manages and applies rules for code generation.

    Features:
    - YAML-based rule definitions
    - Context-aware rule selection
    - Priority-based conflict resolution
    - Dynamic rule loading
    - Rule inheritance and overrides
    """

    def __init__(self):
        self.config = get_settings()
        self.rules: dict[str, Rule] = {}
        self.rule_sets: dict[str, RuleSet] = {}

        # Rule directories
        self.rules_dir = Path("config/rules")
        self.rules_dir.mkdir(parents=True, exist_ok=True)

        # Load default rules
        self._load_default_rules()

        # Load custom rules from files
        self._load_custom_rules()

    def _load_default_rules(self) -> None:
        """Load built-in default rules."""
        # Security rules
        security_rules = [
            Rule(
                id="sec_001",
                name="No hardcoded secrets",
                description="Never hardcode passwords, API keys, or secrets in code",
                category=RuleCategory.SECURITY,
                priority=RulePriority.CRITICAL,
                pattern=r"(password|secret|key|token)\s*=\s*['\"][^'\"]{8,}['\"]",
                tags={"security", "secrets", "credentials"}
            ),
            Rule(
                id="sec_002",
                name="SQL injection prevention",
                description="Always use parameterized queries to prevent SQL injection",
                category=RuleCategory.SECURITY,
                priority=RulePriority.CRITICAL,
                pattern=r"f\"[^\"]*\{[^}]*\}[^\"]*SELECT|INSERT|UPDATE|DELETE",
                action="Use parameterized queries or ORM",
                tags={"security", "sql", "injection"}
            ),
            Rule(
                id="sec_003",
                name="Input validation",
                description="Validate all user input before processing",
                category=RuleCategory.SECURITY,
                priority=RulePriority.HIGH,
                conditions={"has_user_input": True},
                tags={"security", "validation", "input"}
            ),
            Rule(
                id="sec_004",
                name="No eval/exec",
                description="Avoid using eval() or exec() with user input",
                category=RuleCategory.SECURITY,
                priority=RulePriority.CRITICAL,
                pattern=r"\b(eval|exec)\s*\(",
                tags={"security", "code_injection"}
            ),
            Rule(
                id="sec_005",
                name="HTTPS only",
                description="Always use HTTPS for external API calls",
                category=RuleCategory.SECURITY,
                priority=RulePriority.HIGH,
                pattern=r"http://(?!localhost)",
                action="Replace with https://",
                tags={"security", "https", "api"}
            )
        ]

        # Style rules
        style_rules = [
            Rule(
                id="style_001",
                name="Type hints required",
                description="Add type hints to all function signatures",
                category=RuleCategory.STYLE,
                priority=RulePriority.MEDIUM,
                conditions={"language": "python"},
                tags={"style", "python", "types"}
            ),
            Rule(
                id="style_002",
                name="Descriptive variable names",
                description="Use descriptive variable names, not single letters",
                category=RuleCategory.STYLE,
                priority=RulePriority.MEDIUM,
                pattern=r"\b[a-z]\b\s*=",
                action="Use descriptive names",
                tags={"style", "naming"}
            ),
            Rule(
                id="style_003",
                name="Function length limit",
                description="Keep functions under 50 lines",
                category=RuleCategory.STYLE,
                priority=RulePriority.LOW,
                conditions={"function_length": 50},
                tags={"style", "complexity"}
            ),
            Rule(
                id="style_004",
                name="Docstring required",
                description="Add docstrings to all public functions and classes",
                category=RuleCategory.STYLE,
                priority=RulePriority.MEDIUM,
                conditions={"is_public": True},
                tags={"style", "documentation"}
            )
        ]

        # Pattern rules
        pattern_rules = [
            Rule(
                id="pattern_001",
                name="Error handling pattern",
                description="Use try-except blocks for error-prone operations",
                category=RuleCategory.PATTERN,
                priority=RulePriority.HIGH,
                conditions={"has_risky_operation": True},
                tags={"pattern", "error_handling"}
            ),
            Rule(
                id="pattern_002",
                name="Async/await for I/O",
                description="Use async/await for I/O operations",
                category=RuleCategory.PATTERN,
                priority=RulePriority.HIGH,
                conditions={"has_io_operation": True},
                tags={"pattern", "async", "performance"}
            ),
            Rule(
                id="pattern_003",
                name="Dependency injection",
                description="Use dependency injection for better testability",
                category=RuleCategory.PATTERN,
                priority=RulePriority.MEDIUM,
                conditions={"has_dependencies": True},
                tags={"pattern", "architecture", "testing"}
            )
        ]

        # Register all rules
        for rule in security_rules + style_rules + pattern_rules:
            self.register_rule(rule)

    def _load_custom_rules(self) -> None:
        """Load custom rules from YAML files."""
        if not self.rules_dir.exists():
            return

        # Load each YAML file
        for yaml_file in self.rules_dir.glob("*.yaml"):
            try:
                with open(yaml_file) as f:
                    data = yaml.safe_load(f)

                # Parse rules
                if isinstance(data, dict) and "rules" in data:
                    rule_set = RuleSet(
                        name=data.get("name", yaml_file.stem),
                        description=data.get("description", ""),
                        rules=[],
                        context=data.get("context", {})
                    )

                    for rule_data in data["rules"]:
                        rule = self._parse_rule_from_yaml(rule_data)
                        if rule:
                            self.register_rule(rule)
                            rule_set.rules.append(rule)

                    self.rule_sets[rule_set.name] = rule_set

            except Exception as e:
                print(f"Failed to load rules from {yaml_file}: {e}")

    def _parse_rule_from_yaml(self, data: dict[str, Any]) -> Rule | None:
        """Parse a rule from YAML data."""
        try:
            return Rule(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                category=RuleCategory(data["category"]),
                priority=RulePriority(data["priority"]),
                pattern=data.get("pattern"),
                conditions=data.get("conditions"),
                action=data.get("action"),
                examples=data.get("examples", []),
                tags=set(data.get("tags", []))
            )
        except KeyError as e:
            print(f"Missing required field in rule: {e}")
            return None

    def register_rule(self, rule: Rule) -> None:
        """Register a new rule."""
        self.rules[rule.id] = rule

    def get_rule(self, rule_id: str) -> Rule | None:
        """Get a rule by ID."""
        return self.rules.get(rule_id)

    async def get_applicable_rules(self, prompt: str, context: dict[str, Any] | None = None) -> list[Rule]:
        """
        Get rules applicable to the given prompt and context.

        Args:
            prompt: The user prompt
            context: Additional context (language, project type, etc.)

        Returns:
            List of applicable rules sorted by priority
        """
        applicable = []

        for rule in self.rules.values():
            if self._is_rule_applicable(rule, prompt, context):
                applicable.append(rule)

        # Sort by priority (lower number = higher priority)
        applicable.sort(key=lambda r: r.priority.value)

        return applicable

    def _is_rule_applicable(self, rule: Rule, prompt: str, _context: dict[str, Any] | None) -> bool:
        """Check if a rule applies to the given prompt and context."""
        prompt_lower = prompt.lower()

        # Check pattern match
        if rule.pattern:
            import re
            if not re.search(rule.pattern, prompt_lower):
                return False

        # Check conditions
        if rule.conditions:
            local_context = _context or {}

            for condition, value in rule.conditions.items():
                if condition == "language" and local_context.get("language") != value or condition == "has_user_input" and value and "input" not in prompt_lower:
                    return False
                elif condition == "has_risky_operation" and value:
                    risky_keywords = ["file", "network", "database", "api", "external"]
                    if not any(kw in prompt_lower for kw in risky_keywords):
                        return False
                elif condition == "has_io_operation" and value:
                    io_keywords = ["read", "write", "fetch", "request", "query"]
                    if not any(kw in prompt_lower for kw in io_keywords):
                        return False
                elif condition == "is_public" and value and "test" in prompt_lower:
                    return False  # Test files don't need public docstrings

        return True

    def get_rules_by_category(self, category: RuleCategory) -> list[Rule]:
        """Get all rules in a category."""
        return [r for r in self.rules.values() if r.category == category]

    def get_rules_by_tag(self, tag: str) -> list[Rule]:
        """Get all rules with a specific tag."""
        return [r for r in self.rules.values() if tag in r.tags]

    def resolve_conflicts(self, rules: list[Rule]) -> list[Rule]:
        """
        Resolve conflicts between rules based on priority.

        Args:
            rules: List of potentially conflicting rules

        Returns:
            Resolved list of rules
        """
        # Group by category
        by_category = {}
        for rule in rules:
            if rule.category not in by_category:
                by_category[rule.category] = []
            by_category[rule.category].append(rule)

        resolved = []

        # Keep highest priority rules from each category
        for category, category_rules in by_category.items():
            # Sort by priority
            category_rules.sort(key=lambda r: r.priority.value)

            # Keep top rules (limit per category)
            max_per_category = {
                RuleCategory.SECURITY: 5,
                RuleCategory.STYLE: 3,
                RuleCategory.PATTERN: 3,
                RuleCategory.PROJECT: 5,
                RuleCategory.PERFORMANCE: 2
            }

            max_rules = max_per_category.get(category, 3)
            resolved.extend(category_rules[:max_rules])

        return resolved

    def create_rule_files(self) -> None:
        """Create example rule configuration files."""
        # Security rules file
        security_rules = {
            "name": "security_rules",
            "description": "Security-related rules for code generation",
            "context": {"type": "security"},
            "rules": [
                {
                    "id": "custom_sec_001",
                    "name": "Custom security rule",
                    "description": "Example custom security rule",
                    "category": "security",
                    "priority": 1,
                    "pattern": "dangerous_pattern",
                    "action": "Replace with safe alternative",
                    "tags": ["security", "custom"]
                }
            ]
        }

        # Project-specific rules file
        project_rules = {
            "name": "project_rules",
            "description": "Project-specific conventions",
            "context": {"type": "project", "name": "my_project"},
            "rules": [
                {
                    "id": "proj_001",
                    "name": "Use project logger",
                    "description": "Use the project's logging utility instead of print",
                    "category": "project",
                    "priority": 2,
                    "pattern": r"\bprint\s*\(",
                    "action": "Use logger.info() instead",
                    "tags": ["project", "logging"]
                }
            ]
        }

        # Write files
        with open(self.rules_dir / "security.yaml", 'w') as f:
            yaml.dump(security_rules, f, default_flow_style=False)

        with open(self.rules_dir / "project.yaml", 'w') as f:
            yaml.dump(project_rules, f, default_flow_style=False)

    def export_rules(self, output_path: str) -> None:
        """Export all rules to a YAML file."""
        export_data = {
            "exported_at": self._get_timestamp(),
            "total_rules": len(self.rules),
            "categories": {},
            "rules": []
        }

        # Group by category
        for category in RuleCategory:
            category_rules = self.get_rules_by_category(category)
            export_data["categories"][category.value] = len(category_rules)

            for rule in category_rules:
                rule_dict = {
                    "id": rule.id,
                    "name": rule.name,
                    "description": rule.description,
                    "category": rule.category.value,
                    "priority": rule.priority.value,
                    "tags": list(rule.tags)
                }

                if rule.pattern:
                    rule_dict["pattern"] = rule.pattern
                if rule.action:
                    rule_dict["action"] = rule.action
                if rule.conditions:
                    rule_dict["conditions"] = rule.conditions

                export_data["rules"].append(rule_dict)

        # Write export
        with open(output_path, 'w') as f:
            yaml.dump(export_data, f, default_flow_style=False)

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


# CLI interface for testing
if __name__ == "__main__":
    import asyncio

    async def main():
        engine = RulesEngine()

        # Create example rule files
        engine.create_rule_files()
        print("Created example rule files in config/rules/")

        # Test rule application
        test_prompt = "Create a login API with database authentication"
        context = {"language": "python", "has_user_input": True}

        rules = await engine.get_applicable_rules(test_prompt, context)

        print(f"\nFound {len(rules)} applicable rules for prompt:")
        print(f"'{test_prompt}'")
        print("\nApplicable rules:")
        for rule in rules[:10]:  # Show first 10
            print(f"  - [{rule.category.value.upper()}] {rule.name}")
            print(f"    {rule.description}")

        # Export rules
        engine.export_rules("exported_rules.yaml")
        print("\nExported all rules to exported_rules.yaml")

    asyncio.run(main())
