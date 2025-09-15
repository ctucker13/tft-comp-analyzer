"""
TFT Set 15: K.O. Coliseum validation data for champions and traits.
This file contains the official champion and trait lists to prevent hallucination
in LLM analysis results.
"""

from typing import Set, List, Dict

# TFT Set 15 Champions organized by cost
# Based on research from official TFT sources and community databases
TFT_SET15_CHAMPIONS_BY_COST = {
    1: {
        "Aatrox", "Akali", "Darius", "Ezreal", "Garen", "Gnar", "Kai'Sa", "Kalista", 
        "Kennen", "Kog'Maw", "Lulu", "Lucian", "Malphite", "Naafiri", "Poppy", 
        "Rammus", "Rell", "Sivir", "Smolder", "Syndra", "Twisted Fate", "Zac", "Ziggs"
    },
    2: {
        "Dr. Mundo", "Gangplank", "Janna", "Katarina", "Lee Sin", "Lux", "Rakan", 
        "Shen", "Vi", "Xayah", "Xin Zhao"
    },
    3: {
        "Ahri", "Caitlyn", "Jayce", "Jinx", "Neeko", "Senna", "Swain", "Udyr", 
        "Viego", "Yasuo"
    },
    4: {
        "Ashe", "Jarvan IV", "Jhin", "K'Sante", "Karma", "Kayle", "Leona", 
        "Malzahar", "Ryze", "Samira", "Sett", "Varus", "Volibear", "Yuumi"
    },
    5: {
        "Braum", "Gwen", "Seraphine", "Yone", "Zyra"
    }
}

# All TFT Set 15 Champions (flattened)
TFT_SET15_CHAMPIONS: Set[str] = set()
for cost_tier in TFT_SET15_CHAMPIONS_BY_COST.values():
    TFT_SET15_CHAMPIONS.update(cost_tier)

# TFT Set 15 Origin Traits
TFT_SET15_ORIGINS = {
    "Battle Academia",
    "Crystal Gambit", 
    "Luchador",
    "Mentor",
    "Mighty Mech",
    "Monster Trainer",
    "Rogue Captain",
    "Rosemother",
    "Soul Fighter",
    "Stance Master",
    "Star Guardian",
    "Supreme Cells",
    "The Champ",
    "The Crew",
    "Wraith"
}

# TFT Set 15 Class Traits
TFT_SET15_CLASSES = {
    "Bastion",
    "Duelist", 
    "Edgelord",
    "Heavyweight",
    "Juggernaut",
    "Prodigy",
    "Protector",
    "Sniper",
    "Sorcerer",
    "Strategist"
}

# All TFT Set 15 Traits (combined)
TFT_SET15_TRAITS: Set[str] = TFT_SET15_ORIGINS.union(TFT_SET15_CLASSES)

# Champions that are commonly hallucinated but NOT in Set 15
COMMONLY_HALLUCINATED_CHAMPIONS = {
    "Viktor",        # From previous sets
    "Blitzcrank",    # From previous sets  
    "Heimerdinger",  # From previous sets
    "Teemo",         # From previous sets
    "Kha'Zix",       # From previous sets
    "Cho'Gath",      # From previous sets
    "Cassiopeia",    # From Set 14 (Black Rose)
    "Elise",         # From Set 14 (Black Rose)
    "LeBlanc",       # From Set 14 (Black Rose)
    "Vladimir",      # From Set 14 (Black Rose)
    "Kassadin",      # From previous sets
    "Vex",           # From previous sets
    "Vel'Koz"        # From previous sets
}

# Traits that are commonly hallucinated but NOT in Set 15
COMMONLY_HALLUCINATED_TRAITS = {
    "Black Rose",    # From Set 14
    "OldMentor",     # Non-existent trait
    "Void",          # From previous sets
    "Yordle",        # From previous sets
    "Scrap",         # From previous sets
    "Academy",       # From previous sets
    "Chemtech",      # From previous sets
    "Clockwork",     # From previous sets
    "Syndicate",     # From previous sets
    "Rebel",         # From previous sets
    "Socialite"      # From previous sets
}


def validate_champion(champion_name: str) -> bool:
    """
    Validate if a champion exists in TFT Set 15.
    
    Args:
        champion_name: Name of the champion to validate
        
    Returns:
        bool: True if champion exists in Set 15, False otherwise
    """
    return champion_name in TFT_SET15_CHAMPIONS


def validate_trait(trait_name: str) -> bool:
    """
    Validate if a trait exists in TFT Set 15.
    
    Args:
        trait_name: Name of the trait to validate
        
    Returns:
        bool: True if trait exists in Set 15, False otherwise
    """
    return trait_name in TFT_SET15_TRAITS


