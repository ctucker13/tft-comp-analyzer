"""TFT Composition Analyzer - Modern Professional Reflex UI
Built with latest Reflex framework patterns and best practices.
"""

import reflex as rx
from typing import List, Dict, Optional
import asyncio

# Professional color system
class Colors:
    # Brand colors
    primary = "#2563eb"
    primary_light = "#3b82f6"
    primary_dark = "#1d4ed8"

    # Status colors
    success = "#10b981"
    warning = "#f59e0b"
    error = "#ef4444"
    info = "#06b6d4"

    # Neutral palette
    white = "#ffffff"
    gray_50 = "#f9fafb"
    gray_100 = "#f3f4f6"
    gray_200 = "#e5e7eb"
    gray_300 = "#d1d5db"
    gray_400 = "#9ca3af"
    gray_500 = "#6b7280"
    gray_600 = "#4b5563"
    gray_700 = "#374151"
    gray_800 = "#1f2937"
    gray_900 = "#111827"

class AppState(rx.State):
    """Modern application state with comprehensive TFT features."""

    # Navigation
    current_page: str = "dashboard"

    # Chat system
    messages: List[Dict[str, str]] = [
        {
            "role": "assistant",
            "content": "🎮 **Welcome to TFT Strategic Advisor!**\\n\\nI'm your AI companion for Teamfight Tactics Set 15. Ask me about:\\n\\n• 🏆 **Meta compositions** and tier lists\\n• 💰 **Economic strategies** and transitions\\n• 🎯 **Champion builds** and positioning\\n• 📊 **Performance analysis** and trends\\n\\nWhat strategy would you like to explore?"
        }
    ]
    current_message: str = ""
    is_loading: bool = False

    # Dashboard metrics
    win_rate: str = "18.2%"
    games_analyzed: int = 1247
    top_comp: str = "Sniper Reroll"
    meta_stability: str = "High"

    # Settings
    theme: str = "light"
    llm_provider: str = "anthropic"

    def navigate_to(self, page: str):
        """Navigate to different pages."""
        self.current_page = page

    def send_message(self):
        """Handle chat message sending."""
        if not self.current_message.strip():
            return

        # Add user message
        user_msg = self.current_message.strip()
        self.messages.append({"role": "user", "content": user_msg})
        self.current_message = ""
        self.is_loading = True

        # Simulate AI response based on message content
        response = self._generate_response(user_msg.lower())
        self.messages.append({"role": "assistant", "content": response})
        self.is_loading = False

    def _generate_response(self, message: str) -> str:
        """Generate contextual AI responses."""
        if any(word in message for word in ["comp", "composition", "team", "build"]):
            return """🏆 **Elite Set 15 Compositions**\\n\\n**S+ Tier Meta Leaders:**\\n\\n• **Sniper Reroll** (18.2% WR)\\n  └ Gnar carry + Caitlyn support\\n  └ Items: Giant Slayer, Last Whisper\\n  └ Economy: Level 6 rolldown\\n\\n• **Star Guardian** (17.4% WR)\\n  └ Seraphine AP carry\\n  └ Items: Archangel's Staff, JG\\n  └ Economy: Fast 8 transition\\n\\n• **Soul Fighter** (16.8% WR)\\n  └ Lee Sin + Mordekaiser\\n  └ Items: Blue Buff, AP items\\n  └ Economy: Flexible leveling"""

        elif any(word in message for word in ["meta", "tier", "best", "strong"]):
            return """📊 **Current Meta Analysis - Patch 15.3**\\n\\n**Power Rankings:**\\n```\\n🥇 S+: Sniper Reroll, Star Guardian\\n🥈 S:  Soul Fighter, Mighty Mech\\n🥉 A:  Challenger, Shape Shifter\\n💎 B:  Witch, Rebel\\n```\\n\\n**Meta Insights:**\\n• Reroll strategies dominate (42%)\\n• Power Snax create unique advantages\\n• 3-star carries are game-ending\\n• Economic management is crucial\\n\\n**Trending:** Early game strength → midgame transitions"""

        elif any(word in message for word in ["gold", "economy", "eco", "level"]):
            return """💰 **TFT Economic Mastery**\\n\\n**Leveling Curve:**\\n• **Level 6 (3-2):** 50+ gold, roll for pairs\\n• **Level 7 (4-1):** Transition window\\n• **Level 8 (4-5):** 70+ gold, find carries\\n• **Level 9 (5-1+):** Legendary hunt\\n\\n**Golden Rules:**\\n1. Health = Currency, spend wisely\\n2. Interest thresholds: 10, 20, 30, 50\\n3. Roll when weak, greed when strong\\n4. Power spikes: 3-2, 4-1, 5-1\\n\\n**Pro Tip:** Track opponent economy for timing"""

        else:
            return """⚔️ **TFT Strategic Intelligence**\\n\\nI can help with:\\n\\n🎯 **Compositions** - Meta team builds\\n📊 **Analysis** - Win rates and trends\\n💰 **Economics** - Gold optimization\\n🏆 **Strategy** - Decision making\\n\\nAsk me anything about Teamfight Tactics!"""

