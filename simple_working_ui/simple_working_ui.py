"""TFT Composition Analyzer - Simple Working Reflex UI"""

import reflex as rx
from typing import List, Dict

class TFTState(rx.State):
    """Simple working state for TFT Analyzer."""
    current_page: str = "dashboard"

    # Chat
    messages: List[str] = ["🎮 Welcome to TFT Strategic Advisor! Ask me about compositions, economy, or strategy."]
    current_message: str = ""

    # Metrics
    win_rate: str = "18.2%"
    top_comp: str = "Sniper Reroll"

    def navigate_to(self, page: str):
        self.current_page = page

    def send_message(self):
        if not self.current_message.strip():
            return

        user_msg = self.current_message.strip()
        self.messages.append(f"You: {user_msg}")
        self.current_message = ""

        # Simple AI response
        if "comp" in user_msg.lower():
            response = "🏆 Top compositions: Sniper Reroll (18.2%), Star Guardian (17.4%), Soul Fighter (16.8%)"
        elif "meta" in user_msg.lower():
            response = "📊 Meta: S+ Tier includes Sniper Reroll and Star Guardian. Reroll strategies dominate!"
        elif "gold" in user_msg.lower() or "eco" in user_msg.lower():
            response = "💰 Economy: Level 6 at 3-2 with 50+ gold, Level 8 at 4-5 with 70+ gold"
        else:
            response = "⚔️ I can help with compositions, meta analysis, and economic strategies!"

        self.messages.append(f"AI: {response}")

def simple_card(title: str, value: str, icon: str):
    """Create a simple metric card."""
    return rx.card(
        rx.vstack(
            rx.text(icon, size="6"),
            rx.text(title, size="2", weight="medium"),
            rx.text(value, size="4", weight="bold"),
            spacing="2",
            align="center"
        )
    )

def nav_button(icon: str, text: str, page: str):
    """Simple navigation button."""
    return rx.button(
        rx.hstack(
            rx.text(icon),
            rx.text(text),
            spacing="2"
        ),
        variant=rx.cond(TFTState.current_page == page, "solid", "ghost"),
        color_scheme="blue",
        width="100%",
        justify="start",
        on_click=lambda: TFTState.navigate_to(page)
    )

def sidebar():
    """Simple sidebar."""
    return rx.box(
        rx.vstack(
            # Brand
            rx.card(
                rx.vstack(
                    rx.text("⚔️ TFT Analyzer", size="4", weight="bold", color="white"),
                    rx.text("Set 15: K.O. Coliseum", size="2", color="white"),
                    spacing="2"
                ),
                style={
                    "background": "linear-gradient(135deg, #2563eb, #1d4ed8)",
                    "border": "none"
                }
            ),

            # Navigation
            rx.vstack(
                rx.text("Navigation", size="2", weight="bold"),
                nav_button("🏠", "Dashboard", "dashboard"),
                nav_button("💬", "Chat", "chat"),
                nav_button("📊", "Meta", "meta"),
                nav_button("⚙️", "Settings", "settings"),
                spacing="2",
                width="100%"
            ),

            spacing="4",
            width="100%"
        ),
        width="280px",
        padding="6",
        background=rx.color("gray", 1),
        border_right=f"1px solid {rx.color('gray', 3)}",
        position="fixed",
        height="100vh"
    )

def dashboard():
    """Simple dashboard."""
    return rx.vstack(
        # Header
        rx.card(
            rx.hstack(
                rx.vstack(
                    rx.text("TFT Strategic Dashboard", size="5", weight="bold"),
                    rx.text("Real-time analysis for TFT Set 15", size="3"),
                    spacing="2",
                    align_items="start"
                ),
                rx.badge("LIVE", color_scheme="green"),
                justify="between"
            )
        ),

        # Metrics
        rx.grid(
            simple_card("Meta Status", "S+ Tier", "📊"),
            simple_card("Win Rate Leader", TFTState.win_rate, "🏆"),
            simple_card("Top Comp", TFTState.top_comp, "🎯"),
            simple_card("Status", "Active", "⚡"),
            columns="4",
            spacing="4"
        ),

        # Actions
        rx.card(
            rx.vstack(
                rx.text("Quick Actions", size="3", weight="bold"),
                rx.hstack(
                    rx.button(
                        "💬 Start Chat",
                        on_click=lambda: TFTState.navigate_to("chat"),
                        color_scheme="blue"
                    ),
                    rx.button(
                        "📊 View Meta",
                        on_click=lambda: TFTState.navigate_to("meta"),
                        variant="outline"
                    ),
                    spacing="3"
                ),
                spacing="3"
            )
        ),

        spacing="6",
        width="100%",
        padding="6"
    )

def chat():
    """Simple chat interface."""
    return rx.vstack(
        # Header
        rx.card(
            rx.text("Strategic Chat", size="4", weight="bold")
        ),

        # Messages
        rx.card(
            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        TFTState.messages,
                        lambda msg: rx.text(msg, size="2", margin_bottom="3")
                    ),
                    spacing="2",
                    width="100%"
                ),
                style={"height": "400px"}
            ),
            style={"background": rx.color("gray", 1)}
        ),

        # Input
        rx.hstack(
            rx.input(
                placeholder="Ask about TFT strategy...",
                value=TFTState.current_message,
                on_change=TFTState.set_current_message,
                flex_grow="1"
            ),
            rx.button(
                "🚀 Send",
                on_click=TFTState.send_message,
                color_scheme="blue"
            ),
            spacing="3",
            width="100%"
        ),

        spacing="4",
        width="100%",
        padding="6"
    )

def main_content():
    """Main content area."""
    return rx.box(
        rx.cond(
            TFTState.current_page == "dashboard",
            dashboard(),
            rx.cond(
                TFTState.current_page == "chat",
                chat(),
                rx.card(
                    rx.text(f"Page '{TFTState.current_page}' coming soon!", size="4"),
                    padding="4rem",
                    style={"text_align": "center"}
                )
            )
        ),
        margin_left="280px",
        min_height="100vh",
        background=rx.color("gray", 1)
    )

def index():
    """Main app layout."""
    return rx.fragment(
        sidebar(),
        main_content()
    )

# Create app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True
    )
)
app.add_page(index, route="/")