import json
import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, asdict
import re

@dataclass
class PatchData:
    """Data structure for TFT patch information"""
    patch_version: str
    set_number: int
    set_name: str
    champions: Dict[int, Set[str]]  # cost -> champion names
    traits: Set[str]
    augments: Set[str]
    items: Set[str]
    last_updated: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert sets to lists for JSON serialization
        data['champions'] = {str(k): list(v) for k, v in self.champions.items()}
        data['traits'] = list(self.traits)
        data['augments'] = list(self.augments)
        data['items'] = list(self.items)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatchData':
        """Create from dictionary for JSON deserialization"""
        # Convert lists back to sets
        champions = {int(k): set(v) for k, v in data['champions'].items()}
        traits = set(data['traits'])
        augments = set(data['augments'])
        items = set(data['items'])
        last_updated = datetime.fromisoformat(data['last_updated'])
        
        return cls(
            patch_version=data['patch_version'],
            set_number=data['set_number'],
            set_name=data['set_name'],
            champions=champions,
            traits=traits,
            augments=augments,
            items=items,
            last_updated=last_updated
        )


class PatchDataManager:
    """Manages TFT patch data with caching and dynamic fetching"""
    
    def __init__(self, cache_dir: str = "cache/patch_data"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        self._patch_cache: Dict[str, PatchData] = {}
        
    def _get_cache_file(self, patch_version: str) -> Path:
        """Get cache file path for a patch version"""
        return self.cache_dir / f"patch_{patch_version}.json"
    
    async def _load_from_cache(self, patch_version: str) -> Optional[PatchData]:
        """Load patch data from cache if valid"""
        cache_file = self._get_cache_file(patch_version)
        
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            patch_data = PatchData.from_dict(data)
            
            # Check if cache is still valid
            if datetime.now() - patch_data.last_updated < self.cache_duration:
                return patch_data
            else:
                print(f"Cache expired for patch {patch_version}")
                return None
                
        except Exception as e:
            print(f"Error loading cache for patch {patch_version}: {e}")
            return None
    
    async def _save_to_cache(self, patch_data: PatchData) -> None:
        """Save patch data to cache"""
        cache_file = self._get_cache_file(patch_data.patch_version)
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(patch_data.to_dict(), f, indent=2)
        except Exception as e:
            print(f"Error saving cache for patch {patch_data.patch_version}: {e}")
    
    async def _fetch_patch_data_from_sources(self, patch_version: str) -> Optional[PatchData]:
        """Fetch patch data from multiple sources"""
        sources = [
            self._fetch_from_metatft,
            self._fetch_from_tactics_tools,
            self._fetch_from_lolchess
        ]
        
        for source_func in sources:
            try:
                print(f"Trying to fetch patch {patch_version} data from {source_func.__name__}...")
                patch_data = await source_func(patch_version)
                if patch_data:
                    return patch_data
            except Exception as e:
                print(f"Failed to fetch from {source_func.__name__}: {e}")
                continue
        
        # Fallback to hardcoded data for known patches
        return self._get_fallback_patch_data(patch_version)
    
    async def _fetch_from_metatft(self, patch_version: str) -> Optional[PatchData]:
        """Fetch data from MetaTFT (simulated - would need real API)"""
        # This would integrate with MetaTFT API if available
        # For now, return None to fall back to other sources
        return None
    
    async def _fetch_from_tactics_tools(self, patch_version: str) -> Optional[PatchData]:
        """Fetch data from Tactics.tools (simulated)"""
        # This would integrate with tactics.tools API if available
        return None
    
    async def _fetch_from_lolchess(self, patch_version: str) -> Optional[PatchData]:
        """Fetch data from lolchess.gg (simulated)"""
        # This would scrape or use lolchess API if available
        return None
    
    def _get_fallback_patch_data(self, patch_version: str) -> Optional[PatchData]:
        """Get hardcoded patch data for known patches"""
        
        # Extract major version (e.g., "15" from "15.3")
        major_version = patch_version.split('.')[0]
        
        if major_version == "15":
            # Set 15: K.O. Coliseum data
            return PatchData(
                patch_version=patch_version,
                set_number=15,
                set_name="K.O. Coliseum",
                champions={
                    1: {"Aatrox", "Akali", "Darius", "Ezreal", "Garen", "Gragas", "Leona", 
                        "Lux", "Poppy", "Sivir", "Swain", "Twitch", "Varus", "Ziggs"},
                    2: {"Dr. Mundo", "Gangplank", "Janna", "Kassadin", "Kog'Maw", "Malphite",
                        "Nasus", "Nilah", "Nomsy", "Rell", "Shen", "Tristana", "Warwick"},
                    3: {"Amumu", "Cassiopeia", "Elise", "Galio", "Jinx", "Kalista", "Katarina",
                        "Mordekaiser", "Neeko", "Nunu & Willump", "Rumble", "Swain", "Veigar"},
                    4: {"Ambessa", "Blitzcrank", "Fiora", "Gnar", "Lorelei", "Nami", "Olaf",
                        "Renni", "Tahm Kench", "Vi", "Vladimir", "Zoe"},
                    5: {"Caitlyn", "Heimerdinger", "Jayce", "Jinx", "LeBlanc", "Mel", 
                        "Silco", "Urgot", "Viktor", "Warwick"}
                },
                traits={"Academy", "Ambusher", "Artillerist", "Black Rose", "Bruiser", "Challenger",
                       "Chemtech", "Conqueror", "Dominator", "Enforcer", "Experiment", "Family",
                       "Firelight", "Form Swapper", "High Roller", "Junker King", "Mastermind",
                       "Pit Fighter", "Quickstriker", "Rebel", "Scrap", "Sentinel", "Sniper",
                       "Socialite", "Sorcerer", "Transformer", "Watcher"},
                augments={"Axiom Arc", "Battlefield Training", "Binary Airdrop", "Combat Training",
                         "Component Grab Bag", "Cybernetic Implants", "Double Trouble", "Electrocharge",
                         "Featherweights", "Golden Ticket", "Harmonious Bond", "Hustler",
                         "Idealism", "Jeweled Lotus", "Knowledge Download", "Lucky Gloves",
                         "Makeshift Armor", "Metabolic Accelerator", "New Recruit", "Pandora's Items",
                         "Preparation", "Rich Get Richer", "Second Wind", "Self-Repair",
                         "Stand United", "Thrill of the Hunt", "Trade Sector", "Weakspot"},
                items={"B.F. Sword", "Chain Vest", "Giant's Belt", "Needlessly Large Rod", "Negatron Cloak",
                      "Recurve Bow", "Spatula", "Sparring Gloves", "Tear of the Goddess",
                      "Bloodthirster", "Deathblade", "Edge of Night", "Giant Slayer", "Hextech Gunblade",
                      "Infinity Edge", "Last Whisper", "Mercurial Scimitar", "Archangel's Staff",
                      "Blue Buff", "Crownguard", "Guinsoo's Rageblade", "Hextech Gunblade", "Jeweled Gauntlet",
                      "Morellonomicon", "Nashor's Tooth", "Rabadon's Deathcap", "Statikk Shiv",
                      "Bramble Vest", "Dragon's Claw", "Gargoyle Stoneplate", "Steadfast Heart",
                      "Sunfire Cape", "Titan's Resolve", "Warmog's Armor"},
                last_updated=datetime.now()
            )
        
        elif major_version == "14":
            # Set 12/13/14 fallback data
            return PatchData(
                patch_version=patch_version,
                set_number=12,
                set_name="Inkborn Fables",
                champions={
                    1: {"Ahri", "Cho'Gath", "Jax", "Kha'Zix", "Kobuko", "Lillia", "Malphite",
                        "Milio", "Moakai", "Nasus", "Rek'Sai", "Seraphine", "Teemo", "Yone"},
                    # Add more costs as needed...
                },
                traits={"Arcanist", "Dragonlord", "Dryad", "Fated", "Ghostly", "Heavenly",
                       "Inkshadow", "Mythic", "Porcelain", "Sage", "Spirit Walker", "Storyweaver"},
                augments={"Best Friends", "Caretaker's Chosen", "Component Grab Bag", "Duplicator",
                         "Eastward Ho!", "Featherweights", "Gotta Go Fast", "Healing Orb",
                         "Hero Augment", "High Five", "Level Up!", "Lucky Gloves", "March of Progress",
                         "Pandora's Items", "Preparation", "Prismatic Ticket", "Rich Get Richer",
                         "Scoped Weapons", "Stand United", "Thrill of the Hunt", "Trade Sector"},
                items={"B.F. Sword", "Recurve Bow", "Chain Vest", "Negatron Cloak", "Giant's Belt",
                      "Needlessly Large Rod", "Tear of the Goddess", "Sparring Gloves", "Spatula"},
                last_updated=datetime.now()
            )
        
        return None
    
    async def get_available_patches(self) -> List[str]:
        """Get list of available patch versions"""
        # This would typically query APIs or scrape websites for available patches
        # For now, return hardcoded list of recent patches
        patches = [
            "15.17", "15.16", "15.15", "15.14", "15.13", "15.12", "15.11", "15.10",
            "15.9", "15.8", "15.7", "15.6", "15.5", "15.4", "15.3", "15.2", "15.1",
            "14.24", "14.23", "14.22", "14.21", "14.20"
        ]
        
        return patches
    
    async def get_patch_data(self, patch_version: str, force_refresh: bool = False) -> Optional[PatchData]:
        """Get patch data with caching"""
        
        # Check memory cache first
        if not force_refresh and patch_version in self._patch_cache:
            cached_data = self._patch_cache[patch_version]
            if datetime.now() - cached_data.last_updated < self.cache_duration:
                return cached_data
        
        # Check file cache
        if not force_refresh:
            cached_data = await self._load_from_cache(patch_version)
            if cached_data:
                self._patch_cache[patch_version] = cached_data
                return cached_data
        
        # Fetch new data
        print(f"Fetching patch data for {patch_version}...")
        patch_data = await self._fetch_patch_data_from_sources(patch_version)
        
        if patch_data:
            # Save to caches
            self._patch_cache[patch_version] = patch_data
            await self._save_to_cache(patch_data)
            return patch_data
        
        return None
    
    def validate_content(self, patch_data: PatchData, content: str) -> Dict[str, List[str]]:
        """Validate content against patch data"""
        
        # Get all valid names
        all_champions = set()
        for champions_by_cost in patch_data.champions.values():
            all_champions.update(champions_by_cost)
        
        # Find invalid content
        invalid_champions = []
        invalid_traits = []
        invalid_augments = []
        invalid_items = []
        
        # Check for champion names (case insensitive)
        for champion in all_champions:
            # Look for champion names that might appear in different forms
            champion_lower = champion.lower()
            if champion_lower in content.lower():
                continue  # Valid champion found
        
        # Simple validation - look for words that might be invalid champions
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
        
        for word in words:
            word_clean = word.strip(".,!?:")
            
            # Check champions
            if word_clean not in all_champions and word_clean.lower() not in [c.lower() for c in all_champions]:
                # Check if it might be a champion name
                if any(char.isupper() for char in word_clean) and len(word_clean) > 3:
                    invalid_champions.append(word_clean)
            
            # Check traits
            if word_clean not in patch_data.traits and word_clean.lower() not in [t.lower() for t in patch_data.traits]:
                if word_clean.endswith(('er', 'or', 'ian', 'ist')) or 'trait' in content.lower():
                    invalid_traits.append(word_clean)
        
        return {
            'invalid_champions': list(set(invalid_champions)),
            'invalid_traits': list(set(invalid_traits)),
            'invalid_augments': invalid_augments,
            'invalid_items': invalid_items
        }
    
    async def clear_cache(self, patch_version: str = None) -> None:
        """Clear cache for specific patch or all patches"""
        if patch_version:
            # Clear specific patch
            cache_file = self._get_cache_file(patch_version)
            if cache_file.exists():
                cache_file.unlink()
            if patch_version in self._patch_cache:
                del self._patch_cache[patch_version]
        else:
            # Clear all cache
            for cache_file in self.cache_dir.glob("patch_*.json"):
                cache_file.unlink()
            self._patch_cache.clear()