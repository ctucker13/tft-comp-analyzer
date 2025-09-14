#!/usr/bin/env python3
"""
TFT Agentic Model Demo
Interactive CLI demonstrating the intelligent TFT agent with LangGraph workflow
"""

import asyncio
import sys
import os
from typing import List, Dict, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from src.tft_analyzer.agents.tft_agent import TFTAgent, create_tft_agent
    from config.settings import Settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


class TFTAgentDemo:
    """Interactive demonstration of the TFT agentic model."""

    def __init__(self):
        self.settings = Settings()
        self.agent: Optional[TFTAgent] = None
        self.conversation_history: List[Dict[str, str]] = []

    def print_banner(self):
        """Print welcome banner."""
        print("🤖 TFT Agentic Model Demo")
        print("=" * 50)
        print("Intelligent TFT agent with automatic tool selection")
        print("- Strategic decisions → ML analysis")
        print("- Meta questions → Tier list analysis")
        print("- General chat → Direct response")
        print("=" * 50)

    def print_examples(self):
        """Print example conversation types."""
        examples = {
            "🎯 Strategic Decisions (triggers ML analysis)": [
                "I'm at 30 gold, level 6, placement 5, what should I do?",
                "Should I roll or level up with 25 gold at stage 3-2?",
                "I have 15 health left, how should I play this out?",
                "Level 7 with 40 gold, what's my best move?"
            ],
            "📊 Meta Analysis (triggers tier list/composition tools)": [
                "What are the strongest compositions right now?",
                "What comps are meta in patch 15.3?",
                "Give me the current tier list",
                "What's the best reroll comp this patch?",
                "Is Star Guardian good right now?"
            ],
            "💬 General TFT Chat (direct response)": [
                "I love playing TFT, it's so much fun!",
                "How does the Power Up system work?",
                "What's your favorite Set 15 mechanic?",
                "TFT is getting more complex each set"
            ]
        }

        print("\n📝 Example Conversations:")
        print("-" * 40)
        for category, questions in examples.items():
            print(f"\n{category}:")
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")
        print()

    def initialize_agent(self):
        """Initialize the TFT agent with user preferences."""
        print("\n🔧 Agent Configuration")
        print("-" * 30)

        # Check available providers
        available_providers = []
        if self.settings.anthropic_api_key:
            available_providers.append("anthropic")
        if self.settings.openai_api_key:
            available_providers.append("openai")

        if not available_providers:
            print("❌ No API keys found! Please set ANTHROPIC_API_KEY or OPENAI_API_KEY")
            sys.exit(1)

        print(f"Available LLM providers: {', '.join(available_providers)}")

        # Auto-select provider
        if len(available_providers) == 1:
            provider = available_providers[0]
            print(f"Auto-selecting {provider}")
        else:
            provider_input = input(f"Choose provider ({'/'.join(available_providers)}): ").strip().lower()
            provider = provider_input if provider_input in available_providers else available_providers[0]
            print(f"Using {provider}")

        try:
            self.agent = create_tft_agent(provider=provider)
            print(f"✅ Agent initialized with {provider}")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize agent: {e}")
            return False

    def process_user_input(self, user_input: str) -> str:
        """Process user input through the agent."""
        if not self.agent:
            return "❌ Agent not initialized"

        try:
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input
            })

            print("🔄 Processing your message...")
            print("   • Classifying conversation intent")
            print("   • Determining required tools")
            print("   • Running analysis workflow")
            print()

            # Process through agent
            response = self.agent.process_message(user_input, self.conversation_history)

            # Add response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": response
            })

            return response

        except Exception as e:
            error_msg = f"❌ Error processing message: {str(e)}"
            print(error_msg)
            return error_msg

    def run_example_scenarios(self):
        """Run predefined example scenarios to demonstrate functionality."""
        print("\n🎬 Running Example Scenarios")
        print("=" * 40)

        scenarios = [
            {
                "category": "Strategic Decision",
                "message": "I'm at 30 gold, level 6, placement 5, what should I do?",
                "expected_tools": ["ML analysis", "game state extraction"]
            },
            {
                "category": "Meta Analysis",
                "message": "What are the strongest compositions right now?",
                "expected_tools": ["tier list", "meta analysis"]
            },
            {
                "category": "General Chat",
                "message": "I love TFT Set 15, the Power Up system is really cool!",
                "expected_tools": ["direct response"]
            }
        ]

        for i, scenario in enumerate(scenarios, 1):
            print(f"\n--- Scenario {i}: {scenario['category']} ---")
            print(f"User: {scenario['message']}")
            print(f"Expected tools: {', '.join(scenario['expected_tools'])}")
            print()

            response = self.process_user_input(scenario['message'])
            print(f"Agent: {response}")
            print("\n" + "-" * 60)

            # Brief pause between scenarios
            input("\nPress Enter to continue to next scenario...")

    def run_interactive_mode(self):
        """Run interactive chat mode."""
        print("\n💬 Interactive Chat Mode")
        print("-" * 30)
        print("Type your TFT questions and see the agent in action!")
        print("Commands: 'help' for examples, 'quit' to exit\n")

        while True:
            try:
                user_input = input("You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Thanks for trying the TFT agent!")
                    break
                elif user_input.lower() in ['help', 'examples']:
                    self.print_examples()
                    continue
                elif not user_input:
                    continue

                print()
                response = self.process_user_input(user_input)
                print(f"🤖 Agent: {response}\n")

            except KeyboardInterrupt:
                print("\n👋 Thanks for trying the TFT agent!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def run(self):
        """Main demo runner."""
        self.print_banner()

        if not self.initialize_agent():
            return

        print("\n🚀 Demo Options:")
        print("1. Run example scenarios")
        print("2. Interactive chat mode")
        print("3. Show examples and exit")

        choice = input("\nChoose option (1-3): ").strip()

        if choice == "1":
            self.run_example_scenarios()
        elif choice == "2":
            self.run_interactive_mode()
        elif choice == "3":
            self.print_examples()
        else:
            print("Running interactive mode by default...")
            self.run_interactive_mode()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--examples", "-e"]:
            demo = TFTAgentDemo()
            demo.print_examples()
            return
        elif sys.argv[1] in ["--help", "-h"]:
            print("TFT Agentic Model Demo")
            print("Usage: python tft_agent_demo.py [options]")
            print("Options:")
            print("  --examples, -e    Show example conversations")
            print("  --help, -h        Show this help message")
            print("  No arguments      Run interactive demo")
            return

    # Run the demo
    demo = TFTAgentDemo()
    demo.run()


if __name__ == "__main__":
    main()