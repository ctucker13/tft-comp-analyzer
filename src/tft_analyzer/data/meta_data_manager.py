#!/usr/bin/env python3
"""
TFT Meta Data Manager

Provides easy access to TFT Set 15 meta data as both JSON and Polars DataFrames.
Handles loading the latest data and provides convenient query methods.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import polars as pl

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


class TFTMetaDataManager:
    """Manager for TFT Set 15 meta data with Polars DataFrame support."""

    def __init__(self, data_path: Optional[Path] = None):
        """
        Initialize the meta data manager.

        Args:
            data_path: Path to meta data JSON file. If None, loads latest file.
        """
        self.data_path = data_path
        self.data: Dict[str, Any] = {}
        self._dataframes: Dict[str, pl.DataFrame] = {}

        # Auto-load data
        self.load_data()

    def load_data(self, data_path: Optional[Path] = None) -> None:
        """Load meta data from JSON file."""
        if data_path:
            self.data_path = data_path

        if not self.data_path:
            self.data_path = self._find_latest_meta_data_file()

        if not self.data_path or not self.data_path.exists():
            print("⚠️ No meta data file found. Run update_meta_data.py first.")
            self.data = self._get_empty_data_structure()
            return

        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)

            print(f"✅ Loaded meta data from: {self.data_path}")
            print(f"📅 Last updated: {self.data.get('meta_info', {}).get('last_updated', 'Unknown')}")
            print(f"🎮 Patch: {self.data.get('meta_info', {}).get('current_patch', 'Unknown')}")

            # Clear cached DataFrames
            self._dataframes.clear()

        except Exception as e:
            print(f"❌ Failed to load meta data: {e}")
            self.data = self._get_empty_data_structure()

    def _find_latest_meta_data_file(self) -> Optional[Path]:
        """Find the latest meta data JSON file."""
        data_dir = project_root / "data" / "meta_analysis"
        if not data_dir.exists():
            return None

        # Look for meta data files (prefer enhanced data with compositions)
        enhanced_files = list(data_dir.glob("tft15_enhanced_with_compositions_*.json"))
        accurate_set15_files = list(data_dir.glob("tft15_accurate_set15_data_*.json"))
        complete_traits_files = list(data_dir.glob("tft15_complete_traits_with_mighty_mech_*.json"))
        requests_html_files = list(data_dir.glob("tft15_requests_html_extracted_*.json"))
        complete_files = list(data_dir.glob("tft15_complete_meta_data_*.json"))
        meta_files = list(data_dir.glob("tft15_meta_data_*.json"))

        # Prefer enhanced files first (with compositions), then accurate Set 15 data
        all_files = enhanced_files + accurate_set15_files + complete_traits_files + requests_html_files + complete_files + meta_files

        if not all_files:
            return None

        # Return the most recent file
        return max(all_files, key=lambda x: x.stat().st_mtime)

    def _get_empty_data_structure(self) -> Dict[str, Any]:
        """Get empty data structure."""
        return {
            "meta_info": {
                "set_name": "TFT Set 15: K.O. Coliseum",
                "current_patch": "Unknown",
                "last_updated": "Never",
                "data_sources": []
            },
            "champions": [],
            "traits": [],
            "items": [],
            "artifacts": [],
            "power_ups": [],
            "augments": [],
            "compositions": [],
            "meta_tier_list": {}
        }

    def get_meta_info(self) -> Dict[str, Any]:
        """Get meta information about the data."""
        return self.data.get("meta_info", {})

    def get_champions_df(self) -> pl.DataFrame:
        """Get champions data as Polars DataFrame."""
        if "champions" not in self._dataframes:
            champions_data = []

            for champ in self.data.get("champions", []):
                flat_champ = {
                    "name": champ.get("name", "Unknown"),
                    "cost": champ.get("cost", 1),
                    "traits": "|".join(champ.get("traits", [])),
                    "health": champ.get("stats", {}).get("health", 0),
                    "mana": champ.get("stats", {}).get("mana", 0),
                    "armor": champ.get("stats", {}).get("armor", 0),
                    "magic_resist": champ.get("stats", {}).get("magic_resist", 0),
                    "attack_damage": champ.get("stats", {}).get("attack_damage", 0),
                    "attack_speed": champ.get("stats", {}).get("attack_speed", 0.6),
                    "attack_range": champ.get("stats", {}).get("attack_range", 1),
                    "ability_name": champ.get("ability", {}).get("name", ""),
                    "ability_description": champ.get("ability", {}).get("description", "")
                }
                champions_data.append(flat_champ)

            self._dataframes["champions"] = pl.DataFrame(champions_data) if champions_data else pl.DataFrame()

        return self._dataframes["champions"]

    def get_traits_df(self) -> pl.DataFrame:
        """Get traits data as Polars DataFrame."""
        if "traits" not in self._dataframes:
            traits_data = []

            for trait in self.data.get("traits", []):
                flat_trait = {
                    "name": trait.get("name", "Unknown"),
                    "description": trait.get("description", ""),
                    "type": trait.get("type", "unknown"),
                    "synergy_thresholds": "|".join(map(str, trait.get("synergy_thresholds", trait.get("breakpoints", [])))),
                    "champions": "|".join(trait.get("champions", [])),
                    "total_champions": trait.get("total_champions", len(trait.get("champions", [])))
                }
                traits_data.append(flat_trait)

            self._dataframes["traits"] = pl.DataFrame(traits_data) if traits_data else pl.DataFrame()

        return self._dataframes["traits"]

    def get_items_df(self) -> pl.DataFrame:
        """Get items data as Polars DataFrame."""
        if "items" not in self._dataframes:
            items_data = []

            for item in self.data.get("items", []):
                flat_item = {
                    "name": item.get("name", "Unknown"),
                    "description": item.get("description", ""),
                    "type": item.get("type", "unknown"),
                    "components": "|".join(item.get("components", [])),
                    "unique": item.get("unique", False)
                }
                items_data.append(flat_item)

            self._dataframes["items"] = pl.DataFrame(items_data) if items_data else pl.DataFrame()

        return self._dataframes["items"]

    def get_artifacts_df(self) -> pl.DataFrame:
        """Get artifacts data as Polars DataFrame."""
        if "artifacts" not in self._dataframes:
            self._dataframes["artifacts"] = pl.DataFrame(self.data.get("artifacts", []))

        return self._dataframes["artifacts"]

    def get_power_ups_df(self) -> pl.DataFrame:
        """Get power ups data as Polars DataFrame."""
        if "power_ups" not in self._dataframes:
            power_ups_data = []

            for power_up in self.data.get("power_ups", []):
                flat_power_up = {
                    "name": power_up.get("name", "Unknown"),
                    "description": power_up.get("description", ""),
                    "tier": power_up.get("tier", "B"),
                    "category": power_up.get("category", "unknown"),
                    "best_for": "|".join(power_up.get("best_for", []))
                }
                power_ups_data.append(flat_power_up)

            self._dataframes["power_ups"] = pl.DataFrame(power_ups_data) if power_ups_data else pl.DataFrame()

        return self._dataframes["power_ups"]

    def get_augments_df(self) -> pl.DataFrame:
        """Get augments data as Polars DataFrame."""
        if "augments" not in self._dataframes:
            self._dataframes["augments"] = pl.DataFrame(self.data.get("augments", []))

        return self._dataframes["augments"]

    def get_compositions_df(self) -> pl.DataFrame:
        """Get meta compositions data as Polars DataFrame."""
        if "compositions" not in self._dataframes:
            compositions_data = []

            for comp in self.data.get("compositions", []):
                flat_comp = {
                    "name": comp.get("name", "Unknown"),
                    "tier": comp.get("tier", "B"),
                    "avg_placement": comp.get("avg_placement", 4.0),
                    "play_rate": comp.get("play_rate", 0.0),
                    "win_rate": comp.get("win_rate", 0.0),
                    "top4_rate": comp.get("top4_rate", 0.0),
                    "sample_size": comp.get("sample_size", 0),
                    "patch": comp.get("patch", ""),
                    "primary_trait": comp.get("primary_trait", "Mixed"),
                    "key_champions": comp.get("key_champions", []),
                    "champions": "|".join(comp.get("key_champions", [])),
                    "traits": "|".join(comp.get("synergy_traits", [])),
                    "items": "|".join(comp.get("items", [])),
                    "source": comp.get("source", "meta_analysis"),
                    "difficulty": comp.get("difficulty", "Medium"),
                    "description": comp.get("description", ""),
                    "guide": comp.get("guide", "")
                }
                compositions_data.append(flat_comp)

            self._dataframes["compositions"] = pl.DataFrame(compositions_data) if compositions_data else pl.DataFrame()

        return self._dataframes["compositions"]

    def get_meta_tier_list(self) -> Dict[str, Any]:
        """Get the meta tier list data."""
        return self.data.get("meta_tier_list", {})

    def get_all_dataframes(self) -> Dict[str, pl.DataFrame]:
        """Get all meta data as Polars DataFrames."""
        return {
            "champions": self.get_champions_df(),
            "traits": self.get_traits_df(),
            "items": self.get_items_df(),
            "artifacts": self.get_artifacts_df(),
            "power_ups": self.get_power_ups_df(),
            "augments": self.get_augments_df(),
            "compositions": self.get_compositions_df()
        }

    def search_champions(self,
                        name: Optional[str] = None,
                        cost: Optional[int] = None,
                        traits: Optional[List[str]] = None,
                        min_health: Optional[int] = None) -> pl.DataFrame:
        """
        Search champions with filters.

        Args:
            name: Champion name (partial match)
            cost: Champion cost
            traits: List of traits to match
            min_health: Minimum health

        Returns:
            Filtered DataFrame
        """
        df = self.get_champions_df()

        if df.is_empty():
            return df

        # Apply filters
        if name:
            df = df.filter(pl.col("name").str.contains(name, literal=False))

        if cost is not None:
            df = df.filter(pl.col("cost") == cost)

        if traits:
            for trait in traits:
                df = df.filter(pl.col("traits").str.contains(trait))

        if min_health is not None:
            df = df.filter(pl.col("health") >= min_health)

        return df

    def search_items(self,
                    name: Optional[str] = None,
                    item_type: Optional[str] = None,
                    components: Optional[List[str]] = None) -> pl.DataFrame:
        """
        Search items with filters.

        Args:
            name: Item name (partial match)
            item_type: Item type (AD, AP, Tank, Utility)
            components: Components required

        Returns:
            Filtered DataFrame
        """
        df = self.get_items_df()

        if df.is_empty():
            return df

        # Apply filters
        if name:
            df = df.filter(pl.col("name").str.contains(name, literal=False))

        if item_type:
            df = df.filter(pl.col("type") == item_type)

        if components:
            for component in components:
                df = df.filter(pl.col("components").str.contains(component))

        return df

    def search_power_ups(self,
                        name: Optional[str] = None,
                        tier: Optional[str] = None,
                        champion: Optional[str] = None,
                        category: Optional[str] = None) -> pl.DataFrame:
        """
        Search power ups with filters.

        Args:
            name: Power up name (partial match)
            tier: Power up tier (S, A, B, C)
            champion: Champion name to find best power ups for
            category: Power up category

        Returns:
            Filtered DataFrame
        """
        df = self.get_power_ups_df()

        if df.is_empty():
            return df

        # Apply filters
        if name:
            df = df.filter(pl.col("name").str.contains(name, literal=False))

        if tier:
            df = df.filter(pl.col("tier") == tier)

        if champion:
            df = df.filter(pl.col("best_for").str.contains(champion))

        if category:
            df = df.filter(pl.col("category") == category)

        return df

    def search_compositions(self,
                          name: Optional[str] = None,
                          tier: Optional[str] = None,
                          champion: Optional[str] = None,
                          trait: Optional[str] = None,
                          min_win_rate: Optional[float] = None,
                          min_play_rate: Optional[float] = None,
                          source: Optional[str] = None) -> pl.DataFrame:
        """
        Search meta compositions with filters.

        Args:
            name: Composition name (partial match)
            tier: Composition tier (S, A, B, C)
            champion: Champion name to find comps containing this champion
            trait: Trait name to find comps using this trait
            min_win_rate: Minimum win rate (0.0 to 1.0)
            min_play_rate: Minimum play rate (0.0 to 1.0)
            source: Data source (e.g., "metatft.com", "fallback")

        Returns:
            Filtered DataFrame
        """
        df = self.get_compositions_df()

        if df.is_empty():
            return df

        # Apply filters
        if name:
            df = df.filter(pl.col("name").str.contains(name, literal=False))

        if tier:
            df = df.filter(pl.col("tier") == tier)

        if champion:
            df = df.filter(pl.col("champions").str.contains(champion))

        if trait:
            df = df.filter(pl.col("traits").str.contains(trait))

        if min_win_rate is not None:
            df = df.filter(pl.col("win_rate") >= min_win_rate)

        if min_play_rate is not None:
            df = df.filter(pl.col("play_rate") >= min_play_rate)

        if source:
            df = df.filter(pl.col("source") == source)

        return df

    def get_champions_by_cost(self, cost: int) -> pl.DataFrame:
        """Get all champions of a specific cost."""
        return self.search_champions(cost=cost)

    def get_champions_with_trait(self, trait: str) -> pl.DataFrame:
        """Get all champions with a specific trait."""
        return self.search_champions(traits=[trait])

    def get_best_power_ups_for_champion(self, champion_name: str) -> pl.DataFrame:
        """Get the best power ups for a specific champion."""
        return self.search_power_ups(champion=champion_name)

    def get_items_by_type(self, item_type: str) -> pl.DataFrame:
        """Get all items of a specific type."""
        return self.search_items(item_type=item_type)

    def get_compositions_by_tier(self, tier: str) -> pl.DataFrame:
        """Get all compositions of a specific tier."""
        return self.search_compositions(tier=tier)

    def get_compositions_with_champion(self, champion_name: str) -> pl.DataFrame:
        """Get all compositions that use a specific champion."""
        return self.search_compositions(champion=champion_name)

    def get_compositions_with_trait(self, trait_name: str) -> pl.DataFrame:
        """Get all compositions that use a specific trait."""
        return self.search_compositions(trait=trait_name)

    def get_meta_compositions(self, min_win_rate: float = 0.15, min_sample_size: int = 100) -> pl.DataFrame:
        """Get meta compositions with high win rates and sufficient sample sizes."""
        df = self.get_compositions_df()

        if df.is_empty():
            return df

        return df.filter(
            (pl.col("win_rate") >= min_win_rate) &
            (pl.col("sample_size") >= min_sample_size)
        ).sort("avg_placement")

    def export_to_csv(self, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export all DataFrames to CSV files."""
        if output_dir is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = project_root / "data" / "exports" / f"csv_{timestamp}"

        output_dir.mkdir(parents=True, exist_ok=True)

        dataframes = self.get_all_dataframes()
        exported_files = {}

        for name, df in dataframes.items():
            output_path = output_dir / f"tft15_{name}.csv"
            df.write_csv(output_path)
            exported_files[name] = output_path
            print(f"📄 Exported {name} to CSV: {output_path}")

        return exported_files

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded meta data."""
        dataframes = self.get_all_dataframes()

        summary = {
            "meta_info": self.get_meta_info(),
            "data_counts": {name: df.shape[0] for name, df in dataframes.items()},
            "data_path": str(self.data_path) if self.data_path else "None"
        }

        return summary

    def print_summary(self) -> None:
        """Print a summary of the loaded meta data."""
        summary = self.get_summary()

        print("📊 TFT Meta Data Summary")
        print("=" * 40)
        print(f"Set: {summary['meta_info'].get('set_name', 'Unknown')}")
        print(f"Patch: {summary['meta_info'].get('current_patch', 'Unknown')}")
        print(f"Last Updated: {summary['meta_info'].get('last_updated', 'Unknown')}")
        print(f"Data File: {summary['data_path']}")
        print()
        print("Data Counts:")
        for data_type, count in summary['data_counts'].items():
            print(f"  {data_type.capitalize()}: {count}")


# Convenience functions for easy access
def load_meta_data(data_path: Optional[Path] = None) -> TFTMetaDataManager:
    """Load TFT meta data manager."""
    return TFTMetaDataManager(data_path)

def get_champions_df(data_path: Optional[Path] = None) -> pl.DataFrame:
    """Get champions DataFrame directly."""
    manager = TFTMetaDataManager(data_path)
    return manager.get_champions_df()

def get_items_df(data_path: Optional[Path] = None) -> pl.DataFrame:
    """Get items DataFrame directly."""
    manager = TFTMetaDataManager(data_path)
    return manager.get_items_df()

def get_power_ups_df(data_path: Optional[Path] = None) -> pl.DataFrame:
    """Get power ups DataFrame directly."""
    manager = TFTMetaDataManager(data_path)
    return manager.get_power_ups_df()

def get_compositions_df(data_path: Optional[Path] = None) -> pl.DataFrame:
    """Get compositions DataFrame directly."""
    manager = TFTMetaDataManager(data_path)
    return manager.get_compositions_df()


if __name__ == "__main__":
    # Example usage
    print("🚀 TFT Meta Data Manager Example")

    # Load data
    manager = TFTMetaDataManager()
    manager.print_summary()

    # Example queries
    print("\n🔍 Example Queries:")

    # Get all 5-cost champions
    five_cost = manager.get_champions_by_cost(5)
    print(f"\n5-Cost Champions ({five_cost.shape[0]}):")
    if not five_cost.is_empty():
        print(five_cost.select(["name", "traits", "health"]))

    # Get AD items
    ad_items = manager.get_items_by_type("AD")
    print(f"\nAD Items ({ad_items.shape[0]}):")
    if not ad_items.is_empty():
        print(ad_items.select(["name", "components"]))

    # Get S-tier power ups
    s_tier_power_ups = manager.search_power_ups(tier="S")
    print(f"\nS-Tier Power Ups ({s_tier_power_ups.shape[0]}):")
    if not s_tier_power_ups.is_empty():
        print(s_tier_power_ups.select(["name", "category", "best_for"]))