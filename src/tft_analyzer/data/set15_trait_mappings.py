#!/usr/bin/env python3
"""
TFT Set 15: K.O. Coliseum - ACCURATE Champion Trait Mappings
Updated on 2025-09-15 with 100% accurate Set 15 data from user JSON
Contains all 26 traits and 65 champions with correct mappings
"""

from typing import Dict, List, NamedTuple


class ChampionTraits(NamedTuple):
    """Champion trait information."""
    name: str
    cost: int
    traits: List[str]
    primary_trait: str
    secondary_trait: str


# ACCURATE Set 15 champion-trait mappings (100% game data accuracy)
SET15_CHAMPION_TRAITS: Dict[str, ChampionTraits] = {
    "Aatrox": ChampionTraits("Aatrox", 5, ['Mighty Mech', 'Heavyweight', 'Juggernaut'], "Mighty Mech", "Heavyweight"),
    "Ahri": ChampionTraits("Ahri", 3, ['Star Guardian', 'Sorcerer'], "Star Guardian", "Sorcerer"),
    "Akali": ChampionTraits("Akali", 4, ['Supreme Cells', 'Executioner'], "Supreme Cells", "Executioner"),
    "Ashe": ChampionTraits("Ashe", 4, ['Crystal Gambit', 'Duelist'], "Crystal Gambit", "Duelist"),
    "Braum": ChampionTraits("Braum", 5, ['The Champ', 'Luchador', 'Bastion'], "The Champ", "Luchador"),
    "Caitlyn": ChampionTraits("Caitlyn", 2, ['Battle Academia', 'Sniper'], "Battle Academia", "Sniper"),
    "Darius": ChampionTraits("Darius", 4, ['Supreme Cells', 'Heavyweight'], "Supreme Cells", "Heavyweight"),
    "Dr. Mundo": ChampionTraits("Dr. Mundo", 4, ['Luchador', 'Juggernaut'], "Luchador", "Juggernaut"),
    "Ekko": ChampionTraits("Ekko", 3, ['Prodigy', 'Sorcerer', 'Strategist'], "Prodigy", "Sorcerer"),
    "Ezreal": ChampionTraits("Ezreal", 2, ['Battle Academia', 'Prodigy'], "Battle Academia", "Prodigy"),
    "Gangplank": ChampionTraits("Gangplank", 3, ['Mighty Mech', 'Duelist'], "Mighty Mech", "Duelist"),
    "Garen": ChampionTraits("Garen", 2, ['Battle Academia', 'Bastion'], "Battle Academia", "Bastion"),
    "Gnar": ChampionTraits("Gnar", 1, ['Luchador', 'Sniper'], "Luchador", "Sniper"),
    "Gwen": ChampionTraits("Gwen", 3, ['Soul Fighter', 'Sorcerer'], "Soul Fighter", "Sorcerer"),
    "Janna": ChampionTraits("Janna", 4, ['Crystal Gambit', 'Protector', 'Strategist'], "Crystal Gambit", "Protector"),
    "Jarvan IV": ChampionTraits("Jarvan IV", 5, ['Mighty Mech', 'Strategist'], "Mighty Mech", "Strategist"),
    "Jayce": ChampionTraits("Jayce", 3, ['Battle Academia', 'Heavyweight'], "Battle Academia", "Heavyweight"),
    "Jhin": ChampionTraits("Jhin", 3, ['Wraith', 'Sniper'], "Wraith", "Sniper"),
    "Jinx": ChampionTraits("Jinx", 3, ['Star Guardian', 'Sniper'], "Star Guardian", "Sniper"),
    "K'Sante": ChampionTraits("K'Sante", 2, ['Wraith', 'Protector'], "Wraith", "Protector"),
    "Kai'Sa": ChampionTraits("Kai'Sa", 4, ['Supreme Cells', 'Duelist'], "Supreme Cells", "Duelist"),
    "Kalista": ChampionTraits("Kalista", 3, ['Soul Fighter', 'Executioner'], "Soul Fighter", "Executioner"),
    "Karma": ChampionTraits("Karma", 3, ['Mighty Mech', 'Sorcerer'], "Mighty Mech", "Sorcerer"),
    "Katarina": ChampionTraits("Katarina", 3, ['Battle Academia', 'Executioner'], "Battle Academia", "Executioner"),
    "Kayle": ChampionTraits("Kayle", 4, ['Wraith', 'Duelist'], "Wraith", "Duelist"),
    "Kennen": ChampionTraits("Kennen", 3, ['Supreme Cells', 'Protector', 'Sorcerer'], "Supreme Cells", "Protector"),
    "Kobuko": ChampionTraits("Kobuko", 5, ['Mentor', 'Heavyweight'], "Mentor", "Heavyweight"),
    "Kog'Maw": ChampionTraits("Kog'Maw", 1, ['Monster Trainer'], "Monster Trainer", ""),
    "Lee Sin": ChampionTraits("Lee Sin", 5, ['Stance Master', 'Duelist', 'Juggernaut', 'Executioner'], "Stance Master", "Duelist"),
    "Leona": ChampionTraits("Leona", 2, ['Battle Academia', 'Bastion'], "Battle Academia", "Bastion"),
    "Lucian": ChampionTraits("Lucian", 3, ['Mighty Mech', 'Sorcerer'], "Mighty Mech", "Sorcerer"),
    "Lulu": ChampionTraits("Lulu", 1, ['Monster Trainer'], "Monster Trainer", ""),
    "Lux": ChampionTraits("Lux", 3, ['Soul Fighter', 'Sorcerer'], "Soul Fighter", "Sorcerer"),
    "Malphite": ChampionTraits("Malphite", 1, ['The Crew', 'Protector'], "The Crew", "Protector"),
    "Malzahar": ChampionTraits("Malzahar", 4, ['Wraith', 'Prodigy'], "Wraith", "Prodigy"),
    "Naafiri": ChampionTraits("Naafiri", 4, ['Soul Fighter', 'Juggernaut'], "Soul Fighter", "Juggernaut"),
    "Neeko": ChampionTraits("Neeko", 2, ['Star Guardian', 'Protector'], "Star Guardian", "Protector"),
    "Poppy": ChampionTraits("Poppy", 2, ['Star Guardian', 'Heavyweight'], "Star Guardian", "Heavyweight"),
    "Rakan": ChampionTraits("Rakan", 2, ['Battle Academia', 'Protector'], "Battle Academia", "Protector"),
    "Rammus": ChampionTraits("Rammus", 1, ['Monster Trainer'], "Monster Trainer", ""),
    "Rell": ChampionTraits("Rell", 2, ['Star Guardian', 'Bastion'], "Star Guardian", "Bastion"),
    "Ryze": ChampionTraits("Ryze", 5, ['Mentor', 'Executioner', 'Strategist'], "Mentor", "Executioner"),
    "Samira": ChampionTraits("Samira", 3, ['Soul Fighter', 'Edgelord'], "Soul Fighter", "Edgelord"),
    "Senna": ChampionTraits("Senna", 3, ['Mighty Mech', 'Executioner'], "Mighty Mech", "Executioner"),
    "Seraphine": ChampionTraits("Seraphine", 5, ['Star Guardian', 'Prodigy'], "Star Guardian", "Prodigy"),
    "Sett": ChampionTraits("Sett", 4, ['Soul Fighter', 'Juggernaut'], "Soul Fighter", "Juggernaut"),
    "Shen": ChampionTraits("Shen", 3, ['The Crew', 'Bastion', 'Edgelord'], "The Crew", "Bastion"),
    "Sivir": ChampionTraits("Sivir", 1, ['The Crew', 'Sniper'], "The Crew", "Sniper"),
    "Smolder": ChampionTraits("Smolder", 1, ['Monster Trainer'], "Monster Trainer", ""),
    "Swain": ChampionTraits("Swain", 3, ['Crystal Gambit', 'Bastion', 'Sorcerer'], "Crystal Gambit", "Bastion"),
    "Syndra": ChampionTraits("Syndra", 4, ['Crystal Gambit', 'Star Guardian', 'Prodigy'], "Crystal Gambit", "Star Guardian"),
    "Twisted Fate": ChampionTraits("Twisted Fate", 2, ['Rogue Captain', 'The Crew'], "Rogue Captain", "The Crew"),
    "Udyr": ChampionTraits("Udyr", 5, ['Mentor', 'Juggernaut', 'Duelist'], "Mentor", "Juggernaut"),
    "Varus": ChampionTraits("Varus", 2, ['Wraith', 'Sniper'], "Wraith", "Sniper"),
    "Vi": ChampionTraits("Vi", 4, ['Crystal Gambit', 'Juggernaut'], "Crystal Gambit", "Juggernaut"),
    "Viego": ChampionTraits("Viego", 4, ['Soul Fighter', 'Duelist'], "Soul Fighter", "Duelist"),
    "Volibear": ChampionTraits("Volibear", 4, ['Luchador', 'Edgelord'], "Luchador", "Edgelord"),
    "Xayah": ChampionTraits("Xayah", 3, ['Star Guardian', 'Edgelord'], "Star Guardian", "Edgelord"),
    "Xin Zhao": ChampionTraits("Xin Zhao", 3, ['Soul Fighter', 'Bastion'], "Soul Fighter", "Bastion"),
    "Yasuo": ChampionTraits("Yasuo", 4, ['Mentor', 'Edgelord'], "Mentor", "Edgelord"),
    "Yone": ChampionTraits("Yone", 4, ['Mighty Mech', 'Edgelord'], "Mighty Mech", "Edgelord"),
    "Yuumi": ChampionTraits("Yuumi", 2, ['Battle Academia', 'Prodigy'], "Battle Academia", "Prodigy"),
    "Zac": ChampionTraits("Zac", 4, ['Wraith', 'Heavyweight'], "Wraith", "Heavyweight"),
    "Ziggs": ChampionTraits("Ziggs", 1, ['The Crew', 'Strategist'], "The Crew", "Strategist"),
    "Zyra": ChampionTraits("Zyra", 4, ['Crystal Gambit', 'Rosemother'], "Crystal Gambit", "Rosemother"),

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


# ACCURATE trait information for Set 15 (26 total traits)
TRAIT_INFO = {
    # Origins (team-based traits)
    "Star Guardian": {
        "name": "Star Guardian",
        "description": "Star Guardian champions cast spells faster and gain mana on ally death",
        "synergy_thresholds": [3, 5, 7, 9],
        "type": "origin",
        "champions": 8
    },
    "Battle Academia": {
        "name": "Battle Academia",
        "description": "Battle Academia champions gain attack damage and ability power",
        "synergy_thresholds": [3, 5, 7],
        "type": "origin",
        "champions": 8
    },
    "Soul Fighter": {
        "name": "Soul Fighter",
        "description": "Soul Fighter champions gain attack speed and critical strike",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "origin",
        "champions": 8
    },
    "Mighty Mech": {
        "name": "Mighty Mech",
        "description": "Mighty Mech champions are powerful mechanical units with enhanced abilities",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "origin",
        "champions": 7
    },
    "Crystal Gambit": {
        "name": "Crystal Gambit",
        "description": "Crystal Gambit champions manipulate the board and gain tactical advantages",
        "synergy_thresholds": [3, 5, 7],
        "type": "origin",
        "champions": 6
    },
    "Wraith": {
        "name": "Wraith",
        "description": "Wraith champions are spectral beings with life steal abilities",
        "synergy_thresholds": [2, 4, 6],
        "type": "origin",
        "champions": 6
    },
    "The Crew": {
        "name": "The Crew",
        "description": "The Crew champions work together for enhanced teamwork bonuses",
        "synergy_thresholds": [3, 5, 7],
        "type": "origin",
        "champions": 5
    },
    "Supreme Cells": {
        "name": "Supreme Cells",
        "description": "Supreme Cells champions evolve and gain enhanced stats",
        "synergy_thresholds": [3, 5, 7],
        "type": "origin",
        "champions": 4
    },
    "Luchador": {
        "name": "Luchador",
        "description": "Luchador champions are wrestling fighters with special moves",
        "synergy_thresholds": [2, 4],
        "type": "origin",
        "champions": 4
    },

    # Classes (role-based traits)
    "Sorcerer": {
        "name": "Sorcerer",
        "description": "Sorcerer champions gain ability power and spell effectiveness",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 8
    },
    "Juggernaut": {
        "name": "Juggernaut",
        "description": "Juggernaut champions become unstoppable forces with damage reduction",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 7
    },
    "Duelist": {
        "name": "Duelist",
        "description": "Duelist champions gain attack speed and mobility",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 7
    },
    "Bastion": {
        "name": "Bastion",
        "description": "Bastion champions gain armor, magic resistance, and crowd control immunity",
        "synergy_thresholds": [2, 4, 6, 8],
        "type": "class",
        "champions": 7
    },
    "Heavyweight": {
        "name": "Heavyweight",
        "description": "Heavyweight champions gain health and crowd control resistance",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 6
    },
    "Executioner": {
        "name": "Executioner",
        "description": "Executioner champions deal bonus damage to low health enemies",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 6
    },
    "Sniper": {
        "name": "Sniper",
        "description": "Sniper champions gain attack range and critical strike damage",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 6
    },
    "Prodigy": {
        "name": "Prodigy",
        "description": "Prodigy champions gain experience faster and enhanced abilities",
        "synergy_thresholds": [2, 4],
        "type": "class",
        "champions": 6
    },
    "Protector": {
        "name": "Protector",
        "description": "Protector champions shield allies and provide defensive bonuses",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 6
    },
    "Edgelord": {
        "name": "Edgelord",
        "description": "Edgelord champions deal dark damage and gain power from eliminations",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 6
    },
    "Strategist": {
        "name": "Strategist",
        "description": "Strategist champions manipulate the battlefield with tactical abilities",
        "synergy_thresholds": [2, 4, 6],
        "type": "class",
        "champions": 5
    },

    # Unique/Special traits
    "Mentor": {
        "name": "Mentor",
        "description": "Mentor champions provide bonuses to nearby allies",
        "synergy_thresholds": [2, 4],
        "type": "unique",
        "champions": 4
    },
    "Monster Trainer": {
        "name": "Monster Trainer",
        "description": "Monster Trainer champions summon and control creatures",
        "synergy_thresholds": [2, 4],
        "type": "unique",
        "champions": 4
    },
    "The Champ": {
        "name": "The Champ",
        "description": "The Champ trait provides unique championship bonuses",
        "synergy_thresholds": [1],
        "type": "unique",
        "champions": 1
    },
    "Stance Master": {
        "name": "Stance Master",
        "description": "Stance Master champions can switch between different combat forms",
        "synergy_thresholds": [1],
        "type": "unique",
        "champions": 1
    },
    "Rogue Captain": {
        "name": "Rogue Captain",
        "description": "Rogue Captain provides unique leadership abilities",
        "synergy_thresholds": [1],
        "type": "unique",
        "champions": 1
    },
    "Rosemother": {
        "name": "Rosemother",
        "description": "Rosemother trait provides nature-based bonuses",
        "synergy_thresholds": [1],
        "type": "unique",
        "champions": 1
    },
}

def get_trait_info(trait_name: str) -> Dict:
    """Get detailed information about a trait."""
    return TRAIT_INFO.get(trait_name, {})

def get_traits_by_type(trait_type: str) -> List[str]:
    """Get all traits of a specific type (origin, class, unique)."""
    return [
        trait_name
        for trait_name, info in TRAIT_INFO.items()
        if info.get("type") == trait_type
    ]

def get_champion_cost(champion_name: str) -> int:
    """Get the cost of a specific champion."""
    champion = SET15_CHAMPION_TRAITS.get(champion_name)
    return champion.cost if champion else 0

# Special champion notes
SPECIAL_CHAMPIONS = {
    "Ekko": "Available through augments only",
    "Lee Sin": "Has 4 traits (unique Stance Master)",
    "Braum": "Has 3 traits including unique The Champ",
}
