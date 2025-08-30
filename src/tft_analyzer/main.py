import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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

from config.settings import Settings

async def main():
    print("Starting TFT Set 15 Comp Analyzer...")
    
    try:
        settings = Settings()
        
        # Auto-detect current patch
        patch_detector = TFTPatchDetector()
        current_patch_info = await patch_detector.get_current_patch_info()
        
        # Update settings with detected info
        settings.current_patch = current_patch_info["patch"]
        settings.current_tft_set = current_patch_info["set_number"]
        settings.tft_set_name = current_patch_info["set_name"]
        
        print(f"Using LLM provider: {settings.llm_provider}")
        print(f"Auto-detected: Patch {settings.current_patch}, Set {settings.current_tft_set} ({settings.tft_set_name})")
        print(f"Detection method: {current_patch_info.get('detection_method', 'unknown')}")
        
        # Debug both API keys
        riot_key = settings.riot_api_key
        anthropic_key = settings.anthropic_api_key
        
        print(f"Riot API key loaded: {riot_key[:10]}..." if riot_key else "No API key found!")
        print(f"Riot API key: {'✓ Present' if riot_key and riot_key != 'your_riot_api_key_here' else '✗ Missing/Invalid'}")
        print(f"Anthropic API key: {'✓ Present' if anthropic_key and anthropic_key != 'your_anthropic_key_here' else '✗ Missing/Invalid'}")
        
        # Initialize clients
        model = settings.anthropic_model if settings.llm_provider.value == "anthropic" else settings.openai_model
        llm_client = LLMClient(settings.llm_provider, model)
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region)

        print(f"DEBUG: Settings anthropic_model: {settings.anthropic_model}")
        print(f"DEBUG: Model being passed to LLMClient: {model}")
        
        # Test API connection
        print("\n" + "="*50)
        api_working = await riot_api.test_api_connection()
        
        # If API is working, try to get patch from match data for accuracy
        if api_working:
            match_patch = await patch_detector.get_patch_from_recent_matches(riot_api)
            if match_patch and match_patch != settings.current_patch:
                print(f"🔄 Updated patch from match data: {match_patch}")
                settings.current_patch = match_patch
        
        print(f"API Connection: {'✓ Working' if api_working else '✗ Failed'}")
        print("="*50 + "\n")
        
        # Create and run workflow
        workflow = CompAnalysisWorkflow(llm_client, riot_api, settings)
        
        # Run the workflow with empty initial state
        initial_state = {
            "raw_matches": [],
            "extracted_comps": "",
            "performance_analysis": "",
            "final_report": ""
        }
        
        print(f"Running Set {settings.current_tft_set} analysis workflow for Patch {settings.current_patch}...")
        final_state = await workflow.graph.ainvoke(initial_state)
        
        print(f"\n=== TFT Set {settings.current_tft_set} Meta Analysis Complete ===")
        print(final_state["final_report"])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())