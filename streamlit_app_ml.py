"""
ML-Powered TFT Strategy Advisor
Streamlit interface for ML-based TFT strategy recommendations
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import os
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
from src.tft_analyzer.agents.ml_strategist import MLStrategistAgent
from src.tft_analyzer.ml.inference.engine import TFTInferenceEngine
from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector
from src.tft_analyzer.ml.training.trainer import TFTModelTrainer


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


@st.cache_resource
def initialize_ml_components(settings: Settings):
    """Initialize ML components with caching"""
    try:
        # Create LLM client
        llm_client = create_llm_client(settings)

        # Create Riot API client
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=True)

        # Initialize ML inference engine (placeholder path)
        model_path = "data/models/strategy_v1"
        if Path(model_path).exists():
            inference_engine = TFTInferenceEngine(model_path)
            ml_available = True
        else:
            inference_engine = None
            ml_available = False

        # Create ML strategist agent
        strategist = MLStrategistAgent(inference_engine, llm_client, riot_api)

        return {
            "llm_client": llm_client,
            "riot_api": riot_api,
            "inference_engine": inference_engine,
            "strategist": strategist,
            "ml_available": ml_available
        }

    except Exception as e:
        st.error(f"Failed to initialize ML components: {e}")
        return None


def main():
    """Main Streamlit application"""
    st.set_page_config(
        page_title="TFT ML Strategy Advisor",
        page_icon="🧠",
        layout="wide"
    )

    st.title("🧠 TFT Set 15: ML-Powered Strategy Advisor")
    st.markdown("*AI-powered strategic analysis with machine learning predictions*")

    # Initialize settings
    if 'settings' not in st.session_state:
        st.session_state.settings = initialize_settings()

    settings = st.session_state.settings

    # Initialize ML components
    if 'ml_components' not in st.session_state:
        st.session_state.ml_components = initialize_ml_components(settings)

    ml_components = st.session_state.ml_components

    if not ml_components:
        st.error("Failed to initialize ML components. Please check your configuration.")
        return

    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Strategy Advisor", "💬 TFT Chat", "🔧 ML Training"])

    # Sidebar for status and configuration
    with st.sidebar:
        st.header("🔧 System Status")

        # ML Model Status
        if ml_components["ml_available"]:
            st.success("✅ ML Model: Ready")
        else:
            st.warning("⚠️ ML Model: Not Available")
            st.info("Train a model first using the ML Training tab")

        # API Status
        llm_provider = settings.llm_provider.title()
        st.info(f"🤖 LLM: {llm_provider}")
        st.info(f"🌍 Region: {settings.riot_region.upper()}")

        st.markdown("---")

        # Model Information
        if ml_components["ml_available"]:
            st.markdown("### 📊 Model Info")
            st.text("Type: Multi-task Strategy Model")
            st.text("Version: 0.1.0")
            st.text("Training Status: Ready")

    with tab1:
        # Strategy Advisor Tab
        st.header("🎯 ML-Powered Strategy Recommendations")

        if not ml_components["ml_available"]:
            st.warning("ML model not available. Please train a model first or use general chat mode.")

        # Game State Input
        st.subheader("📝 Game State Input")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Basic Information**")
            round_num = st.number_input("Round", min_value=1, max_value=50, value=15)
            level = st.number_input("Level", min_value=1, max_value=9, value=6)
            gold = st.number_input("Gold", min_value=0, max_value=100, value=25)
            health = st.number_input("Health", min_value=0, max_value=100, value=60)

        with col2:
            st.markdown("**Streaks & Context**")
            win_streak = st.number_input("Win Streak", min_value=0, max_value=10, value=0)
            loss_streak = st.number_input("Loss Streak", min_value=0, max_value=10, value=0)

            phase = st.selectbox("Game Phase", ["Early", "Mid", "Late"], index=1)

        # Board State (simplified)
        st.subheader("🏟️ Board State")
        board_description = st.text_area(
            "Describe your current board",
            placeholder="e.g., 2-star Jinx with IE and LW, 1-star Vi, 2-star Caitlyn...",
            height=100
        )

        # Get Strategy Button
        if st.button("🧠 Get ML Strategy Recommendation", type="primary", disabled=not ml_components["ml_available"]):
            if ml_components["ml_available"]:
                with st.spinner("Analyzing game state with ML model..."):
                    # Create game state description
                    game_description = f"""
                    Round {round_num}, Level {level}, {gold} gold, {health} health.
                    Win streak: {win_streak}, Loss streak: {loss_streak}.
                    Game phase: {phase}.
                    Board: {board_description if board_description else 'Not specified'}
                    """

                    # Get ML recommendations
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(
                            ml_components["strategist"].handle_strategy_query(
                                f"What should I do? {game_description}"
                            )
                        )

                        if response["type"] == "strategy_recommendation":
                            st.success("🎯 ML Strategy Analysis Complete!")

                            # Display primary recommendation
                            rec = response["primary_recommendation"]
                            confidence = response["confidence"]

                            st.markdown(f"### 🎯 Primary Recommendation: **{rec.title()}**")
                            st.markdown(f"**Confidence:** {confidence:.1%}")

                            # Display scenarios
                            if "scenarios" in response and response["scenarios"]:
                                st.markdown("### 📊 Scenario Analysis")
                                scenarios_df = []
                                for scenario in response["scenarios"][:3]:
                                    scenarios_df.append({
                                        "Strategy": scenario["strategy"],
                                        "Win Rate": f"{scenario['win_probability']:.1%}",
                                        "Expected Placement": f"{scenario['expected_placement']:.1f}",
                                        "Risk Score": f"{scenario['risk_score']:.1f}"
                                    })

                                st.dataframe(scenarios_df, use_container_width=True)

                            # Display explanation
                            st.markdown("### 💡 Strategic Explanation")
                            st.markdown(response["explanation"])

                            # Key insights
                            if response.get("key_insights"):
                                st.markdown("### 🔑 Key Insights")
                                for insight in response["key_insights"]:
                                    st.markdown(f"• {insight}")

                        else:
                            st.info("Received general advice (no ML prediction)")
                            st.markdown(response["explanation"])

                    except Exception as e:
                        st.error(f"Error getting ML recommendation: {e}")

                    finally:
                        loop.close()

    with tab2:
        # TFT Chat Tab
        st.header("💬 Chat with TFT ML Expert")
        st.markdown("*Ask questions about TFT strategy, and I'll use ML predictions when relevant*")

        # Initialize chat history
        if 'ml_chat_history' not in st.session_state:
            st.session_state.ml_chat_history = []

        # Display chat history
        chat_container = st.container(height=400)
        with chat_container:
            for message in st.session_state.ml_chat_history:
                with st.chat_message(message["role"]):
                    st.write(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about TFT strategy, compositions, meta trends..."):
            # Add user message to history
            st.session_state.ml_chat_history.append({"role": "user", "content": prompt})

            # Get response from ML strategist
            with st.spinner("Consulting ML model and TFT knowledge..."):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(
                        ml_components["strategist"].handle_strategy_query(prompt)
                    )

                    # Add assistant response to history
                    response_content = response.get("explanation", "I couldn't process that request.")
                    st.session_state.ml_chat_history.append({"role": "assistant", "content": response_content})

                    # Rerun to show new messages
                    st.rerun()

                except Exception as e:
                    st.error(f"Chat error: {e}")

                finally:
                    loop.close()

        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state.ml_chat_history = []
            st.rerun()

        # Suggested questions
        st.subheader("💡 Suggested Questions")
        suggested = [
            "What's the current meta for Set 15?",
            "When should I fast 8 vs reroll?",
            "How do I know when to pivot my composition?",
            "What are the strongest late-game carries?",
            "How does the Power Snax system affect strategy?"
        ]

        for suggestion in suggested:
            if st.button(suggestion, key=f"suggest_{suggestion[:20]}"):
                st.session_state.ml_chat_history.append({"role": "user", "content": suggestion})
                st.rerun()

    with tab3:
        # ML Training Tab
        st.header("🔧 ML Model Training")
        st.markdown("*Manage ML model training and data collection*")

        # Initialize training session state
        if 'training_status' not in st.session_state:
            st.session_state.training_status = None
        if 'collection_status' not in st.session_state:
            st.session_state.collection_status = None
        if 'training_results' not in st.session_state:
            st.session_state.training_results = None

        # Model Status
        models_dir = Path("models")
        existing_models = []
        if models_dir.exists():
            existing_models = [d for d in models_dir.iterdir() if d.is_dir()]

        if existing_models:
            st.success(f"✅ Found {len(existing_models)} trained model(s)")
            latest_model = max(existing_models, key=os.path.getmtime)
            st.info(f"Latest model: {latest_model.name}")

            # Model details
            config_path = latest_model / "config.json"
            if config_path.exists():
                import json
                with open(config_path, 'r') as f:
                    config = json.load(f)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Features", config.get('feature_count', 'N/A'))
                with col2:
                    st.metric("Placement MSE", f"{config.get('evaluation_metrics', {}).get('placement_mse', 0):.3f}")
                with col3:
                    st.metric("Comp Accuracy", f"{config.get('evaluation_metrics', {}).get('comp_type_accuracy', 0):.1%}")
        else:
            st.warning("⚠️ No trained models found")

        st.subheader("📊 Data Collection")

        col1, col2 = st.columns(2)
        with col1:
            target_matches = st.number_input("Target Matches", min_value=10, max_value=500, value=50)
            min_rank = st.selectbox("Minimum Rank", ["CHALLENGER", "GRANDMASTER", "MASTER"], index=2)
        with col2:
            days_back = st.number_input("Days Back", min_value=1, max_value=14, value=3)

        # Data collection status
        training_data_dir = Path("data/training")
        if training_data_dir.exists():
            training_files = list(training_data_dir.glob("*.json"))
            if training_files:
                st.info(f"📁 {len(training_files)} training data file(s) available")
        else:
            st.warning("No training data found")

        if st.button("🎯 Collect Training Data", key="collect_data"):
            if not ml_components:
                st.error("ML components not initialized. Check your API keys.")
            else:
                st.session_state.collection_status = "running"

                with st.spinner(f"Collecting training data from {min_rank}+ players..."):
                    try:
                        # Create data collector
                        collector = TFTTrainingDataCollector(settings)

                        # Run data collection in event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        training_data = loop.run_until_complete(
                            collector.collect_training_data(
                                num_matches=target_matches,
                                min_rank=min_rank,
                                days_back=days_back
                            )
                        )

                        # Save collected data
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"training_data_{timestamp}"
                        collector.save_training_data(training_data, filename)

                        st.session_state.collection_status = "completed"
                        st.success(f"✅ Collected {len(training_data)} training data points!")
                        st.info(f"Data saved as: {filename}.json")

                        # Show data summary
                        if training_data:
                            st.subheader("📊 Data Summary")

                            # Basic stats
                            placements = [point.placement for point in training_data]
                            comp_types = [point.comp_type for point in training_data]

                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total Samples", len(training_data))
                            with col2:
                                st.metric("Avg Placement", f"{sum(placements)/len(placements):.1f}")
                            with col3:
                                st.metric("Unique Comps", len(set(comp_types)))

                            # Comp type distribution
                            import pandas as pd
                            comp_df = pd.DataFrame({'comp_type': comp_types})
                            st.bar_chart(comp_df['comp_type'].value_counts())

                        loop.close()

                    except Exception as e:
                        st.session_state.collection_status = "error"
                        st.error(f"Data collection failed: {e}")
                        if 'loop' in locals():
                            loop.close()

        st.subheader("🧠 Model Training")

        col1, col2 = st.columns(2)
        with col1:
            epochs = st.number_input("Training Epochs", min_value=10, max_value=500, value=100)
            batch_size = st.selectbox("Batch Size", [16, 32, 64, 128], index=1)
        with col2:
            learning_rate = st.selectbox("Learning Rate", [0.0001, 0.001, 0.01], index=1)
            optimize_hyperparams = st.checkbox("Optimize Hyperparameters", value=True)

        if st.button("🚀 Train New Model", key="train_model"):
            if not ml_components:
                st.error("ML components not initialized. Check your API keys.")
            else:
                st.session_state.training_status = "running"

                with st.spinner("Training ML model... This may take several minutes."):
                    try:
                        # Create trainer
                        trainer = TFTModelTrainer(settings)

                        # Start training in event loop
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)

                        # Generate model name with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        model_name = f"tft_strategy_{timestamp}"

                        training_results = loop.run_until_complete(
                            trainer.train_model(
                                model_name=model_name,
                                epochs=epochs,
                                batch_size=batch_size,
                                learning_rate=learning_rate,
                                optimize_hyperparams=optimize_hyperparams
                            )
                        )

                        st.session_state.training_status = "completed"
                        st.session_state.training_results = training_results

                        st.success("✅ Model training completed!")

                        # Display training results
                        st.subheader("📈 Training Results")

                        col1, col2, col3, col4 = st.columns(4)
                        metrics = training_results['evaluation_metrics']

                        with col1:
                            st.metric("Training Samples", training_results['training_samples'])
                        with col2:
                            st.metric("Test Samples", training_results['test_samples'])
                        with col3:
                            st.metric("Placement MSE", f"{metrics['placement_mse']:.3f}")
                        with col4:
                            st.metric("Comp Accuracy", f"{metrics['comp_type_accuracy']:.1%}")

                        # Show hyperparameters
                        st.subheader("⚙️ Final Hyperparameters")
                        st.json(training_results['hyperparameters'])

                        # Training history chart
                        if 'training_history' in training_results:
                            history = training_results['training_history']
                            if history.get('val_loss'):
                                st.subheader("📊 Training History")

                                import pandas as pd
                                history_df = pd.DataFrame({
                                    'Epoch': range(0, len(history['val_loss']) * 10, 10),
                                    'Validation Loss': history['val_loss'],
                                    'Comp Type Accuracy': history['comp_type_acc']
                                })

                                st.line_chart(history_df.set_index('Epoch')[['Validation Loss']])
                                st.line_chart(history_df.set_index('Epoch')[['Comp Type Accuracy']])

                        st.info(f"Model saved as: {model_name}")
                        st.rerun()  # Refresh to show new model

                        loop.close()

                    except Exception as e:
                        st.session_state.training_status = "error"
                        st.error(f"Model training failed: {e}")
                        if 'loop' in locals():
                            loop.close()

        # Show previous training results if available
        if st.session_state.training_results:
            st.subheader("📋 Last Training Session")
            results = st.session_state.training_results

            col1, col2 = st.columns(2)
            with col1:
                st.write("**Model Name:**", results['model_name'])
                st.write("**Completed:**", results['training_completed'][:19])
            with col2:
                metrics = results['evaluation_metrics']
                st.write("**Placement MSE:**", f"{metrics['placement_mse']:.3f}")
                st.write("**Comp Accuracy:**", f"{metrics['comp_type_accuracy']:.1%}")

        # Data Management
        st.subheader("📁 Data Management")

        if st.button("🧹 Clear Training Data"):
            if training_data_dir.exists():
                import shutil
                shutil.rmtree(training_data_dir)
                st.success("Training data cleared!")
                st.rerun()

        if st.button("🗑️ Clear Models"):
            if models_dir.exists():
                import shutil
                shutil.rmtree(models_dir)
                st.success("All models cleared!")
                st.rerun()

    # Footer
    st.markdown("---")
    st.markdown("*Powered by ML predictions, LangGraph workflows, and LLM analysis of Riot Games API data*")


if __name__ == "__main__":
    main()