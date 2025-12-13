"""
AI Project Synthesizer - Command Line Interface

Complete CLI for repository search, analysis, synthesis, and documentation generation.
Entry point for the 'ai-synthesizer' and 'synth' commands.

Usage:
    ai-synthesizer search "machine learning transformers"
    ai-synthesizer analyze https://github.com/user/repo
    ai-synthesizer synthesize --repos repo1,repo2 --output ./project
    ai-synthesizer resolve --repos repo1,repo2
    ai-synthesizer docs ./my-project
"""

import asyncio
import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from src.core.config import get_settings
from src.core.logging import get_logger

# Initialize CLI app and console
app = typer.Typer(
    name="ai-synthesizer",
    help="🧬 AI Project Synthesizer - Intelligent multi-repository code synthesis",
    add_completion=True,
    no_args_is_help=True,
)
console = Console()
logger = get_logger(__name__)

# Sub-commands
search_app = typer.Typer(help="Search for repositories across platforms")
analyze_app = typer.Typer(help="Analyze repository structure and dependencies")
synthesize_app = typer.Typer(help="Synthesize projects from multiple repositories")
resolve_app = typer.Typer(help="Resolve dependencies across repositories")
docs_app = typer.Typer(help="Generate documentation for projects")
config_app = typer.Typer(help="Manage configuration settings")


def print_banner() -> None:
    """Print the application banner."""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║           🧬 AI Project Synthesizer v1.0.0                    ║
║     Intelligent Multi-Repository Code Synthesis Platform      ║
╚═══════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(banner, style="bold blue"))


def run_async(coro):
    """Run an async coroutine in the event loop."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ============================================
# SEARCH COMMANDS
# ============================================

@app.command("search")
def search_repositories(
    query: str = typer.Argument(..., help="Search query for repositories"),
    platforms: str = typer.Option(
        "github,huggingface",
        "--platforms", "-p",
        help="Comma-separated platforms to search (github,huggingface,kaggle,arxiv)"
    ),
    max_results: int = typer.Option(
        20,
        "--max-results", "-n",
        help="Maximum number of results per platform"
    ),
    language: str | None = typer.Option(
        None,
        "--language", "-l",
        help="Filter by programming language"
    ),
    min_stars: int = typer.Option(
        10,
        "--min-stars", "-s",
        help="Minimum star count for repositories"
    ),
    output_format: str = typer.Option(
        "table",
        "--format", "-f",
        help="Output format: table, json, or simple"
    ),
) -> None:
    """
    Search for repositories across multiple platforms.

    Examples:
        ai-synthesizer search "machine learning transformers"
        ai-synthesizer search "web scraping" --platforms github,kaggle --min-stars 100
        ai-synthesizer search "llm agents" --language python --format json
    """
    console.print(f"\n🔍 Searching for: [bold cyan]{query}[/bold cyan]\n")

    async def _search():
        from src.discovery.unified_search import create_unified_search

        search = create_unified_search()
        platform_list = [p.strip() for p in platforms.split(",")]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Searching {', '.join(platform_list)}...", total=None)

            results = await search.search(
                query=query,
                platforms=platform_list,
                max_results=max_results,
                language_filter=language,
                min_stars=min_stars,
            )

            progress.update(task, completed=True)

        return results

    try:
        results = run_async(_search())

        if not results.repositories:
            console.print("[yellow]No repositories found matching your query.[/yellow]")
            return

        if output_format == "json":
            output = {
                "query": query,
                "total_results": results.total_count,
                "repositories": [
                    {
                        "name": r.full_name,
                        "url": r.url,
                        "description": r.description,
                        "stars": r.stars,
                        "language": r.language,
                        "platform": r.platform,
                    }
                    for r in results.repositories
                ]
            }
            console.print(Syntax(json.dumps(output, indent=2), "json"))
        elif output_format == "simple":
            for repo in results.repositories:
                console.print(f"• {repo.full_name} ({repo.platform}) - ⭐ {repo.stars}")
        else:
            # Table format
            table = Table(title=f"Search Results ({results.total_count} total)")
            table.add_column("Repository", style="cyan")
            table.add_column("Platform", style="green")
            table.add_column("Stars", justify="right", style="yellow")
            table.add_column("Language", style="magenta")
            table.add_column("Description", max_width=40)

            for repo in results.repositories:
                table.add_row(
                    repo.full_name,
                    repo.platform,
                    str(repo.stars),
                    repo.language or "N/A",
                    (repo.description[:37] + "...") if repo.description and len(repo.description) > 40 else (repo.description or ""),
                )

            console.print(table)

        console.print(f"\n✅ Found [bold green]{len(results.repositories)}[/bold green] repositories")

    except Exception as e:
        console.print(f"[red]Error during search: {e}[/red]")
        logger.exception("Search failed")
        raise typer.Exit(code=1)


# ============================================
# ANALYZE COMMANDS
# ============================================

@app.command("analyze")
def analyze_repository(
    repo_url: str = typer.Argument(..., help="Repository URL to analyze"),
    include_deps: bool = typer.Option(
        True,
        "--include-deps/--no-deps",
        help="Include dependency analysis"
    ),
    include_quality: bool = typer.Option(
        True,
        "--include-quality/--no-quality",
        help="Include code quality scoring"
    ),
    extract_components: bool = typer.Option(
        False,
        "--extract-components", "-e",
        help="Identify extractable code components"
    ),
    output_format: str = typer.Option(
        "rich",
        "--format", "-f",
        help="Output format: rich, json, or summary"
    ),
) -> None:
    """
    Perform deep analysis of a repository.

    Examples:
        ai-synthesizer analyze https://github.com/user/repo
        ai-synthesizer analyze https://github.com/user/repo --extract-components
        ai-synthesizer analyze https://github.com/user/repo --format json
    """
    console.print(f"\n🔬 Analyzing: [bold cyan]{repo_url}[/bold cyan]\n")

    async def _analyze():
        from src.mcp_server.tools import handle_analyze_repository

        return await handle_analyze_repository({
            "repo_url": repo_url,
            "include_transitive_deps": include_deps,
            "extract_components": extract_components,
        })

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Cloning and analyzing repository...", total=None)
            result = run_async(_analyze())
            progress.update(task, completed=True)

        if result.get("error"):
            console.print(f"[red]Analysis failed: {result.get('message')}[/red]")
            raise typer.Exit(code=1)

        if output_format == "json":
            console.print(Syntax(json.dumps(result, indent=2, default=str), "json"))
        elif output_format == "summary":
            repo = result.get("repository", {})
            console.print(f"Repository: {repo.get('name')}")
            console.print(f"Platform: {repo.get('platform')}")
            console.print(f"Language: {repo.get('language')}")
            console.print(f"Stars: {repo.get('stars')}")
            console.print(f"Files Analyzed: {result.get('files_analyzed', 0)}")
            console.print(f"Lines of Code: {result.get('lines_of_code', 0)}")
        else:
            # Rich format
            repo = result.get("repository", {})

            # Repository info panel
            repo_info = f"""
