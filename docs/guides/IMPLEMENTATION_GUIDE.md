# 🔧 Implementation Guide

> **Step-by-Step Instructions for Completing Remaining Components**  
> **Target Audience:** Developers continuing this project

---

## Overview

This guide provides detailed implementation instructions for each incomplete component. Follow these guides to bring each module to 100% completion.

---

## 1. AST Parser (src/analysis/ast_parser.py)

### Current State: ~40%
### Target: Tree-sitter multi-language support

### Step-by-Step Implementation

#### Step 1: Install Dependencies

```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript
```

#### Step 2: Initialize Language Parsers

```python
# Add to __init__ method
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript

class ASTParser:
    def __init__(self):
        self._parsers: dict[str, Parser] = {}
        self._languages: dict[str, Language] = {}
        self._init_languages()
    
    def _init_languages(self):
        """Initialize tree-sitter language parsers."""
        # Python
        PY_LANGUAGE = Language(tspython.language())
        py_parser = Parser(PY_LANGUAGE)
        self._languages["python"] = PY_LANGUAGE
        self._parsers["python"] = py_parser
        
        # JavaScript
        JS_LANGUAGE = Language(tsjavascript.language())
        js_parser = Parser(JS_LANGUAGE)
        self._languages["javascript"] = JS_LANGUAGE
        self._parsers["javascript"] = js_parser
```

#### Step 3: Implement parse_file Method

```python
def parse_file(self, file_path: Path) -> ParsedFile:
    """Parse a source file using tree-sitter."""
    # 1. Detect language from extension
    ext_to_lang = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
    }
    
    lang = ext_to_lang.get(file_path.suffix.lower())
    if not lang or lang not in self._parsers:
        raise UnsupportedLanguageError(f"No parser for {file_path.suffix}")
    
    # 2. Read and parse file
    content = file_path.read_bytes()
    tree = self._parsers[lang].parse(content)
    
    # 3. Extract structure
    return ParsedFile(
        path=file_path,
        language=lang,
        tree=tree,
        imports=self._extract_imports(tree, lang),
        functions=self._extract_functions(tree, lang),
        classes=self._extract_classes(tree, lang),
    )
```

#### Step 4: Implement Extract Methods

```python
def _extract_imports(self, tree, language: str) -> list[Import]:
    """Extract all imports from AST."""
    imports = []
    
    if language == "python":
        # Query for import statements
        query = self._languages[language].query("""
            (import_statement) @import
            (import_from_statement) @import
        """)
        
        for node, _ in query.captures(tree.root_node):
            imports.append(self._parse_python_import(node))
    
    return imports
```

### Testing

```python
# tests/unit/test_ast_parser.py
def test_parse_python_file(tmp_path):
    # Create test file
    test_file = tmp_path / "test.py"
    test_file.write_text("import os\nfrom pathlib import Path\n\ndef hello(): pass")
    
    parser = ASTParser()
    result = parser.parse_file(test_file)
    
    assert result.language == "python"
    assert len(result.imports) == 2
    assert len(result.functions) == 1
```



---

## 2. Code Extractor (src/analysis/code_extractor.py)

### Current State: ~30%
### Target: Component extraction with dependency tracking

### Step-by-Step Implementation

#### Step 1: Define Data Structures

```python
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class ExtractedComponent:
    """Result of component extraction."""
    name: str
    source_repo: str
    files: list[Path]
    dependencies: list[str]
    external_packages: list[str]
    total_lines: int
    
@dataclass
class ExtractionConfig:
    """Configuration for extraction."""
    patterns: list[str]  # Glob patterns for files to include
    exclude_patterns: list[str] = field(default_factory=list)
    include_tests: bool = True
    preserve_structure: bool = True
```

#### Step 2: Implement File Discovery

```python
class CodeExtractor:
    def __init__(self, ast_parser: ASTParser):
        self.ast_parser = ast_parser
    
    def discover_files(
        self,
        repo_path: Path,
        patterns: list[str],
        exclude: list[str] = None,
    ) -> list[Path]:
        """Find all files matching patterns."""
        exclude = exclude or []
        files = []
        
        for pattern in patterns:
            for file in repo_path.glob(pattern):
                if file.is_file():
                    # Check exclusions
                    excluded = any(
                        file.match(exc) for exc in exclude
                    )
                    if not excluded:
                        files.append(file)
        
        return files
```

#### Step 3: Build Import Graph

