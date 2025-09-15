#!/usr/bin/env python3
"""
TFT Composition Analyzer - Modern Typer CLI
Professional CLI interface combining Typer with Rich visuals for AI-powered TFT strategic analysis.
"""

import typer
from typing import Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
import asyncio
from datetime import datetime
from pathlib import Path
import subprocess

# Create Rich console
console = Console()

# Import project components
try:
    from .data.meta_data_manager import TFTMetaDataManager
    from .data.riot_official_units_with_traits import riot_official_db_with_traits as riot_db
    from .agents.tft_agent import create_tft_agent
    from .tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from .tools.ml_recommendation_tool import get_tft_recommendation
    from .chat.ml_chat_interface import chat_with_tft_ml
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
    from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
    from src.tft_analyzer.data.riot_official_units_with_traits import riot_official_db_with_traits as riot_db
    from src.tft_analyzer.agents.tft_agent import create_tft_agent
    from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation
    from src.tft_analyzer.chat.ml_chat_interface import chat_with_tft_ml

# Create the main Typer app
app = typer.Typer(
    name="tft-analyzer",
    help="🎮 TFT Composition Analyzer - AI-powered strategic analysis for Set 15: K.O. Coliseum",
    add_completion=False,
    rich_markup_mode="rich",
)

# Subcommands
chat_app = typer.Typer(help="💬 Interactive AI chat for strategic advice")
meta_app = typer.Typer(help="📊 Meta analysis and tier lists")
database_app = typer.Typer(help="🎯 Champion and trait database")
ml_app = typer.Typer(help="🤖 Machine learning tools and training")

app.add_typer(chat_app, name="chat")
app.add_typer(meta_app, name="meta")
app.add_typer(database_app, name="database")
app.add_typer(ml_app, name="ml")


@app.callback()
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version information"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug mode"),
):
    """
    🎮 TFT Composition Analyzer - Professional CLI with AI-powered strategic analysis.

    Features:
    • Interactive AI chat for strategic decisions
    • Complete meta analysis and tier lists
    • Comprehensive champion and trait database
    • Real-time ML model training and updates
    • Beautiful Rich-based visual output
    """
    if version:
        console.print(Panel(
            "[bold cyan]TFT Composition Analyzer[/bold cyan]\n"
            "[green]Version: 0.3.0[/green]\n"
            "[yellow]Set 15: K.O. Coliseum[/yellow]\n"
            "[blue]Powered by: Typer + Rich + Claude AI[/blue]",
            title="📊 Version Info",
            border_style="cyan"
        ))
        raise typer.Exit()

    if debug:
        console.print("[yellow]🐛 Debug mode enabled[/yellow]")


# ===== CHAT COMMANDS =====

@chat_app.command("interactive")
def chat_interactive(
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider (anthropic/openai)"),
    examples: bool = typer.Option(False, "--examples", "-e", help="Show example questions"),
):
    """Start interactive AI chat session for strategic advice."""
    if examples:
        console.print(Panel(
            "[bold cyan]💡 Example Strategic Questions:[/bold cyan]\n\n"
            "[green]• \"I'm at 30 gold, level 6, what should I do?\"[/green]\n"
            "[blue]• \"Should I roll for Lee Sin or save for level 8?\"[/blue]\n"
            "[yellow]• \"What's the best Mighty Mech composition?\"[/yellow]\n"
            "[purple]• \"I have Star Guardian start, how do I transition?\"[/purple]\n"
            "[red]• \"When should I pivot from my current board?\"[/red]",
            title="🤖 AI Strategic Chat",
            border_style="cyan"
        ))
        return

    console.print(Panel(
        "[bold green]🤖 Interactive TFT Strategic Chat Started[/bold green]\n"
        "Ask strategic questions and get AI-powered recommendations!\n"
        "[dim]Type 'quit' or 'exit' to leave chat mode[/dim]",
        title="💬 Chat Mode",
        border_style="green"
    ))

    # Start interactive chat
    try:
        chat_with_tft_ml()
    except Exception as e:
        console.print(f"[red]❌ Chat error: {e}[/red]")