[bold]Name:[/bold] {repo.get('name')}
[bold]Platform:[/bold] {repo.get('platform')}
[bold]Language:[/bold] {repo.get('language')}
[bold]Stars:[/bold] ⭐ {repo.get('stars')}
[bold]URL:[/bold] {repo.get('url')}
[bold]Description:[/bold] {repo.get('description', 'N/A')}
            """
            console.print(Panel(repo_info, title="📦 Repository Info", border_style="blue"))

            # Analysis stats
            stats = f"""
[bold]Files Analyzed:[/bold] {result.get('files_analyzed', 0)}
[bold]Lines of Code:[/bold] {result.get('lines_of_code', 0)}
            """
            console.print(Panel(stats, title="📊 Analysis Stats", border_style="green"))

            # Dependencies
            deps = result.get("dependencies", {})
            if deps:
                dep_count = deps.get("direct_count", 0)
                console.print(Panel(f"Direct Dependencies: {dep_count}", title="📚 Dependencies", border_style="yellow"))

            # Quality score
            quality = result.get("quality_score", {})
            if quality:
                score = quality.get("overall_score", 0)
                console.print(Panel(f"Overall Score: {score}/100", title="✨ Code Quality", border_style="magenta"))

        console.print("\n✅ Analysis complete!")

    except Exception as e:
        console.print(f"[red]Error during analysis: {e}[/red]")
        logger.exception("Analysis failed")
        raise typer.Exit(code=1)


# ============================================
# SYNTHESIZE COMMANDS
# ============================================

@app.command("synthesize")
def synthesize_project(
    repos: str = typer.Option(
        ...,
        "--repos", "-r",
        help="Comma-separated repository URLs"
    ),
    project_name: str = typer.Option(
        ...,
        "--name", "-n",
        help="Name for the synthesized project"
    ),
    output_path: str = typer.Option(
        "./output",
        "--output", "-o",
        help="Output directory path"
    ),
    template: str = typer.Option(
        "python-default",
        "--template", "-t",
        help="Project template (python-default, python-ml, python-web, minimal)"
    ),
) -> None:
    """
    Synthesize a unified project from multiple repositories.

    Examples:
        ai-synthesizer synthesize --repos url1,url2 --name my-project --output ./projects
        ai-synthesizer synthesize -r url1,url2 -n ml-toolkit -t python-ml
    """
    repo_list = [r.strip() for r in repos.split(",")]
    console.print(f"\n🧬 Synthesizing project: [bold cyan]{project_name}[/bold cyan]")
    console.print(f"   From {len(repo_list)} repositories\n")

    async def _synthesize():
        from src.mcp_server.tools import handle_synthesize_project

        return await handle_synthesize_project({
            "repositories": [{"repo_url": url} for url in repo_list],
            "project_name": project_name,
            "output_path": output_path,
            "template": template,
        })

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Synthesizing project (this may take a few minutes)...", total=None)
            result = run_async(_synthesize())
            progress.update(task, completed=True)

        if result.get("error"):
            console.print(f"[red]Synthesis failed: {result.get('message')}[/red]")
            raise typer.Exit(code=1)

        console.print(Panel(f"""
