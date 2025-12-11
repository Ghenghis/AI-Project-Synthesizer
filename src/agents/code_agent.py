"""
AI Project Synthesizer - Code Agent

AI-powered code agent for:
- Code generation
- Bug fixing
- Code review
- Refactoring
- Documentation
"""

import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path

from src.agents.base import BaseAgent, AgentConfig, AgentTool
from src.core.security import get_secure_logger

secure_logger = get_secure_logger(__name__)


class CodeAgent(BaseAgent):
    """
    Code agent for code-related tasks.
    
    Features:
    - Generate code from descriptions
    - Fix bugs and errors
    - Review code quality
    - Refactor code
    - Generate documentation
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        config = config or AgentConfig(
            name="code_agent",
            description="Generates and improves code",
            auto_continue=True,
            max_iterations=10,
        )
        super().__init__(config)
        self._setup_tools()
    
    def _setup_tools(self):
        """Set up code tools."""
        self.register_tool(AgentTool(
            name="generate_code",
            description="Generate code from description",
            func=self._generate_code,
            parameters={
                "description": {"type": "string"},
                "language": {"type": "string"},
                "style": {"type": "string", "enum": ["minimal", "documented", "production"]},
            },
        ))
        
        self.register_tool(AgentTool(
            name="fix_code",
            description="Fix bugs in code",
            func=self._fix_code,
            parameters={
                "code": {"type": "string"},
                "error": {"type": "string"},
                "language": {"type": "string"},
            },
        ))
        
        self.register_tool(AgentTool(
            name="review_code",
            description="Review code for quality issues",
            func=self._review_code,
            parameters={
                "code": {"type": "string"},
                "language": {"type": "string"},
            },
        ))
        
        self.register_tool(AgentTool(
            name="refactor_code",
            description="Refactor code for better quality",
            func=self._refactor_code,
            parameters={
                "code": {"type": "string"},
                "goal": {"type": "string"},
                "language": {"type": "string"},
            },
        ))
        
        self.register_tool(AgentTool(
            name="generate_docs",
            description="Generate documentation for code",
            func=self._generate_docs,
            parameters={
                "code": {"type": "string"},
                "language": {"type": "string"},
                "style": {"type": "string", "enum": ["docstring", "markdown", "readme"]},
            },
        ))
        
        self.register_tool(AgentTool(
            name="explain_code",
            description="Explain what code does",
            func=self._explain_code,
            parameters={
                "code": {"type": "string"},
                "language": {"type": "string"},
            },
        ))
    
    async def _generate_code(
        self,
        description: str,
        language: str = "python",
        style: str = "production",
    ) -> Dict[str, Any]:
        """Generate code from description."""
        llm = await self._get_llm()
        
        style_instructions = {
            "minimal": "Write minimal, concise code without comments.",
            "documented": "Include docstrings and inline comments.",
            "production": "Write production-ready code with full documentation, error handling, type hints, and tests.",
        }
        
        prompt = f"""Generate {language} code for: {description}

Style: {style_instructions.get(style, style_instructions['production'])}

Requirements:
- Follow {language} best practices
- Include necessary imports
- Handle errors appropriately
- Use type hints where applicable

Return ONLY the code, no explanations."""
        
        code = await llm.complete(prompt)
        
        # Clean up code
        if "```" in code:
            parts = code.split("```")
            if len(parts) >= 2:
                code = parts[1]
                if code.startswith(language):
                    code = "\n".join(code.split("\n")[1:])
        
        return {
            "success": True,
            "code": code.strip(),
            "language": language,
            "style": style,
        }
    
    async def _fix_code(
        self,
        code: str,
        error: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """Fix bugs in code."""
        llm = await self._get_llm()
        
        prompt = f"""Fix the following {language} code that has this error:

Error: {error}

Code:
```{language}
{code}
```

Provide the fixed code. Explain what was wrong briefly, then return the corrected code."""
        
        response = await llm.complete(prompt)
        
        # Extract fixed code
        fixed_code = code
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 2:
                fixed_code = parts[1]
                if fixed_code.startswith(language):
                    fixed_code = "\n".join(fixed_code.split("\n")[1:])
        
        # Extract explanation
        explanation = response.split("```")[0].strip() if "```" in response else ""
        
        return {
            "success": True,
            "original_code": code,
            "fixed_code": fixed_code.strip(),
            "error": error,
            "explanation": explanation,
        }
    
    async def _review_code(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """Review code for quality issues."""
        llm = await self._get_llm()
        
        prompt = f"""Review this {language} code for quality issues:

```{language}
{code}
```

Analyze for:
1. Bugs and potential errors
2. Security vulnerabilities
3. Performance issues
4. Code style and readability
5. Best practices violations

