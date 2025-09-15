import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

class RiotTFTAPI:
    def __init__(self, api_key: str, region: str = "euw1", use_cache: bool = False):
        self.api_key = api_key
        self.region = region  # Platform ID (euw1, eun1, etc.)
        self.base_url = f"https://{region}.api.riotgames.com"
        self.headers = {"X-Riot-Token": self.api_key}
        self.use_cache = use_cache
        
        # Setup cache directory
        self.cache_dir = Path("cache/riot_api")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a given key"""
        return self.cache_dir / f"{cache_key}.json"
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """Save data to cache file"""
        if not self.use_cache:
            return
            
        cache_path = self._get_cache_path(cache_key)
        cache_data = {
            "timestamp": time.time(),
            "data": data
        }
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save cache: {e}")
    
    def _load_from_cache(self, cache_key: str, max_age_hours: float = 24) -> Optional[Any]:
        """Load data from cache if it exists and is not expired"""
        if not self.use_cache:
            return None
            
        cache_path = self._get_cache_path(cache_key)
        
        if not cache_path.exists():
            return None
            
        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Check if cache is expired
            cache_age = time.time() - cache_data["timestamp"]
            if cache_age > (max_age_hours * 3600):
                print(f"📅 Cache expired for {cache_key} (age: {cache_age/3600:.1f}h)")
                return None
                
            print(f"💾 Using cached data for {cache_key} (age: {cache_age/3600:.1f}h)")
            return cache_data["data"]
            
        except Exception as e:
            print(f"⚠️ Failed to load cache: {e}")
            return None
    
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
    
    def validate_api_key(self) -> bool:
        """Validate that we have a real Riot API key"""
        if (not self.api_key or 
            self.api_key == "your_riot_api_key_here" or 
            self.api_key == ""):
            raise ValueError("❌ Real Riot API key required for analysis. Please add a valid RIOT_API_KEY to your environment.")
        return True
    
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
    
    def _is_patch_15_3_or_later(self, match_data: Dict[str, Any]) -> bool:
        """Check if match is from patch 15.3 or later (from 2025/08/26 onwards)
        Note: This is now less aggressive - if we can't determine the patch, we assume it's valid"""
        if not match_data:
            return False
        info = match_data.get("info", {})
        game_version = info.get("game_version", "")
        game_datetime = info.get("game_datetime", 0)
        
        # If no date/version info, assume it's valid (less aggressive filtering)
        if not game_datetime and not game_version:
            return True
        
        # Check by game version first if available (more reliable than date)
        if game_version:
            import re
            version_pattern = r'(\d+\.\d+)'
            version_match = re.search(version_pattern, game_version)
            if version_match:
                version = version_match.group(1)
                # Parse version numbers (e.g., "15.3" -> [15, 3])
                try:
                    major, minor = map(int, version.split('.'))
                    return major > 15 or (major == 15 and minor >= 3)
                except ValueError:
                    # If version parsing fails, assume it's valid
                    return True
        
        # Check by date only if version check didn't work and we have a date
        if game_datetime:
            match_time = datetime.fromtimestamp(game_datetime / 1000)
            patch_15_3_release = datetime(2025, 8, 26)
            return match_time >= patch_15_3_release
        
        # If we can't determine anything, assume it's valid (less aggressive)
        return True
    
    async def test_api_connection(self) -> bool:
        """Test if the API key and connection are working"""
        print("Testing API connection...")
        
        # Validate API key first
        self.validate_api_key()
        
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
    
    
    async def get_challenger_players(self) -> List[Dict]:
        """Get top players for high-quality data - PUUID included directly"""
        cache_key = f"challenger_players_{self.region}"
        
        # Try cache first (extended for development)
        cached_data = self._load_from_cache(cache_key, max_age_hours=6)  # Cache for 6 hours - good for dev iteration
        if cached_data is not None:
            return cached_data
        
        # Validate API key first
        self.validate_api_key()
        
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
                        
                        # Save to cache
                        self._save_to_cache(cache_key, players_with_puuid)
                        
                        return players_with_puuid
                        
                    elif response.status == 401:
                        raise ValueError("✗ 401 Unauthorized - Invalid API key. Please check your RIOT_API_KEY.")
                    elif response.status == 403:
                        raise ValueError("✗ 403 Forbidden - Rate limited or expired key. Development keys expire every 24 hours.")
                    else:
                        text = await response.text()
                        raise ValueError(f"✗ API Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom errors
            raise ValueError(f"✗ Error fetching challenger players: {e}")

    async def get_master_players(self) -> List[Dict]:
        """Get Master tier players - PUUID included directly"""
        cache_key = f"master_players_{self.region}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key, max_age_hours=6)
        if cached_data is not None:
            return cached_data
        
        # Validate API key first
        self.validate_api_key()
        
        # Real API call using platform routing
        url = f"{self.base_url}/tft/league/v1/master"
        print(f"Fetching master data from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Master API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        entries = data.get("entries", [])
                        print(f"✓ Found {len(entries)} master players")
                        
                        # Validate that PUUIDs are present
                        players_with_puuid = []
                        for entry in entries:
                            puuid = entry.get("puuid", "")
                            if puuid:
                                players_with_puuid.append(entry)
                            else:
                                print(f"⚠️ Skipping master player without PUUID: {entry.get('summonerId', 'Unknown')}")
                        
                        print(f"✓ {len(players_with_puuid)} master players have valid PUUIDs")
                        
                        # Save to cache
                        self._save_to_cache(cache_key, players_with_puuid)
                        
                        return players_with_puuid
                        
                    elif response.status == 401:
                        raise ValueError("✗ 401 Unauthorized - Invalid API key. Please check your RIOT_API_KEY.")
                    elif response.status == 403:
                        raise ValueError("✗ 403 Forbidden - Rate limited or expired key. Development keys expire every 24 hours.")
                    else:
                        text = await response.text()
                        raise ValueError(f"✗ Master API Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom errors
            raise ValueError(f"✗ Error fetching master players: {e}")

    async def get_grandmaster_players(self) -> List[Dict]:
        """Get Grandmaster tier players - PUUID included directly"""
        cache_key = f"grandmaster_players_{self.region}"
        
        # Try cache first
        cached_data = self._load_from_cache(cache_key, max_age_hours=6)
        if cached_data is not None:
            return cached_data
        
        # Validate API key first
        self.validate_api_key()
        
        # Real API call using platform routing
        url = f"{self.base_url}/tft/league/v1/grandmaster"
        print(f"Fetching grandmaster data from: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers) as response:
                    print(f"Grandmaster API response status: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        entries = data.get("entries", [])
                        print(f"✓ Found {len(entries)} grandmaster players")
                        
                        # Validate that PUUIDs are present
                        players_with_puuid = []
                        for entry in entries:
                            puuid = entry.get("puuid", "")
                            if puuid:
                                players_with_puuid.append(entry)
                            else:
                                print(f"⚠️ Skipping grandmaster player without PUUID: {entry.get('summonerId', 'Unknown')}")
                        
                        print(f"✓ {len(players_with_puuid)} grandmaster players have valid PUUIDs")
                        
                        # Save to cache
                        self._save_to_cache(cache_key, players_with_puuid)
                        
                        return players_with_puuid
                        
                    elif response.status == 401:
                        raise ValueError("✗ 401 Unauthorized - Invalid API key. Please check your RIOT_API_KEY.")
                    elif response.status == 403:
                        raise ValueError("✗ 403 Forbidden - Rate limited or expired key. Development keys expire every 24 hours.")
                    else:
                        text = await response.text()
                        raise ValueError(f"✗ Grandmaster API Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom errors
            raise ValueError(f"✗ Error fetching grandmaster players: {e}")

    async def get_high_tier_players(self, include_tiers: List[str] = None) -> List[Dict]:
        """Get players from multiple high tiers with tier information
        
        Args:
            include_tiers: List of tiers to include ['challenger', 'grandmaster', 'master']
                          Defaults to all three tiers
        """
        if include_tiers is None:
            include_tiers = ['challenger', 'grandmaster', 'master']
        
        all_players = []
        
        # Get players from each tier
        for tier in include_tiers:
            try:
                if tier == 'challenger':
                    players = await self.get_challenger_players()
                    # Add tier information to each player
                    for player in players:
                        player['tier'] = 'CHALLENGER'
                        player['rank'] = 'I'  # Challenger only has one rank
                    all_players.extend(players)
                    print(f"✓ Added {len(players)} challenger players")
                    
                elif tier == 'grandmaster':
                    players = await self.get_grandmaster_players()
                    # Add tier information to each player
                    for player in players:
                        player['tier'] = 'GRANDMASTER'
                        player['rank'] = 'I'  # Grandmaster only has one rank
                    all_players.extend(players)
                    print(f"✓ Added {len(players)} grandmaster players")
                    
                elif tier == 'master':
                    players = await self.get_master_players()
                    # Add tier information to each player
                    for player in players:
                        player['tier'] = 'MASTER'
                        player['rank'] = 'I'  # Master only has one rank
                    all_players.extend(players)
                    print(f"✓ Added {len(players)} master players")
                    
                # Add delay between tier fetches to respect rate limits
                if tier != include_tiers[-1]:  # Don't sleep after the last tier
                    await asyncio.sleep(2)
                    
            except Exception as e:
                print(f"⚠️ Failed to fetch {tier} players: {e}")
                continue
        
        # Sort by LP (highest first) to prioritize better players
        all_players.sort(key=lambda x: x.get('leaguePoints', 0), reverse=True)
        
        print(f"🎯 Total high-tier players collected: {len(all_players)}")
        return all_players

    async def get_winning_players_from_recent_matches(self, players: List[Dict], sample_matches: int = 3) -> List[Dict]:
        """Filter players based on recent match performance - prioritize winners
        
        Args:
            players: List of player dictionaries with PUUIDs
            sample_matches: Number of recent matches to check for win rate
        
        Returns:
            List of players sorted by recent performance (winners first)
        """
        player_performance = []
        
        print(f"🏆 Analyzing recent performance for {len(players)} players...")
        
        for i, player in enumerate(players[:10]):  # Limit to first 10 players to avoid excessive API calls
            puuid = player.get("puuid", "")
            tier = player.get("tier", "UNKNOWN")
            
            if not puuid:
                continue
            
            try:
                # Get recent match history
                recent_matches = await self.get_match_history(puuid, count=sample_matches)
                
                if not recent_matches:
                    continue
                
                wins = 0
                top4s = 0
                total_matches = 0
                
                for match_id in recent_matches[:sample_matches]:
                    # Add small delay to respect rate limits
                    await asyncio.sleep(1)
                    
                    match_details = await self.get_match_details(match_id, require_patch_15_3=False, debug=False)
                    
                    if not match_details or not self._is_set15_match(match_details):
                        continue
                    
                    # Find this player's placement in the match
                    participants = match_details.get("info", {}).get("participants", [])
                    for participant in participants:
                        if participant.get("puuid") == puuid:
                            placement = participant.get("placement", 8)
                            total_matches += 1
                            
                            if placement == 1:
                                wins += 1
                                top4s += 1
                            elif placement <= 4:
                                top4s += 1
                            break
                
                if total_matches > 0:
                    win_rate = wins / total_matches
                    top4_rate = top4s / total_matches
                    
                    # Add performance metrics to player data
                    player_with_performance = player.copy()
                    player_with_performance.update({
                        'recent_matches_analyzed': total_matches,
                        'recent_wins': wins,
                        'recent_top4s': top4s,
                        'win_rate': win_rate,
                        'top4_rate': top4_rate,
                        'performance_score': (win_rate * 2) + top4_rate  # Weight wins more heavily
                    })
                    
                    player_performance.append(player_with_performance)
                    print(f"  {tier} player: {wins}W/{total_matches}M (WR: {win_rate:.1%}, Top4: {top4_rate:.1%})")
                
            except Exception as e:
                print(f"  ⚠️ Error analyzing {tier} player performance: {e}")
                continue
        
        # Sort by performance score (best performers first)
        player_performance.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
        
        print(f"✅ Performance analysis complete: {len(player_performance)} players with win data")
        return player_performance
    
    # REMOVED: get_summoner_by_id method is no longer needed!
    # The PUUID comes directly from challenger/master/grandmaster APIs
    
    async def get_match_history(self, puuid: str, count: int = 20, hours_back: int = None, set15_optimized: bool = False) -> List[str]:
        """Get recent match IDs using PUUID directly
        
        Args:
            puuid: Player PUUID
            count: Maximum number of matches to return
            hours_back: If provided, only return matches from the last N hours
            set15_optimized: If True, automatically filter to Set 15 launch date or later (disabled by default)
        """
        if not puuid:
            print("✗ No PUUID provided")
            return []
        
        # Create cache key including time filter
        if hours_back:
            if hours_back == 24:
                time_suffix = "_24h"
            elif hours_back == 168:  # 7 days
                time_suffix = "_7d"
            else:
                time_suffix = f"_{hours_back}h"
        else:
            time_suffix = ""
        cache_key = f"match_history_{puuid[:16]}{time_suffix}_{count}"
        
        # Try cache first (extended for development iteration)
        cached_data = self._load_from_cache(cache_key, max_age_hours=2)  # Cache for 2 hours - good for dev iteration
        if cached_data is not None:
            return cached_data
        
        # Rate limiting protection
        await self._rate_limit_wait()
        
        # Use regional cluster for match data (EUROPE for European platforms)
        url = f"https://{self.regional_cluster}.api.riotgames.com/tft/match/v1/matches/by-puuid/{puuid}/ids"
        params = {"count": count}
        
        # Add time-based filtering
        start_time = None
        
        if hours_back:
            # Calculate start time (hours ago) in Unix timestamp (seconds)
            start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp())
            print(f"Getting match history from last {hours_back} hours: {url}")
        elif set15_optimized:
            # Set 15 launched around 2025/08/20, so filter to that date to avoid old matches
            set15_launch = datetime(2025, 8, 20)
            start_time = int(set15_launch.timestamp())
            print(f"Getting match history from Set 15 launch date ({set15_launch.strftime('%Y-%m-%d')}): {url}")
        else:
            print(f"Getting match history from: {url}")
        
        if start_time:
            params["start"] = start_time
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    print(f"Match history API response status: {response.status}")
                    
                    if response.status == 200:
                        matches = await response.json()
                        print(f"✓ Found {len(matches)} matches")
                        
                        # Save to cache
                        self._save_to_cache(cache_key, matches)
                        
                        return matches
                    elif response.status == 401:
                        raise ValueError("✗ 401 Unauthorized - Invalid API key")
                    elif response.status == 403:
                        raise ValueError("✗ 403 Forbidden - Rate limited or expired key")
                    else:
                        text = await response.text()
                        raise ValueError(f"✗ Match history API Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom errors
            raise ValueError(f"✗ Error fetching match history: {e}")
    
    async def get_match_details(self, match_id: str, require_patch_15_3: bool = True, debug: bool = True) -> Dict[str, Any]:
        """Get detailed match data - filtered for Set 15 and optionally patch 15.3+"""
        if not match_id:
            print("✗ No match ID provided")
            return {}
        
        # Create cache key
        cache_key = f"match_details_{match_id}"
        
        # Try cache first (longer cache time for match details as they don't change)
        cached_data = self._load_from_cache(cache_key, max_age_hours=72)  # Cache for 72 hours (match details are immutable)
        if cached_data is not None:
            # Still apply filtering to cached data
            if not self._is_set15_match(cached_data):
                print("⏭️ Cached match is not Set 15")
                return {}
            
            if require_patch_15_3 and not self._is_patch_15_3_or_later(cached_data):
                info = cached_data.get("info", {})
                game_version = info.get("game_version", "Unknown")
                game_datetime = info.get("game_datetime", 0)
                match_date = datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d') if game_datetime else "Unknown"
                print(f"⏭️ Cached match from {match_date} (version: {game_version}) is pre-15.3")
                return {}
            
            # If cached match passes filters, return it
            print("💾 Using cached match details")
            return cached_data
        
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
                        
                        # Debug: Show match info before filtering
                        if debug:
                            info = match_data.get("info", {})
                            set_num = info.get("tft_set_number", "Unknown") 
                            game_version = info.get("game_version", "Unknown")
                            game_datetime = info.get("game_datetime", 0)
                            match_date = datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d') if game_datetime else "Unknown"
                            print(f"🔍 Match {match_id[:8]}: Set {set_num}, Version {game_version}, Date {match_date}")
                        
                        # Filter for Set 15 first
                        if not self._is_set15_match(match_data):
                            set_num = match_data.get("info", {}).get("tft_set_number", "Unknown")
                            if debug:
                                print(f"⏭️ Skipping Set {set_num} match (looking for Set 15)")
                            return {}
                        
                        # Filter for patch 15.3+ if required
                        if require_patch_15_3 and not self._is_patch_15_3_or_later(match_data):
                            info = match_data.get("info", {})
                            game_version = info.get("game_version", "Unknown")
                            game_datetime = info.get("game_datetime", 0)
                            match_date = datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d') if game_datetime else "Unknown"
                            if debug:
                                print(f"⏭️ Skipping pre-15.3 match from {match_date} (version: {game_version})")
                            return {}
                        
                        participants_count = len(match_data.get("info", {}).get("participants", []))
                        set_num = match_data.get("info", {}).get("tft_set_number", "Unknown")
                        info = match_data.get("info", {})
                        game_version = info.get("game_version", "Unknown")
                        game_datetime = info.get("game_datetime", 0)
                        match_date = datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d %H:%M') if game_datetime else "Unknown"
                        print(f"✓ Got Set {set_num} match from {match_date} (version: {game_version}) with {participants_count} participants")
                        
                        # Save to cache
                        self._save_to_cache(cache_key, match_data)
                        
                        return match_data
                    elif response.status == 401:
                        raise ValueError("✗ 401 Unauthorized - Invalid API key")
                    elif response.status == 403:
                        raise ValueError("✗ 403 Forbidden - Rate limited or expired key")
                    else:
                        text = await response.text()
                        raise ValueError(f"✗ Match details API Error {response.status}: {text[:200]}...")
                        
        except Exception as e:
            if isinstance(e, ValueError):
                raise  # Re-raise our custom errors
            raise ValueError(f"✗ Error fetching match details: {e}")
    
    
    async def get_current_patch_from_matches(self) -> Optional[str]:
        """Get current patch by checking recent match data - NO summoner API calls"""
        print("🎮 Checking patch from recent match data...")
        
        # Validate API key first
        self.validate_api_key()
        
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

    async def find_earliest_set15_match(self) -> Optional[Dict[str, Any]]:
        """Find the earliest Set 15 match to determine when the set launched"""
        print("🔍 Searching for earliest Set 15 match...")
        
        earliest_match = None
        earliest_timestamp = float('inf')
        
        # Get challenger players
        players = await self.get_challenger_players()
        if not players:
            print("✗ Could not get challenger players")
            return None
        
        # Check first few players to find earliest matches
        for i, player in enumerate(players[:5]):  # Check first 5 players
            puuid = player.get("puuid")
            if not puuid:
                continue
                
            print(f"Checking player {i+1}/5...")
            
            # Get more match history to find older matches
            matches = await self.get_match_history(puuid, count=10)  # Get more matches
            
            for match_id in matches:
                # Get match details WITHOUT patch filtering
                match_data = await self.get_match_details(match_id, require_patch_15_3=False)
                
                if match_data and self._is_set15_match(match_data):
                    info = match_data.get("info", {})
                    game_datetime = info.get("game_datetime", 0)
                    
                    if game_datetime and game_datetime < earliest_timestamp:
                        earliest_timestamp = game_datetime
                        earliest_match = {
                            "match_id": match_id,
                            "timestamp": game_datetime,
                            "date": datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                            "game_version": info.get("game_version", "Unknown"),
                            "set_number": info.get("tft_set_number", 0)
                        }
                        print(f"  Found earlier Set 15 match: {earliest_match['date']} (version: {earliest_match['game_version']})")
        
        return earliest_match