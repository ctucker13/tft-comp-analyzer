"""
TFT Composition Analyzer - Reflex UI
A modern Python web interface for TFT strategic analysis
"""

import reflex as rx
from typing import List, Dict, Optional
import asyncio
from pathlib import Path
import sys
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.agents.tft_agent import create_tft_agent
from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
from src.tft_analyzer.data.riot_official_units_with_traits import riot_official_db_with_traits


class TFTState(rx.State):
    """Application state for TFT analyzer"""

    # Chat functionality
    messages: List[Dict[str, str]] = []
    current_message: str = ""
    is_loading: bool = False
    error_message: Optional[str] = None

    # Meta analysis
    tier_list_data: str = ""
    trends_data: str = ""

    # Settings
    selected_provider: str = "anthropic"
    api_status: Dict[str, bool] = {}
    riot_ok: bool = False
    anthropic_ok: bool = False
    openai_ok: bool = False

    # Champions data
    champions_data: List[Dict] = []
    search_term: str = ""
    filtered_champions: List[Dict] = []
    cost_filters: List[int] = []  # empty means all

    # UX helpers
    example_prompts: List[str] = [
        "I'm level 6 with 30 gold and 50 HP — what now?",
        "What are the strongest comps this patch?",
        "Should I pivot or keep rerolling at stage 4-1?",
        "Give me an item plan for Jinx carry"
    ]

    async def on_load(self):
        """Initialize data when the page loads"""
        self.load_initial_data()

    def load_initial_data(self):
        """Load initial data on startup"""
        try:
            # Load settings and check API status
            settings = Settings()
            self.api_status = {
                "riot": bool(settings.riot_api_key),
                "anthropic": bool(settings.anthropic_api_key),
                "openai": bool(settings.openai_api_key)
            }
            self.riot_ok = self.api_status["riot"]
            self.anthropic_ok = self.api_status["anthropic"]
            self.openai_ok = self.api_status["openai"]

            # Load champions data
            self.load_champions_data()

        except Exception as e:
            print(f"Error loading initial data: {e}")
            self.api_status = {"riot": False, "anthropic": False, "openai": False}

    def load_champions_data(self):
        """Load champions data from the database"""
        try:
            # Get all champions from the database
            all_champions = []
            for champion in riot_official_db_with_traits.get_all_units():
                all_champions.append({
                    "name": champion.name,
                    "cost": champion.cost,
                    "traits": champion.traits,
                    "type": getattr(champion, 'type', 'Champion')
                })

            self.champions_data = all_champions
            self.filtered_champions = all_champions.copy()
        except Exception as e:
            print(f"Error loading champions: {e}")
            self.champions_data = []
            self.filtered_champions = []

    async def send_chat_message(self):
        """Send chat message to TFT agent"""
        if not self.current_message.strip():
            return

        self.is_loading = True
        user_message = self.current_message
        self.current_message = ""

        # Add user message to chat
        self.messages.append({
            "role": "user",
            "content": user_message
        })

        try:
            # Create agent and get response
            agent = create_tft_agent(provider=self.selected_provider)
            response = agent.process_message(user_message)

            # Add assistant response
            self.messages.append({
                "role": "assistant",
                "content": response
            })

        except Exception as e:
            error_msg = f"Error: {str(e)}\n\nFalling back to basic TFT advice: Focus on strong boards, good economy, and flexible play!"
            self.messages.append({
                "role": "assistant",
                "content": error_msg
            })
            self.error_message = str(e)

        self.is_loading = False

    def load_meta_analysis(self):
        """Load meta analysis data"""
        try:
            self.tier_list_data = get_meta_tier_list()
            self.trends_data = get_meta_trends()
        except Exception as e:
            self.tier_list_data = f"Error loading tier list: {e}"
            self.trends_data = f"Error loading trends: {e}"
            self.error_message = str(e)

    def set_current_message(self, message: str):
        """Update current chat input"""
        self.current_message = message

    def clear_chat(self):
        """Clear chat history"""
        self.messages = []

    async def regenerate_last(self):
        """Regenerate the last assistant message using the last user input."""
        last_user = None
        for msg in reversed(self.messages):
            if msg.get("role") == "user":
                last_user = msg.get("content", "")
                break
        if not last_user:
            return
        self.current_message = last_user
        await self.send_chat_message()

    def filter_champions(self, search_term: str):
        """Filter champions based on search term"""
        self.search_term = search_term
        if not search_term:
            candidates = self.champions_data.copy()
        else:
            search_lower = search_term.lower()
            candidates = [
                champion for champion in self.champions_data
                if search_lower in champion["name"].lower() or
                any(search_lower in trait.lower() for trait in champion["traits"])
            ]

        # Apply cost filter
        if self.cost_filters:
            candidates = [c for c in candidates if int(c.get("cost", 0)) in set(self.cost_filters)]

        self.filtered_champions = candidates

    def set_provider(self, provider: str):
        """Set the LLM provider"""
        self.selected_provider = provider

    def toggle_cost_filter(self, cost: int):
        """Toggle a cost star filter and re-apply filters"""
        if cost in self.cost_filters:
            self.cost_filters.remove(cost)
        else:
            self.cost_filters.append(cost)
        self.filter_champions(self.search_term)

    def use_example(self, text: str):
        """Insert an example into the input."""
        self.current_message = text