Provide a structured review with severity levels (high/medium/low)."""
        
        review = await llm.complete(prompt)
        
        # Parse review for issues
        issues = []
        for line in review.split("\n"):
            line_lower = line.lower()
            if "high" in line_lower or "critical" in line_lower:
                issues.append({"severity": "high", "issue": line})
            elif "medium" in line_lower:
                issues.append({"severity": "medium", "issue": line})
            elif "low" in line_lower:
                issues.append({"severity": "low", "issue": line})
        
        return {
            "success": True,
            "review": review,
            "issues": issues,
            "issue_count": len(issues),
        }
    
    async def _refactor_code(
        self,
        code: str,
        goal: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """Refactor code."""
        llm = await self._get_llm()
        
        prompt = f"""Refactor this {language} code with the goal: {goal}

Original code:
```{language}
{code}
```

Provide the refactored code that achieves the goal while maintaining functionality."""
        
        response = await llm.complete(prompt)
        
        # Extract refactored code
        refactored = code
        if "```" in response:
            parts = response.split("```")
            if len(parts) >= 2:
                refactored = parts[1]
                if refactored.startswith(language):
                    refactored = "\n".join(refactored.split("\n")[1:])
        
        return {
            "success": True,
            "original_code": code,
            "refactored_code": refactored.strip(),
            "goal": goal,
        }
    
    async def _generate_docs(
        self,
        code: str,
        language: str = "python",
        style: str = "docstring",
    ) -> Dict[str, Any]:
        """Generate documentation."""
        llm = await self._get_llm()
        
        style_prompts = {
            "docstring": f"Add comprehensive docstrings to this {language} code",
            "markdown": f"Generate markdown documentation for this {language} code",
            "readme": f"Generate a README.md for a project containing this {language} code",
        }
        
        prompt = f"""{style_prompts.get(style, style_prompts['docstring'])}:

```{language}
{code}
```

Include:
- Function/class descriptions
- Parameter documentation
- Return value documentation
- Usage examples"""
        
        docs = await llm.complete(prompt)
        
        return {
            "success": True,
            "documentation": docs,
            "style": style,
        }
    
    async def _explain_code(
        self,
        code: str,
        language: str = "python",
    ) -> Dict[str, Any]:
        """Explain what code does."""
        llm = await self._get_llm()
        
        prompt = f"""Explain what this {language} code does in simple terms:

```{language}
{code}
```

Provide:
1. High-level summary
2. Step-by-step breakdown
3. Key concepts used
4. Potential use cases"""
        
        explanation = await llm.complete(prompt)
        
        return {
            "success": True,
            "explanation": explanation,
        }
    
    async def _execute_step(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a code task step."""
        llm = await self._get_llm()
        
        # Build prompt
        tools_desc = "\n".join([
            f"- {t.name}: {t.description}"
            for t in self._tools.values()
        ])
        
        prompt = f"""You are a code agent. Your task: {task}

Available tools:
{tools_desc}

Previous context: {context.get('previous_step', 'None')}

Decide the next action. Respond in this format:
TOOL: <tool_name>
PARAMS: <json_params>

Or if task is complete:
COMPLETE: true
OUTPUT: <final output>
"""
        
        response = await llm.complete(prompt)
        
        # Parse response
        if "COMPLETE: true" in response:
            output = ""
            if "OUTPUT:" in response:
                output = response.split("OUTPUT:")[1].strip()
            
            return {
                "action": "complete",
                "output": output,
                "complete": True,
            }
        
        # Extract tool call
        tool_name = None
        params = {}
        
        if "TOOL:" in response:
            tool_name = response.split("TOOL:")[1].split("\n")[0].strip()
        
        if "PARAMS:" in response:
            import json
            try:
                params_str = response.split("PARAMS:")[1].split("\n")[0].strip()
                params = json.loads(params_str)
            except:
                params = {}
        
        # Execute tool
        if tool_name and tool_name in self._tools:
            tool = self._tools[tool_name]
            result = await tool.execute(**params)
            
            return {
                "action": "tool_call",
                "tool": tool_name,
                "params": params,
                "result": result,
                "complete": False,
            }
        
        return {
            "action": "thinking",
            "output": response,
            "complete": False,
        }
    
    def _should_continue(self, step_result: Dict[str, Any]) -> bool:
        """Check if should continue."""
        return not step_result.get("complete", False)
    
    async def generate(self, description: str, language: str = "python") -> str:
        """
        Generate code from description.
        
        Args:
            description: What the code should do
            language: Programming language
            
        Returns:
            Generated code
        """
        result = await self._generate_code(description, language)
        return result.get("code", "")
    
    async def fix(self, code: str, error: str) -> str:
        """
        Fix code with error.
        
        Args:
            code: Broken code
            error: Error message
            
        Returns:
            Fixed code
        """
        result = await self._fix_code(code, error)
        return result.get("fixed_code", code)
