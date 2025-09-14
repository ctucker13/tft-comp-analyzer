import streamlit as st
import asyncio
import sys
from pathlib import Path
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

# Load environment FIRST
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.models.llm_provider import LLMClient
from src.tft_analyzer.data.riot_api import RiotTFTAPI
from src.tft_analyzer.chat.ml_chat_interface import TFTMLChatInterface


def initialize_settings():
    """Initialize and validate settings"""
    return Settings()




def create_llm_client(settings: Settings) -> LLMClient:
    """Create LLM client with proper API key handling"""
    api_key = settings.get_api_key_for_provider(settings.llm_provider)
    model = settings.get_model_for_provider(settings.llm_provider)

    return LLMClient(
        provider=settings.llm_provider,
        model=model,
        api_key=api_key
    )


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="TFT Strategic Chat",
        page_icon="⚔️",
        layout="wide"
    )

    st.title("⚔️ TFT Strategic Chat Advisor")
    st.markdown("*AI-powered TFT strategy assistant with ML recommendations*")

    # Initialize settings globally
    if 'settings' not in st.session_state:
        st.session_state.settings = initialize_settings()

    settings = st.session_state.settings
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key status
        st.subheader("🔑 API Status")

        riot_key = settings.riot_api_key
        anthropic_key = settings.anthropic_api_key

        riot_present = riot_key and not riot_key.startswith('your_')
        anthropic_present = anthropic_key and anthropic_key.startswith('sk-ant-')

        # Display API status
        col1, col2 = st.columns(2)
        with col1:
            if riot_present:
                st.success("🎮 Riot API")
            else:
                st.error("🎮 Riot API")
        with col2:
            if anthropic_present:
                st.success("🤖 Anthropic")
            else:
                st.error("🤖 Anthropic")

        if not riot_present or not anthropic_present:
            st.info("💡 Missing APIs will use cached/mock data")

        st.markdown("---")

        # Development settings
        st.subheader("🛠️ Dev Settings")

        use_cache = st.checkbox(
            "Use Cached Data",
            value=getattr(settings, 'use_cache', False),
            help="Use cached data to avoid API rate limits"
        )
        settings.use_cache = use_cache

        # Clear cache button
        if use_cache and st.button("🗑️ Clear Cache"):
            cache_dir = Path("cache/riot_api")
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                cache_dir.mkdir(parents=True, exist_ok=True)
                st.success("✅ Cache cleared!")

        st.markdown("---")

        # Model info
        st.subheader("🧠 ML Models")
        st.info("""
        **Strategic Model**: Game state → recommendations
        **Meta Model**: Composition tier lists & trends

        Both models use cached match data for real-time strategic advice.
        """)

    # Initialize chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    if 'ml_chat_interface' not in st.session_state:
        try:
            st.session_state.ml_chat_interface = TFTMLChatInterface()
        except Exception as e:
            st.error(f"Failed to initialize ML chat interface: {str(e)}")
            st.session_state.ml_chat_interface = None

    # Main chat interface
    if st.session_state.ml_chat_interface:
        # Welcome message
        if not st.session_state.chat_history:
            has_llm = st.session_state.ml_chat_interface.llm_client is not None
            llm_feature = "conversational AI + " if has_llm else ""

            with st.chat_message("assistant"):
                st.write(f"""
                🚀 **Welcome to TFT Strategic Chat!**

                I'm your AI-powered TFT advisor using {llm_feature}ML models trained on challenger data.

                **What I can help with:**
                - 🎯 Strategic decisions (when to level, roll, pivot)
                - 🏆 Meta composition analysis and tier lists
                - 🧠 Optimal plays based on your game state
                - 📈 Risk assessment and scenario planning
                - 💬 Natural conversation about TFT strategy

                **Try asking:**
                - "I'm level 6 with 30 gold, what should I do?"
                - "What are the best comps in the current meta?"
                - "Should I pivot from reroll to fast 8?"
                - "I'm struggling in late game, any tips?"
                """)

        # Display chat history
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        user_input = st.chat_input("💬 Ask about TFT strategy, meta comps, or game decisions...")

        if user_input:
            # Add user message to history and display immediately
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            with st.chat_message("user"):
                st.write(user_input)

            # Get response from ML chat interface
            has_llm = st.session_state.ml_chat_interface.llm_client is not None
            spinner_text = "🧠 Analyzing with LLM + ML models..." if has_llm else "🧠 Analyzing with ML models..."

            with st.spinner(spinner_text):
                try:
                    response = st.session_state.ml_chat_interface.process_query(user_input)

                    # Add assistant response to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})

                    # Display response
                    with st.chat_message("assistant"):
                        st.write(response)

                except Exception as e:
                    error_msg = f"⚠️ Sorry, I encountered an error: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                    with st.chat_message("assistant"):
                        st.error(error_msg)

        # Chat controls at bottom
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()

        with col2:
            if st.button("💡 Examples"):
                st.session_state.show_examples = not getattr(st.session_state, 'show_examples', False)
                st.rerun()

        # Show examples if toggled
        if getattr(st.session_state, 'show_examples', False):
            with st.expander("💡 Example Questions", expanded=True):
                examples = [
                    "🎯 I'm level 6 with 30 gold and 50 health, what should I do?",
                    "🏆 What are the strongest compositions in the current meta?",
                    "🧠 Should I pivot from reroll to fast 8?",
                    "📈 I'm contested on my comp, what are my options?",
                    "⚡ When should I all-in vs play for top 4?",
                    "🎭 What traits are worth playing this patch?",
                    "💰 How should I manage my economy at stage 4-1?"
                ]

                for example in examples:
                    if st.button(example, key=f"example_{example[:20]}"):
                        # Simulate clicking on the example
                        st.session_state.example_input = example
                        st.rerun()

        # Handle example input
        if hasattr(st.session_state, 'example_input'):
            example = st.session_state.example_input
            del st.session_state.example_input

            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": example})

            # Get response
            has_llm = st.session_state.ml_chat_interface.llm_client is not None
            spinner_text = "🧠 Analyzing with LLM + ML models..." if has_llm else "🧠 Analyzing with ML models..."

            with st.spinner(spinner_text):
                try:
                    response = st.session_state.ml_chat_interface.process_query(example)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"⚠️ Sorry, I encountered an error: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

            st.rerun()

    else:
        st.error("⚠️ ML Chat interface is not available. Please check your configuration.")

    # Footer
    st.markdown("---")
    st.markdown("*Powered by ML models trained on challenger TFT data and strategic analysis*")


if __name__ == "__main__":
    main()