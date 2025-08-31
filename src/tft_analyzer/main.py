import asyncio
import sys
from pathlib import Path
import os
from dotenv import load_dotenv
from config.settings import LLMProvider

# Load environment FIRST
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import settings and modules
from config.settings import Settings

try:
    # Try relative imports first
    from .models.llm_provider import LLMClient
    from .data.riot_api import RiotTFTAPI
    from .workflows.comp_analysis_workflow import CompAnalysisWorkflow
    from .utils.patch_detector import TFTPatchDetector
except ImportError:
    # Fall back to absolute imports
    from src.tft_analyzer.models.llm_provider import LLMClient
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from src.tft_analyzer.workflows.comp_analysis_workflow import CompAnalysisWorkflow
    from src.tft_analyzer.utils.patch_detector import TFTPatchDetector


def initialize_settings():
    """Initialize and validate settings"""
    settings = Settings()
    
    # Debug the configuration
    print("=== SETTINGS DEBUG ===")
    debug_info = settings.debug_info()
    for key, value in debug_info.items():
        print(f"{key}: {value}")
    print("======================\n")
    
    return settings


def create_llm_client(settings: Settings) -> LLMClient:
    """Create LLM client with proper API key handling"""
    api_key = settings.get_api_key_for_provider(settings.llm_provider)
    model = settings.get_model_for_provider(settings.llm_provider)
    
    if not api_key:
        print(f"Warning: No {settings.llm_provider} API key found, will use mock responses")
    
    return LLMClient(
        provider=settings.llm_provider,
        model=model,
        api_key=api_key
    )


async def detect_current_patch(settings: Settings, riot_api: RiotTFTAPI = None) -> dict:
    """Detect current TFT patch using multiple methods"""
    print("🔍 Detecting current TFT patch...")
    
    patch_detector = TFTPatchDetector()
    
    if riot_api:
        # Use comprehensive detection with match data
        current_patch_info = await patch_detector.get_comprehensive_patch_info(riot_api)
    else:
        # Use web-based detection only
        current_patch_info = await patch_detector.get_current_patch_info()
    
    print(f"✅ Detected: Patch {current_patch_info['patch']}, Set {current_patch_info['set_number']} ({current_patch_info['set_name']})")
    print(f"Detection method: {current_patch_info.get('detection_method', 'unknown')}")
    
    return current_patch_info


def update_settings_with_patch_info(settings: Settings, patch_info: dict):
    """Update settings with detected patch information"""
    settings.current_patch = patch_info["patch"]
    settings.current_tft_set = patch_info["set_number"]
    settings.tft_set_name = patch_info["set_name"]


def validate_api_keys(settings: Settings):
    """Validate and report API key status"""
    riot_key = settings.riot_api_key
    anthropic_key = settings.anthropic_api_key
    
    print(f"Riot API key loaded: {riot_key[:10]}..." if riot_key else "No Riot API key found!")
    print(f"Riot API key: {'✓ Present' if riot_key and not riot_key.startswith('your_') else '✗ Missing/Invalid'}")
    print(f"Anthropic API key: {'✓ Present' if anthropic_key and anthropic_key.startswith('sk-ant-') else '✗ Missing/Invalid'}")


async def test_riot_api_connection(riot_api: RiotTFTAPI) -> bool:
    """Test Riot API connection and update patch if needed"""
    print("\n" + "="*50)
    print("Testing API connection...")
    
    api_working = await riot_api.test_api_connection()
    
    print(f"API Connection: {'✓ Working' if api_working else '✗ Failed'}")
    print("="*50 + "\n")
    
    return api_working


async def main():
    """Main application entry point"""
    print("Starting TFT Set 15 Comp Analyzer...")
    
    try:
        # 1. Initialize settings
        settings = initialize_settings()
        
        # 2. Auto-detect current patch (initial detection)
        patch_info = await detect_current_patch(settings)
        update_settings_with_patch_info(settings, patch_info)
        
        # 3. Display configuration
        print(f"Using LLM provider: {settings.llm_provider}")
        print(f"Auto-detected: Patch {settings.current_patch}, Set {settings.current_tft_set} ({settings.tft_set_name})")
        
        # 4. Validate API keys
        validate_api_keys(settings)
        
        print(f"DEBUG: Settings anthropic_model: {settings.anthropic_model}")
        print(f"DEBUG: Model being passed to LLMClient: {settings.get_model_for_provider(settings.llm_provider)}")
        
        # 5. Initialize clients
        llm_client = create_llm_client(settings)
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region)
        
        # 6. Test API connection and refine patch detection
        api_working = await test_riot_api_connection(riot_api)
        
        if api_working:
            # Try to get more accurate patch from match data
            patch_detector = TFTPatchDetector()
            match_patch = await patch_detector.get_patch_from_recent_matches(riot_api)
            if match_patch and match_patch != settings.current_patch:
                print(f"🔄 Updated patch from match data: {match_patch}")
                settings.current_patch = match_patch
        
        # 7. Create and run analysis workflow
        workflow = CompAnalysisWorkflow(llm_client, riot_api, settings)
        
        initial_state = {
            "raw_matches": [],
            "extracted_comps": "",
            "performance_analysis": "",
            "final_report": ""
        }
        
        print(f"Running Set {settings.current_tft_set} analysis workflow for Patch {settings.current_patch}...")
        final_state = await workflow.graph.ainvoke(initial_state)
        
        # 8. Display results
        print(f"\n=== TFT Set {settings.current_tft_set} Meta Analysis Complete ===")
        print(final_state["final_report"])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())