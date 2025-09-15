#!/usr/bin/env python3
"""
Test MetaTFT.com Integration

Tests the integration of MetaTFT.com composition data with the TFT analyzer.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.update_meta_data import TFTMetaDataUpdater
from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list


async def test_metatft_data_collection():
    """Test collecting data from MetaTFT.com"""
    print("🧪 Testing MetaTFT Data Collection")
    print("=" * 50)

    async with TFTMetaDataUpdater() as updater:
        # Test composition data collection
        compositions = await updater.fetch_meta_compositions_data()

        print(f"✅ Collected {len(compositions)} compositions")

        if compositions:
            sample_comp = compositions[0]
            print(f"\n📋 Sample composition: {sample_comp.get('name', 'Unknown')}")
            print(f"   Tier: {sample_comp.get('tier', 'Unknown')}")
            print(f"   Win Rate: {sample_comp.get('win_rate', 0):.1%}")
            print(f"   Play Rate: {sample_comp.get('play_rate', 0):.1%}")
            print(f"   Champions: {', '.join(sample_comp.get('champions', []))}")
            print(f"   Source: {sample_comp.get('source', 'Unknown')}")

        return compositions


def test_composition_dataframes():
    """Test composition DataFrames"""
    print("\n🧪 Testing Composition DataFrames")
    print("=" * 50)

    manager = TFTMetaDataManager()

    # Get compositions DataFrame
    comps_df = manager.get_compositions_df()
    print(f"📊 Compositions DataFrame: {comps_df.shape[0]} rows × {comps_df.shape[1]} columns")

    if not comps_df.is_empty():
        print("\nColumns:", list(comps_df.columns))

        # Test searches
        s_tier = manager.get_compositions_by_tier("S")
        print(f"🏆 S-Tier compositions: {s_tier.shape[0]}")

        # Test champion search
        gnar_comps = manager.get_compositions_with_champion("Gnar")
        print(f"🦎 Compositions with Gnar: {gnar_comps.shape[0]}")

        # Test trait search
        sniper_comps = manager.get_compositions_with_trait("Sniper")
        print(f"🎯 Sniper compositions: {sniper_comps.shape[0]}")

        # Show sample data
        if comps_df.shape[0] > 0:
            print(f"\n📋 Sample data:")
            sample_cols = ["name", "tier", "win_rate", "avg_placement"]
            available_cols = [col for col in sample_cols if col in comps_df.columns]
            if available_cols:
                print(comps_df.select(available_cols).head(3))

    return comps_df


def test_meta_analysis_integration():
    """Test meta analysis tool integration"""
    print("\n🧪 Testing Meta Analysis Integration")
    print("=" * 50)

    try:
        # Test tier list with MetaTFT data
        tier_list = get_meta_tier_list(refresh_data=False)
        print("✅ Meta tier list generation successful")
        print(f"📋 Response length: {len(tier_list)} characters")

        # Check if it contains expected content
        if "tier" in tier_list.lower() or "composition" in tier_list.lower():
            print("✅ Contains tier/composition content")
        else:
            print("⚠️ May not contain expected content")

    except Exception as e:
        print(f"❌ Meta analysis integration failed: {e}")

    return tier_list


def test_polars_operations():
    """Test advanced Polars operations on composition data"""
    print("\n🧪 Testing Polars Operations")
    print("=" * 50)

    manager = TFTMetaDataManager()
    comps_df = manager.get_compositions_df()

    if comps_df.is_empty():
        print("❌ No composition data available for Polars testing")
        return

    try:
        import polars as pl

        # Test aggregations
        if "tier" in comps_df.columns:
            tier_stats = comps_df.group_by("tier").agg([
                pl.col("name").len().alias("count"),
                pl.col("win_rate").mean().alias("avg_win_rate"),
                pl.col("avg_placement").mean().alias("avg_placement")
            ]).sort("tier")

            print("📊 Compositions by Tier:")
            print(tier_stats)

        # Test filtering
        if "win_rate" in comps_df.columns and "sample_size" in comps_df.columns:
            high_performing = comps_df.filter(
                (pl.col("win_rate") > 0.15) &
                (pl.col("sample_size") > 500)
            ).sort("avg_placement")

            print(f"\n🏆 High-performing compositions (>15% WR, >500 games): {high_performing.shape[0]}")

        print("✅ Polars operations successful")

    except Exception as e:
        print(f"❌ Polars operations failed: {e}")


async def main():
    """Run all tests"""
    print("🚀 MetaTFT Integration Test Suite")
    print("=" * 60)

    # Test 1: Data Collection
    compositions = await test_metatft_data_collection()

    # Test 2: DataFrame Operations
    comps_df = test_composition_dataframes()

    # Test 3: Meta Analysis Integration
    tier_list = test_meta_analysis_integration()

    # Test 4: Polars Operations
    test_polars_operations()

    # Summary
    print(f"\n📋 Test Summary")
    print("=" * 30)
    print(f"✅ Compositions collected: {len(compositions) if compositions else 0}")
    print(f"✅ DataFrame rows: {comps_df.shape[0] if not comps_df.is_empty() else 0}")
    print(f"✅ Meta analysis: {'Working' if tier_list and len(tier_list) > 100 else 'Limited'}")

    if compositions and not comps_df.is_empty():
        print("\n🎉 MetaTFT integration is working!")
        print("💡 Next steps:")
        print("   - Run `python scripts/update_meta_data.py` to collect fresh data")
        print("   - Use compositions in your TFT chat interface")
        print("   - Query meta tier lists with enhanced data")
    else:
        print("\n⚠️ Integration has limited functionality")
        print("💡 Try running: python scripts/update_meta_data.py")


if __name__ == "__main__":
    asyncio.run(main())