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
from src.tft_analyzer.agents.tft_agent import TFTAgent, create_tft_agent


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

        # Interface selection
        st.subheader("🤖 Interface Mode")
        interface_mode = st.radio(
            "Choose interface:",
            ["🧠 Agentic Model (Smart Routing)", "🔧 Legacy ML Interface"],
            index=0,
            help="Agentic model automatically routes questions to appropriate tools"
        )

        st.markdown("---")

        # API Key status
        st.subheader("🔑 API Status")

        riot_key = settings.riot_api_key
        anthropic_key = settings.anthropic_api_key
        openai_key = settings.openai_api_key

        riot_present = riot_key and not riot_key.startswith('your_')
        anthropic_present = anthropic_key and anthropic_key.startswith('sk-ant-')
        openai_present = openai_key and openai_key.startswith('sk-')

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
            elif openai_present:
                st.success("🤖 OpenAI")
            else:
                st.error("🤖 LLM APIs")

        # Provider selection for agentic model
        if interface_mode.startswith("🧠"):
            available_providers = []
            if anthropic_present:
                available_providers.append("anthropic")
            if openai_present:
                available_providers.append("openai")

            if available_providers:
                provider = st.selectbox(
                    "LLM Provider:",
                    available_providers,
                    help="Choose between Anthropic Claude and OpenAI GPT"
                )
                st.session_state.selected_provider = provider
            else:
                st.error("No LLM provider available")
                st.session_state.selected_provider = None

        if not riot_present or (not anthropic_present and not openai_present):
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
        st.subheader("🧠 AI Models")
        if interface_mode.startswith("🧠"):
            st.info("""
            **🤖 Agentic Model**: Intelligent conversation routing
            - Strategic questions → ML analysis
            - Meta questions → Tier lists & comps
            - General chat → Direct response

            **🧠 ML Models**: Game state analysis & meta insights
            **🎯 Tool Selection**: Automatic based on question type
            """)
        else:
            st.info("""
            **Strategic Model**: Game state → recommendations
            **Meta Model**: Composition tier lists & trends

            Both models use cached match data for real-time strategic advice.
            """)

    # Initialize chat interface
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Initialize interfaces based on mode
    use_agentic = interface_mode.startswith("🧠")

    if use_agentic:
        # Initialize agentic model
        if 'tft_agent' not in st.session_state:
            try:
                provider = getattr(st.session_state, 'selected_provider', 'anthropic')
                if provider and getattr(st.session_state, 'selected_provider', None):
                    st.session_state.tft_agent = create_tft_agent(provider=provider)
                else:
                    st.session_state.tft_agent = None
            except Exception as e:
                st.error(f"Failed to initialize TFT agent: {str(e)}")
                st.session_state.tft_agent = None
    else:
        # Initialize legacy ML chat interface
        if 'ml_chat_interface' not in st.session_state:
            try:
                st.session_state.ml_chat_interface = TFTMLChatInterface()
            except Exception as e:
                st.error(f"Failed to initialize ML chat interface: {str(e)}")
                st.session_state.ml_chat_interface = None

    # Main chat interface
    interface_available = (use_agentic and st.session_state.tft_agent) or (not use_agentic and st.session_state.ml_chat_interface)

    if interface_available:
        # Welcome message
        if not st.session_state.chat_history:
            with st.chat_message("assistant"):
                if use_agentic:
                    provider = getattr(st.session_state, 'selected_provider', 'anthropic').title()
                    st.write(f"""
                    🚀 **Welcome to TFT Agentic Strategic Chat!**

                    I'm your intelligent TFT advisor using {provider} + LangGraph with automatic tool routing.

                    **🤖 How I work:**
                    - 🎯 **Strategic questions** → I extract your game state and run ML analysis
                    - 🏆 **Meta questions** → I fetch current tier lists and composition data
                    - 💬 **General chat** → I respond directly with TFT knowledge

                    **Try asking:**
                    - "I'm at 30 gold, level 6, placement 5, what should I do?" (→ ML analysis)
                    - "What are the strongest compositions right now?" (→ Meta analysis)
                    - "Should I pivot from reroll to fast 8?" (→ Strategic analysis)
                    - "I love TFT, but struggling with late game" (→ General advice)
                    """)
                else:
                    has_llm = st.session_state.ml_chat_interface.llm_client is not None
                    llm_feature = "conversational AI + " if has_llm else ""

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

            # Get response based on interface mode
            if use_agentic:
                # Use agentic model
                spinner_text = "🤖 Analyzing with agentic model (classifying intent → routing to tools)..."

                with st.spinner(spinner_text):
                    try:
                        response = st.session_state.tft_agent.process_message(user_input, st.session_state.chat_history)

                        # Add assistant response to history
                        st.session_state.chat_history.append({"role": "assistant", "content": response})

                        # Display response
                        with st.chat_message("assistant"):
                            st.write(response)

                    except Exception as e:
                        error_str = str(e).lower()

                        # Provide user-friendly error messages
                        if 'overload' in error_str or '529' in error_str:
                            error_msg = """🔄 **API Temporarily Overloaded**

The AI service is experiencing high demand right now. I've implemented automatic retry logic, but it's still having trouble.

**What you can do:**
- Try asking your question again in a few moments
- Switch to OpenAI in the sidebar if available
- The system will automatically retry and provide fallback responses when possible

Your question was understood and will work once the service recovers!"""
                        elif 'rate limit' in error_str:
                            error_msg = """⏱️ **Rate Limit Reached**

I've hit the API rate limit. This usually resolves quickly.

**Please try again in 1-2 minutes.** The system will automatically retry with exponential backoff."""
                        elif 'api key' in error_str or 'authentication' in error_str:
                            error_msg = """🔑 **API Key Issue**

There's a problem with the API key configuration. Please check your environment variables."""
                        else:
                            error_msg = f"""⚠️ **Unexpected Error**

I encountered an error: {str(e)}

Try asking your question again, or switch to a different interface mode in the sidebar."""

                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                        with st.chat_message("assistant"):
                            st.warning(error_msg)
            else:
                # Use legacy ML chat interface
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
                        error_str = str(e).lower()

                        # Provide user-friendly error messages
                        if 'overload' in error_str or '529' in error_str:
                            error_msg = """🔄 **API Temporarily Overloaded**

The AI service is experiencing high demand right now. I've implemented automatic retry logic, but it's still having trouble.

**What you can do:**
- Try asking your question again in a few moments
- Switch to OpenAI in the sidebar if available
- The system will automatically retry and provide fallback responses when possible

Your question was understood and will work once the service recovers!"""
                        elif 'rate limit' in error_str:
                            error_msg = """⏱️ **Rate Limit Reached**

I've hit the API rate limit. This usually resolves quickly.

**Please try again in 1-2 minutes.** The system will automatically retry with exponential backoff."""
                        elif 'api key' in error_str or 'authentication' in error_str:
                            error_msg = """🔑 **API Key Issue**

There's a problem with the API key configuration. Please check your environment variables."""
                        else:
                            error_msg = f"""⚠️ **Unexpected Error**

I encountered an error: {str(e)}

Try asking your question again, or switch to a different interface mode in the sidebar."""

                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

                        with st.chat_message("assistant"):
                            st.warning(error_msg)

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
                if use_agentic:
                    st.markdown("**🎯 Strategic Decisions (→ ML analysis)**")
                    strategic_examples = [
                        "I'm at 30 gold, level 6, placement 5, what should I do?",
                        "Should I roll or level up with 25 gold at stage 3-2?",
                        "I have 15 health left, how should I play this out?"
                    ]

                    st.markdown("**🏆 Meta Analysis (→ Tier lists & comps)**")
                    meta_examples = [
                        "What are the strongest compositions right now?",
                        "Is Star Guardian good in the current meta?",
                        "Give me the current tier list"
                    ]

                    st.markdown("**💬 General Chat (→ Direct response)**")
                    chat_examples = [
                        "I love TFT but struggling with late game transitions",
                        "How does the Power Up system work?",
                        "What's your favorite Set 15 feature?"
                    ]

                    all_examples = strategic_examples + meta_examples + chat_examples
                else:
                    all_examples = [
                        "🎯 I'm level 6 with 30 gold and 50 health, what should I do?",
                        "🏆 What are the strongest compositions in the current meta?",
                        "🧠 Should I pivot from reroll to fast 8?",
                        "📈 I'm contested on my comp, what are my options?",
                        "⚡ When should I all-in vs play for top 4?",
                        "🎭 What traits are worth playing this patch?",
                        "💰 How should I manage my economy at stage 4-1?"
                    ]

                for example in all_examples:
                    if st.button(example, key=f"example_{hash(example)}"):
                        # Simulate clicking on the example
                        st.session_state.example_input = example
                        st.rerun()

        # Handle example input
        if hasattr(st.session_state, 'example_input'):
            example = st.session_state.example_input
            del st.session_state.example_input

            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": example})

            # Get response based on interface mode
            if use_agentic:
                spinner_text = "🤖 Analyzing with agentic model..."

                with st.spinner(spinner_text):
                    try:
                        response = st.session_state.tft_agent.process_message(example, st.session_state.chat_history)
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                    except Exception as e:
                        error_msg = f"⚠️ Sorry, I encountered an error: {str(e)}"
                        st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            else:
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
        if use_agentic:
            st.error("⚠️ TFT Agentic model is not available. Please check your LLM API key configuration.")
        else:
            st.error("⚠️ ML Chat interface is not available. Please check your configuration.")

    # Footer
    st.markdown("---")
    st.markdown("*Powered by ML models trained on challenger TFT data and strategic analysis*")


if __name__ == "__main__":
    main()