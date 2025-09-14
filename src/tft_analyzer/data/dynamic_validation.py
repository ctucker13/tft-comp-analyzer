"""
Dynamic TFT validation system that works with any patch/set
"""
import re
from typing import Dict, List, Set, Optional
from .patch_data_manager import PatchData, PatchDataManager

class TFTValidator:
    """Dynamic TFT content validator that uses patch-specific data"""
    
    def __init__(self, patch_data: PatchData):
        self.patch_data = patch_data
        
        # Create case-insensitive lookup sets
        self.valid_champions = set()
        for champions_by_cost in patch_data.champions.values():
            self.valid_champions.update(champ.lower() for champ in champions_by_cost)
        
        self.valid_traits = {trait.lower() for trait in patch_data.traits}
        self.valid_augments = {augment.lower() for augment in patch_data.augments}
        self.valid_items = {item.lower() for item in patch_data.items}
        
        # Known hallucinated content that frequently appears
        self.commonly_hallucinated_champions = {
            "viktor", "blitzcrank", "heimerdinger", "teemo", "yasuo", "pyke",
            "shen", "zed", "lucian", "braum", "thresh", "azir", "vayne", 
            "ryze", "brand", "sejuani", "volibear", "draven", "aphelios",
            "olaf", "sett", "zilean", "xerath", "jhin", "kayn", "akshan"
        }
        
        self.commonly_hallucinated_traits = {
            "oldmentor", "mentor", "divine", "elderwood", "cultist", "warlord",
            "moonlight", "assassin", "mystic", "vanguard", "keeper", "duelist",
            "hunter", "shade", "enlightened", "spirit", "fortune", "ninja"
        }
    
    def validate_text(self, text: str) -> Dict[str, List[str]]:
        """Validate text content against patch data"""
        
        # Extract potential champion/trait names
        # Look for capitalized words that could be names
        potential_names = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z&][a-z]+)*\b', text)
        
        # Also look for words after common TFT keywords
        tft_keywords = ['champion', 'unit', 'trait', 'synergy', 'augment', 'item']
        for keyword in tft_keywords:
            pattern = rf'\b{keyword}s?\s+([A-Z][a-z]+(?:\s+[A-Z&][a-z]+)*)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            potential_names.extend(matches)
        
        invalid_champions = []
        invalid_traits = []
        invalid_augments = []
        invalid_items = []
        
        for name in potential_names:
            name_clean = name.strip(".,!?:()[]{}\"'").lower()
            
            # Skip common non-TFT words
            if name_clean in {'the', 'and', 'or', 'but', 'with', 'from', 'into', 'onto',
                             'upon', 'over', 'under', 'above', 'below', 'through', 'across',
                             'between', 'among', 'during', 'before', 'after', 'while',
                             'patch', 'set', 'meta', 'game', 'player', 'match', 'round',
                             'damage', 'health', 'mana', 'gold', 'level', 'tier', 'cost',
                             'early', 'mid', 'late', 'strong', 'weak', 'best', 'good',
                             'team', 'comp', 'composition', 'build', 'strategy', 'guide'}:
                continue
            
            # Check if it's a champion
            if len(name_clean) > 2 and not name_clean in self.valid_champions:
                # Check if it's a commonly hallucinated champion
                if name_clean in self.commonly_hallucinated_champions:
                    invalid_champions.append(name)
                # Or if it looks like a champion name (proper noun, not too common)
                elif self._looks_like_champion_name(name_clean, text):
                    invalid_champions.append(name)
            
            # Check if it's a trait
            if name_clean.endswith(('er', 'or', 'ian', 'ist', 'ian', 'ary')) or 'trait' in text.lower():
                if not name_clean in self.valid_traits:
                    if name_clean in self.commonly_hallucinated_traits:
                        invalid_traits.append(name)
                    elif self._looks_like_trait_name(name_clean, text):
                        invalid_traits.append(name)
        
        return {
            'invalid_champions': list(set(invalid_champions)),
            'invalid_traits': list(set(invalid_traits)),
            'invalid_augments': invalid_augments,
            'invalid_items': invalid_items,
            'patch_version': self.patch_data.patch_version,
            'set_info': f"Set {self.patch_data.set_number}: {self.patch_data.set_name}"
        }
    
    def _looks_like_champion_name(self, name: str, context: str) -> bool:
        """Heuristic to determine if a word looks like a champion name"""
        
        # Common indicators that suggest this is meant to be a champion
        champion_indicators = [
            'carry', 'unit', 'champion', 'character', '1-cost', '2-cost', '3-cost', 
            '4-cost', '5-cost', 'frontline', 'backline', 'damage dealer', 'tank',
            'support', 'assassin', 'marksman', 'mage', 'fighter'
        ]
        
        context_lower = context.lower()
        for indicator in champion_indicators:
            if indicator in context_lower and name in context_lower:
                # Check if they appear near each other
                name_pos = context_lower.find(name)
                indicator_pos = context_lower.find(indicator)
                if abs(name_pos - indicator_pos) < 50:  # Within 50 characters
                    return True
        
        # If name is mentioned with items or positioning
        if any(item_word in context_lower for item_word in ['items', 'positioning', 'build', 'itemization']):
            return True
        
        return False
    
    def _looks_like_trait_name(self, name: str, context: str) -> bool:
        """Heuristic to determine if a word looks like a trait name"""
        
        trait_indicators = [
            'trait', 'synergy', 'bonus', 'effect', 'buff', 'passive',
            'active', 'ability', 'team', 'composition', 'comp'
        ]
        
        context_lower = context.lower()
        for indicator in trait_indicators:
            if indicator in context_lower and name in context_lower:
                name_pos = context_lower.find(name)
                indicator_pos = context_lower.find(indicator)
                if abs(name_pos - indicator_pos) < 50:
                    return True
        
        return False
    
    def get_validation_prompt(self) -> str:
        """Get validation prompt for this patch"""
        
        # Create lists by cost for champions
        champion_lists = []
        for cost in sorted(self.patch_data.champions.keys()):
            champs = sorted(list(self.patch_data.champions[cost]))
            champion_lists.append(f"{cost}-cost: {', '.join(champs)}")
        
        champion_text = '\n'.join(champion_lists)
        traits_text = ', '.join(sorted(self.patch_data.traits))
        
        return f"""
CRITICAL VALIDATION REQUIREMENTS for Patch {self.patch_data.patch_version} (Set {self.patch_data.set_number}: {self.patch_data.set_name}):

APPROVED CHAMPIONS ONLY - DO NOT use any champion names not on this list:
{champion_text}

APPROVED TRAITS ONLY - DO NOT use any trait names not on this list:
{traits_text}

STRICTLY FORBIDDEN - These are commonly hallucinated and MUST NOT appear:
Champions: Viktor, Blitzcrank, Heimerdinger, Teemo, Yasuo, Pyke, Shen, Zed, Lucian, Braum, Thresh, Azir, Vayne
Traits: OldMentor, Mentor, Divine, Elderwood, Cultist, Warlord, Moonlight, Assassin, Mystic, Vanguard

VALIDATION RULE: Every champion and trait name you mention MUST be verified against the above lists before inclusion.
"""
    
    def create_validated_analysis_prompt(self, base_prompt: str) -> str:
        """Add validation requirements to an analysis prompt"""
        validation_prompt = self.get_validation_prompt()
        return f"{validation_prompt}\n\n{base_prompt}"


class ValidationManager:
    """Manages validation across different patches"""
    
    def __init__(self):
        self.patch_manager = PatchDataManager()
        self._validators_cache: Dict[str, TFTValidator] = {}
    
    async def get_validator(self, patch_version: str) -> Optional[TFTValidator]:
        """Get validator for specific patch version"""
        
        if patch_version in self._validators_cache:
            return self._validators_cache[patch_version]
        
        # Load patch data
        patch_data = await self.patch_manager.get_patch_data(patch_version)
        if not patch_data:
            return None
        
        # Create and cache validator
        validator = TFTValidator(patch_data)
        self._validators_cache[patch_version] = validator
        
        return validator
    
    async def validate_analysis_for_patch(self, patch_version: str, analysis_text: str) -> Dict:
        """Validate analysis text for specific patch"""
        
        validator = await self.get_validator(patch_version)
        if not validator:
            return {
                'error': f'Could not load validation data for patch {patch_version}',
                'invalid_champions': [],
                'invalid_traits': [],
                'invalid_augments': [],
                'invalid_items': []
            }
        
        return validator.validate_text(analysis_text)