import aiohttp
import asyncio
import re
from typing import Optional, Dict, Any
from datetime import datetime
from config.settings import LLMProvider

class TFTPatchDetector:
    """Automatically detects the current TFT patch and set information"""
    
    def __init__(self):
        self.patch_sources = [
            "https://teamfighttactics.leagueoflegends.com/en-us/news/tags/teamfight-tactics-patch-notes/",
            "https://www.metatft.com/",
            "https://mobalytics.gg/tft"
        ]
    
    async def get_current_patch_info(self) -> Dict[str, Any]:
        """Get current patch, set number, and set name"""
        print("🔍 Detecting current TFT patch...")
        
        # Try multiple methods to get patch info
        patch_info = await self._get_patch_from_patch_notes()
        
        if not patch_info.get("patch"):
            patch_info = await self._get_patch_from_meta_sites()
        
        # Fallback to reasonable defaults if detection fails
        if not patch_info.get("patch"):
            print("⚠️ Could not detect current patch, using defaults")
            patch_info = {
                "patch": "14.24",  # Updated to match your current data
                "set_number": 15,
                "set_name": "K.O. Coliseum",
                "detection_method": "fallback"
            }
        
        print(f"✅ Detected: Patch {patch_info['patch']}, Set {patch_info['set_number']} ({patch_info['set_name']})")
        return patch_info
    
    async def _get_patch_from_patch_notes(self) -> Dict[str, Any]:
        """Get patch info from official Riot patch notes"""
        url = "https://teamfighttactics.leagueoflegends.com/en-us/news/tags/teamfight-tactics-patch-notes/"
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Look for patch numbers in titles and content
                        patch_patterns = [
                            r'patch\s+(\d+\.\d+)',
                            r'(\d+\.\d+)\s+patch',
                            r'version\s+(\d+\.\d+)',
                            r'tft\s+(\d+\.\d+)'
                        ]
                        set_patterns = [
                            r'set\s+(\d+)',
                            r'TFT\s+Set\s+(\d+)',
                            r'Teamfight\s+Tactics\s+Set\s+(\d+)'
                        ]
                        
                        all_patches = []
                        all_sets = []
                        
                        for pattern in patch_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            all_patches.extend(matches)
                        
                        for pattern in set_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            all_sets.extend([int(m) for m in matches])
                        
                        if all_patches:
                            # Get the most recent patch (highest version number)
                            latest_patch = max(all_patches, key=lambda x: [int(i) for i in x.split('.')])
                            set_number = max(all_sets) if all_sets else 15
                            
                            # Determine set name based on set number
                            set_names = {
                                15: "K.O. Coliseum",
                                14: "Cyber City", 
                                13: "Into the Arcane",
                                12: "Hextech Legends"
                            }
                            
                            return {
                                "patch": latest_patch,
                                "set_number": set_number,
                                "set_name": set_names.get(set_number, f"Set {set_number}"),
                                "detection_method": "official_patch_notes"
                            }
                            
        except Exception as e:
            print(f"Failed to get patch from official source: {e}")
        
        return {}
    
    async def _get_patch_from_meta_sites(self) -> Dict[str, Any]:
        """Get patch info from community meta sites"""
        meta_urls = [
            ("https://www.metatft.com/", "metatft"),
            ("https://mobalytics.gg/tft", "mobalytics"),
            ("https://tactics.tools/", "tactics.tools")
        ]
        
        for url, site_name in meta_urls:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Look for current patch indicators with more patterns
                            patterns = [
                                r'patch\s+(\d+\.\d+)',
                                r'(\d+\.\d+)\s+patch',
                                r'version\s+(\d+\.\d+)',
                                r'current.*?(\d+\.\d+)',
                                r'(\d+\.\d+).*?current'
                            ]
                            
                            found_patches = []
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                found_patches.extend(matches)
                            
                            if found_patches:
                                # Filter for reasonable TFT patch numbers (typically 14.x or 15.x)
                                valid_patches = [p for p in found_patches if p.startswith(('14.', '15.'))]
                                
                                if valid_patches:
                                    latest_patch = max(valid_patches, key=lambda x: [int(i) for i in x.split('.')])
                                    
                                    # Determine set based on patch
                                    set_number = 15 if latest_patch.startswith('15.') else 14
                                    set_name = "K.O. Coliseum" if set_number == 15 else "Cyber City"
                                    
                                    return {
                                        "patch": latest_patch,
                                        "set_number": set_number,
                                        "set_name": set_name,
                                        "detection_method": f"meta_site_{site_name}"
                                    }
                                        
            except Exception as e:
                print(f"Failed to get patch from {url}: {e}")
                continue
        
        return {}
    
    async def get_patch_from_recent_matches(self, riot_api) -> Optional[str]:
        """Get patch info from recent match data - NO summoner API calls"""
        print("🎮 Checking patch from recent match data...")
        
        try:
            # Get challenger players (they already have PUUIDs!)
            players = await riot_api.get_challenger_players()
            
            if not players:
                print("✗ No challenger players found")
                return None
            
            # Try to get patch info from first few players
            for i, player in enumerate(players[:3], 1):
                puuid = player.get("puuid", "")  # Direct PUUID access - no summoner API!
                
                if not puuid:
                    print(f"⚠️ Player {i}: Skipping player without PUUID")
                    continue
                    
                print(f"  Checking player {i} for patch info...")
                
                try:
                    matches = await riot_api.get_match_history(puuid, count=2)
                    
                    if not matches:
                        print(f"  Player {i}: No matches found")
                        continue
                    
                    for j, match_id in enumerate(matches[:1], 1):  # Check first match only
                        print(f"    Checking match {j}...")
                        match_details = await riot_api.get_match_details(match_id)
                        
                        if not match_details:
                            print(f"    Match {j}: No details found")
                            continue
                        
                        info = match_details.get("info", {})
                        game_version = info.get("game_version", "")
                        set_number = info.get("tft_set_number", 0)
                        
                        print(f"    Match {j}: Game version: {game_version}, Set: {set_number}")
                        
                        # Extract patch from game version (e.g., "Version 14.24.567.1234")
                        if game_version and set_number == 15:
                            version_pattern = r'(\d+\.\d+)'
                            version_match = re.search(version_pattern, game_version)
                            
                            if version_match:
                                patch = version_match.group(1)
                                print(f"✅ Detected patch {patch} from recent match data")
                                return patch
                            else:
                                print(f"    Could not parse patch from version: {game_version}")
                        else:
                            print(f"    Skipping: Not Set 15 or no version (Set {set_number})")
                
                except Exception as player_error:
                    print(f"  Player {i}: Error getting matches - {player_error}")
                    continue
            
            print("✗ Could not determine patch from any matches")
            return None
            
        except Exception as e:
            print(f"✗ Failed to get patch from match data: {e}")
            return None
    
    async def get_comprehensive_patch_info(self, riot_api=None) -> Dict[str, Any]:
        """Get patch info using all available methods"""
        print("🔍 Starting comprehensive patch detection...")
        
        # Method 1: Official patch notes (most reliable)
        patch_info = await self._get_patch_from_patch_notes()
        
        # Method 2: Meta sites (backup)
        if not patch_info.get("patch"):
            print("📱 Trying meta sites...")
            patch_info = await self._get_patch_from_meta_sites()
        
        # Method 3: Recent matches (if riot_api provided)
        if not patch_info.get("patch") and riot_api:
            print("🎮 Trying recent match data...")
            match_patch = await self.get_patch_from_recent_matches(riot_api)
            if match_patch:
                patch_info = {
                    "patch": match_patch,
                    "set_number": 15,  # Assume current set
                    "set_name": "K.O. Coliseum",
                    "detection_method": "recent_matches"
                }
        
        # Fallback to defaults
        if not patch_info.get("patch"):
            print("⚠️ All detection methods failed, using fallback")
            patch_info = {
                "patch": "14.24",
                "set_number": 15,
                "set_name": "K.O. Coliseum",
                "detection_method": "fallback"
            }
        
        # Validate patch info
        patch_info = self._validate_patch_info(patch_info)
        
        print(f"✅ Final result: Patch {patch_info['patch']}, Set {patch_info['set_number']} ({patch_info['set_name']})")
        print(f"   Detection method: {patch_info['detection_method']}")
        
        return patch_info
    
    def _validate_patch_info(self, patch_info: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean up patch info"""
        # Ensure all required fields exist
        defaults = {
            "patch": "14.24",
            "set_number": 15,
            "set_name": "K.O. Coliseum",
            "detection_method": "fallback"
        }
        
        for key, default_value in defaults.items():
            if key not in patch_info or not patch_info[key]:
                patch_info[key] = default_value
        
        # Validate patch format
        patch = patch_info["patch"]
        if not re.match(r'^\d+\.\d+$', patch):
            print(f"⚠️ Invalid patch format '{patch}', using default")
            patch_info["patch"] = defaults["patch"]
        
        # Ensure set_number is integer
        try:
            patch_info["set_number"] = int(patch_info["set_number"])
        except (ValueError, TypeError):
            patch_info["set_number"] = defaults["set_number"]
        
        return patch_info