#!/usr/bin/env python3
"""
TFT Set 15 Endgame Units Database

Comprehensive database of all units available at different levels, with special focus
on level 8 and level 9 endgame compositions. Includes drop rates, key synergies,
and strategic value for real-time ML analysis.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class UnitTier(Enum):
    """Unit cost tiers"""
    ONE_COST = 1
    TWO_COST = 2
    THREE_COST = 3
    FOUR_COST = 4
    FIVE_COST = 5


@dataclass
class EndgameUnit:
    """Represents a unit with endgame focus information"""
    name: str
    cost: int
    traits: List[str]
    key_items: List[str]
    synergy_partners: List[str]
    endgame_viability: float  # 0.0-1.0 rating for late game
    level_8_priority: float   # Priority at level 8 (0.0-1.0)
    level_9_priority: float   # Priority at level 9 (0.0-1.0)
    positioning: str          # "front", "mid", "back"
    description: str


class TFTSet15EndgameDatabase:
    """Database of TFT Set 15 units with endgame focus"""

    def __init__(self):
        self.units = self._initialize_units()
        self.level_probabilities = self._initialize_level_probabilities()
        self.endgame_compositions = self._initialize_endgame_compositions()

    def _initialize_units(self) -> Dict[str, EndgameUnit]:
        """Initialize comprehensive unit database for Set 15"""
        return {
            # 1-Cost Units
            "Gnar": EndgameUnit(
                name="Gnar",
                cost=1,
                traits=["TheCrew", "Bruiser"],
                key_items=["Warmogs", "Gargoyle", "Bramble"],
                synergy_partners=["Jinx", "Caitlyn"],
                endgame_viability=0.3,
                level_8_priority=0.1,
                level_9_priority=0.05,
                positioning="front",
                description="Early game frontline, falls off late game"
            ),

            "Zoe": EndgameUnit(
                name="Zoe",
                cost=1,
                traits=["Star Guardian", "Sorcerer"],
                key_items=["AP items", "Mana items"],
                synergy_partners=["Ahri", "Seraphine"],
                endgame_viability=0.4,
                level_8_priority=0.2,
                level_9_priority=0.1,
                positioning="back",
                description="Early Star Guardian activator, useful for trait completion"
            ),

            "Tristana": EndgameUnit(
                name="Tristana",
                cost=1,
                traits=["Sniper", "Yordle"],
                key_items=["IE", "LW", "Giant Slayer"],
                synergy_partners=["Caitlyn", "Sivir"],
                endgame_viability=0.35,
                level_8_priority=0.15,
                level_9_priority=0.08,
                positioning="back",
                description="Sniper trait enabler, decent 3-star potential"
            ),

            "Ziggs": EndgameUnit(
                name="Ziggs",
                cost=1,
                traits=["Yordle", "Sorcerer"],
                key_items=["AP items", "Morello"],
                synergy_partners=["Ahri", "Tristana"],
                endgame_viability=0.3,
                level_8_priority=0.1,
                level_9_priority=0.05,
                positioning="back",
                description="AOE damage, synergy enabler"
            ),

            # 2-Cost Units
            "Caitlyn": EndgameUnit(
                name="Caitlyn",
                cost=2,
                traits=["Sniper", "TheCrew"],
                key_items=["IE", "LW", "Giant Slayer", "Runaans"],
                synergy_partners=["Sivir", "Jinx", "Tristana"],
                endgame_viability=0.7,
                level_8_priority=0.6,
                level_9_priority=0.4,
                positioning="back",
                description="Strong 3-star carry, excellent with Sniper trait"
            ),

            "Katarina": EndgameUnit(
                name="Katarina",
                cost=2,
                traits=["Assassin", "Star Guardian"],
                key_items=["IE", "LW", "BT"],
                synergy_partners=["Ahri", "Seraphine"],
                endgame_viability=0.6,
                level_8_priority=0.5,
                level_9_priority=0.3,
                positioning="back",
                description="High damage assassin, Star Guardian synergy"
            ),

            "Malphite": EndgameUnit(
                name="Malphite",
                cost=2,
                traits=["Protector", "Bruiser"],
                key_items=["Warmogs", "Gargoyle", "Bramble"],
                synergy_partners=["Shen", "Gnar"],
                endgame_viability=0.5,
                level_8_priority=0.4,
                level_9_priority=0.25,
                positioning="front",
                description="Solid frontline tank, good 3-star potential"
            ),

            # 3-Cost Units
            "Sivir": EndgameUnit(
                name="Sivir",
                cost=3,
                traits=["Sniper", "Protector"],
                key_items=["IE", "LW", "Giant Slayer", "QSS"],
                synergy_partners=["Caitlyn", "Tristana", "Shen"],
                endgame_viability=0.8,
                level_8_priority=0.8,
                level_9_priority=0.6,
                positioning="back",
                description="Premier Sniper carry, excellent scaling"
            ),

            "Jinx": EndgameUnit(
                name="Jinx",
                cost=3,
                traits=["TheCrew", "Rebel"],
                key_items=["IE", "LW", "Runaans", "Giant Slayer"],
                synergy_partners=["Caitlyn", "Gnar"],
                endgame_viability=0.75,
                level_8_priority=0.7,
                level_9_priority=0.5,
                positioning="back",
                description="High damage carry with reset potential"
            ),

            "Shen": EndgameUnit(
                name="Shen",
                cost=3,
                traits=["Protector", "Martial Artist"],
                key_items=["Warmogs", "Gargoyle", "Bramble"],
                synergy_partners=["Sivir", "Malphite"],
                endgame_viability=0.65,
                level_8_priority=0.6,
                level_9_priority=0.4,
                positioning="front",
                description="Strong tank with utility, Protector synergy"
            ),

            # 4-Cost Units (Level 8+ Focus)
            "Ahri": EndgameUnit(
                name="Ahri",
                cost=4,
                traits=["Star Guardian", "Sorcerer"],
                key_items=["JG", "IE", "Deathcap", "Shojin"],
                synergy_partners=["Seraphine", "Zoe", "Katarina"],
                endgame_viability=0.95,
                level_8_priority=0.95,
                level_9_priority=0.85,
                positioning="back",
                description="Premier magic carry, incredible scaling with items"
            ),

            "Akali": EndgameUnit(
                name="Akali",
                cost=4,
                traits=["Assassin", "Martial Artist"],
                key_items=["IE", "LW", "BT", "QSS"],
                synergy_partners=["Shen", "Katarina"],
                endgame_viability=0.85,
                level_8_priority=0.8,
                level_9_priority=0.7,
                positioning="back",
                description="High burst assassin, excellent with proper items"
            ),

            "Diana": EndgameUnit(
                name="Diana",
                cost=4,
                traits=["Protector", "Sorcerer"],
                key_items=["AP items", "Tank items"],
                synergy_partners=["Shen", "Ahri"],
                endgame_viability=0.75,
                level_8_priority=0.7,
                level_9_priority=0.6,
                positioning="front",
                description="Tanky AP unit, Protector frontline"
            ),

            "Draven": EndgameUnit(
                name="Draven",
                cost=4,
                traits=["Rebel", "Sniper"],
                key_items=["IE", "LW", "BT", "Giant Slayer"],
                synergy_partners=["Jinx", "Sivir"],
                endgame_viability=0.9,
                level_8_priority=0.9,
                level_9_priority=0.8,
                positioning="back",
                description="Strongest AD carry, requires protection"
            ),

            # 5-Cost Units (Level 9 Focus)
            "Seraphine": EndgameUnit(
                name="Seraphine",
                cost=5,
                traits=["Star Guardian", "Sorcerer"],
                key_items=["Shojin", "Deathcap", "IE", "Morello"],
                synergy_partners=["Ahri", "Zoe"],
                endgame_viability=1.0,
                level_8_priority=0.8,
                level_9_priority=1.0,
                positioning="back",
                description="Game-changing 5-cost, incredible team buffs and damage"
            ),

            "Gangplank": EndgameUnit(
                name="Gangplank",
                cost=5,
                traits=["TheCrew", "Bruiser"],
                key_items=["IE", "LW", "BT", "Warmogs"],
                synergy_partners=["Jinx", "Caitlyn"],
                endgame_viability=0.95,
                level_8_priority=0.75,
                level_9_priority=0.95,
                positioning="front",
                description="Tanky 5-cost carry with AOE damage"
            ),

            "Azir": EndgameUnit(
                name="Azir",
                cost=5,
                traits=["Sorcerer", "Emperor"],
                key_items=["Shojin", "Deathcap", "Morello"],
                synergy_partners=["Ahri", "Diana"],
                endgame_viability=0.9,
                level_8_priority=0.7,
                level_9_priority=0.9,
                positioning="back",
                description="AOE magic damage dealer, Emperor trait"
            ),

            "Jhin": EndgameUnit(
                name="Jhin",
                cost=5,
                traits=["Sniper", "Virtuoso"],
                key_items=["IE", "LW", "Giant Slayer", "QSS"],
                synergy_partners=["Sivir", "Caitlyn"],
                endgame_viability=1.0,
                level_8_priority=0.8,
                level_9_priority=1.0,
                positioning="back",
                description="Ultimate Sniper carry, incredible 1v9 potential"
            )
        }

    def _initialize_level_probabilities(self) -> Dict[int, Dict[int, float]]:
        """Initialize drop rate probabilities by level"""
        return {
            7: {1: 0.19, 2: 0.30, 3: 0.35, 4: 0.15, 5: 0.01},
            8: {1: 0.16, 2: 0.20, 3: 0.35, 4: 0.25, 5: 0.04},
            9: {1: 0.09, 2: 0.15, 3: 0.30, 4: 0.30, 5: 0.16}
        }

    def _initialize_endgame_compositions(self) -> Dict[str, Dict[str, Any]]:
        """Initialize endgame composition templates"""
        return {
            "Star Guardian Sorcerers": {
                "core_units": ["Ahri", "Seraphine"],
                "supporting_units": ["Zoe", "Katarina", "Diana"],
                "traits": ["Star Guardian", "Sorcerer"],
                "level_8_strength": 0.9,
                "level_9_strength": 1.0,
                "playstyle": "AP carry focused",
                "key_items": ["JG", "Deathcap", "Shojin", "IE"]
            },

            "Sniper Reroll": {
                "core_units": ["Sivir", "Jhin"],
                "supporting_units": ["Caitlyn", "Tristana", "Draven"],
                "traits": ["Sniper", "Protector"],
                "level_8_strength": 0.95,
                "level_9_strength": 1.0,
                "playstyle": "AD carry focused",
                "key_items": ["IE", "LW", "Giant Slayer", "QSS"]
            },

            "TheCrew Bruisers": {
                "core_units": ["Gangplank", "Jinx"],
                "supporting_units": ["Caitlyn", "Gnar", "Malphite"],
                "traits": ["TheCrew", "Bruiser"],
                "level_8_strength": 0.85,
                "level_9_strength": 0.9,
                "playstyle": "Tanky damage dealers",
                "key_items": ["IE", "LW", "BT", "Warmogs"]
            }
        }

    def get_level_8_priorities(self) -> List[Dict[str, Any]]:
        """Get units prioritized at level 8"""
        priorities = []
        for unit_name, unit in self.units.items():
            if unit.level_8_priority >= 0.7:
                priorities.append({
                    "name": unit_name,
                    "priority": unit.level_8_priority,
                    "cost": unit.cost,
                    "traits": unit.traits,
                    "description": unit.description
                })
        return sorted(priorities, key=lambda x: x["priority"], reverse=True)

    def get_level_9_priorities(self) -> List[Dict[str, Any]]:
        """Get units prioritized at level 9"""
        priorities = []
        for unit_name, unit in self.units.items():
            if unit.level_9_priority >= 0.8:
                priorities.append({
                    "name": unit_name,
                    "priority": unit.level_9_priority,
                    "cost": unit.cost,
                    "traits": unit.traits,
                    "description": unit.description
                })
        return sorted(priorities, key=lambda x: x["priority"], reverse=True)

    def get_endgame_recommendations(self, level: int, gold: int, current_units: List[str] = None) -> Dict[str, Any]:
        """Get endgame recommendations based on current state"""
        recommendations = {
            "level": level,
            "gold": gold,
            "priority_units": [],
            "composition_suggestions": [],
            "strategic_advice": ""
        }

        if level >= 8:
            # Focus on 4-cost and 5-cost units
            if level == 8:
                priorities = self.get_level_8_priorities()
                recommendations["strategic_advice"] = "Level 8: Focus on 4-cost carries and strong 3-cost units"
            else:
                priorities = self.get_level_9_priorities()
                recommendations["strategic_advice"] = "Level 9: Prioritize 5-cost game-changers"

            recommendations["priority_units"] = priorities[:5]  # Top 5 priorities

            # Suggest compositions based on current units
            if current_units:
                for comp_name, comp_data in self.endgame_compositions.items():
                    matches = sum(1 for unit in current_units if unit in comp_data["core_units"] + comp_data["supporting_units"])
                    if matches >= 2:
                        recommendations["composition_suggestions"].append({
                            "name": comp_name,
                            "match_score": matches,
                            "strength": comp_data[f"level_{level}_strength"] if f"level_{level}_strength" in comp_data else 0.8,
                            "needed_units": [u for u in comp_data["core_units"] if u not in (current_units or [])]
                        })

        return recommendations

    def get_unit_info(self, unit_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific unit"""
        if unit_name not in self.units:
            return {"error": f"Unit {unit_name} not found"}

        unit = self.units[unit_name]
        return {
            "name": unit.name,
            "cost": unit.cost,
            "traits": unit.traits,
            "key_items": unit.key_items,
            "synergy_partners": unit.synergy_partners,
            "endgame_viability": unit.endgame_viability,
            "level_8_priority": unit.level_8_priority,
            "level_9_priority": unit.level_9_priority,
            "positioning": unit.positioning,
            "description": unit.description
        }


# Global instance for easy access
endgame_db = TFTSet15EndgameDatabase()

if __name__ == "__main__":
    # Test the endgame database
    print("🎯 TFT Set 15 Endgame Database Test")
    print("=" * 50)

    print("\n📊 Level 8 Priorities:")
    for unit in endgame_db.get_level_8_priorities():
        print(f"  {unit['name']} ({unit['cost']}-cost): {unit['priority']:.1%} - {unit['description']}")

    print("\n🏆 Level 9 Priorities:")
    for unit in endgame_db.get_level_9_priorities():
        print(f"  {unit['name']} ({unit['cost']}-cost): {unit['priority']:.1%} - {unit['description']}")

    print("\n🎮 Sample Endgame Recommendation (Level 8, 50 gold):")
    rec = endgame_db.get_endgame_recommendations(8, 50, ["Ahri", "Sivir"])
    print(f"  Strategic Advice: {rec['strategic_advice']}")
    print(f"  Priority Units: {[u['name'] for u in rec['priority_units'][:3]]}")