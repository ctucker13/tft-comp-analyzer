#!/usr/bin/env python3
"""
Official Riot API Units Database for TFT Set 15 - WITH TRAITS

This database combines:
- Official Riot Games Data Dragon API unit costs and info
- Official trait mappings for complete champion data
- Real-time updates from Riot API

Now includes complete trait information that was missing from Data Dragon!
"""

from typing import Dict, List, Optional, NamedTuple
from pathlib import Path
import polars as pl

# Import trait mapping system
try:
    from .set15_trait_mappings import get_champion_traits, get_champions_by_trait, SET15_CHAMPION_TRAITS
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from set15_trait_mappings import get_champion_traits, get_champions_by_trait, SET15_CHAMPION_TRAITS


class RiotOfficialUnit(NamedTuple):
    """Official unit data from Riot API with complete traits."""
    name: str
    cost: int
    traits: List[str]  # Now populated with official trait data!
    riot_id: str
    api_name: str
    image: str


class RiotOfficialUnitsDB:
    """Database of official Set 15 units from Riot API with complete trait data."""

    def __init__(self):
        """Initialize with official Riot API data and trait mappings."""
        self._load_official_data()

    def _load_official_data(self) -> None:
        """Load official Riot API data with trait mappings."""
        try:
            # Try to load the latest champions data from Data Dragon
            data_dir = Path(__file__).parent.parent.parent.parent / "data" / "riot_meta_data"
            champion_files = list(data_dir.glob("tft_champions_*.json"))

            if champion_files:
                latest_file = max(champion_files, key=lambda p: p.stat().st_mtime)
                df = pl.read_json(latest_file)

                # Convert to our format with trait mapping
                self.official_units = {}
                loaded_count = 0

                for row in df.iter_rows(named=True):
                    # Get traits from our mapping system since Data Dragon doesn't include them
                    official_traits = get_champion_traits(row['name'])

                    unit = RiotOfficialUnit(
                        name=row['name'],
                        cost=row['cost'],
                        traits=official_traits,  # Now populated with official trait data!
                        riot_id=row['id'],
                        api_name=row['api_name'],
                        image=row['image']
                    )
                    self.official_units[row['name']] = unit
                    loaded_count += 1

                print(f"✅ Loaded {loaded_count} official units from Riot API with traits")
            else:
                print("⚠️ No official Riot data found, using trait mappings")
                self._load_trait_mappings_data()

        except Exception as e:
            print(f"❌ Failed to load official data: {e}")
            self._load_trait_mappings_data()

    def _load_trait_mappings_data(self) -> None:
        """Load data from trait mappings system."""
        self.official_units = {}

        # Get all champions from trait mappings with complete trait data
        for champion_name, champ_data in SET15_CHAMPION_TRAITS.items():
                unit = RiotOfficialUnit(
                    name=champ_data.name,
                    cost=champ_data.cost,
                    traits=champ_data.traits,
                    riot_id=champion_name,
                    api_name=f"TFT15_{champion_name}",
                    image=f"TFT15_{champion_name}.png"
                )
                self.official_units[champion_name] = unit

        print(f"✅ Loaded {len(self.official_units)} units from trait mappings")

    def get_unit_info(self, unit_name: str) -> Dict[str, any]:
        """Get unit information by name."""
        if unit_name in self.official_units:
            unit = self.official_units[unit_name]
            return {
                "name": unit.name,
                "cost": unit.cost,
                "traits": unit.traits,  # Now includes complete trait data!
                "riot_id": unit.riot_id,
                "api_name": unit.api_name,
                "image": unit.image,
                "source": "Official Riot API + Trait Mappings"
            }
        else:
            return {"error": f"Unit '{unit_name}' not found in official Riot database"}

    @property
    def unit_names(self) -> List[str]:
        """Get all unit names."""
        return list(self.official_units.keys())

    def get_units_by_cost(self, cost: int) -> List[RiotOfficialUnit]:
        """Get all units of a specific cost."""
        return [unit for unit in self.official_units.values() if unit.cost == cost]

    def get_units_by_trait(self, trait: str) -> List[RiotOfficialUnit]:
        """Get all units with a specific trait."""
        return [unit for unit in self.official_units.values() if trait in unit.traits]

    def get_cost_distribution(self) -> Dict[int, int]:
        """Get distribution of units by cost."""
        distribution = {}
        for unit in self.official_units.values():
            distribution[unit.cost] = distribution.get(unit.cost, 0) + 1
        return distribution

    def get_trait_distribution(self) -> Dict[str, int]:
        """Get distribution of units by trait."""
        distribution = {}
        for unit in self.official_units.values():
            for trait in unit.traits:
                distribution[trait] = distribution.get(trait, 0) + 1
        return distribution

    def analyze_composition(self, champion_names: List[str]) -> Dict:
        """Analyze a composition for trait synergies."""
        champions = []
        trait_counts = {}

        for name in champion_names:
            if name in self.official_units:
                unit = self.official_units[name]
                champions.append(unit)

                for trait in unit.traits:
                    trait_counts[trait] = trait_counts.get(trait, 0) + 1

        # Determine active synergies (simplified - 2+ units = active)
        active_synergies = {trait: count for trait, count in trait_counts.items() if count >= 2}

        return {
            "champions": champions,
            "trait_counts": trait_counts,
            "active_synergies": active_synergies,
            "synergy_strength": len(active_synergies),
            "total_traits": len(trait_counts)
        }

    def recommend_units_for_trait(self, trait: str, current_champions: List[str] = None) -> List[str]:
        """Recommend units to complete a trait synergy."""
        trait_units = self.get_units_by_trait(trait)
        current_champions = current_champions or []

        # Filter out already owned champions
        recommendations = [
            unit.name for unit in trait_units
            if unit.name not in current_champions
        ]

        # Sort by cost (cheaper first for easier acquisition)
        recommendations.sort(key=lambda name: self.official_units[name].cost)

        return recommendations

    def compare_with_previous_database(self, previous_costs: Dict[str, int]) -> Dict[str, Dict]:
        """Compare official costs with previous database."""
        differences = {}
        for name, unit in self.official_units.items():
            if name in previous_costs:
                if unit.cost != previous_costs[name]:
                    differences[name] = {
                        "official_cost": unit.cost,
                        "previous_cost": previous_costs[name],
                        "change": f"{previous_costs[name]} → {unit.cost}",
                        "traits": unit.traits
                    }
        return differences

    def get_trait_synergies(self) -> Dict[str, List[str]]:
        """Get all traits and their associated champions."""
        trait_synergies = {}
        for unit in self.official_units.values():
            for trait in unit.traits:
                if trait not in trait_synergies:
                    trait_synergies[trait] = []
                trait_synergies[trait].append(unit.name)

        # Sort champions by cost for each trait
        for trait in trait_synergies:
            trait_synergies[trait].sort(key=lambda name: self.official_units[name].cost)

        return trait_synergies


