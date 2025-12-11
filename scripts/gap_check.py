#!/usr/bin/env python
"""
Gap Analysis & Auto-Repair Script

Run comprehensive gap analysis and auto-repair:
    python scripts/gap_check.py
    python scripts/gap_check.py --no-fix
    python scripts/gap_check.py --report
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


async def run_analysis(auto_fix: bool = True, save_report: bool = False):
    """Run gap analysis."""
    from src.core.gap_analyzer import run_gap_analysis, GapSeverity
    from src.core.auto_repair import repair_gaps
    
    console.print(Panel.fit(
        "[bold cyan]AI Project Synthesizer[/bold cyan]\n"
        "[dim]Gap Analysis & Auto-Repair[/dim]",
        border_style="cyan"
    ))
    
    # Run analysis
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Analyzing system...", total=None)
        report = await run_gap_analysis(auto_fix=auto_fix)
        progress.update(task, completed=True)
    
    # Display results
    console.print()
    
    # Summary
    summary_table = Table(title="Analysis Summary", show_header=False)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="green")
    
    summary_table.add_row("Total Gaps Found", str(report.total_gaps))
    summary_table.add_row("Auto-Fixed", str(report.fixed_count))
    summary_table.add_row("Failed Fixes", str(report.failed_count))
    summary_table.add_row("Remaining", str(len(report.unfixed_gaps)))
    
    console.print(summary_table)
    console.print()
    
    # Critical issues
    if report.critical_gaps:
        console.print("[bold red]⚠️ Critical Issues:[/bold red]")
        for gap in report.critical_gaps:
            status = "✅" if gap.fixed else "❌"
            console.print(f"  {status} {gap.description}")
        console.print()
    
    # All gaps by severity
    if report.gaps:
        gaps_table = Table(title="All Gaps")
        gaps_table.add_column("Status", width=6)
        gaps_table.add_column("Severity", width=10)
        gaps_table.add_column("Category", width=12)
        gaps_table.add_column("Description")
        gaps_table.add_column("Location", style="dim")
        
        severity_colors = {
            GapSeverity.CRITICAL: "red",
            GapSeverity.HIGH: "yellow",
            GapSeverity.MEDIUM: "blue",
            GapSeverity.LOW: "dim",
            GapSeverity.INFO: "dim",
        }
        
        for gap in sorted(report.gaps, key=lambda g: list(GapSeverity).index(g.severity)):
            status = "✅" if gap.fixed else "⬜"
            color = severity_colors.get(gap.severity, "white")
            gaps_table.add_row(
                status,
                f"[{color}]{gap.severity.value}[/{color}]",
                gap.category.value,
                gap.description[:50] + "..." if len(gap.description) > 50 else gap.description,
                gap.location,
            )
        
        console.print(gaps_table)
    else:
        console.print("[bold green]✅ No gaps found! System is healthy.[/bold green]")
    
    # Save report
    if save_report:
        report_path = Path(f"reports/gap_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        report_path.parent.mkdir(exist_ok=True)
        report_path.write_text(report.to_markdown())
        console.print(f"\n[dim]Report saved to: {report_path}[/dim]")
    
    # Final status
    console.print()
    if report.unfixed_gaps:
        unfixed_critical = [g for g in report.unfixed_gaps if g.severity == GapSeverity.CRITICAL]
        if unfixed_critical:
            console.print("[bold red]❌ Critical issues remain! Manual intervention required.[/bold red]")
            return 1
        else:
            console.print("[yellow]⚠️ Some non-critical gaps remain.[/yellow]")
            return 0
    else:
        console.print("[bold green]✅ All gaps resolved![/bold green]")
        return 0


def main():
    parser = argparse.ArgumentParser(description="Gap Analysis & Auto-Repair")
    parser.add_argument("--no-fix", action="store_true", help="Don't auto-fix issues")
    parser.add_argument("--report", action="store_true", help="Save markdown report")
    args = parser.parse_args()
    
    exit_code = asyncio.run(run_analysis(
        auto_fix=not args.no_fix,
        save_report=args.report,
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
