#!/usr/bin/env python3
"""
Demo script showing TFT ML Tool Call functionality.

This demonstrates how the ML model can be used as a tool call for
chat-based interactions and strategic recommendations.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.chat.ml_chat_interface import chat_with_tft_ml
from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation


def demo_tool_calls():
    """Demonstrate various tool call scenarios."""

    print("🎯 TFT ML Tool Call Demo")
    print("=" * 50)

    # Scenario 1: Natural language chat interface
    print("\n📝 **Scenario 1: Natural Language Query**")
    query = "I'm at 20 gold, 30 health, level 7, stage 4, in 6th place, what should I do?"
    print(f"Query: {query}")
    print("\nResponse:")
    response = chat_with_tft_ml(query)
    print(response)

    print("\n" + "=" * 50)

    # Scenario 2: Direct parameter tool call
    print("\n🎛️ **Scenario 2: Direct Parameter Call**")
    print("Parameters: placement=7, gold=10, health=15, level=8, late game")
    print("\nResponse:")
    response = get_tft_recommendation(
        current_placement=7,
        gold=10,
        health=15,
        level=8,
        round_number=25,
        stage=5,
        game_phase="late"
    )
    print(response)

    print("\n" + "=" * 50)

    # Scenario 3: Early game scenario
    print("\n🌅 **Scenario 3: Early Game Strong**")
    query = "Stage 2, 45 gold, 80 health, level 4, first place, should I level or save?"
    print(f"Query: {query}")
    print("\nResponse:")
    response = chat_with_tft_ml(query)
    print(response)

    print("\n" + "=" * 50)

    # Scenario 4: Mid game pivot
    print("\n🔄 **Scenario 4: Mid Game Pivot**")
    query = "Stage 3-5, my reroll comp isn't hitting, 35 gold, 55 health, should I pivot?"
    print(f"Query: {query}")
    print("\nResponse:")
    response = chat_with_tft_ml(query)
    print(response)


def demo_chat_interface():
    """Interactive chat demo."""
    print("\n💬 **Interactive Chat Demo**")
    print("Try asking about your TFT game state!")
    print("Examples:")
    print("• 'I'm at 25 gold, level 6, what comp should I go?'")
    print("• 'Stage 4, low health, need to stabilize'")
    print("• 'High roll start, when should I level?'")
    print("\nType 'quit' to exit")

    while True:
        try:
            user_input = input("\n> ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                continue

            response = chat_with_tft_ml(user_input)
            print(response)

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("Demo complete!")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="TFT ML Tool Call Demo")
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run interactive chat demo')

    args = parser.parse_args()

    if args.interactive:
        demo_chat_interface()
    else:
        demo_tool_calls()