[bold green]✅ Project synthesized successfully![/bold green]

[bold]Project Path:[/bold] {result.get('project_path')}
[bold]Template:[/bold] {template}
[bold]Sources:[/bold] {len(repo_list)} repositories
        """, title="🎉 Synthesis Complete", border_style="green"))

    except Exception as e:
        console.print(f"[red]Error during synthesis: {e}[/red]")
        logger.exception("Synthesis failed")
        raise typer.Exit(code=1)


# ============================================
# RESOLVE COMMANDS
# ============================================

@app.command("resolve")
def resolve_dependencies(
    repos: str = typer.Option(
        ...,
        "--repos", "-r",
        help="Comma-separated repository URLs"
    ),
    python_version: str = typer.Option(
        "3.11",
        "--python", "-p",
        help="Target Python version"
    ),
    output_file: str | None = typer.Option(
        None,
        "--output", "-o",
        help="Output file for resolved requirements"
    ),
) -> None:
    """
    Resolve and merge dependencies from multiple repositories.

    Examples:
        ai-synthesizer resolve --repos url1,url2
        ai-synthesizer resolve -r url1,url2 --python 3.12 --output requirements.txt
    """
    repo_list = [r.strip() for r in repos.split(",")]
    console.print(f"\n📦 Resolving dependencies from {len(repo_list)} repositories\n")

    async def _resolve():
        from src.mcp_server.tools import handle_resolve_dependencies

        return await handle_resolve_dependencies({
            "repositories": repo_list,
            "python_version": python_version,
        })

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Resolving dependencies...", total=None)
            result = run_async(_resolve())
            progress.update(task, completed=True)

        if result.get("error"):
            console.print(f"[red]Resolution failed: {result.get('message')}[/red]")
            raise typer.Exit(code=1)

        # Display results
        packages = result.get("packages", [])

        table = Table(title=f"Resolved Dependencies (Python {python_version})")
        table.add_column("Package", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Source", style="yellow")

        for pkg in packages:
            table.add_row(
                pkg.get("name", ""),
                pkg.get("version", ""),
                pkg.get("source", ""),
            )

        console.print(table)

        # Save to file if requested
        if output_file:
            requirements_txt = result.get("requirements_txt", "")
            Path(output_file).write_text(requirements_txt)
            console.print(f"\n✅ Requirements saved to [bold]{output_file}[/bold]")

        console.print(f"\n✅ Resolved [bold green]{len(packages)}[/bold green] packages")

        if result.get("warnings"):
            console.print("\n⚠️ Warnings:")
            for warning in result.get("warnings", []):
                console.print(f"  • {warning}")

    except Exception as e:
        console.print(f"[red]Error during resolution: {e}[/red]")
        logger.exception("Resolution failed")
        raise typer.Exit(code=1)


# ============================================
# DOCS COMMANDS
# ============================================

@app.command("docs")
def generate_documentation(
    project_path: str = typer.Argument(..., help="Path to the project to document"),
    doc_types: str = typer.Option(
        "readme,architecture,api",
        "--types", "-t",
        help="Comma-separated documentation types to generate"
    ),
    llm_enhanced: bool = typer.Option(
        True,
        "--llm/--no-llm",
        help="Use LLM for enhanced documentation quality"
    ),
) -> None:
    """
    Generate comprehensive documentation for a project.

    Examples:
        ai-synthesizer docs ./my-project
        ai-synthesizer docs ./my-project --types readme,api
        ai-synthesizer docs ./my-project --no-llm
    """
    console.print(f"\n📝 Generating documentation for: [bold cyan]{project_path}[/bold cyan]\n")

    async def _generate():
        from src.mcp_server.tools import handle_generate_documentation

        return await handle_generate_documentation({
            "project_path": project_path,
            "doc_types": [t.strip() for t in doc_types.split(",")],
            "llm_enhanced": llm_enhanced,
        })

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating documentation...", total=None)
            result = run_async(_generate())
            progress.update(task, completed=True)

        if result.get("error"):
            console.print(f"[red]Documentation generation failed: {result.get('message')}[/red]")
            raise typer.Exit(code=1)

        documents = result.get("documents", [])

        console.print(Panel(f"""
