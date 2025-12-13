"""
Prompt Enhancer for VIBE MCP

Automatically structures user prompts into 3-layer format:
1. Context Layer: Project state, stack, component references
2. Task Layer: Clear instructions and requirements
3. Constraints Layer: Security rules, style guidelines, patterns

Orchestrates RulesEngine and ContextInjector to create enhanced prompts.
"""

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from src.core.config import get_settings
from src.memory.mem0_integration import MemorySystem
from src.vibe.context_injector import ContextInjector
from src.vibe.rules_engine import RulesEngine


class PromptComplexity(Enum):
    """Complexity levels of prompts."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class PromptLayer:
    """Represents a layer in the enhanced prompt."""
    name: str
    content: str
    priority: int  # 1 = highest priority


@dataclass
class EnhancedPrompt:
    """Complete enhanced prompt with all layers."""
    original: str
    layers: list[PromptLayer]
    complexity: PromptComplexity
    metadata: dict[str, Any]
    enhancement_version: str = "1.0"


class PromptEnhancer:
    """
    Enhances user prompts with context and constraints.

    Features:
    - 3-layer prompt structure
    - Automatic rule injection
    - Context awareness
    - Complexity detection
    - Learning from successful prompts
    """

    def __init__(self):
        self.config = get_settings()
        self.rules_engine = RulesEngine()
        self.context_injector = ContextInjector()
        self.memory = MemorySystem()

        # Enhancement configuration
        self.enable_enhancement = self.config.get("prompt_enhancement", {}).get("enabled", True)
        self.min_complexity_for_enhancement = PromptComplexity.SIMPLE

        # Layer templates
        self.layer_templates = {
            "context": """CONTEXT:
Project: {project_name}
Stack: {tech_stack}
Current State: {current_state}
Component References: {components}
Past Decisions: {decisions}
""",
            "task": """TASK:
{task_description}

Requirements:
{requirements}

Expected Output:
{expected_output}
""",
            "constraints": """CONSTRAINTS:
Security Rules:
{security_rules}

Style Guidelines:
{style_rules}

Code Patterns:
{code_patterns}