```python
def build_import_graph(
    self,
    files: list[Path],
    repo_path: Path,
) -> dict[Path, set[Path]]:
    """Build a graph of internal imports."""
    graph = {}
    
    for file in files:
        try:
            parsed = self.ast_parser.parse_file(file)
            imports = parsed.imports
            
            # Resolve imports to file paths
            resolved = set()
            for imp in imports:
                target = self._resolve_import(imp, file, repo_path)
                if target and target in files:
                    resolved.add(target)
            
            graph[file] = resolved
        except Exception as e:
            logger.warning(f"Failed to parse {file}: {e}")
            graph[file] = set()
    
    return graph

def _resolve_import(
    self,
    imp: Import,
    source_file: Path,
    repo_path: Path,
) -> Path | None:
    """Resolve an import to a file path."""
    # Handle relative imports
    if imp.is_relative:
        base = source_file.parent
        for _ in range(imp.level - 1):
            base = base.parent
        target = base / imp.module.replace(".", "/")
    else:
        target = repo_path / "src" / imp.module.replace(".", "/")
    
    # Check for __init__.py or .py file
    if (target / "__init__.py").exists():
        return target / "__init__.py"
    elif target.with_suffix(".py").exists():
        return target.with_suffix(".py")
    
    return None
```

#### Step 4: Extract Component

```python
async def extract_component(
    self,
    repo_path: Path,
    config: ExtractionConfig,
    output_path: Path,
) -> ExtractedComponent:
    """Extract a component from repository."""
    # 1. Discover files
    files = self.discover_files(
        repo_path,
        config.patterns,
        config.exclude_patterns,
    )
    
    # 2. Build import graph
    graph = self.build_import_graph(files, repo_path)
    
    # 3. Find all required files (transitive closure)
    required = self._transitive_closure(files, graph)
    
    # 4. Copy files maintaining structure
    copied = []
    for file in required:
        rel_path = file.relative_to(repo_path)
        dest = output_path / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        
        # Transform imports if needed
        content = self._transform_imports(file, repo_path, output_path)
        dest.write_text(content)
        copied.append(dest)
    
    # 5. Collect external dependencies
    external_deps = self._collect_external_deps(required)
    
    return ExtractedComponent(
        name=config.patterns[0].split("/")[0],
        source_repo=str(repo_path),
        files=copied,
        dependencies=[],
        external_packages=external_deps,
        total_lines=sum(len(f.read_text().splitlines()) for f in copied),
    )
```



---

## 3. Quality Scorer (src/analysis/quality_scorer.py)

### Current State: ~25%
### Target: Comprehensive quality metrics

### Step-by-Step Implementation

#### Step 1: Define Quality Metrics

```python
@dataclass
class QualityScore:
    """Comprehensive quality assessment."""
    overall: float  # 0.0 - 1.0
    documentation: float
    test_coverage: float
    ci_cd: float
    maintainability: float
    recency: float
    community: float
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def grade(self) -> str:
        """Return letter grade."""
        if self.overall >= 0.9: return "A"
        if self.overall >= 0.8: return "B"
        if self.overall >= 0.7: return "C"
        if self.overall >= 0.6: return "D"
        return "F"
```

#### Step 2: Implement Individual Checks

```python
class QualityScorer:
    def _check_documentation(self, repo_path: Path) -> float:
        """Score documentation quality (0.0 - 1.0)."""
        score = 0.0
        max_score = 4.0
        
        # Check README
        readme_files = list(repo_path.glob("README*"))
        if readme_files:
            readme = readme_files[0].read_text()
            score += 1.0
            # Bonus for comprehensive README
            if len(readme) > 1000:
                score += 0.5
            if "## Installation" in readme:
                score += 0.25
            if "## Usage" in readme:
                score += 0.25
        
        # Check docstrings in Python files
        py_files = list(repo_path.rglob("*.py"))
        if py_files:
            docstring_count = sum(
                1 for f in py_files[:10]  # Sample
                if '"""' in f.read_text() or "'''" in f.read_text()
            )
            score += min(1.0, docstring_count / 5)
        
        # Check for docs folder
        if (repo_path / "docs").exists():
            score += 0.5
        
        return min(1.0, score / max_score)
    
    def _check_test_coverage(self, repo_path: Path) -> float:
        """Score test presence (0.0 - 1.0)."""
        score = 0.0
        
        # Check for test directory
        test_dirs = ["tests", "test", "spec"]
        has_tests = any((repo_path / d).exists() for d in test_dirs)
        if has_tests:
            score += 0.5
        
        # Check for test files
        test_files = (
            list(repo_path.rglob("test_*.py")) +
            list(repo_path.rglob("*_test.py")) +
            list(repo_path.rglob("*.test.js"))
        )
        if test_files:
            score += min(0.5, len(test_files) * 0.05)
        
        # Check for pytest.ini or similar
        config_files = ["pytest.ini", "pyproject.toml", "jest.config.js"]
        if any((repo_path / f).exists() for f in config_files):
            score += 0.1
        
        return min(1.0, score)
    
    def _check_ci_cd(self, repo_path: Path) -> float:
        """Score CI/CD configuration (0.0 - 1.0)."""
        score = 0.0
        
        # GitHub Actions
        if (repo_path / ".github" / "workflows").exists():
            workflows = list((repo_path / ".github" / "workflows").glob("*.yml"))
            score += min(0.5, len(workflows) * 0.2)
        
        # Other CI systems
        ci_files = [
            ".travis.yml",
            ".gitlab-ci.yml",
            "Jenkinsfile",
            ".circleci/config.yml",
            "azure-pipelines.yml",
        ]
        if any((repo_path / f).exists() for f in ci_files):
            score += 0.3
        
        # Docker
        if (repo_path / "Dockerfile").exists():
            score += 0.2
        if (repo_path / "docker-compose.yml").exists():
            score += 0.1
        
        return min(1.0, score)
    
    def _calculate_maintainability(self, repo_path: Path) -> float:
        """Score code maintainability (0.0 - 1.0)."""
        # This would ideally use radon or similar
        # Simplified version based on file structure
        score = 0.5  # Base score
        
        # Good structure indicators
        if (repo_path / "src").exists():
            score += 0.2
        if (repo_path / "pyproject.toml").exists():
            score += 0.1
        if (repo_path / ".editorconfig").exists():
            score += 0.1
        
        # Check for type hints (sample)
        py_files = list(repo_path.rglob("*.py"))[:5]
        for f in py_files:
            content = f.read_text()
            if "def " in content and "->" in content:
                score += 0.02
        
        return min(1.0, score)
```

