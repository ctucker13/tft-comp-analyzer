#!/usr/bin/env python3
"""
Quick Daily Retrain Script

This script automatically retrains the TFT model with the latest 24-hour data.
Designed to be run daily or multiple times per day for the freshest model.

Usage:
    python scripts/quick_retrain.py              # Default settings
    python scripts/quick_retrain.py --matches 150 # More matches
    python scripts/quick_retrain.py --rank CHALLENGER # Higher rank only
"""

import asyncio
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from train_model_24h import collect_24h_training_data, train_model_24h
from config.settings import Settings

# Setup simple logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def quick_retrain(num_matches: int = 120, min_rank: str = "MASTER"):
    """Quick retrain with fresh 24-hour data."""

    print("🔄 TFT Quick Retrain - Last 24 Hours")
    print("=" * 50)
    print(f"⏰ Training with matches from: Last 24 hours")
    print(f"🎯 Target matches: {num_matches}")
    print(f"🏆 Minimum rank: {min_rank}")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Create a simple args object
    class Args:
        def __init__(self):
            self.num_matches = num_matches
            self.min_rank = min_rank
            self.epochs = 75  # Good balance for quick training
            self.batch_size = 32
            self.learning_rate = 0.001

    args = Args()

    try:
        # Step 1: Collect fresh 24-hour data
        print("1️⃣ Collecting fresh training data from last 24 hours...")
        training_data = await collect_24h_training_data(args)

        if not training_data:
            print("❌ No training data collected. Possible reasons:")
            print("   • Not enough high-rank games in last 24h")
            print("   • API rate limiting")
            print("   • Recent patch change")
            return False

        print(f"✅ Collected {len(training_data)} training samples")
        print()

        # Step 2: Train model
        print("2️⃣ Training model with fresh data...")
        model_name = await train_model_24h(args, training_data)

        if model_name:
            print("✅ Model training complete!")
            print(f"📁 Model saved: {model_name}")
            print()
            print("🎉 Quick retrain successful!")

            # Show training summary
            patches = set(d.patch for d in training_data if d.patch)
            avg_placement = sum(d.placement for d in training_data) / len(training_data)

            print("📊 Training Summary:")
            print(f"   • Samples: {len(training_data)}")
            print(f"   • Patches: {', '.join(patches) if patches else 'Unknown'}")
            print(f"   • Avg placement: {avg_placement:.2f}")
            print(f"   • Training epochs: {args.epochs}")

            return True
        else:
            print("❌ Model training failed")
            return False

    except Exception as e:
        print(f"❌ Quick retrain failed: {e}")
        return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quick TFT Model Retrain")
    parser.add_argument("--matches", type=int, default=120, help="Number of matches to collect (default: 120)")
    parser.add_argument("--rank", choices=["CHALLENGER", "GRANDMASTER", "MASTER"], default="MASTER", help="Minimum rank tier")

    args = parser.parse_args()

    success = await quick_retrain(args.matches, args.rank)

    if success:
        print("\n🚀 Your model is now trained on the latest 24-hour meta!")
        print("Run your TFT analysis tools to get fresh strategic advice.")
    else:
        print("\n💡 Tips for better data collection:")
        print("• Try running during peak hours (evening EU time)")
        print("• Use --rank CHALLENGER for smaller but higher quality dataset")
        print("• Check your Riot API key has sufficient quota")


if __name__ == "__main__":
    asyncio.run(main())