# Modern component styles
card_style = {
    "background": Colors.white,
    "border_radius": "12px",
    "box_shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)",
    "border": f"1px solid {Colors.gray_200}",
    "padding": "1.5rem",
    "transition": "all 0.2s ease-in-out",
    "_hover": {
        "box_shadow": "0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
        "transform": "translateY(-2px)"
    }
}

button_primary_style = {
    "background": f"linear-gradient(135deg, {Colors.primary}, {Colors.primary_light})",
    "color": Colors.white,
    "border": "none",
    "border_radius": "8px",
    "padding": "0.75rem 1.5rem",
    "font_weight": "600",
    "cursor": "pointer",
    "transition": "all 0.2s ease-in-out",
    "_hover": {
        "transform": "translateY(-1px)",
        "box_shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
    }
}

def metric_card(icon: str, title: str, value: str, subtitle: str, color: str = Colors.primary):
    """Professional metric card component."""
    return rx.box(
        rx.hstack(
            rx.box(
                rx.text(icon, font_size="2rem"),
                padding="1rem",
                background=f"{color}10",
                border_radius="8px"
            ),
            rx.vstack(
                rx.text(title, font_weight="600", color=Colors.gray_700),
                rx.text(value, font_size="2rem", font_weight="bold", color=color),
                rx.text(subtitle, font_size="0.875rem", color=Colors.gray_500),
                spacing="1",
                align_items="start"
            ),
            spacing="4",
            align_items="center"
        ),
        style=card_style,
        width="100%"
    )

def nav_button(icon: str, text: str, page: str, is_active: bool = False):
    """Modern navigation button."""
    active_style = {
        "background": f"{Colors.primary}10",
        "color": Colors.primary,
        "border_left": f"3px solid {Colors.primary}"
    }

    return rx.button(
        rx.hstack(
            rx.text(icon, font_size="1.25rem"),
            rx.text(text, font_weight="500"),
            spacing="3"
        ),
        on_click=lambda: AppState.navigate_to(page),
        style={
            **({**active_style} if is_active else {}),
            "width": "100%",
            "justify_content": "flex-start",
            "padding": "0.75rem 1rem",
            "border_radius": "8px",
            "border": "none",
            "background": "transparent" if not is_active else active_style["background"],
            "color": Colors.primary if is_active else Colors.gray_600,
            "cursor": "pointer",
            "transition": "all 0.2s ease-in-out",
            "_hover": {
                "background": f"{Colors.gray_100}" if not is_active else active_style["background"],
                "color": Colors.primary
            }
        }
    )

