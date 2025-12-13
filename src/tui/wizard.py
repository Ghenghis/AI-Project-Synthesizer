"""
AI Synthesizer Wizard Mode

Interactive guided project creation wizard.
"""

from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

console = Console()


class ProjectWizard:
    """Interactive wizard for creating projects."""

    PROJECT_TYPES = {
        "1": ("MCP Server", "mcp", "Create an MCP server for Windsurf/Claude"),
        "2": ("CLI Tool", "cli", "Command-line application"),
        "3": ("Web API", "api", "REST/GraphQL API server"),
        "4": ("ML Pipeline", "ml", "Machine learning pipeline"),
        "5": ("Web Scraper", "scraper", "Data extraction tool"),
        "6": ("Custom", "custom", "Start from scratch"),
    }

    TECH_STACKS = {
        "mcp": ["FastMCP", "Python 3.11+", "asyncio"],
        "cli": ["Typer", "Rich", "Python 3.11+"],
        "api": ["FastAPI", "Pydantic", "SQLAlchemy"],
        "ml": ["PyTorch", "LangChain", "Transformers"],
        "scraper": ["Playwright", "aiohttp", "BeautifulSoup"],
        "custom": [],
    }

    def __init__(self):
        """Initialize the wizard."""
        self.config: dict[str, Any] = {}

    def run(self) -> dict[str, Any] | None:
        """Run the interactive wizard."""
        console.print(Panel(
            "[bold cyan]🧙 AI Project Synthesizer Wizard[/bold cyan]\n\n"
            "This wizard will guide you through creating a new project.\n"
            "Press Ctrl+C at any time to cancel.",
            title="Welcome"
        ))

        try:
            # Step 1: Project Type
            self._step_project_type()

            # Step 2: Project Name
            self._step_project_name()

            # Step 3: Tech Stack
            self._step_tech_stack()

            # Step 4: Example Repos
            self._step_example_repos()

            # Step 5: Output Location
            self._step_output_location()

            # Step 6: Confirmation
            if self._step_confirm():
                return self.config
            else:
                console.print("\n[yellow]Wizard cancelled.[/yellow]")
                return None

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Wizard cancelled.[/yellow]")
            return None

    def _step_project_type(self) -> None:
        """Step 1: Select project type."""
        console.print("\n[bold]Step 1/6: Project Type[/bold]\n")

        table = Table(show_header=False, box=None)
        table.add_column("Option", style="cyan")
        table.add_column("Type", style="bold")
        table.add_column("Description")

        for key, (name, _, desc) in self.PROJECT_TYPES.items():
            table.add_row(f"[{key}]", name, desc)

        console.print(table)

        choice = Prompt.ask(
            "\nSelect project type",
            choices=list(self.PROJECT_TYPES.keys()),
            default="1"
        )

        name, type_id, _ = self.PROJECT_TYPES[choice]
        self.config["project_type"] = type_id
        self.config["project_type_name"] = name

        console.print(f"  ✓ Selected: [green]{name}[/green]")

    def _step_project_name(self) -> None:
        """Step 2: Enter project name."""
        console.print("\n[bold]Step 2/6: Project Name[/bold]\n")

        default_name = f"my-{self.config['project_type']}-project"

        name = Prompt.ask(
            "Enter project name",
            default=default_name
        )

        # Sanitize name
        name = name.lower().replace(" ", "-").replace("_", "-")
        self.config["project_name"] = name

        console.print(f"  ✓ Project name: [green]{name}[/green]")

    def _step_tech_stack(self) -> None:
        """Step 3: Confirm/customize tech stack."""
        console.print("\n[bold]Step 3/6: Tech Stack[/bold]\n")

        default_stack = self.TECH_STACKS.get(self.config["project_type"], [])

        if default_stack:
            console.print("Recommended stack for this project type:")
            for tech in default_stack:
                console.print(f"  • {tech}")

            use_default = Confirm.ask("\nUse recommended stack?", default=True)

            if use_default:
                self.config["tech_stack"] = default_stack
            else:
                custom = Prompt.ask("Enter technologies (comma-separated)")
                self.config["tech_stack"] = [t.strip() for t in custom.split(",")]
        else:
            custom = Prompt.ask("Enter technologies (comma-separated)")
            self.config["tech_stack"] = [t.strip() for t in custom.split(",") if t.strip()]

        console.print(f"  ✓ Stack: [green]{', '.join(self.config['tech_stack'])}[/green]")

    def _step_example_repos(self) -> None:
        """Step 4: Add example repositories."""
        console.print("\n[bold]Step 4/6: Example Repositories[/bold]\n")

        console.print("Add GitHub repositories to use as references/sources.")
        console.print("Leave empty to skip.\n")

        repos = []
        while True:
            repo = Prompt.ask(
                f"Repository URL ({len(repos)} added)",
                default=""
            )

            if not repo:
                break

            if repo.startswith(("http://", "https://", "github.com")):
                if not repo.startswith("http"):
                    repo = f"https://{repo}"
                repos.append(repo)
                console.print(f"  ✓ Added: [green]{repo}[/green]")
            else:
                console.print("  [yellow]Invalid URL, skipped[/yellow]")

        self.config["repositories"] = repos
        console.print(f"  ✓ Total repositories: [green]{len(repos)}[/green]")

    def _step_output_location(self) -> None:
        """Step 5: Select output location."""
        console.print("\n[bold]Step 5/6: Output Location[/bold]\n")

        default_path = "G:/" if Path("G:/").exists() else str(Path.home() / "projects")

        output = Prompt.ask(
            "Output directory",
            default=default_path
        )

        self.config["output_path"] = Path(output)
        self.config["full_path"] = self.config["output_path"] / self.config["project_name"]

        console.print(f"  ✓ Project will be created at: [green]{self.config['full_path']}[/green]")

    def _step_confirm(self) -> bool:
        """Step 6: Confirm and create."""
        console.print("\n[bold]Step 6/6: Confirmation[/bold]\n")

        table = Table(title="Project Configuration", show_header=False)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Type", self.config["project_type_name"])
        table.add_row("Name", self.config["project_name"])
        table.add_row("Stack", ", ".join(self.config["tech_stack"]))
        table.add_row("Repositories", str(len(self.config["repositories"])))
        table.add_row("Output", str(self.config["full_path"]))

        console.print(table)

        return Confirm.ask("\nCreate project with these settings?", default=True)


