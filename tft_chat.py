#!/usr/bin/env python3
"""
TFT Chat Interface

Simple, streamlined chat interface for TFT strategic advice.
Users interact naturally and the agent uses tools to respond appropriately.
"""

import sys
import argparse
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.chat.ml_chat_interface import chat_with_tft_ml


def print_welcome():
    """Print welcome message and instructions."""
    print("""
╔══════════════════════════════════════════════╗
║              TFT Strategic Advisor           ║
║            Set 15: K.O. Coliseum            ║
╚══════════════════════════════════════════════╝

🤖 Ask me anything about TFT strategy and I'll help you!

💡 Example questions:
• "I'm at 30 gold, level 6, placement 5, what should I do?"
• "What's the current meta tier list?"
• "What comps are trending right now?"
• "Stage 3, low health, need to stabilize"
• "What's the strongest composition to play?"

Type 'quit' to exit, or just start asking questions!
""")


def chat_loop():
    """Main interactive chat loop."""
    print_welcome()

    while True:
        try:
            # Get user input
            user_input = input("\n💬 You: ").strip()

            # Handle exit commands
            if user_input.lower() in ['quit', 'exit', 'q', 'bye', 'goodbye']:
                print("\n👋 Good luck in your TFT games! Goodbye!")
                break

            # Handle empty input
            if not user_input:
                print("🤔 Please ask me a question about TFT strategy!")
                continue

            # Handle special commands
            if user_input.lower() in ['help', '?']:
                print_help()
                continue

            # Process the query
            print("\n🤖 TFT Advisor: Analyzing your question...")
            response = chat_with_tft_ml(user_input)
            print(f"\n{response}")

        except KeyboardInterrupt:
            print("\n\n👋 Good luck in your TFT games! Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Sorry, I encountered an error: {e}")
            print("Please try asking your question again!")


def print_help():
    """Print help information."""
    print("""
🆘 **Help**

I can help you with two types of TFT questions:

**Strategic Decisions:**
• Describe your current game state and I'll give you strategic advice
• Example: "I'm at 25 gold, level 7, stage 4, in 6th place"

**Meta Analysis:**
• Ask about the current meta, tier lists, or trending compositions
• Example: "What are the best comps right now?"

**Tips:**
• Be specific about your game state (gold, health, level, placement)
• Mention what stage/round you're in
• Ask about specific situations you're facing

**Commands:**
• Type 'help' or '?' for this help message
• Type 'quit', 'exit', or 'q' to leave
""")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TFT Strategic Chat Advisor"
    )

    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Ask a single question (non-interactive mode)'
    )

    parser.add_argument(
        '--examples',
        action='store_true',
        help='Show example questions you can ask'
    )

    args = parser.parse_args()

    if args.examples:
        show_examples()
    elif args.query:
        # Single query mode
        print("🤖 TFT Advisor: Analyzing your question...")
        response = chat_with_tft_ml(args.query)
        print(f"\n{response}")
    else:
        # Interactive chat mode
        chat_loop()


def show_examples():
    """Show example questions users can ask."""
    print("""
💡 **Example Questions You Can Ask:**

**Strategic Decisions:**
• "I'm at 30 gold, 45 health, level 6, placement 5, what should I do?"
• "Stage 3, 25 gold, need to pivot from my current comp"
• "Late game, 15 health, level 8, should I reroll or go fast 8?"
• "Early game with 50 gold, when should I level?"
• "I'm in 7th place with low health, help me stabilize"

**Meta Analysis:**
• "What's the current meta tier list?"
• "What comps are trending right now?"
• "What are the best comps to play?"
• "Show me the strongest compositions"
• "What's the current patch meta?"
• "What comps counter reroll?"

**Specific Situations:**
• "High roll start, when should I all-in?"
• "Mid game transition point, 35 gold available"
• "Should I play reroll or fast 8 comp?"
• "What's the meta like right now?"
• "I keep getting 8th place, what am I doing wrong?"

Just start with: python tft_chat.py
""")


if __name__ == "__main__":
    main()