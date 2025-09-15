#!/usr/bin/env python3
"""
Rate-limited Riot API Test - respects Development API key limits
"""
import asyncio
import aiohttp
import os
import time
from dotenv import load_dotenv

load_dotenv()

async def test_riot_api_with_rate_limits():
    """Test Riot API while respecting rate limits"""
    api_key = os.getenv("RIOT_API_KEY")
    region = os.getenv("RIOT_REGION", "euw1")
    
    if not api_key or api_key == "your_riot_api_key_here":
        print("❌ No valid RIOT_API_KEY found")
        return
    
    headers = {"X-Riot-Token": api_key}
    request_count = 0
    start_time = time.time()
    
    print(f"🚀 Testing Riot API with rate limiting")
    print(f"Region: {region}")
    print(f"API Key: {api_key[:10]}...")
    print("=" * 50)
    
    # Helper function to track requests and wait
    async def make_request_safely(session, url, params=None):
        nonlocal request_count
        request_count += 1
        elapsed = time.time() - start_time
        print(f"   📊 Request #{request_count} (after {elapsed:.1f}s)")
        
        # Wait between requests to avoid rate limits
        if request_count > 1:
            await asyncio.sleep(2)  # 2 second delay between requests
        
        return await session.get(url, headers=headers, params=params)
    
    try:
        async with aiohttp.ClientSession() as session:
            
            # Test 1: Get just ONE challenger player
            print("\n🏆 Test 1: Get Top Challenger Player")
            url = f"https://{region}.api.riotgames.com/tft/league/v1/challenger"
            async with await make_request_safely(session, url) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    entries = data.get("entries", [])
                    print(f"   ✅ Found {len(entries)} players")
                    
                    if entries:
                        top_player = entries[0]
                        summoner_id = top_player.get("summonerId")
                        print(f"   Top: {top_player.get('summonerName')} ({top_player.get('leaguePoints')} LP)")
                        
                        # Test 2: Get summoner details (PUUID)
                        print(f"\n👤 Test 2: Get Summoner PUUID")
                        url = f"https://{region}.api.riotgames.com/tft/summoner/v1/summoners/{summoner_id}"
                        async with await make_request_safely(session, url) as response:
                            print(f"   Status: {response.status}")
                            
                            if response.status == 200:
                                summoner_data = await response.json()
                                puuid = summoner_data.get("puuid", "")
                                print(f"   ✅ PUUID: {puuid[:20]}...")
                                
                                # Test 3: Get match history (just 2 matches)
                                print(f"\n📊 Test 3: Get Recent Matches")
                                url = f"https://europe.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
                                params = {"count": 2}
                                async with await make_request_safely(session, url, params) as response:
                                    print(f"   Status: {response.status}")
                                    
                                    if response.status == 200:
                                        matches = await response.json()
                                        print(f"   ✅ Found {len(matches)} matches")
                                        
                                        if matches:
                                            # Test 4: Get ONE match detail
                                            print(f"\n🎮 Test 4: Get Match Details")
                                            match_id = matches[0]
                                            url = f"https://europe.api.riotgames.com/tft/match/v1/matches/{match_id}"
                                            async with await make_request_safely(session, url) as response:
                                                print(f"   Status: {response.status}")
                                                
                                                if response.status == 200:
                                                    match_data = await response.json()
                                                    info = match_data.get("info", {})
                                                    set_num = info.get("tft_set_number", 0)
                                                    game_version = info.get("game_version", "")
                                                    participants = info.get("participants", [])
                                                    
                                                    print(f"   ✅ SUCCESS! Got match details")
                                                    print(f"   Set: {set_num}")
                                                    print(f"   Version: {game_version}")
                                                    print(f"   Players: {len(participants)}")
                                                    
                                                    if set_num == 15:
                                                        print(f"   🎯 This IS a Set 15 match!")
                                                    else:
                                                        print(f"   ⚠️ This is Set {set_num}, not Set 15")
                                                        
                                                elif response.status == 403:
                                                    print(f"   ❌ Rate limited at match details!")
                                                else:
                                                    text = await response.text()
                                                    print(f"   ❌ Error: {response.status}")
                                                    
                                    elif response.status == 403:
                                        print(f"   ❌ Rate limited at match history!")
                                    else:
                                        text = await response.text()
                                        print(f"   ❌ Error: {response.status}")
                                        
                            elif response.status == 403:
                                print(f"   ❌ Rate limited at summoner lookup!")
                                print(f"   💡 This is where your main app is failing")
                            else:
                                text = await response.text()
                                print(f"   ❌ Error: {response.status}")
                
                elif response.status == 403:
                    print(f"   ❌ Rate limited immediately!")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {response.status}")
                        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    total_time = time.time() - start_time
    print(f"\n📈 Final Summary:")
    print(f"   Total requests: {request_count}")
    print(f"   Total time: {total_time:.1f} seconds")
    print(f"   Average rate: {request_count/total_time:.2f} requests/second")
    print(f"   💡 Development limit: ~1 request/second maximum")

if __name__ == "__main__":
    asyncio.run(test_riot_api_with_rate_limits())