Additional Constraints:
{additional_constraints}
"""
        }

    async def enhance(self, user_prompt: str, project_context: dict[str, Any] | None = None,
                     force_enhance: bool = False) -> EnhancedPrompt:
        """
        Enhance a user prompt with context and constraints.

        Args:
            user_prompt: Original user prompt
            project_context: Project-specific context
            force_enhance: Force enhancement even for simple prompts

        Returns:
            EnhancedPrompt with structured layers
        """
        # Detect complexity
        complexity = self._detect_complexity(user_prompt)

        # Skip enhancement for simple prompts unless forced
        if not self.enable_enhancement and not force_enhance and complexity == self.min_complexity_for_enhancement:
                return EnhancedPrompt(
                    original=user_prompt,
                    layers=[PromptLayer("task", user_prompt, 1)],
                    complexity=complexity,
                    metadata={"enhanced": False}
                )

        # Build layers
        layers = []

        # Layer 1: Context (priority 3)
        context_layer = await self._build_context_layer(user_prompt, project_context)
        if context_layer.content.strip():
            layers.append(context_layer)

        # Layer 2: Task (priority 1 - most important)
        task_layer = self._build_task_layer(user_prompt)
        layers.append(task_layer)

        # Layer 3: Constraints (priority 2)
        constraints_layer = await self._build_constraints_layer(user_prompt, project_context)
        if constraints_layer.content.strip():
            layers.append(constraints_layer)

        # Sort by priority
        layers.sort(key=lambda x: x.priority)

        # Create enhanced prompt
        enhanced = EnhancedPrompt(
            original=user_prompt,
            layers=layers,
            complexity=complexity,
            metadata={
                "enhanced": True,
                "layer_count": len(layers),
                "project_context": bool(project_context),
                "timestamp": self._get_timestamp()
            }
        )

        return enhanced

    def _detect_complexity(self, prompt: str) -> PromptComplexity:
        """Detect the complexity of a user prompt."""
        # Simple indicators
        simple_indicators = [
            r"^(what|how|why|when|where)\b",
            r"^(show|tell|list|get)\b",
            r"\b(explain|describe)\b",
            r"^.+$"  # Very short prompts
        ]

        # Complex indicators
        complex_indicators = [
            r"\b(build|create|implement|develop|design)\b",
            r"\b(integrate|connect|combine)\b",
            r"\b(system|application|api|service)\b",
            r"\b(multiple|several|various)\b",
            r"\b(requirements|specifications|constraints)\b",
            r"\b(test|deploy|optimize|refactor)\b"
        ]

        prompt_lower = prompt.lower()

        # Check for complex indicators first
        for pattern in complex_indicators:
            if re.search(pattern, prompt_lower):
                return PromptComplexity.COMPLEX

        # Check for simple indicators
        for pattern in simple_indicators:
            if re.search(pattern, prompt_lower) and len(prompt) < 100:
                return PromptComplexity.SIMPLE

        # Default to moderate
        return PromptComplexity.MODERATE

    async def _build_context_layer(self, prompt: str, _project_context: dict[str, Any] | None) -> PromptLayer:
        """Build the context layer of the enhanced prompt."""
        # Get context from injector
        context_data = await self.context_injector.get_context(prompt, _project_context)

        # Format using template
        content = self.layer_templates["context"].format(
            project_name=context_data.get("project_name", "Unknown"),
            tech_stack=", ".join(context_data.get("tech_stack", [])),
            current_state=context_data.get("current_state", "Not specified"),
            components="\n".join(f"- {c}" for c in context_data.get("components", [])),
            decisions="\n".join(f"- {d}" for d in context_data.get("past_decisions", [])[:3])
        )

        return PromptLayer(
            name="context",
            content=content.strip(),
            priority=3
        )

    def _build_task_layer(self, prompt: str) -> PromptLayer:
        """Build the task layer from user prompt."""
        # Extract requirements from prompt
        requirements = self._extract_requirements(prompt)
        expected_output = self._extract_expected_output(prompt)

        # Format using template
        content = self.layer_templates["task"].format(
            task_description=prompt.strip(),
            requirements="\n".join(f"- {r}" for r in requirements) if requirements else "- Complete the requested task",
            expected_output=expected_output or "Functional code that meets the requirements"
        )

        return PromptLayer(
            name="task",
            content=content.strip(),
            priority=1
        )

    async def _build_constraints_layer(self, prompt: str, _project_context: dict[str, Any] | None) -> PromptLayer:
        """Build the constraints layer using rules engine."""
        # Get applicable rules
        rules = await self.rules_engine.get_applicable_rules(prompt, _project_context)

        # Categorize rules
        security_rules = [r for r in rules if r.category == "security"]
        style_rules = [r for r in rules if r.category == "style"]
        code_patterns = [r for r in rules if r.category == "pattern"]
        other_rules = [r for r in rules if r.category not in ["security", "style", "pattern"]]

        # Format using template
        content = self.layer_templates["constraints"].format(
            security_rules="\n".join(f"- {r.description}" for r in security_rules[:5]),
            style_rules="\n".join(f"- {r.description}" for r in style_rules[:5]),
            code_patterns="\n".join(f"- {r.description}" for r in code_patterns[:5]),
            additional_constraints="\n".join(f"- {r.description}" for r in other_rules[:3])
        )

        return PromptLayer(
            name="constraints",
            content=content.strip(),
            priority=2
        )

    def _extract_requirements(self, prompt: str) -> list[str]:
        """Extract explicit requirements from prompt."""
        requirements = []

        # Look for requirement patterns
        patterns = [
            r"(?:require|must|should|need to|needs to)\s+([^,.!?]+)",
            r"(?:with|including|that has|which has)\s+([^,.!?]+)",
            r"(?:support|handle|process|manage)\s+([^,.!?]+)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, prompt, re.IGNORECASE)
            requirements.extend(matches)

        # Clean up requirements
        requirements = [r.strip() for r in requirements if len(r.strip()) > 3]

        return requirements[:5]  # Limit to 5 requirements

    def _extract_expected_output(self, prompt: str) -> str | None:
        """Extract expected output from prompt."""
        patterns = [
            r"(?:output|result|return|produce|generate)\s+(?:should|must|will)\s+([^,.!?]+)",
            r"(?:I want|I need|create)\s+(?:a|an)\s+([^,.!?]+)",
            r"(?:build|create|make)\s+(?:a|an)\s+([^,.!?]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

    def format_prompt(self, enhanced: EnhancedPrompt) -> str:
        """Format enhanced prompt into final string."""
        if not enhanced.metadata.get("enhanced", False):
            return enhanced.original

        sections = []

        for layer in enhanced.layers:
            if layer.content.strip():
                sections.append(layer.content)

        # Add metadata note
        sections.append(
            f"\n[This prompt has been enhanced by VIBE MCP - Complexity: {enhanced.complexity.value}]"
        )

        return "\n\n".join(sections)

    async def learn_from_outcome(self, enhanced: EnhancedPrompt, outcome: dict[str, Any]) -> None:
        """
        Learn from the outcome of using an enhanced prompt.

        Args:
            enhanced: The enhanced prompt that was used
            outcome: Result including success, quality metrics, etc.
        """
        # Only learn from successful outcomes
        if not outcome.get("success", False):
            return

        # Store in memory if quality was high
        quality_score = outcome.get("quality_score", 0)
        if quality_score >= 7.0:  # High quality threshold
            memory_entry = {
                "type": "successful_prompt",
                "original": enhanced.original,
                "enhanced": self.format_prompt(enhanced),
                "complexity": enhanced.complexity.value,
                "quality": quality_score,
                "outcome": outcome
            }

            await self.memory.add(
                content=json.dumps(memory_entry),
                category="PATTERN",
                tags=["prompt", "enhanced", enhanced.complexity.value],
                importance=0.7
            )

    async def get_similar_prompts(self, prompt: str, limit: int = 5) -> list[dict[str, Any]]:
        """
        Get similar successful prompts from memory.

        Args:
            prompt: The prompt to find similarities for
            limit: Maximum number of results

        Returns:
            List of similar prompt entries
        """
        # Search memory for similar prompts
        results = await self.memory.search(
            query=prompt,
            category="PATTERN",
            tags=["prompt", "enhanced"],
            limit=limit
        )

        # Parse and return
        similar = []
        for result in results:
            try:
                entry = json.loads(result["content"])
                similar.append(entry)
            except json.JSONDecodeError:
                continue

        return similar

    def create_config_file(self, config_path: str = "config/prompt_enhancement.yaml") -> None:
        """Create default configuration file."""
        config = {
            "enabled": True,
            "min_complexity": "simple",
            "layers": {
                "context": {
                    "enabled": True,
                    "priority": 3,
                    "max_decisions": 3,
                    "max_components": 10
                },
                "task": {
                    "enabled": True,
                    "priority": 1,
                    "extract_requirements": True,
                    "extract_output": True
                },
                "constraints": {
                    "enabled": True,
                    "priority": 2,
                    "max_rules_per_category": 5,
                    "security_first": True
                }
            },
            "learning": {
                "store_successful": True,
                "quality_threshold": 7.0,
                "max_memory_entries": 1000
            }
        }

        # Ensure directory exists
        Path(config_path).parent.mkdir(parents=True, exist_ok=True)

        # Write config
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)


# CLI interface for testing
if __name__ == "__main__":
    import asyncio
    import sys

    async def main():
        enhancer = PromptEnhancer()

        if len(sys.argv) > 1:
            # Enhance prompt from file
            prompt_file = sys.argv[1]
            try:
                with open(prompt_file) as f:
                    prompt = f.read().strip()

                enhanced = await enhancer.enhance(prompt)
                formatted = enhancer.format_prompt(enhanced)

                print("=" * 60)
                print("ENHANCED PROMPT:")
                print("=" * 60)
                print(formatted)
                print("\n" + "=" * 60)
                print(f"Complexity: {enhanced.complexity.value}")
                print(f"Layers: {len(enhanced.layers)}")
                print("=" * 60)

            except FileNotFoundError:
                print(f"File not found: {prompt_file}")
        else:
            # Demo enhancement
            demo_prompts = [
                "Create a login API with OAuth",
                "What is Python?",
                "Build a complete e-commerce system with user auth, payment processing, inventory management, and admin dashboard"
            ]

            for prompt in demo_prompts:
                print(f"\nOriginal: {prompt}")
                enhanced = await enhancer.enhance(prompt)
                print(f"Complexity: {enhanced.complexity.value}")
                print(f"Enhanced: {enhanced.metadata.get('enhanced', False)}")
                print("-" * 40)

    asyncio.run(main())