@chat_app.command("ask")
def chat_ask(
    question: str = typer.Argument(..., help="Strategic question to ask"),
    provider: str = typer.Option("anthropic", "--provider", "-p", help="LLM provider"),
):
    """Ask a single strategic question."""
    console.print(Panel(
        f"[bold cyan]Question:[/bold cyan] {question}",
        title="🤖 AI Strategic Analysis",
        border_style="cyan"
    ))

    try:
        agent = create_tft_agent(provider)
        response = agent.process_message(question, [])
        console.print(Panel(response, title="🎯 Strategic Recommendation", border_style="green"))
    except Exception as e:
        console.print(f"[red]❌ Analysis failed: {e}[/red]")


# ===== META COMMANDS =====

@meta_app.command("tiers")
def meta_tiers(
    format_type: str = typer.Option("table", "--format", "-f", help="Output format (table/json)"),
    save: bool = typer.Option(False, "--save", "-s", help="Save to file"),
):
    """Display current meta tier lists."""
    console.print(Panel(
        "[bold gold1]🏆 Current Meta Tier Lists[/bold gold1]\n"
        "Based on latest challenger gameplay analysis",
        title="Meta Analysis",
        border_style="gold1"
    ))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading meta tier lists...", total=None)
            tier_data = get_meta_tier_list()

        console.print(tier_data)

        if save:
            with open(f"tier_list_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 'w') as f:
                f.write(tier_data)
            console.print("[green]✅ Saved to file[/green]")

    except Exception as e:
        console.print(f"[red]❌ Failed to load tier list: {e}[/red]")


@meta_app.command("trends")
def meta_trends(
    days: int = typer.Option(7, "--days", "-d", help="Number of days to analyze"),
    trait: Optional[str] = typer.Option(None, "--trait", "-t", help="Focus on specific trait"),
):
    """Analyze meta trends over time."""
    console.print(Panel(
        f"[bold blue]📈 Meta Trends Analysis[/bold blue]\n"
        f"Analyzing trends over the last {days} days" + (f" for {trait} trait" if trait else ""),
        title="Trend Analysis",
        border_style="blue"
    ))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing meta trends...", total=None)
            trends_data = get_meta_trends()

        console.print(trends_data)

    except Exception as e:
        console.print(f"[red]❌ Failed to analyze trends: {e}[/red]")


@meta_app.command("comps")
def meta_compositions(
    tier: Optional[str] = typer.Option(None, "--tier", "-t", help="Filter by tier (S/A/B/C)"),
    trait: Optional[str] = typer.Option(None, "--trait", help="Filter by trait"),
):
    """Show top meta compositions."""
    console.print("[bold purple]🎯 Top Meta Compositions[/bold purple]")

    try:
        data_manager = TFTMetaDataManager()
        compositions_df = data_manager.get_compositions_df()

        if not compositions_df.is_empty():
            # Create table
            table = Table(title="Meta Compositions", box=box.ROUNDED)
            table.add_column("Composition", style="cyan")
            table.add_column("Tier", style="gold1")
            table.add_column("Win Rate", style="green")
            table.add_column("Avg Placement", style="blue")
            table.add_column("Primary Trait", style="yellow")

            # Filter data
            filtered_df = compositions_df
            if tier:
                filtered_df = filtered_df.filter(filtered_df["tier"] == tier.upper())
            if trait:
                filtered_df = filtered_df.filter(filtered_df["primary_trait"].str.contains(trait))

            # Display top 10 compositions
            for row in filtered_df.head(10).iter_rows(named=True):
                table.add_row(
                    row["name"],
                    f"{row['tier']} Tier",
                    f"{row['win_rate']:.1%}",
                    f"{row['avg_placement']:.1f}",
                    row["primary_trait"]
                )

            console.print(table)
        else:
            console.print("[yellow]⚠️  No composition data available[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Failed to load compositions: {e}[/red]")


# ===== DATABASE COMMANDS =====

@database_app.command("champions")
def database_champions(
    name: Optional[str] = typer.Option(None, "--name", "-n", help="Specific champion name"),
    cost: Optional[int] = typer.Option(None, "--cost", "-c", help="Filter by cost"),
    trait: Optional[str] = typer.Option(None, "--trait", "-t", help="Filter by trait"),
    comprehensive: bool = typer.Option(False, "--all", "-a", help="Show comprehensive database"),
):
    """Browse champion database with traits and costs."""
    try:
        if name:
            # Show specific champion details
            info = riot_db.get_unit_info(name)
            if 'error' not in info:
                console.print(Panel(
                    f"[bold cyan]Champion:[/bold cyan] {info['name']}\n"
                    f"[yellow]Cost:[/yellow] {info['cost']}⭐\n"
                    f"[green]Traits:[/green] {', '.join(info['traits'])}\n"
                    f"[blue]Type:[/blue] {info.get('type', 'Champion')}",
                    title=f"🎯 {info['name']}",
                    border_style="cyan"
                ))
            else:
                console.print(f"[red]❌ {info['error']}[/red]")
            return

        # Create comprehensive database view
        if comprehensive:
            console.print(Panel(
                "[bold cyan]📊 Complete Set 15 Champion Database[/bold cyan]\n"
                f"Total Champions: {len(riot_db.unit_names)} | Total Traits: {len(riot_db.trait_names)}",
                title="Champion Database",
                border_style="cyan"
            ))

            # Group champions by cost
            cost_distribution = riot_db.get_cost_distribution()

            for cost in sorted(cost_distribution.keys()):
                units = riot_db.get_units_by_cost(cost)

                table = Table(title=f"💰 Cost {cost} Champions ({len(units)} units)", box=box.ROUNDED)
                table.add_column("Champion", style="cyan")
                table.add_column("Traits", style="yellow", width=40)

                for unit in units:
                    info = riot_db.get_unit_info(unit.name)
                    traits_str = ", ".join(info['traits'])
                    table.add_row(unit.name, traits_str)

                console.print(table)
                console.print()  # Add spacing
            return

        # Filter champions
        champions = []
        if cost:
            champions = riot_db.get_units_by_cost(cost)
        elif trait:
            champions = riot_db.get_units_by_trait(trait)
        else:
            champions = [riot_db.get_unit_by_name(name) for name in riot_db.unit_names[:20]]

        # Display results
        if champions:
            table = Table(title="Champions", box=box.ROUNDED)
            table.add_column("Champion", style="cyan")
            table.add_column("Cost", style="green")
            table.add_column("Traits", style="yellow", width=50)

            for unit in champions[:20]:  # Limit to 20
                info = riot_db.get_unit_info(unit.name)
                table.add_row(
                    unit.name,
                    f"{unit.cost}⭐",
                    ", ".join(info['traits'])
                )

            console.print(table)
            if len(champions) > 20:
                console.print(f"[dim]... and {len(champions) - 20} more champions[/dim]")
        else:
            console.print("[yellow]⚠️  No champions found matching criteria[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Database error: {e}[/red]")


@database_app.command("traits")
def database_traits(
    trait: Optional[str] = typer.Option(None, "--name", "-n", help="Specific trait name"),
    champions: bool = typer.Option(False, "--champions", "-c", help="Show champions for each trait"),
):
    """Browse trait information and synergies."""
    try:
        trait_distribution = riot_db.get_trait_distribution()

        if trait:
            # Show specific trait details
            champions_with_trait = riot_db.get_units_by_trait(trait)
            if champions_with_trait:
                table = Table(title=f"🎯 Champions with {trait} trait", box=box.ROUNDED)
                table.add_column("Champion", style="cyan")
                table.add_column("Cost", style="green")
                table.add_column("All Traits", style="yellow", width=50)

                for unit in champions_with_trait:
                    info = riot_db.get_unit_info(unit.name)
                    table.add_row(unit.name, f"{unit.cost}⭐", ", ".join(info['traits']))

                console.print(table)
            else:
                console.print(f"[red]❌ Trait '{trait}' not found[/red]")
            return

        # Show all traits
        console.print(Panel(
            f"[bold yellow]🎯 Set 15 Trait Overview[/bold yellow]\n"
            f"Total Traits: {len(trait_distribution)}",
            title="Trait Database",
            border_style="yellow"
        ))

        table = Table(title="All Set 15 Traits", box=box.ROUNDED)
        table.add_column("Trait", style="cyan")
        table.add_column("Champions", style="green", justify="center")
        if champions:
            table.add_column("Champion Names", style="yellow", width=60)

        sorted_traits = sorted(trait_distribution.items(), key=lambda x: x[1], reverse=True)
        for trait_name, count in sorted_traits:
            row = [trait_name, str(count)]
            if champions:
                trait_champions = [u.name for u in riot_db.get_units_by_trait(trait_name)]
                row.append(", ".join(trait_champions[:5]) + ("..." if len(trait_champions) > 5 else ""))
            table.add_row(*row)

        console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Trait database error: {e}[/red]")


@database_app.command("search")
def database_search(
    query: str = typer.Argument(..., help="Search query"),
    type_filter: str = typer.Option("all", "--type", "-t", help="Search type (champions/traits/all)"),
):
    """Search champions and traits by name."""
    console.print(f"[cyan]🔍 Searching for: '{query}'[/cyan]")

    try:
        results = []

        if type_filter in ["all", "champions"]:
            # Search champions
            matching_champions = [name for name in riot_db.unit_names if query.lower() in name.lower()]
            for champ in matching_champions:
                results.append(("Champion", champ, "green"))

        if type_filter in ["all", "traits"]:
            # Search traits
            trait_distribution = riot_db.get_trait_distribution()
            matching_traits = [trait for trait in trait_distribution.keys() if query.lower() in trait.lower()]
            for trait in matching_traits:
                results.append(("Trait", trait, "blue"))

        if results:
            table = Table(title=f"Search Results for '{query}'", box=box.ROUNDED)
            table.add_column("Type", style="cyan")
            table.add_column("Name", style="yellow")
            table.add_column("Details", style="white")

            for result_type, name, color in results:
                details = ""
                if result_type == "Champion":
                    info = riot_db.get_unit_info(name)
                    details = f"Cost {info['cost']} • {', '.join(info['traits'][:2])}"
                else:  # Trait
                    trait_count = riot_db.get_trait_distribution()[name]
                    details = f"{trait_count} champions"

                table.add_row(result_type, name, details)

            console.print(table)
        else:
            console.print(f"[red]❌ No results found for '{query}'[/red]")

    except Exception as e:
        console.print(f"[red]❌ Search error: {e}[/red]")


# ===== ML COMMANDS =====

@ml_app.command("recommend")
def ml_recommend(
    gold: int = typer.Option(30, "--gold", "-g", help="Current gold amount"),
    level: int = typer.Option(6, "--level", "-l", help="Current level"),
    stage: int = typer.Option(3, "--stage", "-s", help="Current stage"),
    health: int = typer.Option(70, "--health", help="Current health"),
):
    """Get ML-powered strategic recommendations."""
    params = {
        'gold': gold,
        'level': level,
        'stage': stage,
        'health': health,
        'placement': 4,  # Default placement
        'round_number': stage * 7,  # Approximate
        'units_count': level,  # Approximate
        'game_phase': 'early' if stage <= 3 else 'mid' if stage <= 5 else 'late'
    }

    console.print(Panel(
        f"[bold cyan]🤖 ML Strategic Analysis[/bold cyan]\n"
        f"Gold: {gold} | Level: {level} | Stage: {stage} | Health: {health}",
        title="Game State Analysis",
        border_style="cyan"
    ))

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing strategic options...", total=None)
            recommendation = get_tft_recommendation(params)

        console.print(Panel(
            recommendation,
            title="🎯 Strategic Recommendation",
            border_style="green"
        ))

    except Exception as e:
        console.print(f"[red]❌ ML analysis failed: {e}[/red]")


@ml_app.command("train")
def ml_train(
    quick: bool = typer.Option(False, "--quick", "-q", help="Quick retrain with recent data"),
    matches: int = typer.Option(150, "--matches", "-m", help="Number of matches to analyze"),
    rank: str = typer.Option("CHALLENGER", "--rank", "-r", help="Rank filter (CHALLENGER/GRANDMASTER/MASTER)"),
):
    """Train ML models with latest data."""
    console.print("[bold yellow]🧠 ML Model Training[/bold yellow]")

    if quick:
        console.print("[green]⚡ Starting quick retrain...[/green]")
        try:
            result = subprocess.run(
                ["uv", "run", "python", "scripts/quick_retrain.py"],
                capture_output=True, text=True, cwd=Path(__file__).parent.parent.parent
            )
            if result.returncode == 0:
                console.print("[green]✅ Quick retrain completed successfully[/green]")
                console.print(result.stdout)
            else:
                console.print(f"[red]❌ Training failed: {result.stderr}[/red]")
        except Exception as e:
            console.print(f"[red]❌ Training error: {e}[/red]")
    else:
        console.print(f"[blue]🔄 Full training with {matches} matches ({rank} rank)[/blue]")
        console.print("[yellow]⚠️  Full training not yet implemented via CLI[/yellow]")


# ===== UTILITY COMMANDS =====

@app.command("status")
def status():
    """Show system status and loaded data information."""
    console.print(Panel(
        "[bold cyan]🎮 TFT Composition Analyzer[/bold cyan]\n"
        "[green]Status: Operational ✅[/green]\n"
        "[yellow]Set: 15 (K.O. Coliseum)[/yellow]\n"
        "[blue]Version: 0.3.0[/blue]",
        title="🚀 System Status",
        border_style="cyan"
    ))

    try:
        # Data status
        data_manager = TFTMetaDataManager()
        meta_info = data_manager.get_meta_info()
        compositions_df = data_manager.get_compositions_df()

        status_table = Table(title="Data Status", box=box.ROUNDED)
        status_table.add_column("Component", style="cyan")
        status_table.add_column("Status", style="green")
        status_table.add_column("Count", style="yellow")

        status_table.add_row("Champions", "✅ Loaded", str(len(riot_db.unit_names)))
        status_table.add_row("Traits", "✅ Loaded", str(len(riot_db.get_trait_distribution())))
        status_table.add_row("Compositions", "✅ Enhanced", str(len(compositions_df)) if not compositions_df.is_empty() else "0")
        status_table.add_row("Meta Data", "✅ Current", meta_info.get('last_updated', 'Unknown')[:10])

        console.print(status_table)

    except Exception as e:
        console.print(f"[red]❌ Status check failed: {e}[/red]")


@app.command("examples")
def show_examples():
    """Show usage examples for all commands."""
    examples_panel = Panel(
        "[bold cyan]💡 TFT Analyzer CLI Examples:[/bold cyan]\n\n"
        "[green]# Chat Commands[/green]\n"
        "./tft chat ask \"I'm at 30 gold, what should I do?\"\n"
        "./tft chat interactive --examples\n\n"
        "[blue]# Meta Analysis[/blue]\n"
        "./tft meta tiers --format table\n"
        "./tft meta trends --days 7 --trait \"Mighty Mech\"\n"
        "./tft meta comps --tier S\n\n"
        "[yellow]# Database Queries[/yellow]\n"
        "./tft database champions --name \"Lee Sin\"\n"
        "./tft database traits --name \"Star Guardian\" --champions\n"
        "./tft database search \"Mighty\"\n"
        "./tft database champions --all\n\n"
        "[purple]# ML Recommendations[/purple]\n"
        "./tft ml recommend --gold 45 --level 7 --stage 4\n"
        "./tft ml train --quick\n\n"
        "[red]# System[/red]\n"
        "./tft status\n"
        "./tft --version",
        title="🎮 Usage Examples",
        border_style="gold1",
        padding=(1, 2)
    )
    console.print(examples_panel)


def run_cli():
    """Entry point for the Typer CLI."""
    app()


if __name__ == "__main__":
    run_cli()