def chat_interface() -> rx.Component:
    """Chat interface component"""
    return rx.vstack(
        rx.hstack(
            rx.heading("💬 TFT Strategic Chat", size="4"),
            rx.spacer(),
            rx.button("Regenerate", on_click=TFTState.regenerate_last, variant="outline"),
            rx.button("Clear", on_click=TFTState.clear_chat, variant="ghost"),
            width="100%"
        ),
        rx.box(
            rx.foreach(
                TFTState.messages,
                lambda message: rx.hstack(
                    rx.cond(
                        message["role"] == "user",
                        rx.box(
                            rx.text(message["content"]),
                            p="2",
                            border_radius="md",
                            max_width="70%",
                            margin_left="auto"
                        ),
                        rx.box(
                            rx.markdown(message["content"]),
                            p="2",
                            border_radius="md",
                            max_width="70%"
                        )
                    ),
                    width="100%",
                    justify=rx.cond(message["role"] == "user", "end", "start")
                )
            ),
            height="400px",
            overflow_y="auto",
            border="1px solid #ccc",
            p="4",
            border_radius="md"
        ),
        rx.flex(
            rx.foreach(
                TFTState.example_prompts,
                lambda ex: rx.button(
                    ex,
                    size="2",
                    variant="outline",
                    on_click=lambda ex=ex: TFTState.use_example(ex)
                )
            ),
            wrap="wrap",
            gap="2",
            width="100%"
        ),
        rx.hstack(
            rx.input(
                placeholder="Ask about TFT strategy, compositions, or meta...",
                value=TFTState.current_message,
                on_change=TFTState.set_current_message,
                width="100%"
            ),
            rx.button(
                "Send",
                on_click=TFTState.send_chat_message,
                loading=TFTState.is_loading,
                color_scheme="blue",
                is_disabled=TFTState.is_loading
            ),
            width="100%"
        ),
        rx.cond(
            TFTState.is_loading,
            rx.hstack(rx.spinner(size="2"), rx.text("Analyzing..."), spacing="2")
        ),
        rx.cond(
            TFTState.error_message != "",
            rx.alert(
                rx.alert_icon(),
                rx.alert_title("An error occurred"),
                rx.alert_description(rx.text(TFTState.error_message)),
                status="error"
            )
        ),
        width="100%",
        spacing="4"
    )


def meta_analysis_interface() -> rx.Component:
    """Meta analysis interface component"""
    return rx.vstack(
        rx.heading("📊 Meta Analysis", size="4"),
        rx.button(
            "Load Latest Meta Data",
            on_click=TFTState.load_meta_analysis,
            color_scheme="green"
        ),
        rx.tabs.root(
            rx.tabs.list(
                rx.tabs.trigger("Tier Lists", value="tiers"),
                rx.tabs.trigger("Trends", value="trends"),
            ),
            rx.tabs.content(
                rx.box(
                    rx.markdown(TFTState.tier_list_data),
                    p="4",
                    border_radius="md",
                    height="400px",
                    overflow_y="auto"
                ),
                value="tiers"
            ),
            rx.tabs.content(
                rx.box(
                    rx.markdown(TFTState.trends_data),
                    p="4",
                    border_radius="md",
                    height="400px",
                    overflow_y="auto"
                ),
                value="trends"
            ),
            default_value="tiers",
            width="100%"
        ),
        width="100%",
        spacing="4"
    )


def champions_database() -> rx.Component:
    """Champions database component"""
    return rx.vstack(
        rx.heading("🗃️ Champions Database", size="4"),
        rx.input(
            placeholder="Search champions or traits...",
            value=TFTState.search_term,
            on_change=TFTState.filter_champions,
            width="100%"
        ),
        rx.hstack(
            rx.text("Filter by cost:"),
            rx.flex(
                rx.foreach(
                    [1, 2, 3, 4, 5],
                    lambda c: rx.button(
                        f"{c}⭐",
                        size="2",
                        variant=rx.cond(TFTState.cost_filters.contains(c), "solid", "outline"),
                        color_scheme="yellow",
                        on_click=lambda c=c: TFTState.toggle_cost_filter(c)
                    )
                ),
                wrap="wrap",
                gap="2"
            ),
            width="100%"
        ),
        rx.text(f"Found {len(TFTState.filtered_champions)} champions"),
        rx.box(
            rx.grid(
                rx.foreach(
                    TFTState.filtered_champions,
                    lambda champion: rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.heading(champion["name"], size="3"),
                                rx.badge(f"{champion['cost']}⭐", color_scheme="yellow"),
                                justify="between",
                                width="100%"
                            ),
                            rx.flex(
                                rx.foreach(
                                    champion["traits"],
                                    lambda trait: rx.badge(trait, color_scheme="blue", size="2")
                                )
                            , wrap="wrap", gap="1"),
                            align_items="start",
                            spacing="2"
                        ),
                        bg="white",
                        p="3",
                        border_radius="md",
                        border="1px solid #e2e8f0",
                        _hover={"bg": "gray.50"}
                    )
                ),
                columns="4",
                spacing="4"
            ),
            height="500px",
            overflow_y="auto"
        ),
        width="100%",
        spacing="4"
    )


