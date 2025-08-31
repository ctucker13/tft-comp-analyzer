import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime, timedelta
from config.settings import LLMProvider

class RiotTFTAPI:
    def __init__(self, api_key: str, region: str = "euw1"):
        self.api_key = api_key
        self.region = region  # Platform ID (euw1, eun1, etc.)
        self.base_url = f"https://{region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": self.api_key}
        self._force_mock = False
        
        # Rate limiting for Development API key (10 requests per 10 seconds)
        self._request_times = []
        self._max_requests_per_window = 8  # Stay under 10 to be safe
        self._time_window = 12  # 12 seconds to be safe
        
        # Map platform to regional cluster for match data
        self.regional_cluster = self._get_regional_cluster(region)
    
    async def _rate_limit_wait(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        
        # Remove old requests outside the time window
        self._request_times = [t for t in self._request_times if current_time - t < self._time_window]
        
        # If we're at the limit, wait
        if len(self._request_times) >= self._max_requests_per_window:
            sleep_time = self._time_window - (current_time - self._request_times[0]) + 1
            if sleep_time > 0:
                print(f"⏳ Rate limit protection: waiting {sleep_time:.1f} seconds...")
                await asyncio.sleep(sleep_time)
                # Clean up old requests after waiting
                current_time = time.time()
                self._request_times = [t for t in self._request_times if current_time - t < self._time_window]
        
        # Record this request
        self._request_times.append(current_time)
    
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
    
    def _is_set15_match(self, match_data: Dict[str, Any]) -> bool:
        """Check if match is from Set 15"""
        if not match_data:
            return False
        info = match_data.get("info", {})
        set_number = info.get("tft_set_number", 0)
        return set_number == 15
    
    def _is_recent_match(self, match_data: Dict[str, Any], days_back: int = 7) -> bool:
        """Check if match is from the last N days"""
        if not match_data:
            return False
        info = match_data.get("info", {})
        game_datetime = info.get("game_datetime", 0)
        
        if game_datetime:
            # Convert from milliseconds to seconds
            match_time = datetime.fromtimestamp(game_datetime / 1000)
            cutoff_time = datetime.now() - timedelta(days=days_back)
            return match_time > cutoff_time
        
        return False
    
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
        """Return mock challenger data with PUUID directly"""
        return [
            {
                "puuid": "mock_puuid_1", 
                "leaguePoints": 1200,
                "rank": "I",
                "wins": 45,
                "losses": 25,
                "summonerId": "mock_summoner_1"  # For backwards compatibility
            },
            {
                "puuid": "mock_puuid_2", 
                "leaguePoints": 1150,
                "rank": "I", 
                "wins": 42,
                "losses": 28,
                "summonerId": "mock_summoner_2"
            },
            {
                "puuid": "mock_puuid_3", 
                "leaguePoints": 1100,
                "rank": "I",
                "wins": 40,
                "losses": 30,
                "summonerId": "mock_summoner_3"
            }
        ]
    
    async def get_challenger_players(self) -> List[Dict]:
        """Get top players for high-quality data - PUUID included directly"""
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
                        
                        # Validate that PUUIDs are present
                        players_with_puuid = []
                        for entry in entries:
                            puuid = entry.get("puuid", "")
                            if puuid:
                                players_with_puuid.append(entry)
                            else:
                                print(f"⚠️ Skipping player without PUUID: {entry.get('summonerId', 'Unknown')}")
                        
                        print(f"✓ {len(players_with_puuid)} players have valid PUUIDs")
                        return players_with_puuid
                        
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
    
    # REMOVED: get_summoner_by_id method is no longer needed!
    # The PUUID comes directly from challenger API
    
    async def get_match_history(self, puuid: str, count: int = 20) -> List[str]:
        """Get recent match IDs using PUUID directly"""
        if not puuid:
            print("✗ No PUUID provided")
            return []
        
        if self.is_mock_mode() or puuid.startswith("mock_"):
            base_id = puuid.replace("mock_puuid_", "")
            mock_matches = [f"EUW1_set15_mock_match_{base_id}_{i}" for i in range(1, min(count + 1, 6))]
            print(f"Using mock Set 15 match history: {mock_matches}")
            return mock_matches
        
        # Rate limiting protection
        await self._rate_limit_wait()
        
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
                        return [f"EUW1_set15_mock_match_1_{i}" for i in range(1, 4)]
                    elif response.status == 403:
                        print("✗ 403 Forbidden - Rate limited! Using mock matches")
                        return [f"EUW1_set15_mock_match_1_{i}" for i in range(1, 4)]
                    else:
                        print(f"✗ Match history API Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        return [f"EUW1_set15_mock_match_1_{i}" for i in range(1, 4)]
                        
        except Exception as e:
            print(f"✗ Error fetching match history: {e}")
            return []
    
    async def get_match_details(self, match_id: str) -> Dict[str, Any]:
        """Get detailed match data - filtered for Set 15"""
        if not match_id:
            print("✗ No match ID provided")
            return {}
        
        if self.is_mock_mode() or "mock" in match_id:
            print(f"Using mock Set 15 match details for: {match_id}")
            return self._generate_set15_mock_match_details(match_id)
        
        # Rate limiting protection
        await self._rate_limit_wait()
        
        # Use regional cluster for match data
        url = f"https://{self.regional_cluster}.api.riotgames.com/tft/match/v1/matches/{match_id}"
        print(f"Getting match details from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Match details API response status: {response.status}")
                    
                    if response.status == 200:
                        match_data = await response.json()
                        
                        # Filter for Set 15 only
                        if self._is_set15_match(match_data):
                            participants_count = len(match_data.get("info", {}).get("participants", []))
                            set_num = match_data.get("info", {}).get("tft_set_number", "Unknown")
                            print(f"✓ Got Set {set_num} match with {participants_count} participants")
                            return match_data
                        else:
                            set_num = match_data.get("info", {}).get("tft_set_number", "Unknown")
                            print(f"⏭️ Skipping Set {set_num} match (looking for Set 15)")
                            return {}
                    elif response.status == 401:
                        print("✗ 401 Unauthorized - using mock match details")
                        return self._generate_set15_mock_match_details(f"mock_{match_id}")
                    elif response.status == 403:
                        print("✗ 403 Forbidden - using mock match details")
                        return self._generate_set15_mock_match_details(f"mock_{match_id}")
                    else:
                        print(f"✗ Match details API Error: {response.status}")
                        text = await response.text()
                        print(f"  Response: {text[:200]}...")
                        return self._generate_set15_mock_match_details(f"mock_{match_id}")
                        
        except Exception as e:
            print(f"✗ Error fetching match details: {e}")
            return self._generate_set15_mock_match_details(match_id)
    
    def _generate_set15_mock_match_details(self, match_id: str) -> Dict[str, Any]:
        """Generate realistic Set 15 TFT match data with current meta"""
        import random
        
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
        
        # Generate 8 participants with Set 15 meta comps
        participants = []
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
                "puuid": f"set15_mock_puuid_euw_{i}",
                "time_eliminated": 2400 + (placement * 200),  # Set 15 games are longer
                "total_damage_to_players": max(0, 3000 - (placement * 300)),
                "traits": random.sample(set15_traits, k=min(5, len(set15_traits))),
                "units": random.sample(set15_units, k=min(random.randint(7, 9), len(set15_units))),
                # Set 15 specific fields
                "power_snax_used": random.randint(0, 2),
                "role_bonuses": ["Tank", "Marksman"] if placement <= 4 else ["Fighter"]
            })
        
        # Current timestamp for recent matches
        current_timestamp = int(time.time() * 1000)
        
        return {
            "metadata": {
                "data_version": "15.3.567.1234",
                "match_id": match_id,
                "participants": [p["puuid"] for p in participants]
            },
            "info": {
                "game_datetime": current_timestamp - random.randint(3600000, 86400000),  # 1-24 hours ago
                "game_length": random.uniform(1800.0, 2800.0),  # 30-47 minutes (Set 15 games longer)
                "game_version": "Version 15.3.567.1234",
                "participants": participants,
                "queue_id": 1100,  # TFT Ranked
                "tft_game_type": "standard",
                "tft_set_core_name": "TFTSet15",
                "tft_set_number": 15
            }
        }
    
    async def get_current_patch_from_matches(self) -> Optional[str]:
        """Get current patch by checking recent match data - NO summoner API calls"""
        print("🎮 Checking patch from recent match data...")
        
        if self.is_mock_mode():
            return "15.3"  # Mock patch
        
        try:
            # Get challenger players (they already have PUUIDs!)
            players = await self.get_challenger_players()
            
            if not players:
                print("✗ No challenger players found")
                return None
            
            # Try to get patch info from first few players
            for i, player in enumerate(players[:3], 1):
                puuid = player.get("puuid", "")  # Direct PUUID access!
                
                if not puuid:
                    print(f"⚠️ Player {i}: Skipping player without PUUID")
                    continue
                    
                print(f"  Checking player {i} for patch info...")
                
                try:
                    matches = await self.get_match_history(puuid, count=2)
                    
                    if not matches:
                        print(f"  Player {i}: No matches found")
                        continue
                    
                    for j, match_id in enumerate(matches[:1], 1):  # Check first match only
                        match_details = await self.get_match_details(match_id)
                        
                        if not match_details:
                            continue
                        
                        info = match_details.get("info", {})
                        game_version = info.get("game_version", "")
                        set_number = info.get("tft_set_number", 0)
                        
                        # Extract patch from game version
                        if game_version and set_number == 15:
                            import re
                            version_pattern = r'(\d+\.\d+)'
                            version_match = re.search(version_pattern, game_version)
                            
                            if version_match:
                                patch = version_match.group(1)
                                print(f"✅ Detected patch {patch} from recent match data")
                                return patch
                    
                except Exception as player_error:
                    print(f"  Player {i}: Error getting matches - {player_error}")
                    continue
            
            print("✗ Could not determine patch from any matches")
            return None
            
        except Exception as e:
            print(f"✗ Failed to get patch from match data: {e}")
            return None