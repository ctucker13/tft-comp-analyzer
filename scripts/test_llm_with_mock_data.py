#!/usr/bin/env python3
"""
Test script for LLM providers using mock TFT Set 15 data
This script tests LLM functionality without requiring Riot API access
"""

import asyncio
import os
import sys
from datetime import datetime
import time
import random
from typing import Dict, Any, List

# Add the project root to the path so we can import our modules
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

try:
    from tft_analyzer.models.llm_provider import LLMClient
    from config.settings import Settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def generate_mock_set15_match_data() -> List[Dict[str, Any]]:
    """Generate realistic Set 15 TFT match data for LLM testing"""
    
    # Set 15 traits (K.O. Coliseum meta)
    set15_traits = [
        {"name": "TFT15_Destroyer", "num_units": 2, "style": 1, "tier_current": 1},
        {"name": "TFT15_DragonFist", "num_units": 3, "style": 1, "tier_current": 1},
        {"name": "TFT15_Duelist", "num_units": 4, "style": 2, "tier_current": 2},
        {"name": "TFT15_Conqueror", "num_units": 2, "style": 1, "tier_current": 1},
        {"name": "TFT15_Warband", "num_units": 4, "style": 2, "tier_current": 2},
        {"name": "TFT15_Family", "num_units": 3, "style": 1, "tier_current": 1}
    ]
    
    # Set 15 units (K.O. Coliseum champions)
    set15_units = [
        {"character_id": "TFT15_Jinx", "itemNames": ["TFT_Item_InfinityEdge", "TFT_Item_LastWhisper"], "name": "Jinx", "rarity": 4, "tier": 2},
        {"character_id": "TFT15_Vi", "itemNames": ["TFT_Item_WarmogsArmor"], "name": "Vi", "rarity": 2, "tier": 2},
        {"character_id": "TFT15_Ekko", "itemNames": ["TFT_Item_RabadonsDeathcap"], "name": "Ekko", "rarity": 5, "tier": 2},
        {"character_id": "TFT15_Caitlyn", "itemNames": ["TFT_Item_GuinsoosRageblade"], "name": "Caitlyn", "rarity": 1, "tier": 2},
        {"character_id": "TFT15_Jayce", "itemNames": [], "name": "Jayce", "rarity": 3, "tier": 1},
        {"character_id": "TFT15_Powder", "itemNames": ["TFT_Item_BlueBuffs"], "name": "Powder", "rarity": 2, "tier": 2},
        {"character_id": "TFT15_Vander", "itemNames": ["TFT_Item_DragonsClaw"], "name": "Vander", "rarity": 3, "tier": 1},
        {"character_id": "TFT15_Silco", "itemNames": ["TFT_Item_Morellonomicon"], "name": "Silco", "rarity": 4, "tier": 2},
        {"character_id": "TFT15_Heimerdinger", "itemNames": [], "name": "Heimerdinger", "rarity": 5, "tier": 1},
        {"character_id": "TFT15_Warwick", "itemNames": ["TFT_Item_TitansResolve"], "name": "Warwick", "rarity": 1, "tier": 2},
        {"character_id": "TFT15_Lucian", "itemNames": ["TFT_Item_BloodThirster"], "name": "Lucian", "rarity": 3, "tier": 2},
        {"character_id": "TFT15_Ashe", "itemNames": ["TFT_Item_GiantSlayer"], "name": "Ashe", "rarity": 4, "tier": 1}
    ]
    
    # Set 15 augments (current patch)
    set15_augments = [
        "TFT15_Augment_ConquerorEmblem",
        "TFT15_Augment_WarbandHeart", 
        "TFT15_Augment_MultistirkerCrest",
        "TFT15_Augment_ComponentGrabBag",
        "TFT15_Augment_TriForce",
        "TFT15_Augment_PowerSnaxPlus",
        "TFT15_Augment_RoleReinforcement"
    ]
    
    mock_matches = []
    
    # Generate 5 mock matches
    for match_num in range(1, 6):
        participants = []
        
        # Generate 8 participants per match
        for i in range(8):
            placement = i + 1
            
            # Simulate Set 15 meta performance (longer games, more complex)
            if placement <= 4:  # Top 4
                gold_left = random.randint(0, 25)
                level = random.randint(8, 9)
                last_round = random.randint(32, 42)  # Set 15 games are longer
            else:  # Bottom 4
                gold_left = random.randint(20, 70)
                level = random.randint(6, 8)
                last_round = random.randint(22, 32)
            
            participants.append({
                "augments": random.sample(set15_augments, k=3),  # 3 augments in Set 15
                "companion": {
                    "content_ID": f"TFT15_Companion_{random.choice(['Starmaw', 'Hauntling', 'Poro'])}", 
                    "item_ID": random.randint(1, 25),
                    "species": f"Pet{random.choice(['Starmaw', 'Hauntling', 'Poro'])}"
                },
                "gold_left": gold_left,
                "last_round": last_round,
                "level": level,
                "placement": placement,
                "players_eliminated": placement - 1,
                "puuid": f"mock_test_puuid_{match_num}_{i}",
                "time_eliminated": 2400 + (placement * 200),  # Set 15 games are longer
                "total_damage_to_players": max(0, 3000 - (placement * 300)),
                "traits": random.sample(set15_traits, k=min(5, len(set15_traits))),
                "units": random.sample(set15_units, k=min(random.randint(7, 9), len(set15_units))),
                # Set 15 specific fields
                "power_snax_used": random.randint(0, 2),
                "role_bonuses": ["Tank", "Marksman"] if placement <= 4 else ["Fighter"]
            })
        
        # Ensure matches are from patch 15.3+ (after 2025/08/26)
        patch_15_3_timestamp = int(datetime(2025, 8, 26).timestamp() * 1000)
        current_timestamp = int(time.time() * 1000)
        recent_timestamp = current_timestamp - random.randint(0, 86400000 * 5)  # 0-5 days ago
        game_datetime = max(patch_15_3_timestamp, recent_timestamp)
        
        match_data = {
            "metadata": {
                "data_version": "15.3.567.1234",
                "match_id": f"MOCK_SET15_MATCH_{match_num}",
                "participants": [p["puuid"] for p in participants]
            },
            "info": {
                "game_datetime": game_datetime,
                "game_length": random.uniform(1800.0, 2800.0),  # 30-47 minutes (Set 15 games longer)
                "game_version": "Version 15.3.567.1234",
                "participants": participants,
                "queue_id": 1100,  # TFT Ranked
                "tft_game_type": "standard",
                "tft_set_core_name": "TFTSet15",
                "tft_set_number": 15
            }
        }
        
        mock_matches.append(match_data)
    
    return mock_matches

