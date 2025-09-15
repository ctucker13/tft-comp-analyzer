#!/usr/bin/env python3
"""
TFT Meta Data Usage Examples

Demonstrates how to use the TFT meta data update and management system
with Polars DataFrames and current patch detection.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.update_meta_data import TFTMetaDataUpdater
from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
from src.tft_analyzer.utils.patch_detector import TFTPatchDetector


async def example_1_update_and_load_data():
    """Example 1: Update meta data and load as DataFrames"""
    print("🚀 Example 1: Update Meta Data")
    print("=" * 40)

    # Update meta data with current information
    async with TFTMetaDataUpdater() as updater:
        # Detect today's date and current patch
        print(f"📅 Today: {updater.patch_detector.get_today_date()}")

        # Update all data
        data = await updater.update_all_data()

        # Save as both JSON and Parquet
        json_path = updater.save_json_data()
        parquet_files = updater.save_parquet_data()

        print(f"✅ Data updated and saved")
        return json_path


def example_2_load_and_query_data():
    """Example 2: Load data and perform queries using Polars"""
    print("\n🔍 Example 2: Query Meta Data")
    print("=" * 40)

    # Load the data manager
    manager = TFTMetaDataManager()
    manager.print_summary()

    # Get all DataFrames
    dfs = manager.get_all_dataframes()

    print(f"\n📊 Available DataFrames:")
    for name, df in dfs.items():
        print(f"  {name}: {df.shape[0]} rows × {df.shape[1]} columns")

    # Example queries
    print(f"\n🔍 Example Queries:")

    # 1. Find all 5-cost champions
    five_cost_champs = manager.search_champions(cost=5)
    if not five_cost_champs.is_empty():
        print(f"\n5-Cost Champions:")
        print(five_cost_champs.select(["name", "traits", "health", "attack_damage"]))

    # 2. Find AD carry items
    ad_items = manager.search_items(item_type="AD")
    if not ad_items.is_empty():
        print(f"\nAD Carry Items:")
        print(ad_items.select(["name", "components", "description"]))

    # 3. Find best power ups for specific champion
    seraphine_power_ups = manager.search_power_ups(champion="Seraphine")
    if not seraphine_power_ups.is_empty():
        print(f"\nBest Power Ups for Seraphine:")
        print(seraphine_power_ups.select(["name", "tier", "description"]))

    # 4. Get all champions with Star Guardian trait
    star_guardians = manager.search_champions(traits=["Star Guardian"])
    if not star_guardians.is_empty():
        print(f"\nStar Guardian Champions:")
        print(star_guardians.select(["name", "cost", "health"]))

    # 5. Query meta compositions from MetaTFT
    s_tier_comps = manager.get_compositions_by_tier("S")
    if not s_tier_comps.is_empty():
        print(f"\nS-Tier Meta Compositions:")
        print(s_tier_comps.select(["name", "win_rate", "avg_placement", "play_rate"]))

    # 6. Find compositions using a specific champion
    gnar_comps = manager.get_compositions_with_champion("Gnar")
    if not gnar_comps.is_empty():
        print(f"\nCompositions featuring Gnar:")
        print(gnar_comps.select(["name", "tier", "champions"]))

    # 7. Get high-performing meta compositions
    meta_comps = manager.get_meta_compositions(min_win_rate=0.15, min_sample_size=500)
    if not meta_comps.is_empty():
        print(f"\nHigh-performing meta compositions:")
        print(meta_comps.select(["name", "tier", "win_rate", "avg_placement"]).head(5))

    return manager


def example_3_advanced_polars_operations():
    """Example 3: Advanced Polars operations on TFT data"""
    print("\n⚡ Example 3: Advanced Polars Operations")
    print("=" * 40)

    manager = TFTMetaDataManager()
    champions_df = manager.get_champions_df()

    if champions_df.is_empty():
        print("❌ No champions data available")
        return

    # Advanced Polars queries
    import polars as pl

    print("🔍 Advanced Analytics:")

    # 1. Champion stats by cost
    print("\n1. Average Health by Champion Cost:")
    stats_by_cost = (
        champions_df
        .group_by("cost")
        .agg([
            pl.col("health").mean().alias("avg_health"),
            pl.col("attack_damage").mean().alias("avg_attack"),
            pl.col("name").len().alias("champion_count")
        ])
        .sort("cost")
    )
    print(stats_by_cost)

    # 2. Champions with highest health per cost
    print("\n2. Tankiest Champion per Cost:")
    tankiest = (
        champions_df
        .filter(pl.col("health") > 0)
        .sort("health", descending=True)
        .group_by("cost")
        .first()
        .select(["cost", "name", "health", "traits"])
        .sort("cost")
    )
    print(tankiest)

    # 3. Trait frequency analysis
    if "traits" in champions_df.columns:
        print("\n3. Most Common Traits:")

        # Explode traits and count frequency
        trait_counts = (
            champions_df
            .select(["name", "traits"])
            .filter(pl.col("traits") != "")
            .with_columns(pl.col("traits").str.split("|").alias("trait_list"))
            .explode("trait_list")
            .group_by("trait_list")
            .len()
            .sort("len", descending=True)
            .head(10)
        )
        print(trait_counts)

    # 4. Power level analysis
    power_levels = (
        champions_df
        .with_columns([
            (pl.col("health") + pl.col("attack_damage") * 10).alias("power_level")
        ])
        .select(["name", "cost", "health", "attack_damage", "power_level"])
        .sort("power_level", descending=True)
        .head(10)
    )
    print("\n4. Highest Power Level Champions:")
    print(power_levels)


def example_4_export_data():
    """Example 4: Export data in different formats"""
    print("\n💾 Example 4: Export Data")
    print("=" * 40)

    manager = TFTMetaDataManager()

    # Export to CSV
    csv_files = manager.export_to_csv()
    print(f"📄 Exported {len(csv_files)} CSV files")

    # You can also manually export specific DataFrames
    champions_df = manager.get_champions_df()
    if not champions_df.is_empty():
        # Export high-cost champions only
        high_cost_champs = champions_df.filter(pl.col("cost") >= 4)

        export_path = project_root / "data" / "exports" / "high_cost_champions.csv"
        export_path.parent.mkdir(parents=True, exist_ok=True)
        high_cost_champs.write_csv(export_path)

        print(f"📄 Exported high-cost champions to: {export_path}")


async def example_5_patch_detection():
    """Example 5: Patch detection and validation"""
    print("\n🎮 Example 5: Patch Detection")
    print("=" * 40)

    detector = TFTPatchDetector()

    # Get today's date
    today = detector.get_today_date()
    print(f"📅 Today's Date: {today}")

    # Get current time
    now = detector.get_today_datetime()
    print(f"⏰ Current Time: {now}")

    # Detect current patch
    current_patch = await detector.get_current_patch()
    print(f"🎮 Current Patch: {current_patch}")

    # Check patch currency
    patch_releases = detector.get_patch_release_info()
    print(f"\n📋 Known Patch Releases:")
    for patch, date in patch_releases.items():
        is_current = detector.is_patch_current(patch)
        status = "✅ Current" if is_current else "❌ Old"
        print(f"  {patch}: {date} {status}")


async def main():
    """Run all examples"""
    print("🎯 TFT Meta Data System Examples")
    print("=" * 50)

    # Example 1: Update data (commented out to avoid hitting APIs repeatedly)
    # json_path = await example_1_update_and_load_data()

    # Example 2: Load and query existing data
    manager = example_2_load_and_query_data()

    # Example 3: Advanced Polars operations
    example_3_advanced_polars_operations()

    # Example 4: Export data
    example_4_export_data()

    # Example 5: Patch detection
    await example_5_patch_detection()

    print(f"\n✅ Examples completed!")
    print(f"💡 To update meta data: python scripts/update_meta_data.py")
    print(f"🔍 To validate data: python scripts/validate_meta_data.py")


if __name__ == "__main__":
    asyncio.run(main())