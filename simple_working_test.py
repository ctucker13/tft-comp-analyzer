#!/usr/bin/env python3
"""
Simple test using PUUID directly from challenger data
This avoids the rate limiting issue entirely
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_direct_puuid_approach():
    """Test using PUUID directly from challenger data"""
    api_key = os.getenv("RIOT_API_KEY")
    headers = {"X-Riot-Token": api_key}
    
    print("🚀 Testing Direct PUUID Approach (No Rate Limit Issues)")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        
        # Step 1: Get challenger data (includes PUUID directly)
        print("🏆 Step 1: Get Challenger Data with PUUIDs")
        url = "https://euw1.api.riotgames.com/tft/league/v1/challenger"
        
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                entries = data.get("entries", [])
                print(f"✅ Found {len(entries)} players with direct PUUIDs")
                
                # Get top player's PUUID directly
                top_player = entries[0]
                puuid = top_player.get("puuid")
                lp = top_player.get("leaguePoints")
                wins = top_player.get("wins", 0)
                losses = top_player.get("losses", 0)
                
                print(f"Top Player: {lp} LP ({wins}W/{losses}L)")
                print(f"PUUID: {puuid[:30]}...")
                
                # Wait before next request
                print("\n⏳ Waiting 10 seconds to be extra safe...")
                await asyncio.sleep(10)
                
                # Step 2: Get match history directly (skip summoner lookup!)
                print("📊 Step 2: Get Match History (Direct PUUID)")
                url = f"https://europe.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
                params = {"count": 3}
                
                async with session.get(url, headers=headers, params=params) as response:
                    print(f"Status: {response.status}")
                    
                    if response.status == 200:
                        matches = await response.json()
                        print(f"✅ SUCCESS! Found {len(matches)} recent matches")
                        
                        for i, match_id in enumerate(matches, 1):
                            print(f"  Match {i}: {match_id}")
                        
                        if matches:
                            print("\n⏳ Waiting 10 seconds before match details...")
                            await asyncio.sleep(10)
                            
                            # Step 3: Get details for first match
                            print("🎮 Step 3: Get Match Details")
                            match_id = matches[0]
                            url = f"https://europe.api.riotgames.com/tft/match/v1/matches/{match_id}"
                            
                            async with session.get(url, headers=headers) as response:
                                print(f"Status: {response.status}")
                                
                                if response.status == 200:
                                    match_data = await response.json()
                                    info = match_data.get("info", {})
                                    
                                    set_num = info.get("tft_set_number", 0)
                                    game_version = info.get("game_version", "")
                                    game_length = info.get("game_length", 0)
                                    participants = info.get("participants", [])
                                    
                                    print(f"✅ COMPLETE SUCCESS!")
                                    print(f"   Set Number: {set_num}")
                                    print(f"   Game Version: {game_version}")
                                    print(f"   Game Length: {game_length:.1f}s")
                                    print(f"   Participants: {len(participants)}")
                                    
                                    if set_num == 15:
                                        print(f"   🎯 This IS a Set 15 match!")
                                        
                                        # Show some composition data
                                        winner = next((p for p in participants if p.get("placement") == 1), None)
                                        if winner:
                                            traits = winner.get("traits", [])
                                            units = winner.get("units", [])
                                            print(f"   Winner: {len(traits)} traits, {len(units)} units")
                                            
                                            if traits:
                                                trait_names = [t.get("name") for t in traits[:3]]
                                                print(f"   Top traits: {', '.join(trait_names)}")
                                    else:
                                        print(f"   ⚠️ This is Set {set_num}, not current Set 15")
                                        
                                elif response.status == 403:
                                    print(f"   ❌ Rate limited at match details")
                                else:
                                    text = await response.text()
                                    print(f"   ❌ Match details error: {response.status}")
                                    
                    elif response.status == 403:
                        print(f"   ❌ Rate limited at match history")
                        print(f"   💡 Even with 10-second delay, still rate limited")
                        print(f"   💡 Your Development API key may be at its daily limit")
                    else:
                        text = await response.text()
                        print(f"   ❌ Match history error: {response.status}")
                        
            else:
                text = await response.text()
                print(f"❌ Challenger data error: {response.status}")
                print(f"Response: {text[:200]}")
                
    print(f"\n🎯 Key Insight: Challenger data includes PUUID directly!")
    print(f"💡 No need for summoner lookup step - this cuts API calls in half!")
    print(f"🔧 Update your workflow to use puuid directly from challenger data")

if __name__ == "__main__":
    asyncio.run(test_direct_puuid_approach())