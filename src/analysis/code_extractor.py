"""
AI Project Synthesizer - Code Extractor

Identifies and extracts code components from repositories.
Supports selective extraction of modules, classes, and functions.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.analysis.ast_parser import ASTParser, ParsedFile

logger = logging.getLogger(__name__)


@dataclass
class Component:
    """Represents an extractable code component."""

    name: str
    component_type: str  # "module", "package", "class", "function"
    files: list[str]
    entry_point: str | None = None
    internal_deps: list[str] = field(default_factory=list)
    external_deps: list[str] = field(default_factory=list)
    loc: int = 0
    description: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.component_type,
            "files": self.files,
            "entry_point": self.entry_point,
            "internal_dependencies": self.internal_deps,
            "external_dependencies": self.external_deps,
            "lines_of_code": self.loc,
            "description": self.description,
        }


class CodeExtractor:
    """
    Extracts code components from repositories.

    Identifies standalone modules, packages, classes, and functions
    that can be extracted and reused in other projects.

    Example:
        extractor = CodeExtractor()
        components = await extractor.identify_components(Path("./repo"))
        for comp in components:
            print(f"{comp.name}: {comp.component_type}")
    """

    def __init__(self):
        """Initialize the code extractor."""
        self._parser = ASTParser()

    async def identify_components(
        self,
        repo_path: Path,
    ) -> list[Component]:
        """
        Identify extractable components in a repository.

        Args:
            repo_path: Path to repository root

        Returns:
            List of identified components
        """
        components: list[Component] = []

        # Analyze project structure
        analysis = await self._parser.analyze_project(repo_path)
        files: list[ParsedFile] = analysis.get("files", [])

        # Build import graph
        import_graph = self._build_import_graph(files)

        # Identify packages (directories with __init__.py)
        packages = self._identify_packages(repo_path)
        for pkg_path in packages:
            comp = await self._analyze_package(repo_path, pkg_path, files, import_graph)
            if comp:
                components.append(comp)

        # Identify standalone modules
        for parsed in files:
            file_path = Path(parsed.path)
            if file_path.parent in packages:
                continue  # Already part of a package

            if self._is_standalone_module(parsed, import_graph):
                comp = self._create_module_component(parsed)
                components.append(comp)

        # Identify significant classes
        for parsed in files:
            for cls in parsed.classes:
                if self._is_significant_class(cls, parsed):
                    comp = self._create_class_component(cls, parsed)
                    components.append(comp)

        return components

    def _build_import_graph(
        self,
        files: list[ParsedFile],
    ) -> dict[str, set[str]]:
        """Build import dependency graph."""
        graph: dict[str, set[str]] = {}

        for parsed in files:
            deps: set[str] = set()

            for imp in parsed.imports:
                if imp.is_relative:
                    # Relative import - internal dependency
                    deps.add(f"relative:{imp.module}")
                else:
                    deps.add(imp.module.split(".")[0])

            graph[parsed.path] = deps

        return graph

    def _identify_packages(self, repo_path: Path) -> list[Path]:
        """Find Python packages (directories with __init__.py)."""
        packages = []

        for init_file in repo_path.rglob("__init__.py"):
            pkg_path = init_file.parent

            # Skip common non-source directories
            if self._should_skip(pkg_path):
                continue

            packages.append(pkg_path)

        return packages

    async def _analyze_package(
        self,
        repo_path: Path,
        pkg_path: Path,
        files: list[ParsedFile],
        import_graph: dict[str, set[str]],
    ) -> Component | None:
        """Analyze a package and create component."""
        # Get all files in package
        pkg_files = [
            f for f in files
            if Path(f.path).parent == pkg_path
        ]

        if not pkg_files:
            return None

        # Calculate total LOC
        total_loc = sum(f.loc for f in pkg_files)

        # Get internal and external dependencies
        internal_deps: set[str] = set()
        external_deps: set[str] = set()

        for parsed in pkg_files:
            for imp in parsed.imports:
                if imp.is_relative:
                    internal_deps.add(imp.module)
                else:
                    module = imp.module.split(".")[0]
                    if not self._is_stdlib(module):
                        external_deps.add(module)

        pkg_name = pkg_path.relative_to(repo_path).as_posix().replace("/", ".")

        return Component(
            name=pkg_name,
            component_type="package",
            files=[str(Path(f.path).relative_to(repo_path)) for f in pkg_files],
            entry_point=str(pkg_path / "__init__.py"),
            internal_deps=list(internal_deps),
            external_deps=list(external_deps),
            loc=total_loc,
            description=self._get_package_description(pkg_files),
        )

    def _is_standalone_module(
        self,
        parsed: ParsedFile,
        import_graph: dict[str, set[str]],
    ) -> bool:
        """Check if a module can stand alone."""
        # Has significant code
        if parsed.sloc < 50:
            return False

        # Has functions or classes
        return not (not parsed.functions and not parsed.classes)

    def _is_significant_class(self, cls, parsed: ParsedFile) -> bool:
        """Check if a class is significant enough to extract."""
        # Has multiple methods
        if len(cls.methods) < 3:
            return False

        # Has docstring
        return cls.docstring

    def _create_module_component(self, parsed: ParsedFile) -> Component:
        """Create component from a module."""
        external_deps = []
        for imp in parsed.imports:
            if not imp.is_relative:
                module = imp.module.split(".")[0]
                if not self._is_stdlib(module) and module not in external_deps:
                    external_deps.append(module)

        name = Path(parsed.path).stem

        return Component(
            name=name,
            component_type="module",
            files=[parsed.path],
            external_deps=external_deps,
            loc=parsed.loc,
            description=self._get_module_description(parsed),
        )

    def _create_class_component(self, cls, parsed: ParsedFile) -> Component:
        """Create component from a class."""
        return Component(
            name=cls.name,
            component_type="class",
            files=[parsed.path],
            loc=cls.line_end - cls.line_start + 1,
            description=cls.docstring,
        )

    def _get_package_description(self, files: list[ParsedFile]) -> str | None:
        """Extract package description from __init__.py docstring."""
        for f in files:
            if f.path.endswith("__init__.py"):
                # Try to get module docstring
                if f.classes and f.classes[0].docstring:
                    return f.classes[0].docstring[:200]
        return None

    def _get_module_description(self, parsed: ParsedFile) -> str | None:
        """Extract module description."""
        if parsed.functions and parsed.functions[0].docstring:
            return parsed.functions[0].docstring[:200]
        if parsed.classes and parsed.classes[0].docstring:
            return parsed.classes[0].docstring[:200]
        return None

    def _is_stdlib(self, module: str) -> bool:
        """Check if module is part of Python standard library."""
        stdlib_modules = {
            "abc", "aifc", "argparse", "array", "ast", "asynchat",
            "asyncio", "asyncore", "atexit", "base64", "bdb", "binascii",
            "binhex", "bisect", "builtins", "bz2", "calendar", "cgi",
            "cgitb", "chunk", "cmath", "cmd", "code", "codecs",
            "codeop", "collections", "colorsys", "compileall", "concurrent",
            "configparser", "contextlib", "contextvars", "copy", "copyreg",
            "cProfile", "crypt", "csv", "ctypes", "curses", "dataclasses",
            "datetime", "dbm", "decimal", "difflib", "dis", "distutils",
            "doctest", "email", "encodings", "enum", "errno", "faulthandler",
            "fcntl", "filecmp", "fileinput", "fnmatch", "fractions",
            "ftplib", "functools", "gc", "getopt", "getpass", "gettext",
            "glob", "graphlib", "grp", "gzip", "hashlib", "heapq",
            "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
            "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
            "json", "keyword", "lib2to3", "linecache", "locale", "logging",
            "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
            "mmap", "modulefinder", "multiprocessing", "netrc", "nis",
            "nntplib", "numbers", "operator", "optparse", "os", "ossaudiodev",
            "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
            "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
            "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
            "pydoc", "queue", "quopri", "random", "re", "readline",
            "reprlib", "resource", "rlcompleter", "runpy", "sched",
            "secrets", "select", "selectors", "shelve", "shlex", "shutil",
            "signal", "site", "smtpd", "smtplib", "sndhdr", "socket",
            "socketserver", "spwd", "sqlite3", "ssl", "stat", "statistics",
            "string", "stringprep", "struct", "subprocess", "sunau",
            "symtable", "sys", "sysconfig", "syslog", "tabnanny", "tarfile",
            "telnetlib", "tempfile", "termios", "test", "textwrap", "threading",
            "time", "timeit", "tkinter", "token", "tokenize", "tomllib",
            "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
            "types", "typing", "unicodedata", "unittest", "urllib", "uu",
            "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
            "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
            "zipapp", "zipfile", "zipimport", "zlib", "zoneinfo",
        }
        return module in stdlib_modules

    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        skip_patterns = {
            "node_modules", "venv", ".venv", "env", ".env",
            "__pycache__", ".git", "dist", "build", "test",
            "tests", "docs", "examples", "scripts",
        }

        return any(part in skip_patterns for part in path.parts)
