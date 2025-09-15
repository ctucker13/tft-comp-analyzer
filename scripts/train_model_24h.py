#!/usr/bin/env python3
"""
TFT ML Model Training with 24-Hour Real-Time Data Collection

This script trains the TFT model using only matches from the last 24 hours
for the current patch, ensuring the model is trained on the most recent meta.

Usage:
    python scripts/train_model_24h.py --collect-data --num-matches 50
    python scripts/train_model_24h.py --train --epochs 100
    python scripts/train_model_24h.py --full-pipeline --num-matches 100 --epochs 200
    python scripts/train_model_24h.py --retrain --num-matches 200  # Quick retrain
"""

import argparse
import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector
from src.tft_analyzer.ml.training.trainer import TFTModelTrainer
from src.tft_analyzer.data.patch_detector import TFTPatchDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training_24h.log')
    ]
)

logger = logging.getLogger(__name__)


class RealTimeTrainingCollector(TFTTrainingDataCollector):
    """Enhanced training data collector with 24-hour filtering and latest patch detection."""

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.patch_detector = TFTPatchDetector()
        self.current_patch = None

    async def initialize_patch_detection(self):
        """Detect the current TFT patch for filtering."""
        try:
            self.current_patch = await self.patch_detector.get_current_patch()
            logger.info(f"🎮 Detected current TFT patch: {self.current_patch}")
            return self.current_patch
        except Exception as e:
            logger.warning(f"Could not detect current patch, using default: {e}")
            self.current_patch = self.settings.current_patch
            return self.current_patch

    def _is_valid_training_match(self, match_data: dict, days_back: int = 1) -> bool:
        """Enhanced match validation with strict 24-hour and current patch filtering."""
        try:
            # Check if Set 15
            if match_data.get("info", {}).get("tft_set_number") != 15:
                return False

            # STRICT: Only matches from last 24 hours
            game_creation = match_data.get("info", {}).get("game_creation", 0)
            if game_creation:
                game_date = datetime.fromtimestamp(game_creation / 1000)
                cutoff_date = datetime.now() - timedelta(hours=24)  # Exactly 24 hours

                if game_date < cutoff_date:
                    logger.debug(f"Match too old: {game_date} < {cutoff_date}")
                    return False

            # Check if current patch (if detected)
            if self.current_patch:
                match_version = match_data.get("info", {}).get("game_version", "")
                if self.current_patch not in match_version:
                    logger.debug(f"Match patch {match_version} doesn't match current {self.current_patch}")
                    return False

            # Check if ranked
            queue_id = match_data.get("info", {}).get("queue_id")
            if queue_id != 1100:  # TFT Ranked queue
                return False

            # Additional quality checks for training data
            participants = match_data.get("info", {}).get("participants", [])
            if len(participants) != 8:  # Must be full lobby
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating match: {e}")
            return False

    async def collect_24h_training_data(
        self,
        num_matches: int = 100,
        min_rank: str = "MASTER"
    ) -> list:
        """
        Collect training data from the last 24 hours only.

        Args:
            num_matches: Target number of matches to collect
            min_rank: Minimum rank tier (CHALLENGER, GRANDMASTER, MASTER)

        Returns:
            List of training data points from last 24 hours
        """
        logger.info("🔄 Starting 24-hour real-time training data collection")

        # Initialize patch detection
        await self.initialize_patch_detection()

        # Force 24-hour filtering
        logger.info("⏰ Filtering matches to EXACTLY the last 24 hours")
        logger.info(f"🎯 Target patch: {self.current_patch}")

        # Collect training data with 24-hour constraint
        training_data = await super().collect_training_data(
            num_matches=num_matches,
            min_rank=min_rank,
            days_back=1  # This gets overridden by our _is_valid_training_match
        )

        # Filter and validate the data
        valid_data = []
        now = datetime.now()

        for data_point in training_data:
            # Double-check 24-hour constraint
            if data_point.game_datetime and (now - data_point.game_datetime).total_seconds() <= 24 * 3600:
                valid_data.append(data_point)
            else:
                logger.debug(f"Filtered out data point from {data_point.game_datetime}")

        logger.info(f"✅ Collected {len(valid_data)} valid training samples from last 24 hours")

        if len(valid_data) == 0:
            logger.warning("⚠️ No training data found in the last 24 hours!")
            logger.info("This could mean:")
            logger.info("- Not enough high-rank games in last 24h")
            logger.info("- Patch change occurred recently")
            logger.info("- API rate limiting prevented data collection")

        return valid_data


