"""
Mock version of TFT Analyzer for testing without API keys
This version allows mock data for development/demo purposes
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment FIRST
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Mock the API classes to allow mock mode
import src.tft_analyzer.models.llm_provider as llm_module
import src.tft_analyzer.data.riot_api as riot_module

# Backup original functions
original_llm_is_mock = llm_module.LLMClient._is_mock_mode
original_riot_is_mock = riot_module.RiotTFTAPI.is_mock_mode

# Override to allow mock mode
def allow_mock_llm(self):
    return (
        self.client is None or 
        not self.api_key or
        not self._is_valid_api_key(
            self.api_key, 
            "sk-ant-" if self.provider.value == "anthropic" else "sk-"
        )
    )

def allow_mock_riot(self):
    return (not self.api_key or 
            self.api_key == "your_riot_api_key_here" or 
            self.api_key == "" or 
            self._force_mock)

# Apply mock-friendly versions
llm_module.LLMClient._is_mock_mode = allow_mock_llm
riot_module.RiotTFTAPI.is_mock_mode = allow_mock_riot

# Now import the rest normally
from config.settings import Settings
from src.tft_analyzer.models.llm_provider import LLMClient
from src.tft_analyzer.data.riot_api import RiotTFTAPI
from src.tft_analyzer.workflows.comp_analysis_workflow import CompAnalysisWorkflow
from src.tft_analyzer.utils.patch_detector import TFTPatchDetector
from src.tft_analyzer.chat.tft_chat_handler import TFTChatHandler

# Import the main functions from the real app
from streamlit_app import (
    initialize_settings, create_llm_client, run_analysis_with_progress,
    run_analysis, display_composition_native
)

def main():
    """Mock-enabled Streamlit application"""
    st.set_page_config(
        page_title="TFT Comp Analyzer (Mock Mode)",
        page_icon="🎭",
        layout="wide"
    )
    
    st.title("🎭 TFT Set 15: K.O. Coliseum Analyzer (Mock Mode)")
    st.markdown("*Demo version with mock data - for testing without API keys*")
    st.warning("🎭 This is the MOCK VERSION. For real analysis, use the main app with valid API keys.")
    
    # Use the same UI as main app but with mock-friendly APIs
    # ... rest of the UI code would be identical to main app
    
    st.info("Mock mode allows testing without valid API keys. Results will be simulated.")

if __name__ == "__main__":
    main()