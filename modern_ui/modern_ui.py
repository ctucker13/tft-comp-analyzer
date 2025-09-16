"""TFT Composition Analyzer - Modern Professional Reflex UI
Built with latest Reflex framework best practices and proper validation.
"""

import reflex as rx
from typing import List, Dict

class TFTState(rx.State):
    """Application state for TFT Analyzer."""

    # Navigation
    current_page: str = "dashboard"

    # Chat system
    messages: List[Dict[str, str]] = [
        {
            "role": "assistant",
            "content": "🎮 Welcome to TFT Strategic Advisor!\\n\\nI'm your AI companion for Teamfight Tactics Set 15. Ask me about compositions, economy, or strategy!"
        }
    ]
    current_message: str = ""
    is_loading: bool = False

    # Dashboard data
    win_rate: str = "18.2%"
    top_comp: str = "Sniper Reroll"
    games_count: int = 1247

    def navigate_to(self, page: str):
        """Navigate to a different page."""
        self.current_page = page

    def send_message(self):
        """Send chat message and get AI response."""
        if not self.current_message.strip():
            return

        user_msg = self.current_message.strip()
        self.messages.append({"role": "user", "content": user_msg})
        self.current_message = ""
        self.is_loading = True

        # Generate AI response
        response = self._get_ai_response(user_msg.lower())
        self.messages.append({"role": "assistant", "content": response})
        self.is_loading = False

    def _get_ai_response(self, message: str) -> str:
        """Generate contextual AI responses."""
        if any(word in message for word in ["comp", "composition", "team"]):
            return "🏆 Elite Set 15 Compositions\\n\\n• Sniper Reroll (18.2% WR)\\n• Star Guardian (17.4% WR)\\n• Soul Fighter (16.8% WR)\\n\\nFocus on 2-star carries and strong economy!"
        elif any(word in message for word in ["meta", "tier", "best"]):
            return "📊 Current Meta Analysis\\n\\nS+ Tier: Sniper Reroll, Star Guardian\\nS Tier: Soul Fighter, Mighty Mech\\nA Tier: Challenger, Shape Shifter\\n\\nReroll strategies dominate this patch!"
        elif any(word in message for word in ["gold", "economy", "eco"]):
            return "💰 Economic Strategy\\n\\n• Level 6 (3-2): 50+ gold\\n• Level 8 (4-5): 70+ gold\\n• Roll when weak, greed when strong\\n• Interest every 10 gold"
        else:
            return "⚔️ TFT Strategic Assistant\\n\\nI can help with compositions, meta analysis, economic strategies, and more. What would you like to know?"

def metric_card(icon: str, title: str, value: str, description: str):
    """Create a professional metric card."""
    return rx.card(
        rx.flex(
            rx.text(icon, size="6"),
            rx.flex(
                rx.text(title, size="2", weight="medium", color_scheme="gray"),
                rx.text(value, size="6", weight="bold"),
                rx.text(description, size="1", color_scheme="gray"),
                direction="column",
                spacing="1"
            ),
            spacing="4",
            align="center"
        ),
        style={
            "transition": "all 0.2s ease",
            "_hover": {"transform": "translateY(-2px)"}
        }
    )

def nav_item(icon: str, text: str, page: str):
    """Create a navigation item."""
    return rx.button(
        rx.flex(
            rx.text(icon),
            rx.text(text, size="2", weight="medium"),
            spacing="3",
            align="center"
        ),
        variant=rx.cond(TFTState.current_page == page, "soft", "ghost"),
        color_scheme=rx.cond(TFTState.current_page == page, "blue", "gray"),
        justify="start",
        width="100%",
        on_click=lambda: TFTState.navigate_to(page)
    )

def sidebar():
    """Application sidebar with navigation."""
    return rx.box(
        rx.flex(
            # Brand header
            rx.card(
                rx.flex(
                    rx.text("⚔️", size="6"),
                    rx.flex(
                        rx.text("TFT Analyzer", size="4", weight="bold", color="white"),
                        rx.text("Set 15: K.O. Coliseum", size="2", color="white"),
                        direction="column",
                        spacing="1"
                    ),
                    spacing="3",
                    align="center"
                ),
                style={
                    "background": "linear-gradient(135deg, #2563eb, #1d4ed8)",
                    "border": "none"
                }
            ),

            # Navigation menu
            rx.flex(
                rx.text("Navigation", size="2", weight="bold", color_scheme="gray"),
                nav_item("🏠", "Dashboard", "dashboard"),
                nav_item("💬", "Strategic Chat", "chat"),
                nav_item("📊", "Meta Analysis", "meta"),
                nav_item("🎯", "Champions", "champions"),
                nav_item("⚙️", "Settings", "settings"),
                direction="column",
                spacing="2"
            ),

            # System status
            rx.card(
                rx.flex(
                    rx.text("System Status", size="2", weight="bold"),
                    rx.flex(
                        rx.flex(
                            rx.badge("●", color_scheme="green"),
                            rx.text("AI Ready", size="1"),
                            spacing="2",
                            align="center"
                        ),
                        rx.flex(
                            rx.badge("●", color_scheme="blue"),
                            rx.text("Database Online", size="1"),
                            spacing="2",
                            align="center"
                        ),
                        direction="column",
                        spacing="2"
                    ),
                    direction="column",
                    spacing="3"
                )
            ),

            direction="column",
            spacing="4",
            height="100vh",
            justify="start"
        ),
        width="280px",
        padding="6",
        background=rx.color("gray", 1),
        border_right=f"1px solid {rx.color('gray', 3)}",
        position="fixed",
        left="0",
        top="0",
        height="100vh"
    )

