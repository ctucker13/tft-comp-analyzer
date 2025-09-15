#!/usr/bin/env python3
import asyncio
import aiohttp
import os
import json
from dotenv import load_dotenv

load_dotenv()

async def debug_api_structure():
    """Debug the actual structure of API responses"""
    api_key = os.getenv("RIOT_API_KEY")
    headers = {"X-Riot-Token": api_key}
    
    print("🔍 Debugging Riot API Data Structure")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        # Test challenger endpoint and examine structure
        print("📊 Examining Challenger Data Structure...")
        url = "https://euw1.api.riotgames.com/tft/league/v1/challenger"
        
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                data = await response.json()
                
                # Print overall structure
                print(f"✅ Response keys: {list(data.keys())}")
                
                entries = data.get("entries", [])
                if entries:
                    print(f"✅ Found {len(entries)} entries")
                    
                    # Examine first player structure
                    first_player = entries[0]
                    print(f"\n🎯 First Player Structure:")
                    print(json.dumps(first_player, indent=2))
                    
                    # Check for different possible ID fields
                    possible_id_fields = ["summonerId", "id", "playerId", "accountId", "puuid"]
                    print(f"\n🔍 Checking for ID fields:")
                    for field in possible_id_fields:
                        if field in first_player:
                            print(f"   ✅ {field}: {first_player[field]}")
                        else:
                            print(f"   ❌ {field}: not found")
                    
                    # Get the actual summoner ID field
                    summoner_id = None
                    for field in possible_id_fields:
                        if field in first_player:
                            summoner_id = first_player[field]
                            print(f"\n🎯 Using {field} as summoner identifier: {summoner_id}")
                            break
                    
                    if summoner_id:
                        print(f"\nWaiting 5 seconds before next request...")
                        await asyncio.sleep(5)
                        
                        # Test summoner lookup with the correct ID
                        print(f"\n👤 Testing Summoner Lookup with {summoner_id}...")
                        summoner_url = f"https://euw1.api.riotgames.com/tft/summoner/v1/summoners/{summoner_id}"
                        
                        async with session.get(summoner_url, headers=headers) as summoner_response:
                            print(f"Summoner lookup status: {summoner_response.status}")
                            
                            if summoner_response.status == 200:
                                summoner_data = await summoner_response.json()
                                print(f"✅ Summoner data structure:")
                                print(json.dumps(summoner_data, indent=2))
                                
                                puuid = summoner_data.get("puuid")
                                if puuid:
                                    print(f"\n✅ Successfully got PUUID: {puuid}")
                                    print("🎉 Your API is working! The issue is just rate limiting.")
                                else:
                                    print(f"❌ No PUUID in summoner data")
                                    
                            elif summoner_response.status == 403:
                                print("❌ Rate limited on summoner lookup")
                                print("💡 Even with 5-second delay, still rate limited")
                                print("💡 Development keys are VERY restrictive")
                            else:
                                error_text = await summoner_response.text()
                                print(f"❌ Error: {summoner_response.status}")
                                print(f"Response: {error_text[:300]}")
                    
                else:
                    print("❌ Could not find any valid ID field")
                    
            elif response.status == 403:
                print("❌ Rate limited on first request!")
                print("💡 Your API key might be over its daily limit")
            else:
                error_text = await response.text()
                print(f"❌ Error: {response.status}")
                print(f"Response: {error_text}")

if __name__ == "__main__":
    asyncio.run(debug_api_structure())