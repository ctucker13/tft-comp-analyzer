# test_slow_api.py
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_very_slow():
    api_key = os.getenv("RIOT_API_KEY")
    headers = {"X-Riot-Token": api_key}
    
    async with aiohttp.ClientSession() as session:
        # Request 1
        print("Request 1: Challenger data...")
        async with session.get(f"https://euw1.api.riotgames.com/tft/league/v1/challenger", headers=headers) as r:
            print(f"Status: {r.status}")
            if r.status == 200:
                data = await r.json()
                summoner_id = data["entries"][0]["summonerId"]
                print(f"Got summoner ID: {summoner_id}")
        
        print("Waiting 5 seconds...")
        await asyncio.sleep(5)
        
        # Request 2
        print("Request 2: Summoner details...")
        async with session.get(f"https://euw1.api.riotgames.com/tft/summoner/v1/summoners/{summoner_id}", headers=headers) as r:
            print(f"Status: {r.status}")
            if r.status == 200:
                print("✅ Success! No rate limiting with 5-second delay")
            elif r.status == 403:
                print("❌ Still rate limited even with 5-second delay")

if __name__ == "__main__":
    asyncio.run(test_very_slow())