#### Step 3: Calculate Overall Score

```python
def calculate_score(self, repo_path: Path, repo_info: RepositoryInfo = None) -> QualityScore:
    """Calculate comprehensive quality score."""
    documentation = self._check_documentation(repo_path)
    test_coverage = self._check_test_coverage(repo_path)
    ci_cd = self._check_ci_cd(repo_path)
    maintainability = self._calculate_maintainability(repo_path)
    
    # Recency based on git or repo_info
    recency = self._calculate_recency(repo_path, repo_info)
    
    # Community score from repo_info
    community = self._calculate_community(repo_info) if repo_info else 0.5
    
    # Weighted overall score
    overall = (
        documentation * 0.20 +
        test_coverage * 0.20 +
        ci_cd * 0.15 +
        maintainability * 0.20 +
        recency * 0.15 +
        community * 0.10
    )
    
    return QualityScore(
        overall=overall,
        documentation=documentation,
        test_coverage=test_coverage,
        ci_cd=ci_cd,
        maintainability=maintainability,
        recency=recency,
        community=community,
    )
```



---

## 4. Scaffolder (src/synthesis/scaffolder.py)

### Current State: ~20%
### Target: Template-based project generation

### Step-by-Step Implementation

#### Step 1: Template Discovery

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

class Scaffolder:
    TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates" / "project"
    
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader(str(self.TEMPLATES_DIR)),
            autoescape=select_autoescape(),
            keep_trailing_newline=True,
        )
    
    def list_templates(self) -> list[str]:
        """List available project templates."""
        templates = []
        for item in self.TEMPLATES_DIR.iterdir():
            if item.is_dir() and (item / "copier.yaml").exists():
                templates.append(item.name)
        return templates
```

#### Step 2: Context Generation

```python
def generate_context(
    self,
    project_name: str,
    repositories: list[str],
    dependencies: list[str],
    **kwargs,
) -> dict:
    """Generate template context from synthesis data."""
    return {
        "project_name": project_name,
        "package_name": project_name.replace("-", "_"),
        "project_description": kwargs.get("description", f"Synthesized from {len(repositories)} repositories"),
        "python_version": kwargs.get("python_version", "3.11"),
        "author_name": kwargs.get("author", "AI Project Synthesizer"),
        "author_email": kwargs.get("email", "synthesizer@example.com"),
        "license": kwargs.get("license", "MIT"),
        "repositories": repositories,
        "dependencies": dependencies,
        "use_docker": kwargs.get("use_docker", True),
        "use_github_actions": kwargs.get("use_github_actions", True),
    }
```

#### Step 3: Apply Template

```python
async def apply_template(
    self,
    template_name: str,
    output_path: Path,
    context: dict,
) -> Path:
    """Apply a project template to output directory."""
    template_path = self.TEMPLATES_DIR / template_name / "template"
    
    if not template_path.exists():
        raise TemplateNotFoundError(f"Template not found: {template_name}")
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Process each template file
    for src_file in template_path.rglob("*"):
        if src_file.is_file():
            # Calculate destination path
            rel_path = src_file.relative_to(template_path)
            
            # Replace {{package_name}} in path
            rel_str = str(rel_path)
            for key, value in context.items():
                rel_str = rel_str.replace("{{" + key + "}}", str(value))
            
            dest_file = output_path / rel_str
            
            # Handle .j2 templates
            if src_file.suffix == ".j2":
                dest_file = dest_file.with_suffix("")
                content = self._render_template(src_file, context)
            else:
                content = src_file.read_text()
            
            # Write output
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            dest_file.write_text(content)
    
    return output_path

