"""
Clean Reflex UI for TFT chat (production-ready baseline).

This replaces the previous experimental UI with a minimal, stable chat interface
that integrates with the existing agent (`create_tft_agent`). It uses Reflex
components that are widely available across versions and avoids API-volatile props.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
import sys

import reflex as rx


# Ensure project root is on path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from src.tft_analyzer.agents.tft_agent import create_tft_agent
    from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from config.settings import Settings
except Exception:
    # Fallback to absolute import path
    from tft_analyzer.agents.tft_agent import create_tft_agent  # type: ignore
    try:
        from tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends  # type: ignore
        from config.settings import Settings  # type: ignore
    except Exception:  # pragma: no cover
        get_meta_tier_list = None  # type: ignore
        get_meta_trends = None  # type: ignore
        Settings = None  # type: ignore


class ChatState(rx.State):
    """Global state for the chat UI."""

    messages: list[dict] = []  # {role: 'user'|'assistant', content: str}
    input_text: str = ""
    loading: bool = False
    error: str = ""
    provider: str = "anthropic"
    # Theme & layout
    dark_mode: bool = True
    active_view: str = "chat"  # 'chat' | 'meta'
    # API status
    riot_ok: bool = False
    anthropic_ok: bool = False
    openai_ok: bool = False
    # Meta outputs
    meta_tiers: str = ""
    meta_trends: str = ""
    # Persistence
    _history_file: str = str(PROJECT_ROOT / "cache" / "ui_chat_history.json")
    # UX helpers
    example_prompts: list[str] = [
        "I'm level 6 with 30g and 50 HP — what now?",
        "What are the strongest comps this patch?",
        "Should I pivot or keep rerolling at 4-1?",
        "Give me an item plan for Jinx carry",
    ]

    async def send(self):
        """Send the current input to the agent and append the response."""
        text = (self.input_text or "").strip()
        if not text or self.loading:
            return

        self.loading = True
        self.error = ""
        self.messages.append({"role": "user", "content": text})
        self.input_text = ""

        try:
            # Placeholder assistant message for streaming
            self.messages.append({"role": "assistant", "content": ""})
            idx = len(self.messages) - 1
            response = await asyncio.to_thread(self._ask_agent, text)
            if not isinstance(response, str):
                response = str(response)
            # Simulated streaming: chunk by ~200 chars
            chunk_size = 200
            for i in range(0, len(response), chunk_size):
                self.messages[idx]["content"] = response[: i + chunk_size]
                await asyncio.sleep(0.02)
        except Exception as e:
            self.error = str(e)
            self.messages.append({
                "role": "assistant",
                "content": f"⚠️ Error: {e}\n\nTry again or adjust your configuration."
            })
        finally:
            self.loading = False
            # Save history
            self._save_history()

    def _ask_agent(self, text: str) -> str:
        agent = create_tft_agent(provider=self.provider)
        return agent.process_message(text)

    def clear(self):
        self.messages = []
        self.error = ""
        self._save_history()

    # --- Settings & status ---
    def set_provider_anthropic(self):
        self.provider = "anthropic"

    def set_provider_openai(self):
        self.provider = "openai"

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode

    def set_view_chat(self):
        self.active_view = "chat"

    def set_view_meta(self):
        self.active_view = "meta"

    def refresh_status(self):
        try:
            if Settings is None:
                return
            s = Settings()
            self.riot_ok = bool(getattr(s, "riot_api_key", None)) and not s.riot_api_key.startswith("your_")
            self.anthropic_ok = bool(getattr(s, "anthropic_api_key", None))
            self.openai_ok = bool(getattr(s, "openai_api_key", None))
        except Exception:
            self.riot_ok = self.anthropic_ok = self.openai_ok = False

    # --- Meta loaders ---
    async def load_meta_tiers(self):
        if get_meta_tier_list is None:
            self.meta_tiers = "Meta tier list function not available."
            return
        self.meta_tiers = "Loading tier list..."
        try:
            tiers = await asyncio.to_thread(get_meta_tier_list)
            self.meta_tiers = tiers if isinstance(tiers, str) else str(tiers)
        except Exception as e:
            self.meta_tiers = f"Failed to load tier list: {e}"

    async def load_meta_trends(self):
        if get_meta_trends is None:
            self.meta_trends = "Meta trends function not available."
            return
        self.meta_trends = "Loading trends..."
        try:
            trends = await asyncio.to_thread(get_meta_trends)
            self.meta_trends = trends if isinstance(trends, str) else str(trends)
        except Exception as e:
            self.meta_trends = f"Failed to load trends: {e}"

    # --- Persistence ---
    def _save_history(self):
        try:
            path = Path(self._history_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.messages, f)
        except Exception:
            pass

    def load_history(self):
        try:
            import json
            path = Path(self._history_file)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self.messages = json.load(f)
        except Exception:
            self.messages = []

    def use_example(self, text: str):
        self.input_text = text


def message_bubble(message: dict) -> rx.Component:
    """Render a single chat message as a bubble."""
    is_user = message.get("role") == "user"
    content = message.get("content", "")

    bg_color = rx.cond(
        is_user,
        rx.cond(ChatState.dark_mode, "#1e3a8a", "#eff6ff"),  # blue variant
        rx.cond(ChatState.dark_mode, "#111827", "#f9fafb"),  # gray variant
    )
    text_color = rx.cond(ChatState.dark_mode, "#e5e7eb", "#111827")

    bubble = rx.box(
        rx.cond(
            is_user,
            rx.text(content, color=text_color),
            rx.markdown(content),
        ),
        p="2",
        border_radius="md",
        border=rx.cond(ChatState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"),
        bg=bg_color,
        color=text_color,
        max_width="70%",
        style={"boxShadow": rx.cond(ChatState.dark_mode, "0 2px 10px rgba(0,0,0,0.3)", "0 2px 10px rgba(0,0,0,0.08)")},
    )

    avatar = rx.box(
        rx.text(rx.cond(is_user, "🧑", "🤖"), size="3"),
        width="28px",
        height="28px",
        border_radius="9999px",
        display="flex",
        align_items="center",
        justify_content="center",
        bg=rx.cond(ChatState.dark_mode, "#111827", "#e5e7eb"),
        color=rx.cond(ChatState.dark_mode, "#e5e7eb", "#111827"),
    )

    row_inner = rx.hstack(
        rx.cond(is_user, bubble, rx.hstack(avatar, bubble, gap="2")),
        rx.cond(is_user, avatar, rx.box()),
        gap="2",
    )

    row = rx.hstack(row_inner, width="100%", justify=rx.cond(is_user, "end", "start"))
    return row


def top_nav() -> rx.Component:
    """Gradient top navigation bar with title and quick actions."""
    gradient_light = "linear-gradient(90deg, #06b6d4 0%, #6366f1 100%)"
    gradient_dark = "linear-gradient(90deg, #0b1220 0%, #1f2937 100%)"
    return rx.hstack(
        rx.hstack(
            rx.text("⚔️", size="5", color="#ffffff"),
            rx.heading("TFT Analyzer", size="4", color="#ffffff"),
            gap="2",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button("Chat", size="2", variant=rx.cond(ChatState.active_view=="chat", "solid", "outline"), on_click=ChatState.set_view_chat),
            rx.button("Meta", size="2", variant=rx.cond(ChatState.active_view=="meta", "solid", "outline"), on_click=ChatState.set_view_meta),
            gap="2",
        ),
        rx.hstack(
            rx.button("A", size="2", title="Anthropic", on_click=ChatState.set_provider_anthropic, variant=rx.cond(ChatState.provider=="anthropic", "solid", "outline")),
            rx.button("O", size="2", title="OpenAI", on_click=ChatState.set_provider_openai, variant=rx.cond(ChatState.provider=="openai", "solid", "outline")),
            rx.button(rx.cond(ChatState.dark_mode, "🌙", "☀️"), size="2", on_click=ChatState.toggle_dark),
            gap="2",
        ),
        px="4",
        py="3",
        width="100%",
        style={"background": rx.cond(ChatState.dark_mode, gradient_dark, gradient_light), "borderRadius": "10px"},
    )


def chat_page() -> rx.Component:
    """Main chat page."""
    sidebar = rx.vstack(
        rx.heading("Settings", size="4"),
        rx.hstack(
            rx.text("Provider:"),
            rx.button("Anthropic", size="2", on_click=ChatState.set_provider_anthropic, variant=rx.cond(ChatState.provider=="anthropic", "solid", "outline")),
            rx.button("OpenAI", size="2", on_click=ChatState.set_provider_openai, variant=rx.cond(ChatState.provider=="openai", "solid", "outline")),
        ),
        rx.hstack(
            rx.text("Dark Mode:"),
            rx.button(rx.cond(ChatState.dark_mode, "On", "Off"), size="2", on_click=ChatState.toggle_dark, variant="outline"),
        ),
        rx.hstack(
            rx.text("API Status:"),
            rx.button("Refresh", size="2", on_click=ChatState.refresh_status, variant="outline"),
        ),
        rx.vstack(
            rx.text(rx.cond(ChatState.riot_ok, "Riot: OK", "Riot: Missing"), size="1"),
            rx.text(rx.cond(ChatState.anthropic_ok, "Anthropic: OK", "Anthropic: Missing"), size="1"),
            rx.text(rx.cond(ChatState.openai_ok, "OpenAI: OK", "OpenAI: Missing"), size="1"),
        ),
        rx.divider(),
        rx.heading("Views", size="3"),
        rx.hstack(
            rx.button("Chat", size="2", on_click=ChatState.set_view_chat, variant=rx.cond(ChatState.active_view=="chat", "solid", "outline")),
            rx.button("Meta", size="2", on_click=ChatState.set_view_meta, variant=rx.cond(ChatState.active_view=="meta", "solid", "outline")),
        ),
        rx.divider(),
        rx.heading("History", size="3"),
        rx.hstack(
            rx.button("Load", size="2", on_click=ChatState.load_history, variant="outline"),
            rx.button("Clear", size="2", on_click=ChatState.clear, variant="outline"),
        ),
        width="260px",
        p="4",
        border=rx.cond(ChatState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"),
        border_radius="md",
        bg=rx.cond(ChatState.dark_mode, "#0b1220", "#f8fafc"),
        color=rx.cond(ChatState.dark_mode, "#e5e7eb", "#111827"),
        gap="3",
        align_items="stretch",
        height="calc(100vh - 2rem)",
    )

    # Chat content
    messages_panel = rx.box(
        rx.foreach(ChatState.messages, message_bubble),
        height="60vh",
        overflow_y="auto",
        border=rx.cond(ChatState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"),
        border_radius="md",
        p="4",
        width="100%",
        style={"background": rx.cond(ChatState.dark_mode, "#0e1525", "#ffffff"), "boxShadow": rx.cond(ChatState.dark_mode, "0 4px 18px rgba(0,0,0,0.35)", "0 8px 24px rgba(0,0,0,0.08)")},
    )

    input_row = rx.hstack(
        rx.input(
            value=ChatState.input_text,
            on_change=ChatState.set_input_text,
            placeholder="Ask about TFT strategy, comps, or meta...",
            width="100%",
        ),
        rx.button(
            "Send",
            on_click=ChatState.send,
            is_disabled=ChatState.loading,
            loading=ChatState.loading,
            size="2",
        ),
        width="100%",
    )

    examples_row = rx.flex(
        rx.foreach(
            ChatState.example_prompts,
            lambda ex: rx.button(ex, size="2", variant="outline", on_click=lambda ex=ex: ChatState.use_example(ex)),
        ),
        wrap="wrap",
        gap="2",
        width="100%",
    )

    chat_view = rx.vstack(
        top_nav(),
        rx.hstack(
            rx.heading("TFT Strategic Chat", size="5"), rx.spacer(),
            rx.button("Clear", size="2", on_click=ChatState.clear, variant="outline"),
            width="100%",
        ),
        messages_panel,
        rx.cond(ChatState.loading, rx.hstack(rx.text("Assistant is typing"), rx.text("…"), gap="1")),
        rx.cond(
            ChatState.error != "",
            rx.box(
                rx.text(ChatState.error),
                border="1px solid #fecaca",
                border_radius="md",
                p="3",
                width="100%",
            ),
        ),
        examples_row,
        input_row,
        gap="3",
        width="min(1100px, 95vw)",
    )

    # Meta view
    meta_view = rx.vstack(
        rx.hstack(
            rx.heading("Meta Analysis", size="5"),
            rx.spacer(),
            rx.button("Load Tiers", size="2", on_click=ChatState.load_meta_tiers, variant="outline"),
            rx.button("Load Trends", size="2", on_click=ChatState.load_meta_trends, variant="outline"),
            width="100%",
        ),
        rx.hstack(
            rx.box(rx.markdown(ChatState.meta_tiers), p="4", border_radius="md", border=rx.cond(ChatState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"), width="50%", min_height="50vh", overflow_y="auto"),
            rx.box(rx.markdown(ChatState.meta_trends), p="4", border_radius="md", border=rx.cond(ChatState.dark_mode, "1px solid #374151", "1px solid #e5e7eb"), width="50%", min_height="50vh", overflow_y="auto"),
            width="100%",
        ),
        gap="3",
        width="min(1100px, 95vw)",
    )

    main_panel = rx.cond(ChatState.active_view=="chat", chat_view, meta_view)

    return rx.hstack(
        sidebar,
        rx.center(
            rx.vstack(
                main_panel,
                rx.text("Built with Reflex • Powered by your TFT agent", size="1"),
                gap="3",
                width="100%",
            ),
            min_height="100vh",
            padding="5",
            width="100%",
            bg=rx.cond(ChatState.dark_mode, "#0b1220", "#ffffff"),
            color=rx.cond(ChatState.dark_mode, "#e5e7eb", "#111827"),
            style={"backgroundImage": rx.cond(ChatState.dark_mode, "radial-gradient(1000px 400px at 10% 0%, rgba(99,102,241,0.12), transparent 60%)", "radial-gradient(1000px 400px at 10% 0%, rgba(99,102,241,0.06), transparent 60%)")},
        ),
        gap="4",
        align_items="start",
        width="100%",
    )


app = rx.App()
app.add_page(chat_page, route="/", title="TFT Chat")