def sidebar():
    """Modern sidebar with professional styling."""
    return rx.box(
        rx.vstack(
            # Brand section
            rx.box(
                rx.hstack(
                    rx.text("⚔️", font_size="2rem"),
                    rx.vstack(
                        rx.text("TFT Analyzer", font_size="1.25rem", font_weight="bold", color=Colors.white),
                        rx.text("Set 15: K.O. Coliseum", font_size="0.875rem", color="#cbd5e1"),
                        spacing="1",
                        align_items="start"
                    ),
                    spacing="3"
                ),
                background=f"linear-gradient(135deg, {Colors.primary}, {Colors.primary_dark})",
                padding="1.5rem",
                border_radius="12px",
                margin_bottom="2rem"
            ),

            # Navigation
            rx.vstack(
                rx.text("Navigation", font_weight="600", color=Colors.gray_700, margin_bottom="0.5rem"),
                nav_button("🏠", "Dashboard", "dashboard", AppState.current_page == "dashboard"),
                nav_button("💬", "Strategic Chat", "chat", AppState.current_page == "chat"),
                nav_button("📊", "Meta Analysis", "meta", AppState.current_page == "meta"),
                nav_button("🎯", "Champions", "champions", AppState.current_page == "champions"),
                nav_button("⚙️", "Settings", "settings", AppState.current_page == "settings"),
                spacing="2",
                width="100%"
            ),

            # Status
            rx.box(
                rx.vstack(
                    rx.text("System Status", font_weight="600", color=Colors.gray_700, margin_bottom="0.5rem"),
                    rx.hstack(
                        rx.box(
                            width="8px",
                            height="8px",
                            background=Colors.success,
                            border_radius="50%"
                        ),
                        rx.text("AI Ready", font_size="0.875rem", color=Colors.gray_600),
                        spacing="2"
                    ),
                    rx.hstack(
                        rx.box(
                            width="8px",
                            height="8px",
                            background=Colors.info,
                            border_radius="50%"
                        ),
                        rx.text("Database Online", font_size="0.875rem", color=Colors.gray_600),
                        spacing="2"
                    ),
                    spacing="3",
                    align_items="start"
                ),
                style={
                    **card_style,
                    "margin_top": "auto"
                }
            ),

            spacing="4",
            height="100vh",
            align_items="stretch"
        ),
        width="280px",
        background=Colors.gray_50,
        padding="1.5rem",
        position="fixed",
        left="0",
        top="0",
        height="100vh",
        border_right=f"1px solid {Colors.gray_200}"
    )

def dashboard_page():
    """Modern dashboard with key metrics and insights."""
    return rx.vstack(
        # Header
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("TFT Strategic Dashboard", font_size="2rem", font_weight="bold", color=Colors.gray_900),
                    rx.text("Real-time analysis for Teamfight Tactics Set 15", color=Colors.gray_600),
                    spacing="2",
                    align_items="start"
                ),
                rx.box(
                    rx.hstack(
                        rx.box(
                            width="8px",
                            height="8px",
                            background=Colors.success,
                            border_radius="50%"
                        ),
                        rx.text("LIVE", font_weight="600", color=Colors.success),
                        spacing="2"
                    ),
                    padding="0.5rem 1rem",
                    background=f"{Colors.success}10",
                    border_radius="20px"
                ),
                justify_content="space-between",
                align_items="start"
            ),
            style=card_style,
            margin_bottom="2rem"
        ),

        # Metrics grid
        rx.grid(
            metric_card("📊", "Meta Overview", "S+ Tier", "2 elite compositions", Colors.primary),
            metric_card("🏆", "Win Rate Leader", AppState.win_rate, AppState.top_comp, Colors.success),
            metric_card("🎮", "Games Analyzed", f"{AppState.games_analyzed:,}", "Recent matches", Colors.info),
            metric_card("⚡", "Meta Stability", AppState.meta_stability, "Current patch", Colors.warning),
            columns="4",
            spacing="6",
            margin_bottom="2rem"
        ),

        # Quick actions
        rx.box(
            rx.vstack(
                rx.text("Quick Actions", font_size="1.25rem", font_weight="600", margin_bottom="1rem"),
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.text("💬"),
                            rx.text("Start Strategic Chat"),
                            spacing="2"
                        ),
                        on_click=lambda: AppState.navigate_to("chat"),
                        style=button_primary_style
                    ),
                    rx.button(
                        rx.hstack(
                            rx.text("📊"),
                            rx.text("View Meta Analysis"),
                            spacing="2"
                        ),
                        on_click=lambda: AppState.navigate_to("meta"),
                        style={
                            **button_primary_style,
                            "background": "transparent",
                            "color": Colors.primary,
                            "border": f"2px solid {Colors.primary}",
                            "_hover": {
                                **button_primary_style["_hover"],
                                "background": Colors.primary,
                                "color": Colors.white
                            }
                        }
                    ),
                    spacing="4"
                ),
                spacing="0",
                align_items="start"
            ),
            style=card_style
        ),

        spacing="0",
        align_items="stretch",
        width="100%",
        padding="2rem"
    )

