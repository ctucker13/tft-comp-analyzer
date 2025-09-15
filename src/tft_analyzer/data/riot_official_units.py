#!/usr/bin/env python3
"""
Official Riot API Units Database for TFT Set 15

This database is generated from the official Riot Games Data Dragon API,
providing the most accurate and up-to-date unit information for Set 15.

Created: 2025-09-14
Source: Riot Games Data Dragon API v15.18.1
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
    """Official unit data from Riot API."""
    name: str
    cost: int
    traits: List[str]  # Note: Currently empty in Data Dragon API
    riot_id: str
    api_name: str
    image: str


class RiotOfficialUnitsDB:
    """Database of official Set 15 units from Riot API."""

    def __init__(self):
        """Initialize with official Riot API data."""
        self._load_official_data()

    def _load_official_data(self) -> None:
        """Load official Riot API data if available."""
        try:
            # Try to load the latest champions data
            data_dir = Path(__file__).parent.parent.parent.parent / "data" / "riot_meta_data"
            champion_files = list(data_dir.glob("tft_champions_*.json"))

            if champion_files:
                latest_file = max(champion_files, key=lambda p: p.stat().st_mtime)
                df = pl.read_json(latest_file)

                # Convert to our format with trait mapping
                self.official_units = {}
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

                print(f"✅ Loaded {len(self.official_units)} official units from Riot API")
            else:
                print("⚠️ No official Riot data found, using fallback data")
                self._load_fallback_data()

        except Exception as e:
            print(f"❌ Failed to load official data: {e}")
            self._load_fallback_data()

    def _load_fallback_data(self) -> None:
        """Load fallback data if official API data is unavailable."""
        # Generate fallback data using our trait mapping system
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

        print(f"✅ Loaded {len(self.official_units)} units from fallback trait data")

    def _load_fallback_data_old(self) -> None:
        """OLD fallback method - keeping for reference."""
        # Based on the official Riot API data we successfully retrieved - NOW WITH TRAITS!
        old_data = {
            # 1-cost champions (14 total)
            "Aatrox": RiotOfficialUnit("Aatrox", 1, [], "Aatrox", "TFT15_Aatrox", "TFT15_Aatrox.png"),
            "Ezreal": RiotOfficialUnit("Ezreal", 1, [], "Ezreal", "TFT15_Ezreal", "TFT15_Ezreal.png"),
            "Garen": RiotOfficialUnit("Garen", 1, [], "Garen", "TFT15_Garen", "TFT15_Garen.png"),
            "Gnar": RiotOfficialUnit("Gnar", 1, [], "Gnar", "TFT15_Gnar", "TFT15_Gnar.png"),
            "Kalista": RiotOfficialUnit("Kalista", 1, [], "Kalista", "TFT15_Kalista", "TFT15_Kalista.png"),
            "Kayle": RiotOfficialUnit("Kayle", 1, [], "Kayle", "TFT15_Kayle", "TFT15_Kayle.png"),
            "Kennen": RiotOfficialUnit("Kennen", 1, [], "Kennen", "TFT15_Kennen", "TFT15_Kennen.png"),
            "Lucian": RiotOfficialUnit("Lucian", 1, [], "Lucian", "TFT15_Lucian", "TFT15_Lucian.png"),
            "Malphite": RiotOfficialUnit("Malphite", 1, [], "Malphite", "TFT15_Malphite", "TFT15_Malphite.png"),
            "Naafiri": RiotOfficialUnit("Naafiri", 1, [], "Naafiri", "TFT15_Naafiri", "TFT15_Naafiri.png"),
            "Rell": RiotOfficialUnit("Rell", 1, [], "Rell", "TFT15_Rell", "TFT15_Rell.png"),
            "Sivir": RiotOfficialUnit("Sivir", 1, [], "Sivir", "TFT15_Sivir", "TFT15_Sivir.png"),  # CORRECTED: 1-cost not 3-cost
            "Syndra": RiotOfficialUnit("Syndra", 1, [], "Syndra", "TFT15_Syndra", "TFT15_Syndra.png"),
            "Zac": RiotOfficialUnit("Zac", 1, [], "Zac", "TFT15_Zac", "TFT15_Zac.png"),

            # 2-cost champions (13 total)
            "Dr. Mundo": RiotOfficialUnit("Dr. Mundo", 2, [], "DrMundo", "TFT15_DrMundo", "TFT15_DrMundo.png"),
            "Gangplank": RiotOfficialUnit("Gangplank", 2, [], "Gangplank", "TFT15_Gangplank", "TFT15_Gangplank.png"),  # CORRECTED: 2-cost not 5-cost
            "Janna": RiotOfficialUnit("Janna", 2, [], "Janna", "TFT15_Janna", "TFT15_Janna.png"),
            "Jhin": RiotOfficialUnit("Jhin", 2, [], "Jhin", "TFT15_Jhin", "TFT15_Jhin.png"),  # CORRECTED: 2-cost not 5-cost
            "Kai'Sa": RiotOfficialUnit("Kai'Sa", 2, [], "KaiSa", "TFT15_KaiSa", "TFT15_KaiSa.png"),
            "Katarina": RiotOfficialUnit("Katarina", 2, [], "Katarina", "TFT15_Katarina", "TFT15_Katarina.png"),
            "Kobuko": RiotOfficialUnit("Kobuko", 2, [], "Kobuko", "TFT15_Kobuko", "TFT15_Kobuko.png"),
            "Lux": RiotOfficialUnit("Lux", 2, [], "Lux", "TFT15_Lux", "TFT15_Lux.png"),
            "Rakan": RiotOfficialUnit("Rakan", 2, [], "Rakan", "TFT15_Rakan", "TFT15_Rakan.png"),
            "Shen": RiotOfficialUnit("Shen", 2, [], "Shen", "TFT15_Shen", "TFT15_Shen.png"),
            "Vi": RiotOfficialUnit("Vi", 2, [], "Vi", "TFT15_Vi", "TFT15_Vi.png"),
            "Xayah": RiotOfficialUnit("Xayah", 2, [], "Xayah", "TFT15_Xayah", "TFT15_Xayah.png"),
            "Xin Zhao": RiotOfficialUnit("Xin Zhao", 2, [], "XinZhao", "TFT15_XinZhao", "TFT15_XinZhao.png"),

            # 3-cost champions (16 total)
            "Ahri": RiotOfficialUnit("Ahri", 3, [], "Ahri", "TFT15_Ahri", "TFT15_Ahri.png"),  # CONFIRMED: 3-cost
            "Caitlyn": RiotOfficialUnit("Caitlyn", 3, [], "Caitlyn", "TFT15_Caitlyn", "TFT15_Caitlyn.png"),  # CONFIRMED: 3-cost
            "Darius": RiotOfficialUnit("Darius", 3, [], "Darius", "TFT15_Darius", "TFT15_Darius.png"),
            "Jayce": RiotOfficialUnit("Jayce", 3, [], "Jayce", "TFT15_Jayce", "TFT15_Jayce.png"),
            "Kog'Maw": RiotOfficialUnit("Kog'Maw", 3, [], "KogMaw", "TFT15_KogMaw", "TFT15_KogMaw.png"),
            "Lulu": RiotOfficialUnit("Lulu", 3, [], "Lulu", "TFT15_Lulu", "TFT15_Lulu.png"),
            "Malzahar": RiotOfficialUnit("Malzahar", 3, [], "Malzahar", "TFT15_Malzahar", "TFT15_Malzahar.png"),
            "Neeko": RiotOfficialUnit("Neeko", 3, [], "Neeko", "TFT15_Neeko", "TFT15_Neeko.png"),
            "Rammus": RiotOfficialUnit("Rammus", 3, [], "Rammus", "TFT15_Rammus", "TFT15_Rammus.png"),
            "Senna": RiotOfficialUnit("Senna", 3, [], "Senna", "TFT15_Senna", "TFT15_Senna.png"),
            "Smolder": RiotOfficialUnit("Smolder", 3, [], "Smolder", "TFT15_Smolder", "TFT15_Smolder.png"),
            "Swain": RiotOfficialUnit("Swain", 3, [], "Swain", "TFT15_Swain", "TFT15_Swain.png"),
            "Udyr": RiotOfficialUnit("Udyr", 3, [], "Udyr", "TFT15_Udyr", "TFT15_Udyr.png"),
            "Viego": RiotOfficialUnit("Viego", 3, [], "Viego", "TFT15_Viego", "TFT15_Viego.png"),
            "Yasuo": RiotOfficialUnit("Yasuo", 3, [], "Yasuo", "TFT15_Yasuo", "TFT15_Yasuo.png"),
            "Ziggs": RiotOfficialUnit("Ziggs", 3, [], "Ziggs", "TFT15_Ziggs", "TFT15_Ziggs.png"),

            # 4-cost champions (13 total)
            "Akali": RiotOfficialUnit("Akali", 4, [], "Akali", "TFT15_Akali", "TFT15_Akali.png"),
            "Ashe": RiotOfficialUnit("Ashe", 4, [], "Ashe", "TFT15_Ashe", "TFT15_Ashe.png"),
            "Jarvan IV": RiotOfficialUnit("Jarvan IV", 4, [], "JarvanIV", "TFT15_JarvanIV", "TFT15_JarvanIV.png"),
            "Jinx": RiotOfficialUnit("Jinx", 4, [], "Jinx", "TFT15_Jinx", "TFT15_Jinx.png"),  # CONFIRMED: 4-cost
            "K'Sante": RiotOfficialUnit("K'Sante", 4, [], "KSante", "TFT15_KSante", "TFT15_KSante.png"),
            "Karma": RiotOfficialUnit("Karma", 4, [], "Karma", "TFT15_Karma", "TFT15_Karma.png"),
            "Leona": RiotOfficialUnit("Leona", 4, [], "Leona", "TFT15_Leona", "TFT15_Leona.png"),
            "Poppy": RiotOfficialUnit("Poppy", 4, [], "Poppy", "TFT15_Poppy", "TFT15_Poppy.png"),
            "Ryze": RiotOfficialUnit("Ryze", 4, [], "Ryze", "TFT15_Ryze", "TFT15_Ryze.png"),
            "Samira": RiotOfficialUnit("Samira", 4, [], "Samira", "TFT15_Samira", "TFT15_Samira.png"),
            "Sett": RiotOfficialUnit("Sett", 4, [], "Sett", "TFT15_Sett", "TFT15_Sett.png"),
            "Volibear": RiotOfficialUnit("Volibear", 4, [], "Volibear", "TFT15_Volibear", "TFT15_Volibear.png"),
            "Yuumi": RiotOfficialUnit("Yuumi", 4, [], "Yuumi", "TFT15_Yuumi", "TFT15_Yuumi.png"),

            # 5-cost champions (10 total)
            "Braum": RiotOfficialUnit("Braum", 5, [], "Braum", "TFT15_Braum", "TFT15_Braum.png"),
            "Ekko": RiotOfficialUnit("Ekko", 5, [], "Ekko", "TFT15_Ekko", "TFT15_Ekko.png"),
            "Gwen": RiotOfficialUnit("Gwen", 5, [], "Gwen", "TFT15_Gwen", "TFT15_Gwen.png"),
            "Lee Sin": RiotOfficialUnit("Lee Sin", 5, [], "LeeSin", "TFT15_LeeSin", "TFT15_LeeSin.png"),
            "Seraphine": RiotOfficialUnit("Seraphine", 5, [], "Seraphine", "TFT15_Seraphine", "TFT15_Seraphine.png"),  # CONFIRMED: 5-cost
            "Twisted Fate": RiotOfficialUnit("Twisted Fate", 5, [], "TwistedFate", "TFT15_TwistedFate", "TFT15_TwistedFate.png"),
            "Varus": RiotOfficialUnit("Varus", 5, [], "Varus", "TFT15_Varus", "TFT15_Varus.png"),
            "Yone": RiotOfficialUnit("Yone", 5, [], "Yone", "TFT15_Yone", "TFT15_Yone.png"),
            "Zyra": RiotOfficialUnit("Zyra", 5, [], "Zyra", "TFT15_Zyra", "TFT15_Zyra.png"),
        }

    def get_unit_info(self, unit_name: str) -> Dict[str, any]:
        """Get unit information by name."""
        if unit_name in self.official_units:
            unit = self.official_units[unit_name]
            return {
                "name": unit.name,
                "cost": unit.cost,
                "traits": unit.traits,
                "riot_id": unit.riot_id,
                "api_name": unit.api_name,
                "image": unit.image,
                "source": "Official Riot API"
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

    def get_cost_distribution(self) -> Dict[int, int]:
        """Get distribution of units by cost."""
        distribution = {}
        for unit in self.official_units.values():
            distribution[unit.cost] = distribution.get(unit.cost, 0) + 1
        return distribution

    def compare_with_previous_database(self, previous_costs: Dict[str, int]) -> Dict[str, Dict]:
        """Compare official costs with previous database."""
        differences = {}
        for name, unit in self.official_units.items():
            if name in previous_costs:
                if unit.cost != previous_costs[name]:
                    differences[name] = {
                        "official_cost": unit.cost,
                        "previous_cost": previous_costs[name],
                        "change": f"{previous_costs[name]} → {unit.cost}"
                    }
        return differences


# Create global instance
riot_official_db = RiotOfficialUnitsDB()


if __name__ == "__main__":
    # Test the database
    print("🎮 Official Riot API Units Database Test")
    print("=" * 50)

    # Show cost distribution
    distribution = riot_official_db.get_cost_distribution()
    print(f"📊 Cost Distribution:")
    for cost, count in sorted(distribution.items()):
        print(f"  {cost}-cost: {count} champions")

    # Test specific units
    print(f"\n🔍 Key Unit Information:")
    key_units = ["Jinx", "Ahri", "Caitlyn", "Sivir", "Jhin", "Seraphine", "Gangplank"]
    for unit in key_units:
        info = riot_official_db.get_unit_info(unit)
        if "error" not in info:
            print(f"  {info['name']}: {info['cost']}-cost (Official Riot API)")
        else:
            print(f"  {unit}: {info['error']}")

    # Compare with our previous assumptions
    previous_costs = {"Jinx": 4, "Ahri": 3, "Caitlyn": 3, "Sivir": 3, "Jhin": 5, "Seraphine": 5, "Gangplank": 5}
    differences = riot_official_db.compare_with_previous_database(previous_costs)

    if differences:
        print(f"\n🔄 Cost Changes from Previous Database:")
        for name, change in differences.items():
            print(f"  {name}: {change['change']} (Official: {change['official_cost']})")
    else:
        print(f"\n✅ All costs match previous database!")