#!/usr/bin/env python3
"""
TFT Analyzer CLI Interface

Provides a command-line interface for accessing both the meta analysis workflow
and the new ML recommendation tool.
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.chat.ml_chat_interface import chat_with_tft_ml
from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation
from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends


def print_banner():
    """Print application banner."""
    print("""
╔══════════════════════════════════════════════╗
║            TFT Comp Analyzer                 ║
║         Set 15: K.O. Coliseum               ║
╚══════════════════════════════════════════════╝
    """)


def print_menu():
    """Print main menu options."""
    print("\nChoose an option:")
    print("1. 🤖 ML Strategy Recommendation (Chat)")
    print("2. 📊 ML Strategy Recommendation (Parameters)")
    print("3. 🏆 Meta Tier List & Analysis")
    print("4. 📈 Meta Trends & Rising Comps")
    print("5. 📋 Full Meta Analysis (Original Workflow)")
    print("6. ❓ Help & Examples")
    print("7. 🚪 Exit")


def print_help():
    """Print help information and examples."""
    print("""
🤖 **ML Strategy Recommendation**

The ML tool provides AI-powered recommendations based on your current game state.

**Chat Mode Examples:**
• "I'm at 30 gold, 45 health, level 6, placement 5, what should I do?"
• "Stage 3, 25 gold, need to pivot from my current comp"
• "Late game, 15 health, level 8, should I reroll or go fast 8?"
• "Early game with 50 gold, when should I level?"
• "I'm in 7th place with low health, help me stabilize"

**Parameter Mode:**
Manually specify exact values for:
- Current placement (1-8)
- Gold amount
- Health points
- Player level
- Round number
- Stage
- Active traits
- Units on board

**Meta Analysis:**
The original workflow that analyzes current challenger gameplay to identify
meta trends and optimal compositions.
    """)


async def ml_chat_mode():
    """Interactive ML chat interface."""
    print("\n🤖 **TFT ML Chat Interface**")
    print("Describe your game state in natural language and get strategic advice!")
    print("Type 'quit' to return to main menu.\n")

    while True:
        try:
            query = input("> ").strip()

            if query.lower() in ['quit', 'exit', 'q', 'back']:
                break

            if not query:
                print("Please describe your game state or ask a question.")
                continue

            print("\nAnalyzing... 🤔")
            response = chat_with_tft_ml(query)
            print(response)
            print("\n" + "-" * 50)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("Returning to main menu...")


def ml_parameter_mode():
    """Manual parameter input for ML recommendations."""
    print("\n📊 **TFT ML Parameter Mode**")
    print("Enter your game state parameters (press Enter for default values)")

    try:
        # Get parameters from user
        placement = input("Current placement (1-8) [4]: ").strip()
        placement = int(placement) if placement else 4

        gold = input("Gold amount [30]: ").strip()
        gold = int(gold) if gold else 30

        health = input("Health points [50]: ").strip()
        health = int(health) if health else 50

        level = input("Player level [6]: ").strip()
        level = int(level) if level else 6

        round_num = input("Round number [15]: ").strip()
        round_num = int(round_num) if round_num else 15

        stage = input("Stage [3]: ").strip()
        stage = int(stage) if stage else 3

        units = input("Units on board [6]: ").strip()
        units = int(units) if units else 6

        phase = input("Game phase (early/mid/late) [mid]: ").strip()
        phase = phase if phase else "mid"

        print("\nAnalyzing... 🤔")

        # Get recommendation
        response = get_tft_recommendation(
            current_placement=placement,
            gold=gold,
            health=health,
            level=level,
            round_number=round_num,
            stage=stage,
            units_count=units,
            game_phase=phase
        )

        print(response)

    except ValueError:
        print("❌ Invalid input. Please enter numeric values where required.")
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
    except Exception as e:
        print(f"❌ Error: {e}")

    input("\nPress Enter to continue...")


async def run_meta_analysis():
    """Run the original meta analysis workflow."""
    print("\n📈 **Running Full Meta Analysis**")
    print("This may take a few minutes...")

    try:
        # Import and run the main workflow
        from src.tft_analyzer.main import main
        await main()
    except Exception as e:
        print(f"❌ Error running meta analysis: {e}")

    input("\nPress Enter to continue...")


async def show_meta_tier_list():
    """Show current meta tier list."""
    print("\n🏆 **Getting Current Meta Tier List**")
    print("Analyzing recent match data...\n")

    try:
        # Use the chat interface which handles the async properly
        result = chat_with_tft_ml("What is the current meta tier list?")
        print(result)
    except Exception as e:
        print(f"❌ Error getting tier list: {e}")

    input("\nPress Enter to continue...")


async def show_meta_trends():
    """Show meta trends and rising compositions."""
    print("\n📈 **Getting Meta Trends Analysis**")
    print("Analyzing composition performance changes...\n")

    try:
        # Use the chat interface which handles the async properly
        result = chat_with_tft_ml("What comps are trending right now?")
        print(result)
    except Exception as e:
        print(f"❌ Error getting trends: {e}")

    input("\nPress Enter to continue...")


async def main_menu():
    """Main CLI menu loop."""
    print_banner()

    while True:
        print_menu()

        try:
            choice = input("\nEnter choice (1-7): ").strip()

            if choice == '1':
                await ml_chat_mode()
            elif choice == '2':
                ml_parameter_mode()
            elif choice == '3':
                await show_meta_tier_list()
            elif choice == '4':
                await show_meta_trends()
            elif choice == '5':
                await run_meta_analysis()
            elif choice == '6':
                print_help()
                input("\nPress Enter to continue...")
            elif choice == '7':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="TFT Set 15 Composition Analyzer with ML Recommendations"
    )

    parser.add_argument(
        '--chat',
        action='store_true',
        help='Start directly in ML chat mode'
    )

    parser.add_argument(
        '--query',
        type=str,
        help='Single ML query (non-interactive)'
    )

    args = parser.parse_args()

    if args.query:
        # Single query mode
        print("Analyzing... 🤔")
        response = chat_with_tft_ml(args.query)
        print(response)
    elif args.chat:
        # Direct to chat mode
        print_banner()
        asyncio.run(ml_chat_mode())
    else:
        # Interactive menu
        asyncio.run(main_menu())


if __name__ == "__main__":
    main()