def sidebar() -> rx.Component:
    """Sidebar with configuration"""
    return rx.vstack(
        rx.heading("⚙️ Settings", size="3"),

        # API Status
        rx.vstack(
            rx.heading("🔑 API Status", size="2"),
            rx.hstack(rx.badge("Riot"), rx.badge(rx.cond(TFTState.riot_ok, "OK", "Missing"), color_scheme=rx.cond(TFTState.riot_ok, "green", "red"))),
            rx.hstack(rx.badge("Anthropic"), rx.badge(rx.cond(TFTState.anthropic_ok, "OK", "Missing"), color_scheme=rx.cond(TFTState.anthropic_ok, "green", "red"))),
            rx.hstack(rx.badge("OpenAI"), rx.badge(rx.cond(TFTState.openai_ok, "OK", "Missing"), color_scheme=rx.cond(TFTState.openai_ok, "green", "red"))),
            align_items="start"
        ),

        # Provider Selection
        rx.vstack(
            rx.heading("🤖 LLM Provider", size="2"),
            rx.select(
                ["anthropic", "openai"],
                value=TFTState.selected_provider,
                on_change=TFTState.set_provider
            )
        ),

        width="250px",
        spacing="6",
        p="4",
        bg="gray.50",
        height="100vh"
    )

def top_nav() -> rx.Component:
    """Top navigation bar with branding and quick actions"""
    return rx.hstack(
        rx.hstack(
            rx.text("⚔️"),
            rx.heading("TFT Composition Analyzer", size="3"),
            spacing="3",
            align="center"
        ),
        rx.spacer(),
        # API status chips
        rx.hstack(
            rx.badge("Riot", color_scheme=rx.cond(TFTState.riot_ok, "green", "red")),
            rx.badge("Anthropic", color_scheme=rx.cond(TFTState.anthropic_ok, "green", "red")),
            rx.badge("OpenAI", color_scheme=rx.cond(TFTState.openai_ok, "green", "red")),
            spacing="2"
        ),
        rx.text("Provider:"),
        rx.select(["anthropic", "openai"], value=TFTState.selected_provider, on_change=TFTState.set_provider, size="2"),
        spacing="4",
        px="4",
        py="3",
        border_bottom="1px solid #e2e8f0",
        bg="white",
        width="100%",
        position="sticky",
        top="0",
        z_index="10"
    )


def main_layout() -> rx.Component:
    """Main application layout"""
    return rx.vstack(
        top_nav(),
        rx.hstack(
            sidebar(),
            rx.box(
                rx.container(
                    rx.vstack(
                        rx.center(
                            rx.vstack(
                                rx.heading(
                                    "⚔️ TFT Composition Analyzer",
                                    size="6",
                                ),
                                rx.text(
                                    "AI-powered strategic analysis for Teamfight Tactics Set 15",
                                    size="2"
                                ),
                                spacing="2"
                            ),
                            py="6"
                        ),

                    rx.tabs.root(
                        rx.tabs.list(
                            rx.tabs.trigger("💬 Chat", value="chat"),
                            rx.tabs.trigger("📊 Meta Analysis", value="meta"),
                            rx.tabs.trigger("🗃️ Champions", value="champions"),
                        ),
                        rx.tabs.content(chat_interface(), value="chat"),
                        rx.tabs.content(meta_analysis_interface(), value="meta"),
                        rx.tabs.content(champions_database(), value="champions"),
                        default_value="chat",
                        width="100%"
                    ),
                        rx.divider(),
                        rx.text("Built with Reflex • Powered by your TFT models", size="1"),
                        width="100%",
                        spacing="6"
                    ),
                    max_width="1200px"
                ),
                flex="1",
                p="4"
            ),
            width="100%",
            align_items="start"
        ),
        width="100%"
    )


# Create the main app
app = rx.App(
    style={
        "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    }
)

app.add_page(main_layout, route="/")

if __name__ == "__main__":
    app._compile()