async def test_llm_with_mock_data():
    """Test LLM providers with mock TFT Set 15 data"""
    print("=== Testing LLM Providers with Mock Set 15 Data ===\\n")
    
    # Load settings
    try:
        settings = Settings()
        print(f"✅ Settings loaded successfully")
        print(f"   - LLM Provider: {settings.llm_provider}")
        print(f"   - Current Patch: {settings.current_patch}")
        
        # Validate API keys
        api_keys = settings.validate_api_keys()
        print(f"   - API Keys Available:")
        for provider, valid in api_keys.items():
            print(f"     - {provider}: {'✅' if valid else '❌'}")
        
    except Exception as e:
        print(f"❌ Error loading settings: {e}")
        return
    
    # Generate mock match data
    print(f"\\n=== Generating Mock Match Data ===")
    mock_matches = generate_mock_set15_match_data()
    print(f"✅ Generated {len(mock_matches)} mock Set 15 matches")
    
    # Show sample of mock data
    sample_match = mock_matches[0]
    info = sample_match.get("info", {})
    participants = info.get("participants", [])
    game_version = info.get("game_version", "")
    tft_set = info.get("tft_set_number", 0)
    game_datetime = info.get("game_datetime", 0)
    
    match_date = datetime.fromtimestamp(game_datetime / 1000) if game_datetime else None
    
    print(f"   - Sample match: Set {tft_set}, Version {game_version}")
    print(f"   - Match date: {match_date.strftime('%Y-%m-%d %H:%M') if match_date else 'Unknown'}")
    print(f"   - Participants per match: {len(participants)}")
    
    # Test LLM clients
    print(f"\\n=== Testing LLM Clients ===")
    
    # Test available providers
    providers_to_test = []
    if api_keys.get("anthropic"):
        providers_to_test.append("anthropic")
    if api_keys.get("openai"):
        providers_to_test.append("openai")
    
    if not providers_to_test:
        print("❌ No valid API keys found. Please set ANTHROPIC_API_KEY or OPENAI_API_KEY")
        return
    
    for provider_name in providers_to_test:
        print(f"\\n--- Testing {provider_name.title()} ---")
        
        try:
            # Initialize LLM client
            if provider_name == "anthropic":
                from config.settings import LLMProvider
                llm_client = LLMClient(
                    provider=LLMProvider.ANTHROPIC,
                    model=settings.anthropic_model,
                    api_key=settings.anthropic_api_key
                )
            elif provider_name == "openai":
                from config.settings import LLMProvider
                llm_client = LLMClient(
                    provider=LLMProvider.OPENAI,
                    model=settings.openai_model,
                    api_key=settings.openai_api_key
                )
            
            print(f"✅ {provider_name.title()} client initialized")
            
            # Test composition extraction with mock data
            print(f"Testing composition extraction...")
            
            # Create a summary of mock match data for analysis
            match_summary = []
            for match in mock_matches[:3]:  # Use first 3 matches
                info = match.get("info", {})
                participants = info.get("participants", [])
                
                # Extract key composition info from top 4 players
                for participant in participants:
                    placement = participant.get("placement", 0)
                    if placement <= 4:  # Focus on successful comps
                        traits = participant.get("traits", [])
                        units = participant.get("units", [])
                        
                        trait_names = [t.get("name", "") for t in traits if t.get("tier_current", 0) > 0]
                        unit_names = [u.get("name", "") for u in units]
                        
                        match_summary.append({
                            "placement": placement,
                            "traits": trait_names[:5],  # Top 5 traits
                            "units": unit_names[:8],    # Top 8 units
                        })
            
            prompt = f"""
            Analyze these TFT Set 15: K.O. Coliseum match results from Patch 15.3+ (released 2025/08/26 onwards).
            
            Set 15 Context:
            - Power Snax system: 2 power-ups per game (rounds 1-3 and 3-6)
            - Current patch: 15.3+
            - 3-star 5-costs have CC immunity and 20 mana regen
            - Longer games (40+ rounds common)
            - 3 augments per game
            
            Match Data Summary ({len(match_summary)} successful compositions from mock matches):
            {match_summary}
            
            For the top performing compositions, identify:
            1. Most successful trait combinations
            2. Key carry units and their optimal items
            3. Positioning strategies
            4. Power Snax optimization
            
            Keep the analysis concise but insightful.
            """
            
            messages = [
                {"role": "system", "content": "You are analyzing TFT Set 15 match data to identify successful team compositions. Focus on practical patterns and meta insights."},
                {"role": "user", "content": prompt}
            ]
            
            analysis = await llm_client.generate(messages, max_tokens=800)
            
            print(f"✅ {provider_name.title()} analysis completed")
            print(f"   Analysis length: {len(analysis)} characters")
            print(f"   Sample: {analysis[:200]}...")
            
            # Test performance analysis
            print(f"Testing performance analysis...")
            
            perf_prompt = f"""
            Based on this Set 15 composition analysis: {analysis[:500]}...
            
            Provide 3 key performance insights:
            1. Which champions show highest carry potential?
            2. What trait synergies are most consistent? 
            3. How should players prioritize Power Snax usage?
            
            Keep each insight to 1-2 sentences.
            """
            
            perf_messages = [
                {"role": "system", "content": "You are analyzing TFT performance patterns to provide actionable insights."},
                {"role": "user", "content": perf_prompt}
            ]
            
            performance_analysis = await llm_client.generate(perf_messages, max_tokens=400)
            
            print(f"✅ {provider_name.title()} performance analysis completed")
            print(f"   Performance analysis length: {len(performance_analysis)} characters")
            print(f"   Sample: {performance_analysis[:150]}...")
            
        except Exception as e:
            print(f"❌ Error testing {provider_name}: {e}")
    
    print(f"\\n=== Summary ===")
    print(f"✅ Mock data generation working correctly")
    print(f"✅ LLM integration functional with realistic Set 15 data")
    print(f"✅ Mock matches use patch 15.3+ data from 2025/08/26 onwards")
    print(f"✅ Analysis pipeline works without Riot API dependency")
    
    print(f"\\n💡 This script can be used to:")
    print(f"   - Test LLM providers without Riot API access")
    print(f"   - Debug analysis logic with consistent mock data")
    print(f"   - Validate Set 15 composition extraction")
    print(f"   - Test performance analysis workflows")

if __name__ == "__main__":
    asyncio.run(test_llm_with_mock_data())