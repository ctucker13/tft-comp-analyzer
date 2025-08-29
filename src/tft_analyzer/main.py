import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from .models.llm_provider import LLMClient
from .data.riot_api import RiotTFTAPI
from .workflows.comp_analysis_workflow import CompAnalysisWorkflow

async def main():
    print("Starting TFT Comp Analyzer...")
    
    try:
        settings = Settings()
        print(f"Using LLM provider: {settings.llm_provider}")
        
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
        
        # Test API connection
        print("\n" + "="*50)
        api_working = await riot_api.test_api_connection()
        print(f"API Connection: {'✓ Working' if api_working else '✗ Failed'}")
        print("="*50 + "\n")
        
        # Create and run workflow
        workflow = CompAnalysisWorkflow(llm_client, riot_api)
        
        # Run the workflow with empty initial state
        initial_state = {
            "raw_matches": [],
            "extracted_comps": "",
            "performance_analysis": "",
            "final_report": ""
        }
        
        print("Running analysis workflow...")
        final_state = await workflow.graph.ainvoke(initial_state)
        
        print("\n=== TFT Meta Analysis Complete ===")
        print(final_state["final_report"])
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())