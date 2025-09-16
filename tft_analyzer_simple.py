"""
TFT Composition Analyzer - Simple Reflex App
"""

import reflex as rx
from typing import List, Dict
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from config.settings import Settings
    from src.tft_analyzer.agents.tft_agent import create_tft_agent
except ImportError as e:
    print(f"Import warning: {e}")


class ChatState(rx.State):
    """Simple chat state"""

    messages: List[Dict[str, str]] = [
        {"role": "assistant", "content": "Hello! I'm your TFT strategic advisor. Ask me about team compositions, meta trends, or strategic decisions!"}
    ]
    current_message: str = ""
    is_loading: bool = False
    provider: str = "anthropic"

    def send_message(self):
        """Send a message"""
        if not self.current_message.strip():
            return

        # Add user message
        self.messages.append({
            "role": "user",
            "content": self.current_message
        })

        user_msg = self.current_message
        self.current_message = ""
        self.is_loading = True

        # Simple fallback response for now
        try:
            # Try to use the TFT agent
            agent = create_tft_agent(provider=self.provider)
            response = agent.process_message(user_msg)

            self.messages.append({
                "role": "assistant",
                "content": response
            })
        except Exception as e:
            # Fallback response
            fallback_response = self.get_fallback_response(user_msg)
            self.messages.append({
                "role": "assistant",
                "content": fallback_response
            })

        self.is_loading = False

    def get_fallback_response(self, message: str) -> str:
        """Provide fallback TFT advice when agent fails"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["comp", "composition", "team", "build"]):
            return """Here are some strong Set 15 compositions:

**S-Tier:**
• **Sniper Reroll** - Gnar carry with Luchador/Sniper synergy
• **Star Guardian** - Seraphine carry with guardian frontline
• **Soul Fighter** - Flexible composition with good scaling

**Key Tips:**
- Focus on 2-star units early
- Prioritize completed trait synergies
- Adapt based on what you hit in shop"""

        elif any(word in message_lower for word in ["meta", "tier", "strong", "best"]):
            return """**Current TFT Set 15 Meta:**

**Strong Traits:**
- Sniper (reroll focused)
- Star Guardian (fast 8)
- Soul Fighter (flexible)
- Mighty Mech (reroll)

**Key Strategy Tips:**
- Power Snax add unique combat bonuses
- 3-star 5-cost champions are very powerful
- Role-based positioning is crucial"""

        elif any(word in message_lower for word in ["gold", "eco", "level", "when"]):
            return """**TFT Economic Strategy:**

**Early Game (Stages 1-3):**
- Save to 50 gold for maximum interest
- Only spend gold on guaranteed upgrades
- Level naturally to 6 by stage 3-2

**Mid Game (Stages 4-5):**
- Roll at level 6 if you need immediate strength
- Push to level 8 if you have strong economy
- Look for your end-game composition

**Late Game (Stage 6+):**
- Commit gold to find key upgrades
- Perfect your positioning
- Look for 5-cost carries"""

        else:
            return """**General TFT Strategy Tips:**

• **Flexible Play** - Don't force specific compositions
• **Strong Economy** - Prioritize gold management
• **Board Strength** - Always play your strongest available units
• **Positioning** - Adjust based on enemy threats
• **Itemization** - Build items on your main carries

Ask me about specific compositions, meta analysis, or strategic decisions!"""


def chat_message(message: Dict[str, str]) -> rx.Component:
    """Render a single chat message"""
    if message["role"] == "user":
        return rx.box(
            rx.text(
                message["content"],
                bg="blue.100",
                p="3",
                border_radius="lg",
                max_width="80%",
                margin_left="auto"
            ),
            width="100%",
            display="flex",
            justify_content="flex-end",
            mb="2"
        )
    else:
        return rx.box(
            rx.text(
                message["content"],
                bg="gray.100",
                p="3",
                border_radius="lg",
                max_width="80%",
                white_space="pre-line"
            ),
            width="100%",
            display="flex",
            justify_content="flex-start",
            mb="2"
        )


def chat_interface() -> rx.Component:
    """Main chat interface"""
    return rx.vstack(
        # Header
        rx.heading("⚔️ TFT Strategic Chat", size="6", color="blue.600"),
        rx.text("AI-powered strategic analysis for Teamfight Tactics Set 15", color="gray.600"),

        # Chat messages
        rx.box(
            rx.foreach(ChatState.messages, chat_message),
            height="500px",
            overflow_y="auto",
            border="1px solid #e2e8f0",
            border_radius="md",
            p="4",
            bg="white"
        ),

        # Input area
        rx.hstack(
            rx.input(
                placeholder="Ask about TFT strategy, compositions, or meta trends...",
                value=ChatState.current_message,
                on_change=ChatState.set_current_message,
                size="3",
                flex="1"
            ),
            rx.button(
                "Send",
                on_click=ChatState.send_message,
                loading=ChatState.is_loading,
                size="3",
                color_scheme="blue"
            ),
            width="100%",
            spacing="2"
        ),

        # Provider selection
        rx.hstack(
            rx.text("Provider:", size="2"),
            rx.select(
                ["anthropic", "openai"],
                value=ChatState.provider,
                on_change=ChatState.set_provider,
                size="1"
            ),
            justify="start",
            spacing="2",
            mt="2"
        ),

        width="100%",
        max_width="800px",
        spacing="4",
        p="6"
    )


def index() -> rx.Component:
    """Main page"""
    return rx.center(
        chat_interface(),
        height="100vh",
        bg="gray.50"
    )


# Create and configure the app
app = rx.App()
app.add_page(index, route="/")

if __name__ == "__main__":
    print("Use 'reflex run' to start the application.")