"""
AI Project Synthesizer - Terminal UI Application

Rich-based TUI for full system control:
- Dashboard view
- Settings management
- Agent control
- Workflow monitoring
- Real-time logs
"""

import asyncio
from typing import List
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

console = Console()


class SynthesizerTUI:
    """
    Terminal UI for AI Project Synthesizer.

    Features:
    - Interactive menus
    - Real-time status
    - Settings management
    - Agent execution
    - Workflow control
    """

    def __init__(self):
        self.running = True
        self.current_view = "main"
        self._history: List[str] = []

    def clear(self):
        """Clear terminal."""
        console.clear()

    def header(self):
        """Display header."""
        console.print(Panel.fit(
            "[bold blue]🧬 AI Project Synthesizer[/bold blue]\n"
            "[dim]Terminal Interface v1.0[/dim]",
            border_style="blue"
        ))

    def main_menu(self) -> str:
        """Display main menu and get choice."""
        self.clear()
        self.header()

        menu = Table(show_header=False, box=None, padding=(0, 2))
        menu.add_column("Key", style="cyan bold")
        menu.add_column("Action")

        menu.add_row("1", "📊 Dashboard - View system status")
        menu.add_row("2", "🔍 Search - Search for resources")
        menu.add_row("3", "🚀 Assemble - Create new project")
        menu.add_row("4", "🤖 Agents - Run AI agents")
        menu.add_row("5", "⚙️  Settings - Configure system")
        menu.add_row("6", "📈 Metrics - View performance")
        menu.add_row("7", "🔧 Workflows - Manage n8n workflows")
        menu.add_row("8", "💬 Chat - Interactive AI chat")
        menu.add_row("q", "❌ Quit")

        console.print(Panel(menu, title="Main Menu", border_style="green"))

        return Prompt.ask("\n[cyan]Select option[/cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "q"])

    async def dashboard_view(self):
        """Display dashboard with system status."""
        self.clear()
        self.header()
        console.print("\n[bold]📊 System Dashboard[/bold]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading health status...", total=None)

            try:
                from src.core.health import check_health
                health = await check_health()
                progress.remove_task(task)

                # Health table
                table = Table(title="Component Health")
                table.add_column("Component", style="cyan")
                table.add_column("Status", justify="center")
                table.add_column("Latency", justify="right")
                table.add_column("Message")

                for c in health.components:
                    status_icon = "✅" if c.status.value == "healthy" else "❌"
                    table.add_row(
                        c.name,
                        f"{status_icon} {c.status.value}",
                        f"{c.latency_ms:.0f}ms" if c.latency_ms else "-",
                        c.message or "",
                    )

                console.print(table)

                # Overall status
                overall = "🟢 Healthy" if health.overall_status.value == "healthy" else "🔴 Unhealthy"
                console.print(f"\n[bold]Overall Status:[/bold] {overall}")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Error loading health: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def search_view(self):
        """Search for resources."""
        self.clear()
        self.header()
        console.print("\n[bold]🔍 Resource Search[/bold]\n")

        query = Prompt.ask("[cyan]Enter search query[/cyan]")
        if not query:
            return

        platforms = []
        if Confirm.ask("Search GitHub?", default=True):
            platforms.append("github")
        if Confirm.ask("Search HuggingFace?", default=True):
            platforms.append("huggingface")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Searching for '{query}'...", total=None)

            try:
                from src.discovery.unified_search import create_unified_search

                search = create_unified_search()
                results = await search.search(query, platforms=platforms, max_results=10)
                progress.remove_task(task)

                # Results table
                table = Table(title=f"Results for '{query}'")
                table.add_column("#", style="dim")
                table.add_column("Name", style="cyan")
                table.add_column("Platform")
                table.add_column("Stars", justify="right")
                table.add_column("Description", max_width=40)

                for i, r in enumerate(results.repositories[:10], 1):
                    table.add_row(
                        str(i),
                        r.name,
                        r.platform,
                        str(r.stars) if r.stars else "-",
                        (r.description or "")[:40],
                    )

                console.print(table)
                console.print(f"\n[green]Found {len(results.repositories)} repositories[/green]")

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Search error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def assemble_view(self):
        """Assemble a new project."""
        self.clear()
        self.header()
        console.print("\n[bold]🚀 Project Assembly[/bold]\n")

        idea = Prompt.ask("[cyan]Enter project idea[/cyan]")
        if not idea:
            return

        name = Prompt.ask("[cyan]Project name (optional)[/cyan]", default="")
        output_dir = Prompt.ask("[cyan]Output directory[/cyan]", default="G:/")

        if not Confirm.ask(f"\nAssemble project '{idea}' to {output_dir}?"):
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Assembling project...", total=None)

            try:
                from src.synthesis.project_assembler import ProjectAssembler, AssemblerConfig

                config = AssemblerConfig(base_output_dir=Path(output_dir))
                assembler = ProjectAssembler(config)
                project = await assembler.assemble(idea, name or None)

                progress.remove_task(task)

                console.print(Panel(
                    f"[green]✅ Project assembled successfully![/green]\n\n"
                    f"[bold]Name:[/bold] {project.name}\n"
                    f"[bold]Path:[/bold] {project.base_path}\n"
                    f"[bold]GitHub:[/bold] {project.github_repo_url or 'Not created'}",
                    title="Success",
                    border_style="green"
                ))

            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Assembly error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def agents_view(self):
        """Agent control panel."""
        self.clear()
        self.header()
        console.print("\n[bold]🤖 AI Agents[/bold]\n")

        menu = Table(show_header=False, box=None)
        menu.add_column("Key", style="cyan bold")
        menu.add_column("Agent")
        menu.add_column("Description")

        menu.add_row("1", "Research Agent", "Discover resources across platforms")
        menu.add_row("2", "Synthesis Agent", "Plan and create projects")
        menu.add_row("3", "Code Agent", "Generate and fix code")
        menu.add_row("4", "Automation Agent", "Run workflows and health checks")
        menu.add_row("b", "Back", "Return to main menu")

        console.print(menu)

        choice = Prompt.ask("\n[cyan]Select agent[/cyan]", choices=["1", "2", "3", "4", "b"])

        if choice == "b":
            return

        if choice == "1":
            await self._run_research_agent()
        elif choice == "2":
            await self._run_synthesis_agent()
        elif choice == "3":
            await self._run_code_agent()
        elif choice == "4":
            await self._run_automation_agent()

    async def _run_research_agent(self):
        """Run research agent."""
        topic = Prompt.ask("[cyan]Research topic[/cyan]")
        if not topic:
            return

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("Researching...", total=None)

            try:
                from src.agents import ResearchAgent
                agent = ResearchAgent()
                result = await agent.research(topic)
                progress.remove_task(task)

                console.print(Panel(
                    f"[bold]Research Results:[/bold]\n\n{result.get('output', 'No output')}",
                    title="Research Agent",
                    border_style="blue"
                ))
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def _run_synthesis_agent(self):
        """Run synthesis agent."""
        idea = Prompt.ask("[cyan]Project idea[/cyan]")
        if not idea:
            return

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
            task = progress.add_task("Planning project...", total=None)

            try:
                from src.agents import SynthesisAgent
                agent = SynthesisAgent()
                result = await agent._plan_project(idea)
                progress.remove_task(task)

                console.print(Panel(
                    f"[bold]Project Plan:[/bold]\n\n{result}",
                    title="Synthesis Agent",
                    border_style="green"
                ))
            except Exception as e:
                progress.remove_task(task)
                console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def _run_code_agent(self):
        """Run code agent."""
        console.print("\n[bold]Code Agent Options:[/bold]")
        console.print("1. Generate code")
        console.print("2. Fix code")
        console.print("3. Review code")

        choice = Prompt.ask("[cyan]Select[/cyan]", choices=["1", "2", "3"])

        try:
            from src.agents import CodeAgent
            agent = CodeAgent()

            if choice == "1":
                desc = Prompt.ask("[cyan]What should the code do?[/cyan]")
                lang = Prompt.ask("[cyan]Language[/cyan]", default="python")

                with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                    task = progress.add_task("Generating...", total=None)
                    code = await agent.generate(desc, lang)
                    progress.remove_task(task)

                console.print(Panel(Syntax(code, lang, theme="monokai"), title="Generated Code"))

            elif choice == "2":
                console.print("[cyan]Paste code (end with empty line):[/cyan]")
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                code = "\n".join(lines)

                error = Prompt.ask("[cyan]Error message[/cyan]")

                with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                    task = progress.add_task("Fixing...", total=None)
                    fixed = await agent.fix(code, error)
                    progress.remove_task(task)

                console.print(Panel(Syntax(fixed, "python", theme="monokai"), title="Fixed Code"))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def _run_automation_agent(self):
        """Run automation agent."""
        console.print("\n[bold]Automation Options:[/bold]")
        console.print("1. Health check")
        console.print("2. Run tests")
        console.print("3. Get metrics")

        choice = Prompt.ask("[cyan]Select[/cyan]", choices=["1", "2", "3"])

        try:
            from src.agents import AutomationAgent
            agent = AutomationAgent()

            with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                if choice == "1":
                    task = progress.add_task("Checking health...", total=None)
                    result = await agent._check_health()
                elif choice == "2":
                    task = progress.add_task("Running tests...", total=None)
                    result = await agent._run_tests()
                else:
                    task = progress.add_task("Getting metrics...", total=None)
                    result = await agent._get_metrics()

                progress.remove_task(task)

            console.print(Panel(str(result), title="Result"))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def settings_view(self):
        """Settings management."""
        self.clear()
        self.header()
        console.print("\n[bold]⚙️ Settings[/bold]\n")

        from src.core.settings_manager import get_settings_manager, SettingsTab
        manager = get_settings_manager()

        menu = Table(show_header=False, box=None)
        menu.add_column("Key", style="cyan bold")
        menu.add_column("Tab")

        tabs = [
            ("1", "General"),
            ("2", "Voice"),
            ("3", "Automation"),
            ("4", "Hotkeys"),
            ("5", "AI/ML"),
            ("6", "Workflows"),
            ("7", "Advanced"),
            ("b", "Back"),
        ]

        for key, name in tabs:
            menu.add_row(key, name)

        console.print(menu)

        choice = Prompt.ask("\n[cyan]Select tab[/cyan]", choices=["1", "2", "3", "4", "5", "6", "7", "b"])

        if choice == "b":
            return

        tab_map = {
            "1": SettingsTab.GENERAL,
            "2": SettingsTab.VOICE,
            "3": SettingsTab.AUTOMATION,
            "4": SettingsTab.HOTKEYS,
            "5": SettingsTab.AI_ML,
            "6": SettingsTab.WORKFLOWS,
            "7": SettingsTab.ADVANCED,
        }

        tab = tab_map[choice]
        settings = manager.get_tab(tab)

        # Display settings
        table = Table(title=f"{tab.value.title()} Settings")
        table.add_column("Setting", style="cyan")
        table.add_column("Value")
        table.add_column("Type")

        for field_name, field_value in settings:
            table.add_row(
                field_name,
                str(field_value),
                type(field_value).__name__,
            )

        console.print(table)

        if Confirm.ask("\nModify a setting?"):
            setting_name = Prompt.ask("[cyan]Setting name[/cyan]")
            if hasattr(settings, setting_name):
                current = getattr(settings, setting_name)
                if isinstance(current, bool):
                    new_value = Confirm.ask(f"Enable {setting_name}?", default=current)
                else:
                    new_value = Prompt.ask(f"New value for {setting_name}", default=str(current))
                    # Convert type
                    if isinstance(current, int):
                        new_value = int(new_value)
                    elif isinstance(current, float):
                        new_value = float(new_value)

                manager.update(tab, **{setting_name: new_value})
                console.print(f"[green]✅ Updated {setting_name}[/green]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def metrics_view(self):
        """View metrics."""
        self.clear()
        self.header()
        console.print("\n[bold]📈 Performance Metrics[/bold]\n")

        try:
            from src.automation.metrics import get_metrics_collector
            collector = get_metrics_collector()
            summary = collector.get_summary()

            if summary.get("actions"):
                table = Table(title="Action Metrics")
                table.add_column("Action", style="cyan")
                table.add_column("Count", justify="right")
                table.add_column("Avg (ms)", justify="right")
                table.add_column("P95 (ms)", justify="right")
                table.add_column("Success %", justify="right")

                for action, metrics in summary["actions"].items():
                    table.add_row(
                        action,
                        str(metrics.get("count", 0)),
                        f"{metrics.get('avg_ms', 0):.1f}",
                        f"{metrics.get('p95_ms', 0):.1f}",
                        f"{metrics.get('success_rate', 0):.0f}%",
                    )

                console.print(table)
            else:
                console.print("[dim]No metrics recorded yet[/dim]")

            console.print(f"\n[bold]Uptime:[/bold] {summary.get('uptime_seconds', 0):.0f}s")

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def workflows_view(self):
        """Workflow management."""
        self.clear()
        self.header()
        console.print("\n[bold]🔧 n8n Workflows[/bold]\n")

        # List available workflows
        workflows_dir = Path("src/automation/n8n_workflows")

        if workflows_dir.exists():
            table = Table(title="Available Workflows")
            table.add_column("#", style="dim")
            table.add_column("Workflow", style="cyan")
            table.add_column("File")

            workflow_files = list(workflows_dir.glob("*.json"))
            for i, f in enumerate(workflow_files, 1):
                name = f.stem.replace("_", " ").title()
                table.add_row(str(i), name, f.name)

            console.print(table)

        console.print("\n[bold]Options:[/bold]")
        console.print("1. Check n8n status")
        console.print("2. Trigger workflow")
        console.print("3. View workflow details")
        console.print("b. Back")

        choice = Prompt.ask("[cyan]Select[/cyan]", choices=["1", "2", "3", "b"])

        if choice == "1":
            try:
                from src.workflows import N8NClient
                client = N8NClient()
                status = await client.health_check()
                console.print(f"[green]n8n Status: {status}[/green]")
            except Exception as e:
                console.print(f"[red]n8n not available: {e}[/red]")

        Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def chat_view(self):
        """Interactive chat."""
        self.clear()
        self.header()
        console.print("\n[bold]💬 AI Chat[/bold]")
        console.print("[dim]Type 'exit' to return to menu[/dim]\n")

        try:
            from src.llm import LMStudioClient
            client = LMStudioClient()

            history = []

            while True:
                user_input = Prompt.ask("[cyan]You[/cyan]")

                if user_input.lower() in ["exit", "quit", "q"]:
                    break

                history.append({"role": "user", "content": user_input})

                with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
                    task = progress.add_task("Thinking...", total=None)

                    response = await client.complete(
                        user_input,
                        system_prompt="You are a helpful AI assistant for the AI Project Synthesizer."
                    )

                    progress.remove_task(task)

                console.print(f"[green]AI:[/green] {response}\n")
                history.append({"role": "assistant", "content": response})

        except Exception as e:
            console.print(f"[red]Chat error: {e}[/red]")
            Prompt.ask("\n[dim]Press Enter to continue[/dim]")

    async def run(self):
        """Run the TUI."""
        while self.running:
            choice = self.main_menu()

            if choice == "q":
                if Confirm.ask("Exit?"):
                    self.running = False
                    console.print("[dim]Goodbye![/dim]")
            elif choice == "1":
                await self.dashboard_view()
            elif choice == "2":
                await self.search_view()
            elif choice == "3":
                await self.assemble_view()
            elif choice == "4":
                await self.agents_view()
            elif choice == "5":
                await self.settings_view()
            elif choice == "6":
                await self.metrics_view()
            elif choice == "7":
                await self.workflows_view()
            elif choice == "8":
                await self.chat_view()


def run_tui():
    """Run the terminal UI."""
    tui = SynthesizerTUI()
    asyncio.run(tui.run())


if __name__ == "__main__":
    run_tui()
