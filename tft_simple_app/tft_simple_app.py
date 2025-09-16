"""TFT Composition Analyzer - Simplified Premium UI Test"""

import reflex as rx
from typing import List, Dict

# Premium colors
colors = {
    "primary": "#2563eb",
    "primary_light": "#3b82f6",
    "success": "#10b981",
    "gray_50": "#f9fafb",
    "gray_100": "#f3f4f6",
    "gray_800": "#1f2937",
    "gray_900": "#111827"
}

class SimpleState(rx.State):
    current_page: str = "dashboard"

    def set_page(self, page: str):
        self.current_page = page

def simple_nav_button(icon: str, text: str, page: str):
    """Simple navigation button."""
    return rx.button(
        rx.flex(
            rx.text(icon, font_size="1.25rem"),
            rx.text(text, font_weight="600"),
            spacing="3",
            align="center"
        ),
        on_click=lambda: SimpleState.set_page(page),
        variant="ghost",
        color_scheme="blue",
        width="100%",
        justify="start"
    )

def simple_sidebar():
    """Simple sidebar."""
    return rx.box(
        rx.flex(
            rx.box(
                rx.heading("🎮 TFT Analyzer", size="6", weight="bold"),
                rx.text("Premium UI Demo", size="2"),
                background="linear-gradient(135deg, #2563eb, #7c3aed)",
                color="white",
                p="6",
                border_radius="16px",
                mb="6"
            ),
            rx.flex(
                simple_nav_button("🏠", "Dashboard", "dashboard"),
                simple_nav_button("💬", "Chat", "chat"),
                simple_nav_button("📊", "Meta", "meta"),
                direction="column",
                spacing="2"
            ),
            direction="column"
        ),
        width="280px",
        height="100vh",
        background=colors["gray_50"],
        p="6",
        position="fixed",
        left="0",
        top="0"
    )

def simple_dashboard():
    """Simple dashboard."""
    return rx.flex(
        rx.box(
            rx.heading("🚀 Premium TFT Dashboard", size="8", weight="bold"),
            rx.text("JavaScript-quality UI with Reflex", size="4"),
            background="white",
            p="8",
            border_radius="16px",
            style={
                "box_shadow": "0 10px 25px rgba(0,0,0,0.1)",
                "border": "1px solid #e5e7eb"
            },
            mb="6"
        ),
        rx.grid(
            rx.box(
                rx.text("📊", font_size="3rem", mb="4"),
                rx.heading("Meta Status", size="5", weight="bold", mb="2"),
                rx.text("S+ Tier Active", size="3", color=colors["primary"]),
                background="white",
                p="6",
                border_radius="12px",
                style={"box_shadow": "0 4px 6px rgba(0,0,0,0.1)"}
            ),
            rx.box(
                rx.text("🏆", font_size="3rem", mb="4"),
                rx.heading("Win Rate", size="5", weight="bold", mb="2"),
                rx.text("18.2%", size="6", weight="bold", color=colors["success"]),
                background="white",
                p="6",
                border_radius="12px",
                style={"box_shadow": "0 4px 6px rgba(0,0,0,0.1)"}
            ),
            columns="2",
            spacing="6"
        ),
        direction="column",
        p="8",
        width="100%"
    )

def simple_content():
    """Main content area."""
    return rx.box(
        simple_dashboard(),
        margin_left="280px",
        min_height="100vh",
        background="linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)"
    )

def simple_index():
    """Simple main app."""
    return rx.box(
        simple_sidebar(),
        simple_content(),
        width="100%",
        min_height="100vh"
    )

# Create simple app
app = rx.App()
app.add_page(simple_index, route="/")