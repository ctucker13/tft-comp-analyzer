#!/usr/bin/env python3
"""
Script to find the earliest Set 15 match in the Riot API.
This will help determine when Set 15 actually launched vs patch 15.3.
"""

import asyncio
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from config.settings import Settings
except ImportError:
    from tft_analyzer.data.riot_api import RiotTFTAPI
    from tft_analyzer.config.settings import Settings

async def main():
    print("🔍 Finding earliest Set 15 match...")
    
    # Load settings
    settings = Settings()
    
    # Validate API key
    if not settings.riot_api_key or settings.riot_api_key.startswith("your_"):
        print("✗ No valid Riot API key found. Please check your .env file.")
        return
    
    # Create API client
    riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region)
    
    try:
        # Find earliest Set 15 match
        earliest_match = await riot_api.find_earliest_set15_match()
        
        if earliest_match:
            print("\n🎉 Found earliest Set 15 match:")
            print(f"  Match ID: {earliest_match['match_id']}")
            print(f"  Date: {earliest_match['date']}")
            print(f"  Game Version: {earliest_match['game_version']}")
            print(f"  Set Number: {earliest_match['set_number']}")
            print(f"  Timestamp: {earliest_match['timestamp']}")
            
            # Compare to patch 15.3 release date
            from datetime import datetime
            patch_15_3_release = datetime(2025, 8, 26)
            match_datetime = datetime.fromtimestamp(earliest_match['timestamp'] / 1000)
            
            print(f"\n📊 Analysis:")
            print(f"  Earliest Set 15 match: {match_datetime.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Patch 15.3 release: {patch_15_3_release.strftime('%Y-%m-%d')}")
            
            if match_datetime < patch_15_3_release:
                days_before = (patch_15_3_release - match_datetime).days
                print(f"  ⚠️  Set 15 launched {days_before} days BEFORE patch 15.3")
                print(f"  💡 Consider adjusting patch filter to include earlier Set 15 matches")
            else:
                print(f"  ✅ Set 15 match aligns with patch 15.3+ filter")
        else:
            print("✗ No Set 15 matches found")
            
    except Exception as e:
        print(f"✗ Error during search: {e}")

if __name__ == "__main__":
    asyncio.run(main())