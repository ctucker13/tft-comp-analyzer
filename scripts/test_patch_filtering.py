#!/usr/bin/env python3
"""
Test script to verify patch 15.3+ filtering is working correctly
"""

import asyncio
import os
import sys
from datetime import datetime

# Add the project root to the path so we can import our modules
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

try:
    from tft_analyzer.data.riot_api import RiotTFTAPI
    from config.settings import Settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

async def test_filtering():
    """Test the new patch filtering functionality"""
    print("=== Testing Patch 15.3+ Filtering ===\n")
    
    # Load settings
    try:
        settings = Settings()
        print(f"✅ Settings loaded successfully")
        print(f"   - require_patch_15_3: {settings.require_patch_15_3}")
        print(f"   - use_24h_filter: {settings.use_24h_filter}")
        print(f"   - current_patch: {settings.current_patch}")
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return
    
    # Initialize Riot API client
    try:
        riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region)
        print(f"✅ Riot API client initialized (region: {settings.riot_region})")
    except Exception as e:
        print(f"❌ Error initializing Riot API: {e}")
        return
    
    print("\n=== Testing API Key Validation ===")
    
    # Test API key validation
    try:
        riot_api.validate_api_key()
        print(f"✅ API key validation passed")
    except ValueError as e:
        print(f"❌ API key validation failed: {e}")
        print(f"Note: This is expected if no valid RIOT_API_KEY is set")
    
    print("\n=== Testing Patch Detection ===")
    
    # Test patch validation function
    test_matches = [
        # Valid match (patch 15.3+, after 2025/08/26)
        {
            "info": {
                "game_version": "Version 15.3.567.1234",
                "game_datetime": int(datetime(2025, 8, 27).timestamp() * 1000),
                "tft_set_number": 15
            }
        },
        # Invalid match (before patch 15.3 date)
        {
            "info": {
                "game_version": "Version 15.2.567.1234", 
                "game_datetime": int(datetime(2025, 8, 20).timestamp() * 1000),
                "tft_set_number": 15
            }
        },
        # Edge case (exact date)
        {
            "info": {
                "game_version": "Version 15.3.567.1234",
                "game_datetime": int(datetime(2025, 8, 26).timestamp() * 1000),
                "tft_set_number": 15
            }
        }
    ]
    
    for i, match_data in enumerate(test_matches, 1):
        info = match_data.get("info", {})
        game_datetime = info.get("game_datetime", 0)
        game_version = info.get("game_version", "")
        
        match_date = datetime.fromtimestamp(game_datetime / 1000) if game_datetime else None
        is_patch_15_3 = riot_api._is_patch_15_3_or_later(match_data)
        is_set_15 = riot_api._is_set15_match(match_data)
        
        print(f"Test match {i}:")
        print(f"   - Date: {match_date.strftime('%Y-%m-%d') if match_date else 'Unknown'}")
        print(f"   - Version: {game_version}")
        print(f"   - Is Set 15: {'✅' if is_set_15 else '❌'}")
        print(f"   - Is Patch 15.3+: {'✅' if is_patch_15_3 else '❌'}")
        print()
    
    print("=== Testing API Integration ===")
    
    # Test connection
    if settings.riot_api_key and not settings.riot_api_key.startswith("your_"):
        print("Testing real API connection...")
        try:
            api_working = await riot_api.test_api_connection()
            if api_working:
                print("✅ API connection successful")
                
                # Test getting challenger players 
                print("Testing challenger player retrieval...")
                players = await riot_api.get_challenger_players()
                print(f"✅ Found {len(players)} challenger players")
                
                if players:
                    # Test match history with 24h filter
                    test_player = players[0]
                    puuid = test_player.get("puuid", "")
                    if puuid:
                        print(f"Testing match history for player (PUUID: {puuid[:20]}...)...")
                        
                        # Test normal match history
                        matches = await riot_api.get_match_history(puuid, count=5)
                        print(f"✅ Normal history: {len(matches)} matches")
                        
                        # Test 24h filtered match history
                        matches_24h = await riot_api.get_match_history(puuid, count=5, hours_back=24)
                        print(f"✅ 24h history: {len(matches_24h)} matches")
                        
                        # Test match details with filtering
                        if matches:
                            match_id = matches[0]
                            print(f"Testing match details for: {match_id}")
                            
                            # Without patch filtering
                            match_details = await riot_api.get_match_details(match_id, require_patch_15_3=False)
                            if match_details:
                                info = match_details.get("info", {})
                                game_version = info.get("game_version", "Unknown")
                                tft_set = info.get("tft_set_number", "Unknown")
                                print(f"✅ Match details (no filter): Set {tft_set}, Version {game_version}")
                            else:
                                print("❌ No match details returned (no filter)")
                            
                            # With patch filtering
                            match_details_filtered = await riot_api.get_match_details(match_id, require_patch_15_3=True)
                            if match_details_filtered:
                                info = match_details_filtered.get("info", {})
                                game_version = info.get("game_version", "Unknown")
                                tft_set = info.get("tft_set_number", "Unknown")
                                print(f"✅ Match details (patch 15.3+ filter): Set {tft_set}, Version {game_version}")
                            else:
                                print("⏭️ Match filtered out (not patch 15.3+)")
                    
            else:
                print("❌ API connection failed")
        except Exception as e:
            print(f"❌ API test error: {e}")
    else:
        print("⏭️ Skipping real API tests (no valid API key)")
    
    print("\n=== Summary ===")
    print("✅ Patch 15.3+ filtering has been implemented with:")
    print("   - Date-based filtering (matches from 2025/08/26 onwards)")
    print("   - Version-based filtering (patch 15.3+)")
    print("   - 24-hour match history option")
    print("   - Configuration options in settings")
    print("   - Riot API only mode (no mock data fallbacks)")
    print(f"   - require_patch_15_3: {settings.require_patch_15_3}")
    print(f"   - use_24h_filter: {settings.use_24h_filter}")
    
    print("\n💡 To enable 24-hour filtering, set USE_24H_FILTER=true in your .env file")
    print("💡 To disable patch 15.3+ filtering, set REQUIRE_PATCH_15_3=false in your .env file")
    print("💡 For LLM testing with mock data, use: python scripts/test_llm_with_mock_data.py")

if __name__ == "__main__":
    asyncio.run(test_filtering())