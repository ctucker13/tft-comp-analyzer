"""
Training Script for TFT Strategy Model
"""

import asyncio
import argparse
from pathlib import Path
import json
import torch
from torch.utils.data import DataLoader
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.ml.data.collector import TFTMLDataCollector
from src.tft_analyzer.ml.models.strategy_model import TFTStrategyModel
from src.tft_analyzer.data.riot_api import RiotTFTAPI
from config.settings import Settings


async def collect_training_data(args):
    """Collect training data from Riot API"""
    print("🎯 Starting training data collection...")

    # Initialize settings and API
    settings = Settings()
    riot_api = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=True)

    # Initialize data collector
    collector = TFTMLDataCollector(riot_api, output_dir=args.data_dir)

    # Collect data
    stats = await collector.collect_training_data(
        target_games=args.target_games,
        max_players=args.max_players,
        days_back=args.days_back
    )

    print(f"✅ Data collection complete!")
    print(f"   - Games collected: {stats['games_collected']}")
    print(f"   - Players processed: {stats['players_processed']}")

    # Generate training examples
    if stats['games_collected'] > 0:
        examples_count = await collector.generate_training_examples(args.data_dir)
        print(f"   - Training examples generated: {examples_count}")

    return stats


def train_model(args):
    """Train the TFT strategy model"""
    print("🧠 Starting model training...")

    # This would implement the actual training loop
    # For now, just create a placeholder model
    model = TFTStrategyModel(
        input_dim=50,  # Would be determined from actual data
        hidden_dim=256,
        dropout=0.3,
        use_attention=True
    )

    print(f"📊 Model architecture:")
    print(f"   - Input dimension: 50")
    print(f"   - Hidden dimension: 256")
    print(f"   - Using attention: True")

    # Save model configuration
    config = {
        "model_type": "strategy",
        "input_dim": 50,
        "hidden_dim": 256,
        "dropout": 0.3,
        "use_attention": True,
        "version": "0.1.0"
    }

    output_dir = Path(args.model_output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Save initial model weights
    torch.save(model.state_dict(), output_dir / "model.pt")

    print(f"✅ Model training setup complete!")
    print(f"   - Model saved to: {output_dir}")

    return {"status": "success", "model_path": str(output_dir)}


async def main():
    parser = argparse.ArgumentParser(description="Train TFT Strategy Model")

    # Data collection arguments
    parser.add_argument("--collect-data", action="store_true", help="Collect training data")
    parser.add_argument("--target-games", type=int, default=100, help="Number of games to collect")
    parser.add_argument("--max-players", type=int, default=50, help="Maximum players to analyze")
    parser.add_argument("--days-back", type=int, default=7, help="Days to look back for matches")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Data output directory")

    # Training arguments
    parser.add_argument("--train", action="store_true", help="Train the model")
    parser.add_argument("--model-output-dir", type=str, default="data/models/strategy_v1", help="Model output directory")

    # General arguments
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if not (args.collect_data or args.train):
        print("❌ Please specify either --collect-data or --train")
        parser.print_help()
        return

    try:
        if args.collect_data:
            await collect_training_data(args)

        if args.train:
            train_model(args)

        print("🎉 Training pipeline completed successfully!")

    except Exception as e:
        print(f"❌ Error in training pipeline: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())