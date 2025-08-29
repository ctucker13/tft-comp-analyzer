import aiohttp
import asyncio
from typing import List, Dict, Any
import json

class RiotTFTAPI:
    def __init__(self, api_key: str, region: str = "euw1"):
        self.api_key = api_key
        self.region = region  # Platform ID (euw1, eun1, etc.)
        self.base_url = f"https://{region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": self.api_key}
        self._force_mock = False
        
        # Map platform to regional cluster for match data
        self.regional_cluster = self._get_regional_cluster(region)
    
    def _get_regional_cluster(self, platform: str) -> str:
        """Map platform ID to regional cluster for match data"""
        europe_platforms = ["euw1", "eun1", "tr1", "ru1"]
        americas_platforms = ["na1", "br1", "la1", "la2", "oc1"]
        asia_platforms = ["kr", "jp1", "ph2", "sg2", "th2", "tw2", "vn2"]
        
        if platform in europe_platforms:
            return "europe"
        elif platform in americas_platforms:
            return "americas"
        elif platform in asia_platforms:
            return "asia"
        else:
            return "americas"  # Default fallback
    
    def is_mock_mode(self) -> bool:
        """Check if we should use mock data"""
        return (not self.api_key or 
                self.api_key == "your_riot_api_key_here" or 
                self.api_key == "" or 
                self._force_mock)
    
    async def test_api_connection(self) -> bool:
        """Test if the API key and connection are working"""
        print("Testing API connection...")
        
        if self.is_mock_mode():
            print("In mock mode - skipping API test")
            return False
        
        # Simple test endpoint - TFT status
        url = f"{self.base_url}/tft/status/v1/platform-data"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"API test response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ API is working! Platform: {data.get('name', 'Unknown')}")
                        print(f"  Region: {self.region}")
                        print(f"  Regional cluster: {self.regional_cluster}")
                        return True
                    elif response.status == 401:
                        print("✗ API Error: 401 Unauthorized - Invalid API key")
                    elif response.status == 403:
                        print("✗ API Error: 403 Forbidden - API key expired or rate limited")
                        print("  Tip: Development keys expire every 24 hours")
                    elif response.status == 404:
                        print("✗ API Error: 404 Not Found - Check your region setting")
                    else:
                        print(f"✗ API Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                    
                    return False
                    
        except Exception as e:
            print(f"✗ API connection test failed: {e}")
            return False
    
    def _get_mock_challenger_players(self) -> List[Dict]:
        """Return mock challenger data"""
        return [
            {
                "summonerId": "mock_player_1_encrypted_id", 
                "summonerName": "EUWChallenger1", 
                "leaguePoints": 1200,
                "rank": "I",
                "wins": 45,
                "losses": 25
            },
            {
                "summonerId": "mock_player_2_encrypted_id", 
                "summonerName": "EUWChallenger2", 
                "leaguePoints": 1150,
                "rank": "I", 
                "wins": 42,
                "losses": 28
            },
            {
                "summonerId": "mock_player_3_encrypted_id", 
                "summonerName": "EUWChallenger3", 
                "leaguePoints": 1100,
                "rank": "I",
                "wins": 40,
                "losses": 30
            }
        ]
    
    async def get_challenger_players(self) -> List[Dict]:
        """Get top players for high-quality data"""
        if self.is_mock_mode():
            print("Using mock challenger player data...")
            return self._get_mock_challenger_players()
        
        # Real API call using platform routing
        url = f"{self.base_url}/tft/league/v1/challenger"
        print(f"Fetching challenger data from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Challenger API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        entries = data.get("entries", [])
                        print(f"✓ Found {len(entries)} challenger players")
                        return entries
                    elif response.status == 401:
                        print("✗ 401 Unauthorized - Invalid API key, falling back to mock data")
                        return self._get_mock_challenger_players()
                    elif response.status == 403:
                        print("✗ 403 Forbidden - Rate limited or expired key, falling back to mock data")
                        return self._get_mock_challenger_players()
                    else:
                        print(f"✗ API Error: {response.status} - falling back to mock data")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        return self._get_mock_challenger_players()
                        
        except Exception as e:
            print(f"✗ Error fetching challenger players: {e} - falling back to mock data")
            return self._get_mock_challenger_players()
    
    async def get_summoner_by_id(self, summoner_id: str) -> Dict[str, Any]:
        """Get summoner details including PUUID from summonerId"""
        if self.is_mock_mode() or summoner_id.startswith("mock_"):
            mock_puuid = f"mock_puuid_{summoner_id.replace('mock_player_', '').replace('_encrypted_id', '')}"
            print(f"Using mock PUUID: {mock_puuid}")
            return {
                "puuid": mock_puuid,
                "name": f"EUWMockSummoner_{summoner_id[-1:]}"
            }
        
        # Use platform routing for summoner data (euw1, not europe)
        url = f"{self.base_url}/tft/summoner/v1/summoners/{summoner_id}"
        print(f"Getting summoner data from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Summoner API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        puuid = data.get("puuid", "")
                        print(f"✓ Got PUUID: {puuid[:20]}..." if puuid else "✗ No PUUID in response")
                        return data
                    elif response.status == 401:
                        print("✗ 401 Unauthorized - using mock data")
                        return {"puuid": f"mock_puuid_{summoner_id}"}
                    elif response.status == 403:
                        print("✗ 403 Forbidden - using mock data")  
                        return {"puuid": f"mock_puuid_{summoner_id}"}
                    else:
                        print(f"✗ Summoner API Error: {response.status} - using mock data")
                        return {"puuid": f"mock_puuid_{summoner_id}"}
                        
        except Exception as e:
            print(f"✗ Error fetching summoner: {e}")
            return {"puuid": f"mock_puuid_{summoner_id}"}
    
    async def get_match_history(self, puuid: str, count: int = 20) -> List[str]:
        """Get recent match IDs"""
        if not puuid:
            print("✗ No PUUID provided")
            return []
        
        if self.is_mock_mode() or puuid.startswith("mock_"):
            base_id = puuid.replace("mock_puuid_", "")
            mock_matches = [f"EUW1_mock_match_{base_id}_{i}" for i in range(1, min(count + 1, 6))]
            print(f"Using mock match history: {mock_matches}")
            return mock_matches
        
        # Use regional cluster for match data (EUROPE for European platforms)
        url = f"https://{self.regional_cluster}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"count": count}
        print(f"Getting match history from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    print(f"Match history API response status: {response.status}")
                    
                    if response.status == 200:
                        matches = await response.json()
                        print(f"✓ Found {len(matches)} matches")
                        return matches
                    elif response.status == 401:
                        print("✗ 401 Unauthorized - using mock matches")
                        return [f"EUW1_mock_match_1_{i}" for i in range(1, 4)]
                    elif response.status == 403:
                        print("✗ 403 Forbidden - using mock matches")
                        return [f"EUW1_mock_match_1_{i}" for i in range(1, 4)]
                    else:
                        print(f"✗ Match history API Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        return [f"EUW1_mock_match_1_{i}" for i in range(1, 4)]
                        
        except Exception as e:
            print(f"✗ Error fetching match history: {e}")
            return []
    
    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Get detailed match data"""
        if not match_id:
            print("✗ No match ID provided")
            return {}
        
        if self.is_mock_mode() or match_id.startswith("EUW1_mock_"):
            print(f"Using mock match details for: {match_id}")
            return self._generate_mock_match_details(match_id)
        
        # Use regional cluster for match data
        url = f"https://{self.regional_cluster}.api.riotgames.com/tft/match/v1/matches/{match_id}"
        print(f"Getting match details from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Match details API response status: {response.status}")
                    
                    if response.status == 200:
                        match_data = await response.json()
                        participants_count = len(match_data.get("info", {}).get("participants", []))
                        print(f"✓ Got match details with {participants_count} participants")
                        return match_data
                    elif response.status == 401:
                        print("✗ 401 Unauthorized - using mock match details")
                        return self._generate_mock_match_details(f"mock_{match_id}")
                    elif response.status == 403:
                        print("✗ 403 Forbidden - using mock match details")
                        return self._generate_mock_match_details(f"mock_{match_id}")
                    else:
                        print(f"✗ Match details API Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        return self._generate_mock_match_details(f"mock_{match_id}")
                        
        except Exception as e:
            print(f"✗ Error fetching match details: {e}")
            return self._generate_mock_match_details(match_id)
    
    def _generate_mock_match_details(self, match_id: str) -> Dict[str, Any]:
        """Generate realistic mock TFT match data"""
        import random
        
        # Mock TFT traits and units (expanded to avoid sample errors)
        mock_traits = [
            {"name": "Invoker", "num_units": 2, "style": 1, "tier_current": 1},
            {"name": "Scrap", "num_units": 4, "style": 2, "tier_current": 2},
            {"name": "Challenger", "num_units": 3, "style": 1, "tier_current": 1},
            {"name": "Bodyguard", "num_units": 2, "style": 1, "tier_current": 1},
            {"name": "Scholar", "num_units": 2, "style": 1, "tier_current": 1},
            {"name": "Assassin", "num_units": 3, "style": 1, "tier_current": 1},
            {"name": "Syndicate", "num_units": 3, "style": 1, "tier_current": 1},
            {"name": "Enchanter", "num_units": 2, "style": 1, "tier_current": 1}
        ]
        
        mock_units = [
            {"character_id": "TFT7_Jinx", "itemNames": ["TFT_Item_InfinityEdge"], "name": "Jinx", "rarity": 4, "tier": 2},
            {"character_id": "TFT7_Vi", "itemNames": ["TFT_Item_WarmogsArmor"], "name": "Vi", "rarity": 2, "tier": 2},
            {"character_id": "TFT7_Ezreal", "itemNames": [], "name": "Ezreal", "rarity": 1, "tier": 2},
            {"character_id": "TFT7_Blitzcrank", "itemNames": [], "name": "Blitzcrank", "rarity": 2, "tier": 1},
            {"character_id": "TFT7_Viktor", "itemNames": ["TFT_Item_RabadonsDeathcap"], "name": "Viktor", "rarity": 4, "tier": 2},
            {"character_id": "TFT7_Jayce", "itemNames": [], "name": "Jayce", "rarity": 3, "tier": 1},
            {"character_id": "TFT7_Caitlyn", "itemNames": ["TFT_Item_LastWhisper"], "name": "Caitlyn", "rarity": 1, "tier": 1},
            {"character_id": "TFT7_Darius", "itemNames": ["TFT_Item_WarmogsArmor"], "name": "Darius", "rarity": 1, "tier": 2},
        ]
        
        # Generate 8 participants with varying placements
        participants = []
        for i in range(8):
            placement = i + 1
            # Better comps = better placement simulation
            if placement <= 4:  # Top 4
                gold_left = random.randint(0, 15)
                level = random.randint(7, 9)
                last_round = random.randint(25, 35)
            else:  # Bottom 4
                gold_left = random.randint(20, 50)
                level = random.randint(5, 7)
                last_round = random.randint(15, 25)
            
            participants.append({
                "augments": ["TFT7_Augment_ScrapHeap", "TFT7_Augment_CyberneticImplants"],
                "companion": {"content_ID": "TFT7_Companion_Pengu", "item_ID": 1, "species": "PetLLTurtle"},
                "gold_left": gold_left,
                "last_round": last_round,
                "level": level,
                "placement": placement,
                "players_eliminated": placement - 1,
                "puuid": f"mock_puuid_euw_{i}",
                "time_eliminated": 1800 + (placement * 100),
                "total_damage_to_players": max(0, 2000 - (placement * 200)),
                "traits": random.sample(mock_traits, k=min(4, len(mock_traits))),
                "units": random.sample(mock_units, k=min(random.randint(5, 7), len(mock_units)))
            })
        
        return {
            "metadata": {
                "data_version": "7",
                "match_id": match_id,
                "participants": [p["puuid"] for p in participants]
            },
            "info": {
                "game_datetime": 1650000000000,
                "game_length": 1800.0 + random.randint(-300, 300),
                "game_version": "Version 14.15.567.1234",
                "participants": participants,
                "queue_id": 1100,
                "tft_game_type": "standard",
                "tft_set_core_name": "TFTSet12",
                "tft_set_number": 12
            }
        }