def get_champion_cost(champion_name: str) -> int:
    """
    Get the cost tier of a champion in TFT Set 15.
    
    Args:
        champion_name: Name of the champion
        
    Returns:
        int: Cost tier (1-5) or 0 if champion doesn't exist
    """
    for cost, champions in TFT_SET15_CHAMPIONS_BY_COST.items():
        if champion_name in champions:
            return cost
    return 0


def filter_valid_champions(champion_list: List[str]) -> List[str]:
    """
    Filter a list to only include valid Set 15 champions.
    
    Args:
        champion_list: List of champion names to filter
        
    Returns:
        List[str]: Filtered list containing only valid Set 15 champions
    """
    return [champ for champ in champion_list if validate_champion(champ)]


def filter_valid_traits(trait_list: List[str]) -> List[str]:
    """
    Filter a list to only include valid Set 15 traits.
    
    Args:
        trait_list: List of trait names to filter
        
    Returns:
        List[str]: Filtered list containing only valid Set 15 traits
    """
    return [trait for trait in trait_list if validate_trait(trait)]


def identify_hallucinated_champions(champion_list: List[str]) -> List[str]:
    """
    Identify commonly hallucinated champions in a list.
    
    Args:
        champion_list: List of champion names to check
        
    Returns:
        List[str]: List of hallucinated champions found
    """
    return [champ for champ in champion_list if champ in COMMONLY_HALLUCINATED_CHAMPIONS]


def identify_hallucinated_traits(trait_list: List[str]) -> List[str]:
    """
    Identify commonly hallucinated traits in a list.
    
    Args:
        trait_list: List of trait names to check
        
    Returns:
        List[str]: List of hallucinated traits found
    """
    return [trait for trait in trait_list if trait in COMMONLY_HALLUCINATED_TRAITS]


def validate_analysis_text(text: str) -> Dict[str, List[str]]:
    """
    Validate analysis text for hallucinated champions and traits.
    
    Args:
        text: Analysis text to validate
        
    Returns:
        Dict containing validation results with keys:
        - invalid_champions: List of invalid champions found
        - invalid_traits: List of invalid traits found
        - hallucinated_champions: List of commonly hallucinated champions
        - hallucinated_traits: List of commonly hallucinated traits
    """
    import re
    
    # Extract potential champion names (capitalized words)
    potential_champions = re.findall(r'\b[A-Z][a-z\']+(?:\s[A-Z][a-z]+)*\b', text)
    
    # Extract potential trait names (look for trait-like patterns)
    potential_traits = re.findall(r'\b[A-Z][a-z]*(?:\s[A-Z][a-z]*)*\b', text)
    
    invalid_champions = [champ for champ in potential_champions if not validate_champion(champ) and len(champ) > 2]
    invalid_traits = [trait for trait in potential_traits if not validate_trait(trait) and len(trait) > 3]
    
    hallucinated_champions = identify_hallucinated_champions(potential_champions)
    hallucinated_traits = identify_hallucinated_traits(potential_traits)
    
    return {
        "invalid_champions": invalid_champions,
        "invalid_traits": invalid_traits, 
        "hallucinated_champions": hallucinated_champions,
        "hallucinated_traits": hallucinated_traits
    }


# Set 15 specific information for prompts
SET15_CONTEXT = {
    "set_number": 15,
    "set_name": "K.O. Coliseum",
    "current_patch": "15.3",
    "key_mechanic": "Power Snax system - 2 power-ups per game (rounds 1-3 and 3-6)",
    "special_features": [
        "3-star 5-costs have CC immunity and 20 mana regen",
        "Longer games (40+ rounds common)",
        "3 augments per game",
        "Role-based gameplay"
    ]
}

def get_set15_validation_prompt() -> str:
    """
    Generate a validation prompt for Set 15 analysis.
    
    Returns:
        str: Prompt text with validation requirements
    """
    champions_text = ", ".join(sorted(list(TFT_SET15_CHAMPIONS)[:20]))  # First 20 for brevity
    traits_text = ", ".join(sorted(list(TFT_SET15_TRAITS)))
    
    return f"""
STRICT SET 15 VALIDATION REQUIREMENTS:

ONLY use these EXACT champion names from Set 15: {champions_text}... (and others in the official roster)

ONLY use these EXACT trait names from Set 15: {traits_text}

NEVER mention these hallucinated units: {", ".join(COMMONLY_HALLUCINATED_CHAMPIONS)}

NEVER mention these invalid traits: {", ".join(COMMONLY_HALLUCINATED_TRAITS)}

Current Set: {SET15_CONTEXT["set_number"]} - {SET15_CONTEXT["set_name"]}
Current Patch: {SET15_CONTEXT["current_patch"]}+
Key Mechanic: {SET15_CONTEXT["key_mechanic"]}
"""