"""
Recipe Loader - Load and validate recipe files.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class RecipeSource:
    """A source repository in a recipe."""

    repo: str
    branch: str = "main"
    extract: list[str] = field(default_factory=list)
    components: list[dict[str, str]] = field(default_factory=list)
    rename: dict[str, str] = field(default_factory=dict)


@dataclass
class RecipeSynthesis:
    """Synthesis configuration for a recipe."""

    strategy: str = "selective"
    output_name: str = "project"
    template: str = "python-default"
    dependencies: dict[str, Any] = field(
        default_factory=lambda: {"merge": True, "python_version": "3.11"}
    )
    conflicts: dict[str, str] = field(
        default_factory=lambda: {"strategy": "prefer_first"}
    )


@dataclass
class Recipe:
    """A complete recipe definition."""

    name: str
    version: str
    description: str
    sources: list[RecipeSource]
    synthesis: RecipeSynthesis
    author: str = ""
    tags: list[str] = field(default_factory=list)
    post_synthesis: list[str] = field(default_factory=list)
    variables: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recipe":
        """Create a Recipe from a dictionary."""
        sources = [
            RecipeSource(
                repo=s["repo"],
                branch=s.get("branch", "main"),
                extract=s.get("extract", []),
                components=s.get("components", []),
                rename=s.get("rename", {}),
            )
            for s in data.get("sources", [])
        ]

        synth_data = data.get("synthesis", {})
        synthesis = RecipeSynthesis(
            strategy=synth_data.get("strategy", "selective"),
            output_name=synth_data.get("output_name", "project"),
            template=synth_data.get("template", "python-default"),
            dependencies=synth_data.get(
                "dependencies", {"merge": True, "python_version": "3.11"}
            ),
            conflicts=synth_data.get("conflicts", {"strategy": "prefer_first"}),
        )

        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            sources=sources,
            synthesis=synthesis,
            author=data.get("author", ""),
            tags=data.get("tags", []),
            post_synthesis=data.get("post_synthesis", []),
            variables=data.get("variables", {}),
        )


class RecipeLoader:
    """Load recipes from the recipes directory."""

    def __init__(self, recipes_dir: Path | None = None):
        """Initialize the recipe loader."""
        if recipes_dir is None:
            # Default to project's recipes directory
            self.recipes_dir = Path(__file__).parent.parent.parent / "recipes"
        else:
            self.recipes_dir = Path(recipes_dir)

    def list_recipes(self) -> list[dict[str, str]]:
        """List all available recipes."""
        recipes = []

        if not self.recipes_dir.exists():
            return recipes

        for file in self.recipes_dir.glob("*.yaml"):
            if file.name == "README.md":
                continue

            try:
                with open(file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    recipes.append(
                        {
                            "name": data.get("name", file.stem),
                            "version": data.get("version", "1.0.0"),
                            "description": data.get("description", ""),
                            "tags": data.get("tags", []),
                            "file": str(file),
                        }
                    )
            except Exception as e:
                recipes.append(
                    {
                        "name": file.stem,
                        "version": "unknown",
                        "description": f"Error loading: {e}",
                        "tags": [],
                        "file": str(file),
                    }
                )

        return recipes

    def load_recipe(self, name: str) -> Recipe | None:
        """Load a recipe by name."""
        # Try exact filename first
        recipe_file = self.recipes_dir / f"{name}.yaml"

        if not recipe_file.exists():
            # Try finding by recipe name
            for file in self.recipes_dir.glob("*.yaml"):
                try:
                    with open(file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data.get("name") == name:
                            recipe_file = file
                            break
                except Exception:
                    continue

        if not recipe_file.exists():
            return None

        try:
            with open(recipe_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return Recipe.from_dict(data)
        except Exception as e:
            raise ValueError(f"Failed to load recipe {name}: {e}")

    def validate_recipe(self, recipe: Recipe) -> list[str]:
        """Validate a recipe and return any errors."""
        errors = []

        if not recipe.name:
            errors.append("Recipe name is required")

        if not recipe.version:
            errors.append("Recipe version is required")

        if not recipe.sources:
            errors.append("At least one source is required")

        for i, source in enumerate(recipe.sources):
            if not source.repo:
                errors.append(f"Source {i + 1}: repo URL is required")
            if not source.repo.startswith(("http://", "https://")):
                errors.append(f"Source {i + 1}: invalid repo URL")

        if recipe.synthesis.strategy not in ["merge", "copy", "selective"]:
            errors.append(f"Invalid synthesis strategy: {recipe.synthesis.strategy}")

        return errors
