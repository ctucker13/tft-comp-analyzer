#!/usr/bin/env python3
"""
Demo script to showcase the modern Typer CLI features
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.typer_cli import console
from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
from src.tft_analyzer.data.riot_official_units_with_traits import riot_official_db_with_traits as riot_db
from rich.panel import Panel
from rich.table import Table
from rich import box
import time

def demo_modern_cli():
    """Demonstrate the modern Typer CLI features."""
    console.clear()

    # Banner and introduction
    console.print(Panel(
        "[bold cyan]🎮 TFT Composition Analyzer Demo[/bold cyan]\n"
        "[green]Showcasing the modern Typer + Rich CLI interface[/green]",
        title="CLI Demo",
        border_style="cyan"
    ))

    time.sleep(2)

    console.print("\n[yellow]1. System Data Status:[/yellow]")
    try:
        data_manager = TFTMetaDataManager()
        meta_info = data_manager.get_meta_info()
        compositions_df = data_manager.get_compositions_df()

        status_table = Table(title="System Status", box=box.ROUNDED)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Count", style="yellow")

        status_table.add_row("Champions", "✅ Loaded", str(len(riot_db.unit_names)))
        status_table.add_row("Traits", "✅ Loaded", str(len(riot_db.trait_names)))
        status_table.add_row("Compositions", "✅ Enhanced", str(len(compositions_df)) if not compositions_df.is_empty() else "0")
        status_table.add_row("Meta Data", "✅ Current", meta_info.get('last_updated', 'Unknown')[:10])

        console.print(status_table)
    except Exception as e:
        console.print(f"[red]❌ Status error: {e}[/red]")

    time.sleep(2)

    console.print("\n[yellow]2. Champion Database Sample:[/yellow]")
    # Show cost distribution
    try:
        cost_distribution = riot_db.get_cost_distribution()
        cost_table = Table(title="Champion Cost Distribution", box=box.ROUNDED)
        cost_table.add_column("Cost", justify="center", style="cyan")
        cost_table.add_column("Count", justify="center", style="green")
        cost_table.add_column("Examples", style="yellow")

        for cost in sorted(cost_distribution.keys()):
            units = riot_db.get_units_by_cost(cost)[:3]  # First 3 examples
            examples = ", ".join([u.name for u in units])
            cost_table.add_row(f"{cost}⭐", str(cost_distribution[cost]), examples)

        console.print(cost_table)
    except Exception as e:
        console.print(f"[red]❌ Database error: {e}[/red]")

    time.sleep(2)

    console.print("\n[yellow]3. Meta Compositions Preview:[/yellow]")
    try:
        compositions_df = data_manager.get_compositions_df()

        if not compositions_df.is_empty():
            comp_table = Table(title="Top Meta Compositions", box=box.ROUNDED)
            comp_table.add_column("Composition", style="cyan")
            comp_table.add_column("Tier", style="gold1")
            comp_table.add_column("Win Rate", style="green")

            for row in compositions_df.head(3).iter_rows(named=True):
                comp_table.add_row(
                    row["name"],
                    f"{row['tier']} Tier",
                    f"{row['win_rate']:.1%}"
                )

            console.print(comp_table)
        else:
            console.print("[yellow]⚠️  No composition data available[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Composition error: {e}[/red]")

    time.sleep(2)

    console.print("\n[yellow]4. Available CLI Commands:[/yellow]")
    commands_table = Table(title="Modern CLI Commands", box=box.ROUNDED)
    commands_table.add_column("Category", style="cyan")
    commands_table.add_column("Command", style="yellow")
    commands_table.add_column("Description", style="white")

    commands_table.add_row("Chat", "./tft chat ask \"question\"", "AI strategic advice")
    commands_table.add_row("Meta", "./tft meta tiers", "Current tier lists")
    commands_table.add_row("Database", "./tft database champions --all", "Champion database")
    commands_table.add_row("ML", "./tft ml recommend --gold 30", "ML recommendations")

    console.print(commands_table)

    console.print(Panel(
        "[bold green]✨ Demo Complete![/bold green]\n"
        "[white]The modern Typer CLI provides professional command-line access[/white]\n"
        "[dim]Use './tft --help' to explore all features[/dim]",
        title="🎯 CLI Ready",
        border_style="green"
    ))


if __name__ == "__main__":
    print("🎮 Starting TFT CLI Demo...")
    demo_modern_cli()