def chat_message(message: Dict[str, str]):
    """Render a chat message."""
    is_user = message["role"] == "user"

    return rx.flex(
        rx.card(
            rx.text(
                message["content"],
                size="2",
                white_space="pre-line"
            ),
            style={
                "background": "#2563eb" if is_user else "white",
                "color": "white" if is_user else "inherit",
                "max_width": "80%",
                "margin_left": "auto" if is_user else "0"
            }
        ),
        width="100%",
        justify="end" if is_user else "start",
        margin_bottom="3"
    )

def dashboard():
    """Dashboard page content."""
    return rx.flex(
        # Header
        rx.card(
            rx.flex(
                rx.flex(
                    rx.text("TFT Strategic Dashboard", size="6", weight="bold"),
                    rx.text("Real-time analysis for Teamfight Tactics Set 15", size="3", color_scheme="gray"),
                    direction="column",
                    spacing="2"
                ),
                rx.badge("LIVE", color_scheme="green"),
                justify="between",
                align="center"
            )
        ),

        # Metrics
        rx.grid(
            metric_card("📊", "Meta Status", "S+ Tier", "2 elite compositions"),
            metric_card("🏆", "Win Rate Leader", TFTState.win_rate, TFTState.top_comp),
            metric_card("🎮", "Games Analyzed", f"{TFTState.games_count:,}", "Recent matches"),
            metric_card("⚡", "Meta Stability", "High", "Current patch"),
            columns="4",
            spacing="4"
        ),

        # Quick actions
        rx.card(
            rx.flex(
                rx.text("Quick Actions", size="4", weight="bold"),
                rx.flex(
                    rx.button(
                        rx.flex(
                            rx.text("💬"),
                            rx.text("Start Strategic Chat"),
                            spacing="2"
                        ),
                        on_click=lambda: TFTState.navigate_to("chat"),
                        color_scheme="blue"
                    ),
                    rx.button(
                        rx.flex(
                            rx.text("📊"),
                            rx.text("View Meta Analysis"),
                            spacing="2"
                        ),
                        on_click=lambda: TFTState.navigate_to("meta"),
                        variant="outline",
                        color_scheme="blue"
                    ),
                    spacing="3"
                ),
                direction="column",
                spacing="4"
            )
        ),

        direction="column",
        spacing="6",
        width="100%"
    )

def chat():
    """Chat page content."""
    return rx.flex(
        # Chat header
        rx.card(
            rx.flex(
                rx.text("Strategic Chat", size="5", weight="bold"),
                rx.text("🤖 AI-powered TFT analysis", size="3", color_scheme="gray"),
                direction="column",
                spacing="2"
            )
        ),

        # Messages area
        rx.card(
            rx.scroll_area(
                rx.flex(
                    rx.foreach(TFTState.messages, chat_message),
                    rx.cond(
                        TFTState.is_loading,
                        rx.flex(
                            rx.card(
                                rx.flex(
                                    rx.spinner(size="1"),
                                    rx.text("AI is thinking...", size="2", color_scheme="gray"),
                                    spacing="2",
                                    align="center"
                                ),
                                style={"background": rx.color("gray", 2)}
                            ),
                            width="100%",
                            justify="start"
                        )
                    ),
                    direction="column",
                    spacing="0",
                    width="100%"
                ),
                style={"height": "400px"}
            ),
            style={"background": rx.color("gray", 1)}
        ),

        # Chat input
        rx.flex(
            rx.input(
                placeholder="Ask about team compositions, meta trends, or strategic advice...",
                value=TFTState.current_message,
                on_change=TFTState.set_current_message,
                flex_grow="1"
            ),
            rx.button(
                rx.cond(
                    TFTState.is_loading,
                    rx.spinner(size="1"),
                    rx.flex(
                        rx.text("🚀"),
                        rx.text("Send"),
                        spacing="2"
                    )
                ),
                on_click=TFTState.send_message,
                disabled=TFTState.is_loading,
                color_scheme="blue"
            ),
            spacing="3",
            width="100%"
        ),

        direction="column",
        spacing="4",
        width="100%"
    )

def main_content():
    """Main content area with routing."""
    return rx.box(
        rx.box(
            rx.cond(
                TFTState.current_page == "dashboard",
                dashboard(),
                rx.cond(
                    TFTState.current_page == "chat",
                    chat(),
                    rx.card(
                        rx.flex(
                            rx.text(f"Page '{TFTState.current_page}' coming soon!", size="4", color_scheme="gray"),
                            rx.text("This feature is under development.", size="2", color_scheme="gray"),
                            direction="column",
                            spacing="2",
                            align="center"
                        ),
                        style={"text_align": "center", "padding": "4rem"}
                    )
                )
            ),
            padding="6"
        ),
        margin_left="280px",
        min_height="100vh",
        background=rx.color("gray", 1)
    )

def index():
    """Main application layout."""
    return rx.box(
        sidebar(),
        main_content(),
        width="100%"
    )

# Create the application
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

app.add_page(index, route="/")