[bold green]✅ Documentation generated successfully![/bold green]

[bold]Documents Created:[/bold] {len(documents)}
[bold]LLM Enhanced:[/bold] {'Yes' if result.get('llm_enhanced') else 'No'}
        """, title="📚 Documentation Complete", border_style="green"))

        for doc in documents:
            console.print(f"  • {doc}")

    except Exception as e:
        console.print(f"[red]Error during documentation generation: {e}[/red]")
        logger.exception("Documentation generation failed")
        raise typer.Exit(code=1)


# ============================================
# CONFIG COMMANDS
# ============================================

@app.command("config")
def show_config(
    show_all: bool = typer.Option(
        False,
        "--all", "-a",
        help="Show all configuration including sensitive values"
    ),
) -> None:
    """
    Show current configuration settings.

    Examples:
        ai-synthesizer config
        ai-synthesizer config --all
    """
    settings = get_settings()

    # Get enabled platforms using the proper method
    enabled_platforms = settings.platforms.get_enabled_platforms()

    config_info = f"""
[bold]Environment:[/bold] {settings.app.app_env}
[bold]Debug Mode:[/bold] {settings.app.debug}
[bold]Log Level:[/bold] {settings.app.log_level}

[bold]Enabled Platforms:[/bold]
  • GitHub: {'✅' if 'github' in enabled_platforms else '❌'}
  • HuggingFace: {'✅' if 'huggingface' in enabled_platforms else '❌'}
  • Kaggle: {'✅' if 'kaggle' in enabled_platforms else '❌'}
  • arXiv: {'✅' if 'arxiv' in enabled_platforms else '❌'}

[bold]LLM Settings:[/bold]
  • Ollama Host: {settings.llm.ollama_host}
  • Default Model: {settings.llm.default_model}

[bold]Cache Settings:[/bold]
  • Enabled: {settings.cache.enabled}
  • TTL: {settings.cache.ttl}s
    """

    console.print(Panel(config_info, title="⚙️ Configuration", border_style="blue"))

    if show_all:
        console.print("\n[yellow]⚠️ Sensitive values:[/yellow]")
        github_token = settings.platforms.github_token.get_secret_value() if settings.platforms.github_token else ""
        hf_token = settings.platforms.huggingface_token.get_secret_value() if settings.platforms.huggingface_token else ""
        console.print(f"  GitHub Token: {'Set' if github_token else 'Not set'}")
        console.print(f"  HuggingFace Token: {'Set' if hf_token else 'Not set'}")


# ============================================
# VERSION AND INFO
# ============================================

@app.command("version")
def show_version() -> None:
    """Show version information."""
    console.print("AI Project Synthesizer v1.0.0")


@app.command("info")
def show_info() -> None:
    """Show detailed information about the tool."""
    print_banner()

    info = """
[bold]AI Project Synthesizer[/bold] is an intelligent platform for discovering,
analyzing, and synthesizing code from multiple repositories into unified projects.