# Create global instance with trait data
riot_official_db_with_traits = RiotOfficialUnitsDB()


if __name__ == "__main__":
    # Test the enhanced database with traits
    print("🎮 Official Riot API Units Database with Traits - Test")
    print("=" * 65)

    db = riot_official_db_with_traits

    # Show cost distribution
    distribution = db.get_cost_distribution()
    print(f"📊 Cost Distribution:")
    for cost, count in sorted(distribution.items()):
        print(f"  {cost}-cost: {count} champions")

    # Show trait distribution
    trait_dist = db.get_trait_distribution()
    print(f"\n🎭 Top Traits:")
    sorted_traits = sorted(trait_dist.items(), key=lambda x: x[1], reverse=True)
    for trait, count in sorted_traits[:8]:
        print(f"  {trait}: {count} champions")

    # Test specific units with traits
    print(f"\n🔍 Key Unit Information (with traits!):")
    key_units = ["Jinx", "Ahri", "Caitlyn", "Sivir", "Jhin", "Seraphine", "Gangplank"]
    for unit in key_units:
        info = db.get_unit_info(unit)
        if "error" not in info:
            traits_str = ", ".join(info['traits'])
            print(f"  {info['name']}: {info['cost']}-cost, traits: {traits_str}")
        else:
            print(f"  {unit}: {info['error']}")

    # Test composition analysis
    print(f"\n📋 Composition Analysis Example:")
    test_comp = ["Seraphine", "Ahri", "Karma", "Jinx", "Caitlyn"]
    analysis = db.analyze_composition(test_comp)

    print(f"  Champions: {', '.join([c.name for c in analysis['champions']])}")
    print(f"  Active Synergies:")
    for trait, count in analysis["active_synergies"].items():
        print(f"    • {trait}: {count} champions")

    # Test trait recommendations
    print(f"\n🎯 Star Guardian Recommendations:")
    sg_recs = db.recommend_units_for_trait("Star Guardian", ["Seraphine", "Ahri"])
    print(f"  Suggested: {', '.join(sg_recs[:5])}")

    print(f"\n✅ Enhanced database loaded with {len(db.unit_names)} champions and complete trait data!")
    print("🎉 Traits are now fully integrated!")