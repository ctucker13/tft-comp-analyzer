import aiohttp
import asyncio
import re
from typing import Optional, Dict, Any
from datetime import datetime

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
                "patch": "15.3",
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
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Look for patch numbers in titles
                        patch_pattern = r'patch\s+(\d+\.\d+)'
                        set_pattern = r'set\s+(\d+)'
                        
                        patch_matches = re.findall(patch_pattern, content, re.IGNORECASE)
                        set_matches = re.findall(set_pattern, content, re.IGNORECASE)
                        
                        if patch_matches:
                            latest_patch = max(patch_matches, key=lambda x: [int(i) for i in x.split('.')])
                            set_number = int(max(set_matches)) if set_matches else 15
                            
                            # Determine set name based on set number
                            set_names = {
                                15: "K.O. Coliseum",
                                14: "Cyber City", 
                                13: "Into the Arcane"
                            }
                            
                            return {
                                "patch": latest_patch,
                                "set_number": set_number,
                                "set_name": set_names.get(set_number, "Unknown Set"),
                                "detection_method": "official_patch_notes"
                            }
                            
        except Exception as e:
            print(f"Failed to get patch from official source: {e}")
        
        return {}
    
    async def _get_patch_from_meta_sites(self) -> Dict[str, Any]:
        """Get patch info from community meta sites"""
        meta_urls = [
            "https://www.metatft.com/",
            "https://mobalytics.gg/tft"
        ]
        
        for url in meta_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            content = await response.text()
                            
                            # Look for current patch indicators
                            patterns = [
                                r'patch\s+(\d+\.\d+)',
                                r'(\d+\.\d+)\s+patch',
                                r'set\s+(\d+)'
                            ]
                            
                            for pattern in patterns:
                                matches = re.findall(pattern, content, re.IGNORECASE)
                                if matches:
                                    if 'patch' in pattern:
                                        latest_patch = max(matches, key=lambda x: [int(i) for i in x.split('.')])
                                        return {
                                            "patch": latest_patch,
                                            "set_number": 15,  # Assume current
                                            "set_name": "K.O. Coliseum",
                                            "detection_method": f"meta_site_{url}"
                                        }
                                        
            except Exception as e:
                print(f"Failed to get patch from {url}: {e}")
                continue
        
        return {}
    
    async def get_patch_from_recent_matches(self, riot_api) -> Optional[str]:
        """Get patch info from recent match data"""
        print("🎮 Checking patch from recent match data...")
        
        try:
            # Get a few recent matches to check game version
            players = await riot_api.get_challenger_players()
            
            for player in players[:3]:
                summoner_data = await riot_api.get_summoner_by_id(player.get("summonerId", ""))
                puuid = summoner_data.get("puuid", "")
                
                if puuid:
                    matches = await riot_api.get_match_history(puuid, count=3)
                    
                    for match_id in matches:
                        match_details = await riot_api.get_match_details(match_id)
                        
                        if match_details:
                            info = match_details.get("info", {})
                            game_version = info.get("game_version", "")
                            set_number = info.get("tft_set_number", 0)
                            
                            # Extract patch from game version
                            version_pattern = r'(\d+\.\d+)'
                            version_match = re.search(version_pattern, game_version)
                            
                            if version_match and set_number == 15:
                                patch = version_match.group(1)
                                print(f"✅ Detected patch {patch} from match data")
                                return patch
            
        except Exception as e:
            print(f"Failed to get patch from match data: {e}")
        
        return None