[bold]Key Features:[/bold]
  • Multi-platform search (GitHub, HuggingFace, Kaggle, arXiv)
  • Deep code analysis with AST parsing
  • Intelligent dependency resolution
  • Code synthesis from multiple sources
  • Automated documentation generation

[bold]Usage:[/bold]
  ai-synthesizer search "query"     - Search repositories
  ai-synthesizer analyze <url>      - Analyze a repository
  ai-synthesizer synthesize ...     - Create unified project
  ai-synthesizer resolve ...        - Resolve dependencies
  ai-synthesizer docs <path>        - Generate documentation
  ai-synthesizer config             - Show configuration

[bold]Documentation:[/bold]
  https://github.com/Ghenghis/AI-Project-Synthesizer

[bold]Support:[/bold]
  https://github.com/Ghenghis/AI-Project-Synthesizer/issues
    """
    console.print(Panel(info, title="ℹ️ About", border_style="cyan"))


# ============================================
# MCP SERVER COMMAND
# ============================================

@app.command("check")
def run_gap_check(
    fix: bool = typer.Option(
        True,
        "--fix/--no-fix",
        help="Auto-fix issues"
    ),
    report: bool = typer.Option(
        False,
        "--report", "-r",
        help="Save markdown report"
    ),
) -> None:
    """
    Run gap analysis and auto-repair.

    Checks for:
    - Missing files and directories
    - Configuration issues
    - Import errors
    - Integration problems

    Examples:
        ai-synthesizer check
        ai-synthesizer check --no-fix
        ai-synthesizer check --report
    """
    import asyncio
    from datetime import datetime
    from pathlib import Path

    from src.core.gap_analyzer import GapSeverity, run_gap_analysis

    console.print("\n🔍 Running Gap Analysis...\n")

    async def analyze():
        report_data = await run_gap_analysis(auto_fix=fix)
        return report_data

    result = asyncio.run(analyze())

    # Summary table
    table = Table(title="Gap Analysis Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Gaps", str(result.total_gaps))
    table.add_row("Fixed", str(result.fixed_count))
    table.add_row("Failed", str(result.failed_count))
    table.add_row("Remaining", str(len(result.unfixed_gaps)))

    console.print(table)

    # Show critical issues
    if result.critical_gaps:
        console.print("\n[bold red]⚠️ Critical Issues:[/bold red]")
        for gap in result.critical_gaps:
            status = "✅" if gap.fixed else "❌"
            console.print(f"  {status} {gap.description}")

    # Show all gaps
    if result.gaps:
        console.print("\n[bold]All Gaps:[/bold]")
        for gap in result.gaps:
            status = "✅" if gap.fixed else "⬜"
            severity_color = {
                GapSeverity.CRITICAL: "red",
                GapSeverity.HIGH: "yellow",
                GapSeverity.MEDIUM: "blue",
            }.get(gap.severity, "dim")
            console.print(f"  {status} [{severity_color}]{gap.severity.value}[/{severity_color}] {gap.description}")
    else:
        console.print("\n[bold green]✅ No gaps found![/bold green]")

    # Save report
    if report:
        report_path = Path(f"reports/gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(result.to_markdown(), encoding="utf-8")
        console.print(f"\n[dim]Report saved: {report_path}[/dim]")

    # Exit code
    if result.unfixed_gaps and any(g.severity == GapSeverity.CRITICAL for g in result.unfixed_gaps):
        raise typer.Exit(code=1)


@app.command("tui")
def start_tui() -> None:
    """
    Start the Terminal UI for interactive control.

    Full-featured terminal interface with:
    - Dashboard view
    - Search and assembly
    - Agent control
    - Settings management
    - AI chat
    """
    console.print("\n🖥️ Starting Terminal UI...\n")

    try:
        from src.tui import run_tui
        run_tui()
    except KeyboardInterrupt:
        console.print("\n👋 TUI closed.")
    except Exception as e:
        console.print(f"[red]Failed to start TUI: {e}[/red]")
        raise typer.Exit(code=1)


@app.command("settings")
def manage_settings(
    tab: str = typer.Option(
        "general",
        "--tab", "-t",
        help="Settings tab (general, voice, automation, hotkeys, ai_ml, workflows, advanced)"
    ),
    show: bool = typer.Option(
        False,
        "--show", "-s",
        help="Show current settings for the tab"
    ),
    toggle: str | None = typer.Option(
        None,
        "--toggle",
        help="Toggle a boolean setting (e.g., auto_save)"
    ),
    set_value: str | None = typer.Option(
        None,
        "--set",
        help="Set a value (format: key=value)"
    ),
    reset: bool = typer.Option(
        False,
        "--reset",
        help="Reset tab to defaults"
    ),
) -> None:
    """
    Manage system settings from the command line.

    Examples:
        ai-synthesizer settings --show
        ai-synthesizer settings --tab voice --show
        ai-synthesizer settings --tab general --toggle auto_save
        ai-synthesizer settings --tab voice --set mode=continuous
        ai-synthesizer settings --tab general --reset
    """
    from src.core.settings_manager import SettingsTab, get_settings_manager

    manager = get_settings_manager()

    try:
        settings_tab = SettingsTab(tab)
    except ValueError:
        console.print(f"[red]Invalid tab: {tab}[/red]")
        console.print("Valid tabs: general, voice, automation, hotkeys, ai_ml, workflows, advanced")
        raise typer.Exit(code=1)

    if reset:
        manager.reset_to_defaults(settings_tab)
        console.print(f"[green]✅ Reset {tab} settings to defaults[/green]")
        return

    if toggle:
        try:
            new_value = manager.toggle(settings_tab, toggle)
            console.print(f"[green]✅ {toggle} = {new_value}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to toggle {toggle}: {e}[/red]")
        return

    if set_value:
        try:
            key, value = set_value.split("=", 1)
            # Try to convert value to appropriate type
            if value.lower() in ("true", "false"):
                value = value.lower() == "true"
            elif value.isdigit():
                value = int(value)
            elif value.replace(".", "").isdigit():
                value = float(value)

            manager.update(settings_tab, **{key: value})
            console.print(f"[green]✅ {key} = {value}[/green]")
        except Exception as e:
            console.print(f"[red]Failed to set value: {e}[/red]")
        return

    if True:  # Default to show
        tab_settings = manager.get_tab(settings_tab)

        table = Table(title=f"{tab.title()} Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Type", style="dim")

        for field_name, field_value in tab_settings:
            value_str = str(field_value)
            if len(value_str) > 50:
                value_str = value_str[:47] + "..."
            table.add_row(field_name, value_str, type(field_value).__name__)

        console.print(table)


@app.command("serve")
def start_mcp_server() -> None:
    """
    Start the MCP server for Windsurf IDE integration.

    This command starts the Model Context Protocol server that allows
    Windsurf IDE to interact with AI Project Synthesizer.
    """
    console.print("\n🚀 Starting MCP Server...\n")

    try:
        from src.mcp_server.server import main as server_main
        asyncio.run(server_main())
    except KeyboardInterrupt:
        console.print("\n👋 MCP Server stopped.")
    except Exception as e:
        console.print(f"[red]Failed to start MCP server: {e}[/red]")
        logger.exception("MCP server failed")
        raise typer.Exit(code=1)


# ============================================
# WIZARD COMMAND
# ============================================

@app.command("wizard")
def wizard_command() -> None:
    """
    Interactive project creation wizard.

    Guides you through creating a new project step-by-step:
    1. Select project type (MCP, CLI, API, ML, etc.)
    2. Enter project name
    3. Choose tech stack
    4. Add example repositories
    5. Select output location
    6. Confirm and create

    Example:
        ai-synthesizer wizard
    """
    from src.tui.wizard import execute_wizard_config, run_wizard

    config = run_wizard()

    if config:
        # Execute the configuration
        success = asyncio.run(execute_wizard_config(config))

        if success:
            console.print("\n[bold green]🎉 Project ready![/bold green]")
            console.print("\nNext steps:")
            console.print(f"  cd {config['full_path']}")
            console.print("  pip install -r requirements.txt")
            console.print("  python -m src.main")
        else:
            raise typer.Exit(code=1)


# ============================================
# RECIPE COMMANDS
# ============================================

@app.command("recipe")
def recipe_command(
    action: str = typer.Argument(..., help="Action: list, show, run, validate"),
    name: str | None = typer.Argument(None, help="Recipe name (for show/run/validate)"),
    output: str | None = typer.Option(
        None,
        "--output", "-o",
        help="Output directory for run action"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without executing"
    ),
) -> None:
    """
    Manage and run synthesis recipes.

    Actions:
        list     - List all available recipes
        show     - Show details of a specific recipe
        run      - Run a recipe to create a project
        validate - Validate a recipe file

    Examples:
        ai-synthesizer recipe list
        ai-synthesizer recipe show mcp-server-starter
        ai-synthesizer recipe run rag-chatbot --output G:/projects
    """
    from src.recipes import RecipeLoader, RecipeRunner

    loader = RecipeLoader()

    if action == "list":
        recipes = loader.list_recipes()

        if not recipes:
            console.print("[yellow]No recipes found in recipes/ directory[/yellow]")
            return

        table = Table(title="Available Recipes")
        table.add_column("Name", style="cyan")
        table.add_column("Version", style="green")
        table.add_column("Description")
        table.add_column("Tags", style="dim")

        for recipe in recipes:
            table.add_row(
                recipe["name"],
                recipe["version"],
                recipe["description"][:50] + "..." if len(recipe["description"]) > 50 else recipe["description"],
                ", ".join(recipe["tags"][:3])
            )

        console.print(table)

    elif action == "show":
        if not name:
            console.print("[red]Recipe name required for 'show' action[/red]")
            raise typer.Exit(code=1)

        recipe = loader.load_recipe(name)
        if not recipe:
            console.print(f"[red]Recipe not found: {name}[/red]")
            raise typer.Exit(code=1)

        console.print(Panel(f"[bold]{recipe.name}[/bold] v{recipe.version}", title="Recipe"))
        console.print(f"\n[bold]Description:[/bold] {recipe.description}")
        console.print(f"[bold]Author:[/bold] {recipe.author or 'Unknown'}")
        console.print(f"[bold]Tags:[/bold] {', '.join(recipe.tags)}")

        console.print("\n[bold]Sources:[/bold]")
        for source in recipe.sources:
            console.print(f"  - {source.repo}")
            if source.extract:
                console.print(f"    Extract: {', '.join(source.extract[:3])}")

        console.print("\n[bold]Synthesis:[/bold]")
        console.print(f"  Strategy: {recipe.synthesis.strategy}")
        console.print(f"  Template: {recipe.synthesis.template}")

        if recipe.post_synthesis:
            console.print(f"\n[bold]Post-synthesis:[/bold] {', '.join(recipe.post_synthesis)}")

        if recipe.variables:
            console.print("\n[bold]Variables:[/bold]")
            for var_name, var_config in recipe.variables.items():
                default = var_config.get("default", "")
                console.print(f"  - {var_name}: {var_config.get('description', '')} (default: {default})")

    elif action == "run":
        if not name:
            console.print("[red]Recipe name required for 'run' action[/red]")
            raise typer.Exit(code=1)

        output_path = Path(output) if output else Path.cwd()

        runner = RecipeRunner()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(f"Running recipe: {name}...", total=None)

            result = asyncio.run(runner.run(
                recipe_name=name,
                output_path=output_path,
                dry_run=dry_run,
            ))

        if result.success:
            console.print("\n[green]✅ Recipe completed successfully![/green]")
            console.print(f"   Project: {result.project_path}")
            console.print(f"   Repos cloned: {result.repos_cloned}")
            console.print(f"   Files created: {result.files_created}")

            if result.warnings:
                console.print("\n[yellow]Warnings:[/yellow]")
                for warning in result.warnings:
                    console.print(f"  - {warning}")
        else:
            console.print("\n[red]❌ Recipe failed[/red]")
            for error in result.errors:
                console.print(f"  - {error}")
            raise typer.Exit(code=1)

    elif action == "validate":
        if not name:
            console.print("[red]Recipe name required for 'validate' action[/red]")
            raise typer.Exit(code=1)

        recipe = loader.load_recipe(name)
        if not recipe:
            console.print(f"[red]Recipe not found: {name}[/red]")
            raise typer.Exit(code=1)

        errors = loader.validate_recipe(recipe)

        if errors:
            console.print("[red]❌ Recipe validation failed:[/red]")
            for error in errors:
                console.print(f"  - {error}")
            raise typer.Exit(code=1)
        else:
            console.print(f"[green]✅ Recipe '{name}' is valid[/green]")

    else:
        console.print(f"[red]Unknown action: {action}[/red]")
        console.print("Valid actions: list, show, run, validate")
        raise typer.Exit(code=1)


# ============================================
# MAIN ENTRY POINT
# ============================================

def main() -> None:
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        logger.exception("CLI fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Export for tests
__all__ = ["app", "main"]
