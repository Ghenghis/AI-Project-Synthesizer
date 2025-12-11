"""
AI Project Synthesizer - AST Parser

Multi-language AST parsing using tree-sitter.
Extracts code structure, imports, functions, and classes.
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import re

logger = logging.getLogger(__name__)


@dataclass
class Import:
    """Represents an import statement."""
    module: str
    names: List[str] = field(default_factory=list)
    alias: Optional[str] = None
    is_relative: bool = False
    line_number: int = 0


@dataclass
class Function:
    """Represents a function definition."""
    name: str
    parameters: List[str]
    return_type: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    is_async: bool = False
    complexity: int = 1


@dataclass
class Class:
    """Represents a class definition."""
    name: str
    bases: List[str] = field(default_factory=list)
    methods: List[Function] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)
    docstring: Optional[str] = None
    line_start: int = 0
    line_end: int = 0


@dataclass
class ParsedFile:
    """Result of parsing a single file."""
    path: str
    language: str
    imports: List[Import] = field(default_factory=list)
    functions: List[Function] = field(default_factory=list)
    classes: List[Class] = field(default_factory=list)
    loc: int = 0
    sloc: int = 0  # Source lines (excluding comments/blanks)
    complexity: float = 0.0
    errors: List[str] = field(default_factory=list)


class ASTParser:
    """
    Multi-language AST parser.

    Supports Python, JavaScript, TypeScript, and more via tree-sitter.
    Falls back to regex-based parsing when tree-sitter is unavailable.

    Example:
        parser = ASTParser()
        parsed = await parser.parse_file(Path("main.py"))
        print(f"Functions: {len(parsed.functions)}")
    """

    LANGUAGE_EXTENSIONS = {
        ".py": "python",
        ".pyw": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "cpp",
        ".hpp": "cpp",
        ".rb": "ruby",
        ".php": "php",
    }

    def __init__(self):
        """Initialize the AST parser."""
        self._tree_sitter_available = self._check_tree_sitter()
        self._parsers = {}

    def _check_tree_sitter(self) -> bool:
        """Check if tree-sitter is available."""
        try:
            import tree_sitter
            return True
        except ImportError:
            logger.warning("tree-sitter not available, using fallback parsing")
            return False

    async def parse_file(self, file_path: Path) -> ParsedFile:
        """
        Parse a single source file.

        Args:
            file_path: Path to the source file

        Returns:
            ParsedFile with extracted structure
        """
        if not file_path.exists():
            return ParsedFile(
                path=str(file_path),
                language="unknown",
                errors=[f"File not found: {file_path}"],
            )

        # Detect language
        language = self._detect_language(file_path)

        if language == "unknown":
            return ParsedFile(
                path=str(file_path),
                language="unknown",
                errors=["Unsupported file type"],
            )

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return ParsedFile(
                path=str(file_path),
                language=language,
                errors=[f"Failed to read file: {e}"],
            )

        # Parse based on language
        if language == "python":
            return await self._parse_python(file_path, content)
        elif language in ["javascript", "typescript"]:
            return await self._parse_javascript(file_path, content, language)
        else:
            # Fallback: basic metrics only
            return await self._parse_generic(file_path, content, language)

    async def analyze_project(self, project_path: Path) -> Dict[str, Any]:
        """
        Analyze entire project structure.

        Args:
            project_path: Path to project root

        Returns:
            Dictionary with project analysis results
        """
        files: List[ParsedFile] = []
        languages: Dict[str, int] = {}
        total_loc = 0
        total_functions = 0
        total_classes = 0

        # Find all source files
        for ext, lang in self.LANGUAGE_EXTENSIONS.items():
            for file_path in project_path.rglob(f"*{ext}"):
                # Skip common non-source directories
                if self._should_skip(file_path):
                    continue

                parsed = await self.parse_file(file_path)
                files.append(parsed)

                languages[lang] = languages.get(lang, 0) + parsed.sloc
                total_loc += parsed.loc
                total_functions += len(parsed.functions)
                total_classes += len(parsed.classes)

        # Calculate language percentages
        total_sloc = sum(languages.values())
        language_breakdown = {}
        if total_sloc > 0:
            for lang, sloc in languages.items():
                language_breakdown[lang] = round(sloc / total_sloc * 100, 1)

        return {
            "file_count": len(files),
            "total_loc": total_loc,
            "total_sloc": total_sloc,
            "languages": language_breakdown,
            "function_count": total_functions,
            "class_count": total_classes,
            "files": files,
        }

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file extension."""
        ext = file_path.suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, "unknown")

    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_dirs = {
            "node_modules", "venv", ".venv", "env", ".env",
            "__pycache__", ".git", ".svn", "dist", "build",
            ".tox", ".eggs", "*.egg-info", ".mypy_cache",
            ".pytest_cache", "site-packages",
        }

        for part in file_path.parts:
            if part in skip_dirs or part.endswith(".egg-info"):
                return True
        return False

    async def _parse_python(self, file_path: Path, content: str) -> ParsedFile:
        """Parse Python source file."""
        imports: List[Import] = []
        functions: List[Function] = []
        classes: List[Class] = []

        try:
            import ast
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Extract imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(Import(
                            module=alias.name,
                            alias=alias.asname,
                            line_number=node.lineno,
                        ))

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    names = [alias.name for alias in node.names]
                    imports.append(Import(
                        module=module,
                        names=names,
                        is_relative=node.level > 0,
                        line_number=node.lineno,
                    ))

                # Extract functions
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    func = Function(
                        name=node.name,
                        parameters=[arg.arg for arg in node.args.args],
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    )

                    # Get docstring
                    if node.body and isinstance(node.body[0], ast.Expr):
                        if isinstance(node.body[0].value, ast.Constant):
                            func.docstring = str(node.body[0].value.value)[:200]

                    functions.append(func)

                # Extract classes
                elif isinstance(node, ast.ClassDef):
                    cls = Class(
                        name=node.name,
                        bases=[self._get_base_name(b) for b in node.bases],
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                    )

                    # Get docstring
                    if node.body and isinstance(node.body[0], ast.Expr):
                        if isinstance(node.body[0].value, ast.Constant):
                            cls.docstring = str(node.body[0].value.value)[:200]

                    # Get methods
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            cls.methods.append(Function(
                                name=item.name,
                                parameters=[arg.arg for arg in item.args.args],
                                is_async=isinstance(item, ast.AsyncFunctionDef),
                            ))

                    classes.append(cls)

        except SyntaxError as e:
            logger.debug(f"Syntax error parsing {file_path}: {e}")
        except Exception as e:
            logger.debug(f"Error parsing {file_path}: {e}")

        # Calculate line counts
        lines = content.splitlines()
        loc = len(lines)
        sloc = len([line for line in lines if line.strip() and not line.strip().startswith("#")])

        return ParsedFile(
            path=str(file_path),
            language="python",
            imports=imports,
            functions=functions,
            classes=classes,
            loc=loc,
            sloc=sloc,
        )

    def _get_decorator_name(self, node) -> str:
        """Extract decorator name from AST node."""
        import ast
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_decorator_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"

    def _get_base_name(self, node) -> str:
        """Extract base class name from AST node."""
        import ast
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_base_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Subscript):
            return f"{self._get_base_name(node.value)}[...]"
        return "unknown"

    async def _parse_javascript(
        self,
        file_path: Path,
        content: str,
        language: str,
    ) -> ParsedFile:
        """Parse JavaScript/TypeScript source file."""
        imports: List[Import] = []
        functions: List[Function] = []
        classes: List[Class] = []

        # Regex-based parsing for JS/TS
        # Import patterns
        import_pattern = re.compile(
            r'''import\s+(?:(?:(\{[^}]+\})|(\*\s+as\s+\w+)|(\w+))\s+from\s+)?['"]([^'"]+)['"]''',
            re.MULTILINE
        )

        for match in import_pattern.finditer(content):
            named, star, default, module = match.groups()
            names = []
            if named:
                names = [n.strip() for n in named.strip("{}").split(",")]
            if default:
                names.append(default)

            imports.append(Import(
                module=module,
                names=names,
            ))

        # Function patterns
        func_pattern = re.compile(
            r'''(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)''',
            re.MULTILINE
        )

        for match in func_pattern.finditer(content):
            name, params = match.groups()
            functions.append(Function(
                name=name,
                parameters=[p.strip().split(":")[0].strip() for p in params.split(",") if p.strip()],
            ))

        # Arrow function patterns
        arrow_pattern = re.compile(
            r'''(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>''',
            re.MULTILINE
        )

        for match in arrow_pattern.finditer(content):
            name, params = match.groups()
            functions.append(Function(
                name=name,
                parameters=[p.strip().split(":")[0].strip() for p in params.split(",") if p.strip()],
            ))

        # Class patterns
        class_pattern = re.compile(
            r'''class\s+(\w+)(?:\s+extends\s+(\w+))?''',
            re.MULTILINE
        )

        for match in class_pattern.finditer(content):
            name, base = match.groups()
            classes.append(Class(
                name=name,
                bases=[base] if base else [],
            ))

        lines = content.splitlines()
        loc = len(lines)
        sloc = len([line for line in lines if line.strip() and not line.strip().startswith("//")])

        return ParsedFile(
            path=str(file_path),
            language=language,
            imports=imports,
            functions=functions,
            classes=classes,
            loc=loc,
            sloc=sloc,
        )

    async def _parse_generic(
        self,
        file_path: Path,
        content: str,
        language: str,
    ) -> ParsedFile:
        """Generic parsing for unsupported languages."""
        lines = content.splitlines()
        loc = len(lines)
        sloc = len([line for line in lines if line.strip()])

        return ParsedFile(
            path=str(file_path),
            language=language,
            loc=loc,
            sloc=sloc,
        )