def run_wizard() -> dict[str, Any] | None:
    """Run the project wizard and return configuration."""
    wizard = ProjectWizard()
    return wizard.run()


async def execute_wizard_config(config: dict[str, Any]) -> bool:
    """Execute the wizard configuration to create a project."""

    console.print("\n[bold]Creating project...[/bold]\n")

    try:
        # Create output directory
        config["full_path"].mkdir(parents=True, exist_ok=True)

        # Create basic structure
        (config["full_path"] / "src").mkdir(exist_ok=True)
        (config["full_path"] / "tests").mkdir(exist_ok=True)
        (config["full_path"] / "docs").mkdir(exist_ok=True)

        # Create README
        readme_content = f"""# {config['project_name']}

{config['project_type_name']} project created with AI Synthesizer.

## Tech Stack

{chr(10).join(f'- {tech}' for tech in config['tech_stack'])}

## Getting Started

```bash
# Install dependencies
pip install -r requirements.txt

# Run the project
python -m src.main
```

## Project Structure

```
{config['project_name']}/
├── src/           # Source code
├── tests/         # Test files
├── docs/          # Documentation
└── requirements.txt
```

## Created with AI Synthesizer

This project was created using the AI Project Synthesizer wizard.
"""
        (config["full_path"] / "README.md").write_text(readme_content)

        # Create requirements.txt
        requirements = ["# Project dependencies\n"]
        if "FastAPI" in config["tech_stack"]:
            requirements.append("fastapi>=0.100.0\nuvicorn>=0.23.0\n")
        if "Typer" in config["tech_stack"]:
            requirements.append("typer>=0.9.0\nrich>=13.0.0\n")
        if "FastMCP" in config["tech_stack"]:
            requirements.append("fastmcp>=0.1.0\nmcp>=1.0.0\n")
        if "PyTorch" in config["tech_stack"]:
            requirements.append("torch>=2.0.0\n")
        if "LangChain" in config["tech_stack"]:
            requirements.append("langchain>=0.1.0\n")

        (config["full_path"] / "requirements.txt").write_text("".join(requirements))

        # Create main.py
        main_content = f'''"""
{config['project_name']} - Main Entry Point
"""

def main():
    """Main function."""
    print("Hello from {config['project_name']}!")


if __name__ == "__main__":
    main()
'''
        (config["full_path"] / "src" / "__init__.py").write_text("")
        (config["full_path"] / "src" / "main.py").write_text(main_content)

        console.print("[green]✅ Project created successfully![/green]")
        console.print(f"   Location: {config['full_path']}")

        return True

    except Exception as e:
        console.print(f"[red]❌ Failed to create project: {e}[/red]")
        return False