def _render_template(self, template_path: Path, context: dict) -> str:
    """Render a Jinja2 template."""
    template = self.env.get_template(str(template_path.relative_to(self.TEMPLATES_DIR)))
    return template.render(**context)
```

---

## 5. README Generator (src/generation/readme_generator.py)

### Current State: ~30%
### Target: LLM-powered README generation

### Step-by-Step Implementation

```python
class ReadmeGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client
    
    async def generate(
        self,
        project_path: Path,
        analysis: AnalysisResult,
        template: str = "default",
    ) -> str:
        """Generate README.md using LLM."""
        # 1. Gather project information
        context = self._build_context(project_path, analysis)
        
        # 2. Build prompt
        prompt = self._build_prompt(context, template)
        
        # 3. Generate with LLM
        response = await self.llm.generate(prompt)
        
        # 4. Post-process
        readme = self._post_process(response)
        
        return readme
    
    def _build_context(self, project_path: Path, analysis: AnalysisResult) -> dict:
        """Build context for README generation."""
        # Read existing files
        package_json = None
        pyproject = None
        
        if (project_path / "pyproject.toml").exists():
            import tomli
            pyproject = tomli.loads((project_path / "pyproject.toml").read_text())
        
        return {
            "project_name": project_path.name,
            "languages": analysis.language_breakdown,
            "dependencies": analysis.dependencies.direct,
            "components": [c.name for c in analysis.components],
            "has_tests": (project_path / "tests").exists(),
            "has_docker": (project_path / "Dockerfile").exists(),
            "pyproject": pyproject,
        }
    
    def _build_prompt(self, context: dict, template: str) -> str:
        """Build prompt for LLM."""
        return f"""Generate a professional README.md for this project:

Project Name: {context['project_name']}
Languages: {context['languages']}
Dependencies: {', '.join(d.name for d in context['dependencies'][:10])}
Components: {', '.join(context['components'])}
Has Tests: {context['has_tests']}
Has Docker: {context['has_docker']}

Generate a README with these sections:
1. Title with badge shields
2. Overview (2-3 sentences)
3. Features (bullet points)
4. Quick Start (installation + usage)
5. Project Structure
6. Configuration
7. Testing
8. License

Use markdown formatting. Be concise but comprehensive."""
```

---

## 6. Diagram Generator (src/generation/diagram_generator.py)

### Current State: ~35%
### Target: Mermaid diagram generation with rendering

### Step-by-Step Implementation

```python
class DiagramGenerator:
    async def generate_architecture(self, analysis: AnalysisResult) -> str:
        """Generate Mermaid architecture diagram."""
        components = analysis.components
        
        mermaid = ["flowchart TB"]
        
        # Add nodes
        for comp in components:
            safe_name = comp.name.replace("-", "_")
            mermaid.append(f'    {safe_name}["{comp.name}"]')
        
        # Add edges based on dependencies
        for comp in components:
            safe_name = comp.name.replace("-", "_")
            for dep in comp.dependencies:
                safe_dep = dep.replace("-", "_")
                mermaid.append(f'    {safe_name} --> {safe_dep}')
        
        return "\n".join(mermaid)
    
    async def generate_dependency_graph(self, deps: DependencyGraph) -> str:
        """Generate Mermaid dependency graph."""
        mermaid = ["graph LR"]
        
        # Group by category
        for dep in deps.direct[:20]:  # Limit for readability
            safe_name = dep.name.replace("-", "_")
            mermaid.append(f'    {safe_name}["{dep.name}\\n{dep.version_spec}"]')
        
        return "\n".join(mermaid)
    
    async def render_to_image(
        self,
        mermaid_code: str,
        format: str = "svg",
    ) -> bytes:
        """Render Mermaid to image using Kroki or local mmdc."""
        import httpx
        
        # Use Kroki API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://kroki.io/mermaid/" + format,
                content=mermaid_code,
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()
            return response.content
```

---

## Next Steps

After implementing these components:

1. **Write Unit Tests** for each new implementation
2. **Run Integration Tests** to verify everything works together
3. **Update Documentation** to reflect actual implementation
4. **Run Linters** (black, ruff, mypy) on all new code

See `docs/WORK_IN_PROGRESS.md` for the complete task checklist.
