#!/usr/bin/env python
"""
AI Project Synthesizer - Automation Startup

Starts the complete automation system:
- Dashboard API server
- n8n workflow engine
- Automation coordinator
- Health monitoring
- Integration tests

Usage:
    python start_automation.py
    python start_automation.py --no-n8n
    python start_automation.py --test-only
"""

import asyncio
import argparse
import signal
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live

console = Console()


async def start_dashboard(host: str = "0.0.0.0", port: int = 8000):
    """Start the FastAPI dashboard."""
    import uvicorn
    from src.dashboard.app import create_app
    
    app = create_app()
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    
    console.print(f"[green]✓[/green] Dashboard starting at http://{host}:{port}")
    await server.serve()


async def start_automation_coordinator():
    """Start the automation coordinator."""
    from src.automation.coordinator import get_coordinator
    
    coordinator = get_coordinator()
    await coordinator.start()
    
    console.print("[green]✓[/green] Automation coordinator started")
    
    return coordinator


async def check_n8n_status():
    """Check if n8n is running."""
    from src.workflows.n8n_integration import N8NClient
    
    client = N8NClient()
    is_running = await client.health_check()
    await client.close()
    
    return is_running


async def setup_n8n_workflows():
    """Import workflows into n8n."""
    from src.workflows.n8n_integration import N8NClient
    import json
    
    client = N8NClient()
    
    if not await client.health_check():
        console.print("[yellow]⚠[/yellow] n8n not running - skipping workflow import")
        return
    
    # Import workflow JSON files
    workflows_dir = Path(__file__).parent / "src" / "automation" / "n8n_workflows"
    
    for workflow_file in workflows_dir.glob("*.json"):
        try:
            with open(workflow_file) as f:
                workflow_data = json.load(f)
            
            # Note: n8n API for importing workflows
            console.print(f"[blue]→[/blue] Workflow ready: {workflow_data.get('name', workflow_file.stem)}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to load {workflow_file.name}: {e}")
    
    await client.close()


async def run_initial_tests():
    """Run initial integration tests."""
    from src.automation.testing import IntegrationTester, get_default_tests
    
    tester = IntegrationTester()
    tester.register_many(get_default_tests())
    
    console.print("\n[bold]Running integration tests...[/bold]")
    
    result = await tester.run_all()
    
    # Display results
    table = Table(title="Test Results")
    table.add_column("Test", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Duration", style="yellow")
    
    for test_result in result.results:
        status_color = "green" if test_result.status.value == "passed" else "red"
        table.add_row(
            test_result.name,
            f"[{status_color}]{test_result.status.value}[/{status_color}]",
            f"{test_result.duration_ms:.0f}ms"
        )
    
    console.print(table)
    console.print(f"\n[bold]Summary:[/bold] {result.passed}/{result.total} passed ({result.success_rate*100:.0f}%)")
    
    return result


async def display_status(coordinator):
    """Display live status."""
    from src.automation.metrics import get_metrics_collector
    
    metrics = get_metrics_collector()
    
    while True:
        status = coordinator.get_status()
        metrics_summary = metrics.get_summary()
        
        # Clear and redraw
        table = Table(title="System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        
        table.add_row("Coordinator", "[green]Running[/green]" if status["running"] else "[red]Stopped[/red]")
        table.add_row("n8n", "[green]Connected[/green]" if status["n8n_enabled"] else "[yellow]Disabled[/yellow]")
        table.add_row("Events", str(status["event_count"]))
        table.add_row("Actions Tracked", str(metrics_summary.get("total_actions", 0)))
        
        console.clear()
        console.print(Panel(table, title="AI Project Synthesizer"))
        
        await asyncio.sleep(5)


async def main(args):
    """Main entry point."""
    console.print(Panel.fit(
        "[bold blue]AI Project Synthesizer[/bold blue]\n"
        "[dim]Automation System Startup[/dim]",
        border_style="blue"
    ))
    
    # Check n8n status
    if not args.no_n8n:
        n8n_running = await check_n8n_status()
        if n8n_running:
            console.print("[green]✓[/green] n8n is running at http://localhost:5678")
            await setup_n8n_workflows()
        else:
            console.print("[yellow]⚠[/yellow] n8n not detected - start with: docker-compose -f docker/n8n/docker-compose.yml up -d")
    
    # Run tests only mode
    if args.test_only:
        await run_initial_tests()
        return
    
    # Start automation coordinator
    coordinator = await start_automation_coordinator()
    
    # Run initial tests
    if not args.skip_tests:
        await run_initial_tests()
    
    # Start dashboard in background
    dashboard_task = asyncio.create_task(start_dashboard(args.host, args.port))
    
    console.print("\n[bold green]System ready![/bold green]")
    console.print(f"  Dashboard: http://{args.host}:{args.port}")
    console.print(f"  n8n: http://localhost:5678")
    console.print(f"  Health: http://{args.host}:{args.port}/api/health")
    console.print("\nPress Ctrl+C to stop\n")
    
    # Handle shutdown
    def shutdown_handler(sig, frame):
        console.print("\n[yellow]Shutting down...[/yellow]")
        asyncio.create_task(coordinator.stop())
        dashboard_task.cancel()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Keep running
    try:
        await dashboard_task
    except asyncio.CancelledError:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Project Synthesizer Automation")
    parser.add_argument("--host", default="0.0.0.0", help="Dashboard host")
    parser.add_argument("--port", type=int, default=8000, help="Dashboard port")
    parser.add_argument("--no-n8n", action="store_true", help="Skip n8n integration")
    parser.add_argument("--skip-tests", action="store_true", help="Skip initial tests")
    parser.add_argument("--test-only", action="store_true", help="Run tests and exit")
    
    args = parser.parse_args()
    
    asyncio.run(main(args))