def chat_message(message: Dict[str, str]):
    """Professional chat message bubble."""
    is_user = message["role"] == "user"

    return rx.box(
        rx.text(
            message["content"],
            color=Colors.white if is_user else Colors.gray_800,
            line_height="1.6",
            white_space="pre-line"
        ),
        style={
            "background": f"linear-gradient(135deg, {Colors.primary}, {Colors.primary_light})" if is_user else Colors.white,
            "padding": "1rem 1.25rem",
            "border_radius": "12px",
            "max_width": "80%",
            "margin_left": "auto" if is_user else "0",
            "margin_bottom": "1rem",
            "border": f"1px solid {Colors.gray_200}" if not is_user else "none",
            "box_shadow": "0 1px 3px 0 rgba(0, 0, 0, 0.1)" if not is_user else "0 4px 6px -1px rgba(0, 0, 0, 0.1)"
        }
    )

def chat_page():
    """Modern chat interface."""
    return rx.vstack(
        # Chat header
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.text("Strategic Chat", font_size="1.5rem", font_weight="600"),
                    rx.text("AI-powered TFT strategic analysis", color=Colors.gray_600),
                    spacing="1",
                    align_items="start"
                ),
                rx.text("🤖", font_size="1.5rem"),
                justify_content="space-between"
            ),
            style=card_style,
            margin_bottom="1.5rem"
        ),

        # Chat messages
        rx.box(
            rx.vstack(
                rx.foreach(AppState.messages, chat_message),
                rx.cond(
                    AppState.is_loading,
                    rx.box(
                        rx.hstack(
                            rx.text("🤖", font_size="1rem"),
                            rx.text("Analyzing...", color=Colors.gray_500, font_style="italic"),
                            spacing="2"
                        ),
                        padding="1rem",
                        background=f"{Colors.gray_100}",
                        border_radius="12px",
                        max_width="80%"
                    )
                ),
                spacing="0",
                align_items="stretch"
            ),
            style={
                **card_style,
                "height": "400px",
                "overflow_y": "auto",
                "background": f"linear-gradient(135deg, {Colors.gray_50}, {Colors.gray_100})"
            },
            margin_bottom="1rem"
        ),

        # Chat input
        rx.hstack(
            rx.input(
                placeholder="Ask about team compositions, meta trends, or strategic advice...",
                value=AppState.current_message,
                on_change=AppState.set_current_message,
                style={
                    "flex_grow": "1",
                    "padding": "0.75rem",
                    "border_radius": "8px",
                    "border": f"2px solid {Colors.gray_200}",
                    "_focus": {
                        "border_color": Colors.primary,
                        "outline": "none"
                    }
                }
            ),
            rx.button(
                rx.cond(
                    AppState.is_loading,
                    rx.text("⏳ Analyzing..."),
                    rx.hstack(
                        rx.text("🚀"),
                        rx.text("Send"),
                        spacing="2"
                    )
                ),
                on_click=AppState.send_message,
                disabled=AppState.is_loading,
                style={
                    **button_primary_style,
                    "opacity": "0.6" if AppState.is_loading else "1"
                }
            ),
            spacing="4",
            width="100%"
        ),

        spacing="0",
        align_items="stretch",
        width="100%",
        padding="2rem"
    )

def main_content():
    """Main content area with routing."""
    return rx.box(
        rx.cond(
            AppState.current_page == "dashboard",
            dashboard_page(),
            rx.cond(
                AppState.current_page == "chat",
                chat_page(),
                rx.box(
                    rx.text(f"Page '{AppState.current_page}' coming soon!",
                           font_size="1.5rem",
                           text_align="center",
                           color=Colors.gray_500),
                    padding="4rem",
                    style=card_style,
                    margin="2rem"
                )
            )
        ),
        margin_left="280px",
        min_height="100vh",
        background=f"linear-gradient(135deg, {Colors.gray_50}, {Colors.white})"
    )

def index():
    """Main application."""
    return rx.fragment(
        sidebar(),
        main_content()
    )

# Create the modern app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        scaling="100%"
    )
)

app.add_page(index, route="/")