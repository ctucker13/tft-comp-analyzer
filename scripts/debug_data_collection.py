#!/usr/bin/env python3
"""
Debug script to test TFT training data collection.

This script helps diagnose issues with the data collection pipeline
by running it step-by-step with detailed logging.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_collection.log')
    ]
)

async def debug_data_collection():
    """Debug the data collection process step by step."""
    print("=== TFT Training Data Collection Debug ===")

    try:
        # Initialize settings
        print("1. Loading settings...")
        settings = Settings()
        print(f"   Riot API Key: {'*' * (len(settings.riot_api_key) - 4) + settings.riot_api_key[-4:]}")
        print(f"   Riot Region: {settings.riot_region}")

        # Initialize collector
        print("2. Creating data collector...")
        collector = TFTTrainingDataCollector(settings)

        # Test API connection
        print("3. Testing Riot API connection...")
        api_test = await collector.riot_client.test_api_connection()
        print(f"   API Connection: {'✅ SUCCESS' if api_test else '❌ FAILED'}")

        if not api_test:
            print("❌ Cannot proceed without API connection")
            return

        # Get players for each tier
        print("4. Fetching high-tier players...")

        print("   4a. Fetching Challenger players...")
        try:
            challenger_players = await collector.riot_client.get_challenger_players()
            print(f"       Found {len(challenger_players)} challenger players")
            if challenger_players:
                print(f"       Sample: {challenger_players[0]['summonerName']}")
        except Exception as e:
            print(f"       Error: {e}")
            challenger_players = []

        print("   4b. Fetching Master players...")
        try:
            master_players = await collector.riot_client.get_master_players()
            print(f"       Found {len(master_players)} master players")
            if master_players:
                print(f"       Sample: {master_players[0]['summonerName']}")
        except Exception as e:
            print(f"       Error: {e}")
            master_players = []

        all_players = challenger_players + master_players
        print(f"   Total players available: {len(all_players)}")

        if not all_players:
            print("❌ No players found - cannot collect data")
            return

        # Test match history for first player
        print("5. Testing match history collection...")
        test_player = all_players[0]
        print(f"   Testing with player: {test_player['summonerName']} ({test_player['puuid'][:8]}...)")

        try:
            match_ids = await collector.riot_client.get_match_history(
                test_player['puuid'],
                count=5
            )
            print(f"   Found {len(match_ids)} recent matches")

            if match_ids:
                print("   Sample match IDs:")
                for i, match_id in enumerate(match_ids[:3]):
                    print(f"     {i+1}. {match_id}")

                # Test match details
                print("6. Testing match details...")
                test_match = match_ids[0]
                match_details = await collector.riot_client.get_match_details(
                    test_match,
                    require_patch_15_3=True
                )

                if match_details:
                    print(f"   ✅ Match details retrieved for {test_match}")

                    # Check if it's Set 15
                    set_number = match_details.get("info", {}).get("tft_set_number")
                    patch = match_details.get("info", {}).get("game_version", "unknown")
                    print(f"   Set: {set_number}, Patch: {patch}")

                    # Check participants
                    participants = match_details.get("info", {}).get("participants", [])
                    print(f"   Participants: {len(participants)}")

                    # Find our test player
                    test_participant = None
                    for p in participants:
                        if p.get("puuid") == test_player["puuid"]:
                            test_participant = p
                            break

                    if test_participant:
                        print(f"   Player placement: {test_participant.get('placement', 'N/A')}")
                        print(f"   Player level: {test_participant.get('level', 'N/A')}")
                        print(f"   Units: {len(test_participant.get('units', []))}")
                        print(f"   Traits: {len(test_participant.get('traits', []))}")
                    else:
                        print("   ⚠️ Test player not found in match participants")

                else:
                    print("   ❌ Failed to get match details")

        except Exception as e:
            print(f"   Error getting match history: {e}")

        # Test small data collection
        print("7. Testing small data collection (3 matches)...")
        try:
            training_data = await collector.collect_training_data(
                num_matches=3,
                min_rank="MASTER",
                days_back=7
            )

            print(f"   ✅ Collected {len(training_data)} training data points")

            if training_data:
                sample = training_data[0]
                print(f"   Sample data point:")
                print(f"     Match ID: {sample.match_id}")
                print(f"     Placement: {sample.placement}")
                print(f"     Comp Type: {sample.comp_type}")
                print(f"     Features: {len(sample.features)} features")
                print(f"     Round: {sample.round_number}")
            else:
                print("   ⚠️ No training data points collected")

                # Let's debug why
                print("8. Debugging empty collection...")

                # Check match validation
                if match_ids and match_details:
                    is_valid = collector._is_valid_training_match(match_details, 7)
                    print(f"   Match validation result: {is_valid}")

                    if not is_valid:
                        print("   Checking validation criteria:")

                        # Check Set 15
                        set_num = match_details.get("info", {}).get("tft_set_number")
                        print(f"     Set 15 check: {set_num == 15} (found: {set_num})")

                        # Check queue
                        queue_id = match_details.get("info", {}).get("queue_id")
                        print(f"     Ranked queue check: {queue_id == 1100} (found: {queue_id})")

                        # Check date
                        from datetime import datetime, timedelta
                        game_creation = match_details.get("info", {}).get("game_creation", 0)
                        if game_creation:
                            game_date = datetime.fromtimestamp(game_creation / 1000)
                            cutoff_date = datetime.now() - timedelta(days=7)
                            is_recent = game_date >= cutoff_date
                            print(f"     Date check: {is_recent} (game: {game_date}, cutoff: {cutoff_date})")

        except Exception as e:
            print(f"   Error in data collection: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"❌ Script error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_data_collection())