#!/usr/bin/env python3
"""
TFT Meta Data Validator

Validates TFT Set 15 meta data against current sources and provides
data quality reports. Identifies outdated or missing information.
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any
import polars as pl

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.update_meta_data import TFTMetaDataUpdater
from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
from src.tft_analyzer.utils.patch_detector import TFTPatchDetector


class TFTMetaDataValidator:
    """Validates TFT meta data quality and currency."""

    def __init__(self):
        self.patch_detector = TFTPatchDetector()
        self.validation_results = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_date": self.patch_detector.get_today_date(),
            "current_patch": "",
            "validations": {}
        }

    async def validate_all_data(self, data_path: Path = None) -> Dict[str, Any]:
        """Run comprehensive validation on TFT meta data."""
        print("🔍 TFT Meta Data Validation")
        print("=" * 50)

        # Load current data
        manager = TFTMetaDataManager(data_path)

        # Detect current patch
        current_patch = await self.patch_detector.get_current_patch()
        self.validation_results["current_patch"] = current_patch

        print(f"📅 Today's Date: {self.validation_results['current_date']}")
        print(f"🎮 Current Patch: {current_patch}")
        print(f"💾 Data Source: {manager.data_path}")
        print()

        # Get all DataFrames
        dataframes = manager.get_all_dataframes()

        # Validate each data type
        await self._validate_champions_data(dataframes["champions"], manager)
        await self._validate_items_data(dataframes["items"], manager)
        await self._validate_power_ups_data(dataframes["power_ups"], manager)
        await self._validate_artifacts_data(dataframes["artifacts"], manager)
        await self._validate_patch_currency(manager)

        # Generate summary
        self._generate_validation_summary()

        return self.validation_results

    async def _validate_champions_data(self, champions_df: pl.DataFrame, manager: TFTMetaDataManager):
        """Validate champions data quality."""
        print("🔍 Validating Champions Data...")

        validation = {
            "total_champions": champions_df.shape[0],
            "missing_data": {},
            "invalid_values": {},
            "cost_distribution": {},
            "trait_coverage": {},
            "issues": []
        }

        if champions_df.is_empty():
            validation["issues"].append("❌ No champions data found")
            self.validation_results["validations"]["champions"] = validation
            return

        # Check for missing essential data
        required_fields = ["name", "cost", "traits", "health"]
        for field in required_fields:
            if field in champions_df.columns:
                null_count = champions_df.select(pl.col(field).is_null().sum()).item()
                empty_count = champions_df.select((pl.col(field) == "").sum()).item() if field in ["name", "traits"] else 0
                total_missing = null_count + empty_count

                if total_missing > 0:
                    validation["missing_data"][field] = total_missing
                    validation["issues"].append(f"⚠️ {total_missing} champions missing {field}")

        # Validate cost distribution
        if "cost" in champions_df.columns:
            cost_counts = champions_df.group_by("cost").len().sort("cost")
            validation["cost_distribution"] = dict(zip(cost_counts["cost"].to_list(), cost_counts["len"].to_list()))

            # Check for unreasonable costs
            max_cost = champions_df["cost"].max()
            min_cost = champions_df["cost"].min()

            if max_cost > 5:
                validation["issues"].append(f"⚠️ Unusually high champion cost found: {max_cost}")
            if min_cost < 1:
                validation["issues"].append(f"⚠️ Invalid champion cost found: {min_cost}")

        # Check for known Set 15 champions
        known_set15_champions = {
            "Gnar", "Caitlyn", "Sivir", "Seraphine", "Ahri", "Jayce",
            "Kalista", "Lux", "Aatrox", "Gangplank", "Lucian", "Rell",
            "Naafiri", "Garen", "Poppy", "Rammus", "Lulu", "Darius",
            "Malzahar", "Kai'Sa", "Senna", "Ryze", "Xayah", "Rakan"
        }

        if "name" in champions_df.columns:
            current_champions = set(champions_df["name"].to_list())
            missing_champions = known_set15_champions - current_champions
            extra_champions = current_champions - known_set15_champions

            if missing_champions:
                validation["issues"].append(f"⚠️ Missing known Set 15 champions: {', '.join(sorted(missing_champions))}")

            if extra_champions:
                validation["issues"].append(f"ℹ️ Additional champions found: {', '.join(sorted(extra_champions))}")

        # Validate traits
        if "traits" in champions_df.columns:
            trait_coverage = {}
            all_traits = set()

            for traits_str in champions_df["traits"]:
                if traits_str and traits_str != "":
                    traits = traits_str.split("|")
                    all_traits.update(traits)

            validation["trait_coverage"]["total_unique_traits"] = len(all_traits)
            validation["trait_coverage"]["traits"] = sorted(all_traits)

            # Check for common Set 15 traits
            known_traits = {"Sniper", "Star Guardian", "TheCrew", "Battle Academia", "Soul Fighter", "Mighty Mech"}
            missing_traits = known_traits - all_traits

            if missing_traits:
                validation["issues"].append(f"⚠️ Missing expected traits: {', '.join(missing_traits)}")

        if not validation["issues"]:
            validation["issues"].append("✅ Champions data looks good")

        self.validation_results["validations"]["champions"] = validation
        print(f"  Champions: {validation['total_champions']} found, {len(validation['issues'])} issues")

    async def _validate_items_data(self, items_df: pl.DataFrame, manager: TFTMetaDataManager):
        """Validate items data quality."""
        print("🔍 Validating Items Data...")

        validation = {
            "total_items": items_df.shape[0],
            "type_distribution": {},
            "component_coverage": {},
            "issues": []
        }

        if items_df.is_empty():
            validation["issues"].append("❌ No items data found")
            self.validation_results["validations"]["items"] = validation
            return

        # Check type distribution
        if "type" in items_df.columns:
            type_counts = items_df.group_by("type").len().sort("type")
            validation["type_distribution"] = dict(zip(type_counts["type"].to_list(), type_counts["len"].to_list()))

        # Check for essential items
        essential_items = {
            "Infinity Edge", "Last Whisper", "Bloodthirster",
            "Archangel's Staff", "Morellonomicon", "Jeweled Gauntlet",
            "Warmog's Armor", "Titan's Resolve", "Dragon's Claw"
        }

        if "name" in items_df.columns:
            current_items = set(items_df["name"].to_list())
            missing_items = essential_items - current_items

            if missing_items:
                validation["issues"].append(f"⚠️ Missing essential items: {', '.join(missing_items)}")

        if not validation["issues"]:
            validation["issues"].append("✅ Items data looks good")

        self.validation_results["validations"]["items"] = validation
        print(f"  Items: {validation['total_items']} found, {len(validation['issues'])} issues")

    async def _validate_power_ups_data(self, power_ups_df: pl.DataFrame, manager: TFTMetaDataManager):
        """Validate power ups data quality."""
        print("🔍 Validating Power Ups Data...")

        validation = {
            "total_power_ups": power_ups_df.shape[0],
            "tier_distribution": {},
            "category_distribution": {},
            "issues": []
        }

        if power_ups_df.is_empty():
            validation["issues"].append("❌ No power ups data found")
            self.validation_results["validations"]["power_ups"] = validation
            return

        # Check tier distribution
        if "tier" in power_ups_df.columns:
            tier_counts = power_ups_df.group_by("tier").len().sort("tier")
            validation["tier_distribution"] = dict(zip(tier_counts["tier"].to_list(), tier_counts["len"].to_list()))

        # Check category distribution
        if "category" in power_ups_df.columns:
            category_counts = power_ups_df.group_by("category").len().sort("category")
            validation["category_distribution"] = dict(zip(category_counts["category"].to_list(), category_counts["len"].to_list()))

        # Check for essential S-tier power ups
        essential_power_ups = {"Over 9000", "Shadow Clone", "Fan Service"}

        if "name" in power_ups_df.columns:
            current_power_ups = set(power_ups_df["name"].to_list())
            missing_power_ups = essential_power_ups - current_power_ups

            if missing_power_ups:
                validation["issues"].append(f"⚠️ Missing essential power ups: {', '.join(missing_power_ups)}")

            # Should have reasonable number of power ups (Set 15 has 100+)
            if len(current_power_ups) < 10:
                validation["issues"].append(f"⚠️ Only {len(current_power_ups)} power ups found, expected more")

        if not validation["issues"]:
            validation["issues"].append("✅ Power ups data looks good")

        self.validation_results["validations"]["power_ups"] = validation
        print(f"  Power Ups: {validation['total_power_ups']} found, {len(validation['issues'])} issues")

    async def _validate_artifacts_data(self, artifacts_df: pl.DataFrame, manager: TFTMetaDataManager):
        """Validate artifacts data quality."""
        print("🔍 Validating Artifacts Data...")

        validation = {
            "total_artifacts": artifacts_df.shape[0],
            "tier_distribution": {},
            "issues": []
        }

        if artifacts_df.is_empty():
            validation["issues"].append("❌ No artifacts data found")
            self.validation_results["validations"]["artifacts"] = validation
            return

        # Check tier distribution
        if "tier" in artifacts_df.columns:
            tier_counts = artifacts_df.group_by("tier").len().sort("tier")
            validation["tier_distribution"] = dict(zip(tier_counts["tier"].to_list(), tier_counts["len"].to_list()))

        # Check for key artifacts
        key_artifacts = {"Flickerblade", "Manazane", "The Indomitable", "Zhonya's Paradox"}

        if "name" in artifacts_df.columns:
            current_artifacts = set(artifacts_df["name"].to_list())
            missing_artifacts = key_artifacts - current_artifacts

            if missing_artifacts:
                validation["issues"].append(f"⚠️ Missing key artifacts: {', '.join(missing_artifacts)}")

        if not validation["issues"]:
            validation["issues"].append("✅ Artifacts data looks good")

        self.validation_results["validations"]["artifacts"] = validation
        print(f"  Artifacts: {validation['total_artifacts']} found, {len(validation['issues'])} issues")

    async def _validate_patch_currency(self, manager: TFTMetaDataManager):
        """Validate if data is current for the detected patch."""
        print("🔍 Validating Data Currency...")

        validation = {
            "data_patch": "",
            "current_patch": self.validation_results["current_patch"],
            "is_current": False,
            "age_days": 0,
            "issues": []
        }

        meta_info = manager.get_meta_info()
        data_patch = meta_info.get("current_patch", "Unknown")
        validation["data_patch"] = data_patch

        if data_patch == validation["current_patch"]:
            validation["is_current"] = True
            validation["issues"].append("✅ Data patch matches current patch")
        else:
            validation["issues"].append(f"⚠️ Data patch ({data_patch}) differs from current patch ({validation['current_patch']})")

        # Check data age
        last_updated = meta_info.get("last_updated", "")
        if last_updated:
            try:
                if ":" in last_updated:  # Full datetime
                    data_date = datetime.strptime(last_updated, "%Y-%m-%d %H:%M:%S")
                else:  # Date only
                    data_date = datetime.strptime(last_updated, "%Y-%m-%d")

                age_days = (datetime.now() - data_date).days
                validation["age_days"] = age_days

                if age_days == 0:
                    validation["issues"].append("✅ Data is current (updated today)")
                elif age_days <= 7:
                    validation["issues"].append(f"✅ Data is recent ({age_days} days old)")
                elif age_days <= 30:
                    validation["issues"].append(f"⚠️ Data is {age_days} days old")
                else:
                    validation["issues"].append(f"❌ Data is outdated ({age_days} days old)")

            except ValueError:
                validation["issues"].append(f"⚠️ Could not parse last updated date: {last_updated}")

        self.validation_results["validations"]["currency"] = validation
        print(f"  Currency: Data patch {data_patch}, Age {validation['age_days']} days")

    def _generate_validation_summary(self):
        """Generate overall validation summary."""
        print("\n📊 Validation Summary")
        print("=" * 30)

        total_issues = 0
        critical_issues = 0

        for validation_type, validation in self.validation_results["validations"].items():
            issues = validation.get("issues", [])
            type_issues = len([i for i in issues if not i.startswith("✅")])
            type_critical = len([i for i in issues if i.startswith("❌")])

            total_issues += type_issues
            critical_issues += type_critical

            print(f"{validation_type.capitalize()}: {type_issues} issues ({type_critical} critical)")

        print(f"\nOverall: {total_issues} total issues, {critical_issues} critical")

        # Overall health score
        max_possible_issues = len(self.validation_results["validations"]) * 3  # Rough estimate
        health_score = max(0, 100 - (total_issues / max_possible_issues * 100))

        print(f"Data Health Score: {health_score:.1f}%")

        if health_score >= 90:
            print("🟢 Data quality: Excellent")
        elif health_score >= 70:
            print("🟡 Data quality: Good")
        elif health_score >= 50:
            print("🟠 Data quality: Fair - Consider updating")
        else:
            print("🔴 Data quality: Poor - Update recommended")

    def save_validation_report(self, output_path: Path = None) -> Path:
        """Save validation results to JSON."""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = project_root / "data" / "meta_analysis" / f"validation_report_{timestamp}.json"

        output_path.parent.mkdir(parents=True, exist_ok=True)

        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.validation_results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Validation report saved to: {output_path}")
        return output_path


async def main():
    """Main validation function."""
    validator = TFTMetaDataValidator()

    # Run validation
    results = await validator.validate_all_data()

    # Save report
    validator.save_validation_report()

    # Check if update is needed
    currency_validation = results["validations"].get("currency", {})
    age_days = currency_validation.get("age_days", 0)

    if age_days > 7:
        print(f"\n🔄 Recommendation: Data is {age_days} days old. Consider running update_meta_data.py")
    elif not currency_validation.get("is_current", False):
        print(f"\n🔄 Recommendation: Data patch mismatch. Consider running update_meta_data.py")


if __name__ == "__main__":
    asyncio.run(main())