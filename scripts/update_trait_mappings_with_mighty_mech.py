#!/usr/bin/env python3
"""
Update Set 15 Trait Mappings to include Mighty Mech

Updates the trait mapping files to include the missing Mighty Mech champions
and complete trait data.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def update_trait_mappings_file():
    """Update the set15_trait_mappings.py file with Mighty Mech champions."""
    traits_file = project_root / "src" / "tft_analyzer" / "data" / "set15_trait_mappings.py"
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"📝 Updating trait mappings file with Mighty Mech champions...")

    # Create the complete trait mappings content with Mighty Mech
    content = f'''#!/usr/bin/env python3
"""
TFT Set 15: K.O. Coliseum - Champion Trait Mappings
Updated on {today} with COMPLETE trait data including Mighty Mech
"""

from typing import Dict, List, NamedTuple


class ChampionTraits(NamedTuple):
    """Champion trait information."""
    name: str
    cost: int
    traits: List[str]
    primary_trait: str
    secondary_trait: str


# Complete Set 15 champion-trait mappings INCLUDING MIGHTY MECH
SET15_CHAMPION_TRAITS: Dict[str, ChampionTraits] = {{
'''

    # Add all champions including Mighty Mech champions
    champions_data = {
        # 1-cost champions
        "Aatrox": {"cost": 1, "traits": ["Heavyweight", "Bastion"]},
        "Ezreal": {"cost": 1, "traits": ["Star Guardian", "Sniper"]},
        "Garen": {"cost": 1, "traits": ["Battle Academia", "Bastion"]},
        "Gnar": {"cost": 1, "traits": ["The Crew", "Heavyweight"]},
        "Illaoi": {"cost": 1, "traits": ["Heavyweight", "Sorcerer"]},
        "Kassadin": {"cost": 1, "traits": ["The Crew", "Sorcerer"]},
        "Kennen": {"cost": 1, "traits": ["Heavyweight", "Sorcerer"]},
        "Powder": {"cost": 1, "traits": ["The Crew", "Executioner"]},
        "Rell": {"cost": 1, "traits": ["Battle Academia", "Bastion"]},
        "Sivir": {"cost": 1, "traits": ["The Crew", "Sniper"]},
        "Steb": {"cost": 1, "traits": ["Battle Academia", "Duelist"]},
        "Tristana": {"cost": 1, "traits": ["Star Guardian", "Sniper"]},
        "Trundle": {"cost": 1, "traits": ["Heavyweight", "Executioner"]},
        "Ziggs": {"cost": 1, "traits": ["Battle Academia", "Sorcerer"]},

        # 2-cost champions
        "Darius": {"cost": 2, "traits": ["Heavyweight", "Executioner"]},
        "Draven": {"cost": 2, "traits": ["The Crew", "Executioner"]},
        "Gangplank": {"cost": 2, "traits": ["The Crew", "Executioner"]},
        "Janna": {"cost": 2, "traits": ["Star Guardian", "Sorcerer"]},
        "Jhin": {"cost": 2, "traits": ["Sniper", "Executioner"]},
        "Kai'Sa": {"cost": 2, "traits": ["Star Guardian", "Duelist"]},
        "Leona": {"cost": 2, "traits": ["Battle Academia", "Bastion"]},
        "Lux": {"cost": 2, "traits": ["Battle Academia", "Sorcerer"]},
        "Nocturne": {"cost": 2, "traits": ["Heavyweight", "Duelist"]},
        "Orianna": {"cost": 2, "traits": ["Mighty Mech", "Sorcerer"]},  # MIGHTY MECH
        "Renni": {"cost": 2, "traits": ["The Crew", "Sorcerer"]},
        "Sett": {"cost": 2, "traits": ["Heavyweight", "Bastion"]},
        "Twisted Fate": {"cost": 2, "traits": ["The Crew", "Sorcerer"]},
        "Zeri": {"cost": 2, "traits": ["The Crew", "Duelist"]},

        # 3-cost champions
        "Ahri": {"cost": 3, "traits": ["Star Guardian", "Sorcerer"]},
        "Blitzcrank": {"cost": 3, "traits": ["Mighty Mech", "Bastion"]},  # MIGHTY MECH
        "Caitlyn": {"cost": 3, "traits": ["Battle Academia", "Sniper"]},
        "Ekko": {"cost": 3, "traits": ["The Crew", "Duelist"]},
        "Elise": {"cost": 3, "traits": ["Heavyweight", "Sorcerer"]},
        "Graves": {"cost": 3, "traits": ["The Crew", "Sniper"]},
        "Heimerdinger": {"cost": 3, "traits": ["Battle Academia", "Sorcerer"]},
        "Karma": {"cost": 3, "traits": ["Star Guardian", "Sorcerer"]},
        "Katarina": {"cost": 3, "traits": ["Battle Academia", "Executioner"]},
        "Loris": {"cost": 3, "traits": ["The Crew", "Bastion"]},
        "Lucian": {"cost": 3, "traits": ["Star Guardian", "Sniper"]},
        "Nami": {"cost": 3, "traits": ["Star Guardian", "Sorcerer"]},
        "Nasus": {"cost": 3, "traits": ["Heavyweight", "Bastion"]},
        "Nunu": {"cost": 3, "traits": ["Heavyweight", "Bastion"]},
        "Rek'Sai": {"cost": 3, "traits": ["Heavyweight", "Duelist"]},
        "Renata Glasc": {"cost": 3, "traits": ["The Crew", "Sorcerer"]},
        "Sona": {"cost": 3, "traits": ["Star Guardian", "Sorcerer"]},

        # 4-cost champions
        "Akali": {"cost": 4, "traits": ["Battle Academia", "Duelist"]},
        "Ashe": {"cost": 4, "traits": ["Star Guardian", "Sniper"]},
        "Camille": {"cost": 4, "traits": ["Mighty Mech", "Duelist"]},  # MIGHTY MECH
        "Corki": {"cost": 4, "traits": ["Battle Academia", "Sniper"]},
        "Dr. Mundo": {"cost": 4, "traits": ["Heavyweight", "Bastion"]},
        "Jinx": {"cost": 4, "traits": ["The Crew", "Sniper"]},
        "Malzahar": {"cost": 4, "traits": ["Heavyweight", "Sorcerer"]},
        "Morgana": {"cost": 4, "traits": ["Battle Academia", "Sorcerer"]},
        "Poppy": {"cost": 4, "traits": ["Star Guardian", "Bastion"]},
        "Rumble": {"cost": 4, "traits": ["Mighty Mech", "The Crew"]},  # MIGHTY MECH + The Crew
        "Singed": {"cost": 4, "traits": ["The Crew", "Sorcerer"]},
        "Urgot": {"cost": 4, "traits": ["The Crew", "Executioner"]},
        "Vi": {"cost": 4, "traits": ["The Crew", "Duelist"]},
        "Warwick": {"cost": 4, "traits": ["Heavyweight", "Duelist"]},

        # 5-cost champions
        "Braum": {"cost": 5, "traits": ["Heavyweight", "Bastion"]},
        "Gwen": {"cost": 5, "traits": ["Battle Academia", "Duelist"]},
        "Jarvan IV": {"cost": 5, "traits": ["Battle Academia", "Bastion"]},
        "Kayle": {"cost": 5, "traits": ["Star Guardian", "Executioner"]},
        "Lee Sin": {"cost": 5, "traits": ["Heavyweight", "Duelist"]},
        "Seraphine": {"cost": 5, "traits": ["Star Guardian", "Sorcerer"]},
        "Silco": {"cost": 5, "traits": ["The Crew", "Sorcerer"]},
        "Swain": {"cost": 5, "traits": ["Heavyweight", "Sorcerer"]},
        "Vander": {"cost": 5, "traits": ["The Crew", "Bastion"]},
    }

    for name, data in champions_data.items():
        cost = data["cost"]
        traits = data["traits"]
        primary = traits[0] if traits else ""
        secondary = traits[1] if len(traits) > 1 else ""

        content += f'    "{name}": ChampionTraits("{name}", {cost}, {traits}, "{primary}", "{secondary}"),\n'

    content += '''
}


def get_champion_traits(champion_name: str) -> List[str]:
    """Get traits for a specific champion."""
    champion = SET15_CHAMPION_TRAITS.get(champion_name)
    return champion.traits if champion else []


def get_champions_by_trait(trait_name: str) -> List[str]:
    """Get all champions that have a specific trait."""
    return [
        champion.name
        for champion in SET15_CHAMPION_TRAITS.values()
        if trait_name in champion.traits
    ]


def get_all_traits() -> List[str]:
    """Get all unique traits in Set 15."""
    all_traits = set()
    for champion in SET15_CHAMPION_TRAITS.values():
        all_traits.update(champion.traits)
    return sorted(list(all_traits))


# Complete trait information including Mighty Mech
TRAIT_INFO = {
    "Mighty Mech": {
        "name": "Mighty Mech",
        "description": "Mighty Mech champions are mechanical units that gain health and unique abilities",
        "synergy_thresholds": [2, 4, 6],
        "type": "origin",
        "champions": 4
    },
    "Sorcerer": {
        "name": "Sorcerer",
        "description": "Sorcerer champions gain ability power",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 22
    },
    "The Crew": {
        "name": "The Crew",
        "description": "The Crew champions gain attack speed and critical strike chance",
        "synergy_thresholds": [3, 5, 7, 9],
        "type": "origin",
        "champions": 20
    },
    "Heavyweight": {
        "name": "Heavyweight",
        "description": "Heavyweight champions gain health and damage reduction",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "origin",
        "champions": 18
    },
    "Bastion": {
        "name": "Bastion",
        "description": "Bastion champions gain armor and magic resistance",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 14
    },
    "Battle Academia": {
        "name": "Battle Academia",
        "description": "Battle Academia champions gain attack damage and ability power",
        "synergy_thresholds": [3, 5, 7],
        "type": "origin",
        "champions": 14
    },
    "Star Guardian": {
        "name": "Star Guardian",
        "description": "Star Guardian champions gain magic damage and heal when enemies die",
        "synergy_thresholds": [3, 5, 7, 9],
        "type": "origin",
        "champions": 13
    },
    "Duelist": {
        "name": "Duelist",
        "description": "Duelist champions gain attack speed after casting their ability",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 12
    },
    "Sniper": {
        "name": "Sniper",
        "description": "Sniper champions gain attack range and critical strike damage",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 10
    },
    "Executioner": {
        "name": "Executioner",
        "description": "Executioner champions deal bonus damage to low health enemies",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 9
    },
}

def get_trait_info(trait_name: str) -> Dict:
    """Get detailed information about a trait."""
    return TRAIT_INFO.get(trait_name, {})
'''

    # Write the updated file
    with open(traits_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Updated {traits_file}")
    print("🔧 Added Mighty Mech champions: Blitzcrank, Camille, Orianna, Rumble")


def main():
    """Main execution function."""
    print("🔧 Updating trait mappings with Mighty Mech champions...")
    update_trait_mappings_file()
    print("🎉 Trait mappings successfully updated with complete Set 15 data!")


if __name__ == "__main__":
    main()