async def collect_24h_training_data(args):
    """Collect training data from last 24 hours only."""
    logger.info("=== Starting 24-Hour Training Data Collection ===")

    try:
        # Force 24-hour filtering environment
        os.environ['USE_24H_FILTER'] = 'true'

        settings = Settings()
        collector = RealTimeTrainingCollector(settings)

        # Test API connection
        logger.info("Testing Riot API connection...")
        api_test = await collector.riot_client.test_api_connection()

        if not api_test:
            logger.error("❌ API connection failed. Check your RIOT_API_KEY in .env")
            return None

        logger.info("✅ API connection successful")

        # Collect 24-hour training data
        logger.info(f"Collecting {args.num_matches} matches from last 24 hours ({args.min_rank}+ players)")
        training_data = await collector.collect_24h_training_data(
            num_matches=args.num_matches,
            min_rank=args.min_rank
        )

        if not training_data:
            logger.error("❌ No training data collected from last 24 hours")
            return None

        logger.info(f"✅ Collected {len(training_data)} training samples from last 24 hours")

        # Save training data with 24h timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_24h_{args.min_rank}_{len(training_data)}samples_{timestamp}"
        collector.save_training_data(training_data, filename)

        logger.info(f"💾 24-hour training data saved as: {filename}.json")

        # Log 24-hour data summary
        game_times = [point.game_datetime for point in training_data if point.game_datetime]
        if game_times:
            oldest = min(game_times)
            newest = max(game_times)
            logger.info(f"📊 24-Hour Data Summary:")
            logger.info(f"   • Data range: {oldest} to {newest}")
            logger.info(f"   • Time span: {(newest - oldest).total_seconds() / 3600:.1f} hours")
            logger.info(f"   • Average placement: {sum(p.placement for p in training_data) / len(training_data):.2f}")
            logger.info(f"   • Unique patches: {len(set(p.patch for p in training_data))}")

        return training_data

    except Exception as e:
        logger.error(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def train_model_24h(args, training_data=None):
    """Train model using 24-hour data."""
    logger.info("=== Starting 24-Hour Model Training ===")

    try:
        settings = Settings()
        trainer = TFTModelTrainer(settings)

        # Load training data if not provided
        if not training_data:
            logger.info("Loading latest 24-hour training data...")
            data_files = list(Path("data/training").glob("training_data_24h_*.json"))

            if not data_files:
                logger.error("❌ No 24-hour training data found. Run --collect-data first.")
                return None

            # Use most recent 24-hour data
            latest_file = max(data_files, key=lambda x: x.stat().st_mtime)
            logger.info(f"Using training data: {latest_file}")

            with open(latest_file) as f:
                data = json.load(f)
                training_data = [trainer.data_collector.TrainingDataPoint(**point) for point in data]

        if not training_data:
            logger.error("❌ No training data available")
            return None

        logger.info(f"Training model with {len(training_data)} 24-hour samples")

        # Train the model
        success = await trainer.train_model(
            training_data=training_data,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate
        )

        if success:
            # Save model with 24h identifier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            model_name = f"tft_model_24h_{len(training_data)}samples_{timestamp}"
            trainer.save_model(model_name)

            logger.info(f"✅ 24-hour model training complete: {model_name}")
            return model_name
        else:
            logger.error("❌ Model training failed")
            return None

    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main training pipeline with 24-hour data."""
    parser = argparse.ArgumentParser(description="TFT ML Training with 24-Hour Real-Time Data")

    # Action selection
    parser.add_argument("--collect-data", action="store_true", help="Collect 24-hour training data")
    parser.add_argument("--train", action="store_true", help="Train model using 24-hour data")
    parser.add_argument("--full-pipeline", action="store_true", help="Collect data + train model")
    parser.add_argument("--retrain", action="store_true", help="Quick retrain with fresh 24h data")

    # Data collection parameters
    parser.add_argument("--num-matches", type=int, default=100, help="Number of matches to collect")
    parser.add_argument("--min-rank", choices=["CHALLENGER", "GRANDMASTER", "MASTER"], default="MASTER", help="Minimum rank tier")

    # Training parameters
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate")

    args = parser.parse_args()

    if not any([args.collect_data, args.train, args.full_pipeline, args.retrain]):
        parser.print_help()
        return

    # Create directories
    Path("data/training").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

    logger.info("🚀 Starting TFT 24-Hour Real-Time Training Pipeline")
    logger.info(f"Target: {args.num_matches} matches from last 24 hours")
    logger.info(f"Minimum rank: {args.min_rank}")

    training_data = None

    # Collect fresh 24-hour data
    if args.collect_data or args.full_pipeline or args.retrain:
        training_data = await collect_24h_training_data(args)
        if not training_data:
            logger.error("❌ Cannot proceed without training data")
            return

    # Train model
    if args.train or args.full_pipeline or args.retrain:
        model_name = await train_model_24h(args, training_data)
        if model_name:
            logger.info(f"🎉 24-Hour Training Pipeline Complete!")
            logger.info(f"Model saved as: {model_name}")
        else:
            logger.error("❌ Training pipeline failed")


if __name__ == "__main__":
    asyncio.run(main())