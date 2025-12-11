"""
Recipe Runner - Execute recipes to create projects.
"""

from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field

from .loader import Recipe, RecipeLoader


@dataclass
class RecipeResult:
    """Result of running a recipe."""
    success: bool
    project_path: Optional[Path] = None
    repos_cloned: int = 0
    components_extracted: int = 0
    files_created: int = 0
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class RecipeRunner:
    """Execute recipes to create projects."""

    def __init__(self):
        """Initialize the recipe runner."""
        self.loader = RecipeLoader()

    async def run(
        self,
        recipe_name: str,
        output_path: Path,
        variables: Optional[Dict[str, str]] = None,
        dry_run: bool = False,
    ) -> RecipeResult:
        """
        Run a recipe to create a project.

        Args:
            recipe_name: Name of the recipe to run
            output_path: Where to create the project
            variables: Override recipe variables
            dry_run: If True, only show what would be done

        Returns:
            RecipeResult with status and details
        """
        # Load recipe
        recipe = self.loader.load_recipe(recipe_name)
        if recipe is None:
            return RecipeResult(
                success=False,
                errors=[f"Recipe not found: {recipe_name}"]
            )

        # Validate recipe
        errors = self.loader.validate_recipe(recipe)
        if errors:
            return RecipeResult(
                success=False,
                errors=errors
            )

        # Merge variables
        merged_vars = {}
        for var_name, var_config in recipe.variables.items():
            if variables and var_name in variables:
                merged_vars[var_name] = variables[var_name]
            elif "default" in var_config:
                merged_vars[var_name] = var_config["default"]
            elif var_config.get("required", False):
                return RecipeResult(
                    success=False,
                    errors=[f"Required variable not provided: {var_name}"]
                )

        # Determine output name
        output_name = merged_vars.get("project_name", recipe.synthesis.output_name)
        project_path = output_path / output_name

        if dry_run:
            return RecipeResult(
                success=True,
                project_path=project_path,
                repos_cloned=len(recipe.sources),
                warnings=[f"DRY RUN - would create project at {project_path}"]
            )

        # Create project directory
        project_path.mkdir(parents=True, exist_ok=True)

        result = RecipeResult(
            success=True,
            project_path=project_path,
        )

        try:
            # Clone and extract from each source
            for source in recipe.sources:
                try:
                    await self._process_source(source, project_path, recipe.synthesis)
                    result.repos_cloned += 1
                except Exception as e:
                    result.warnings.append(f"Failed to process {source.repo}: {e}")

            # Run post-synthesis steps
            for step in recipe.post_synthesis:
                try:
                    await self._run_post_step(step, project_path, recipe)
                except Exception as e:
                    result.warnings.append(f"Post-synthesis step {step} failed: {e}")

            # Count created files
            result.files_created = sum(1 for _ in project_path.rglob("*") if _.is_file())

        except Exception as e:
            result.success = False
            result.errors.append(str(e))

        return result

    async def _process_source(
        self,
        source,
        project_path: Path,
        synthesis,
    ) -> None:
        """Process a single source repository."""

        # For now, create placeholder structure
        # Full implementation would clone and extract

        # Create component directories
        for component in source.components:
            comp_path = project_path / component.get("name", "component")
            comp_path.mkdir(parents=True, exist_ok=True)

            # Create placeholder file
            readme = comp_path / "README.md"
            readme.write_text(f"# {component.get('name', 'Component')}\n\nExtracted from: {source.repo}\n")

    async def _run_post_step(
        self,
        step: str,
        project_path: Path,
        recipe: Recipe,
    ) -> None:
        """Run a post-synthesis step."""
        if step == "generate_readme":
            readme_path = project_path / "README.md"
            content = f"""# {recipe.synthesis.output_name}

{recipe.description}

## Created with AI Synthesizer

This project was created using the `{recipe.name}` recipe.

## Sources

"""
            for source in recipe.sources:
                content += f"- {source.repo}\n"

            content += """
## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the project
python main.py
```

## License

MIT
"""
            readme_path.write_text(content)

        elif step == "install_dependencies":
            # Create requirements.txt placeholder
            req_path = project_path / "requirements.txt"
            if not req_path.exists():
                req_path.write_text("# Dependencies\n")

        elif step == "generate_api_docs":
            docs_path = project_path / "docs"
            docs_path.mkdir(exist_ok=True)
            (docs_path / "API.md").write_text(f"# API Documentation\n\nGenerated for {recipe.name}\n")

        elif step == "generate_diagrams":
            docs_path = project_path / "docs"
            docs_path.mkdir(exist_ok=True)
            (docs_path / "ARCHITECTURE.md").write_text(f"# Architecture\n\nDiagrams for {recipe.name}\n")
