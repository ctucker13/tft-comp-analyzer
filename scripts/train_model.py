#!/usr/bin/env python3
"""
Standalone ML model training script for TFT strategy prediction.

This script handles the complete training pipeline independently from the UI,
including data collection, preprocessing, training, and evaluation.

Usage:
    python scripts/train_model.py --collect-data --num-matches 50
    python scripts/train_model.py --train --epochs 100
    python scripts/train_model.py --full-pipeline --num-matches 100 --epochs 200
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import Settings
from src.tft_analyzer.ml.training.data_collector import TFTTrainingDataCollector
from src.tft_analyzer.ml.training.trainer import TFTModelTrainer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('training.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_directories():
    """Create necessary directories for training."""
    dirs = [
        Path("data/training"),
        Path("data/processed"),
        Path("models"),
        Path("logs"),
        Path("scripts/results")
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {dir_path}")

async def collect_training_data(args):
    """Collect training data from Riot API."""
    logger.info("=== Starting Training Data Collection ===")

    try:
        settings = Settings()
        collector = TFTTrainingDataCollector(settings)

        # Test API connection first
        logger.info("Testing Riot API connection...")
        api_test = await collector.riot_client.test_api_connection()

        if not api_test:
            logger.error("❌ API connection failed. Check your RIOT_API_KEY in .env")
            return None

        logger.info("✅ API connection successful")

        # Collect training data
        logger.info(f"Collecting {args.num_matches} matches from {args.min_rank}+ players")
        training_data = await collector.collect_training_data(
            num_matches=args.num_matches,
            min_rank=args.min_rank,
            days_back=args.days_back
        )

        if not training_data:
            logger.error("❌ No training data collected")
            return None

        logger.info(f"✅ Collected {len(training_data)} training data points")

        # Save training data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"training_data_{args.min_rank}_{len(training_data)}samples_{timestamp}"
        collector.save_training_data(training_data, filename)

        logger.info(f"💾 Data saved as: {filename}.json")

        # Log data summary
        placements = [point.placement for point in training_data]
        comp_types = [point.comp_type for point in training_data]

        logger.info(f"📊 Data Summary:")
        logger.info(f"   Average placement: {sum(placements)/len(placements):.2f}")
        logger.info(f"   Unique comp types: {len(set(comp_types))}")
        logger.info(f"   Comp distribution: {dict(sorted([(ct, comp_types.count(ct)) for ct in set(comp_types)], key=lambda x: x[1], reverse=True))}")

        return filename

    except Exception as e:
        logger.error(f"❌ Data collection failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def train_model(args, training_data_file=None):
    """Train the ML model."""
    logger.info("=== Starting Model Training ===")

    try:
        settings = Settings()
        trainer = TFTModelTrainer(settings)

        # Load existing training data if specified
        training_data = None
        if training_data_file:
            logger.info(f"Loading training data from: {training_data_file}")
            collector = TFTTrainingDataCollector(settings)
            training_data = collector.load_training_data(training_data_file)

            if not training_data:
                logger.error(f"❌ Failed to load training data from {training_data_file}")
                return None

            logger.info(f"✅ Loaded {len(training_data)} training samples")

        # Generate model name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        model_name = f"tft_strategy_{timestamp}"

        if args.model_name:
            model_name = f"{args.model_name}_{timestamp}"

        logger.info(f"Training model: {model_name}")

        # Train model
        training_results = await trainer.train_model(
            training_data=training_data,
            model_name=model_name,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            optimize_hyperparams=args.optimize_hyperparams
        )

        logger.info("✅ Model training completed!")

        # Log results
        metrics = training_results['evaluation_metrics']
        logger.info(f"📈 Training Results:")
        logger.info(f"   Training samples: {training_results['training_samples']}")
        logger.info(f"   Test samples: {training_results['test_samples']}")
        logger.info(f"   Placement MSE: {metrics['placement_mse']:.4f}")
        logger.info(f"   Comp Type Accuracy: {metrics['comp_type_accuracy']:.1%}")
        logger.info(f"   Risk Level MSE: {metrics['risk_mse']:.4f}")

        # Save results summary
        results_file = f"scripts/results/{model_name}_results.json"
        with open(results_file, 'w') as f:
            json.dump(training_results, f, indent=2, default=str)

        logger.info(f"💾 Results saved to: {results_file}")

        return model_name, training_results

    except Exception as e:
        logger.error(f"❌ Model training failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def full_pipeline(args):
    """Run the complete training pipeline."""
    logger.info("=== Starting Full ML Training Pipeline ===")

    # Step 1: Collect data
    logger.info("Step 1: Data Collection")
    data_file = await collect_training_data(args)

    if not data_file:
        logger.error("❌ Pipeline failed at data collection")
        return

    # Step 2: Train model
    logger.info("Step 2: Model Training")
    result = await train_model(args, data_file)

    if not result:
        logger.error("❌ Pipeline failed at model training")
        return

    model_name, training_results = result

    # Step 3: Summary
    logger.info("=== Pipeline Complete ===")
    logger.info(f"✅ Data collected: {data_file}.json")
    logger.info(f"✅ Model trained: {model_name}")
    logger.info(f"✅ Final accuracy: {training_results['evaluation_metrics']['comp_type_accuracy']:.1%}")

    return model_name

def main():
    """Main script entry point."""
    parser = argparse.ArgumentParser(description="TFT ML Model Training Pipeline")

    # Mode selection
    parser.add_argument('--collect-data', action='store_true', help='Collect training data only')
    parser.add_argument('--train', action='store_true', help='Train model only')
    parser.add_argument('--full-pipeline', action='store_true', help='Run complete pipeline')

    # Data collection parameters
    parser.add_argument('--num-matches', type=int, default=50, help='Number of matches to collect')
    parser.add_argument('--min-rank', choices=['CHALLENGER', 'GRANDMASTER', 'MASTER'], default='MASTER', help='Minimum player rank')
    parser.add_argument('--days-back', type=int, default=3, help='Days back to look for matches')

    # Training parameters
    parser.add_argument('--training-data', type=str, help='Training data file to use (without .json extension)')
    parser.add_argument('--epochs', type=int, default=100, help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Training batch size')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--model-name', type=str, help='Custom model name prefix')
    parser.add_argument('--no-hyperopt', action='store_true', help='Skip hyperparameter optimization')

    args = parser.parse_args()
    args.optimize_hyperparams = not args.no_hyperopt

    # Setup
    setup_directories()

    # Validate arguments
    if not any([args.collect_data, args.train, args.full_pipeline]):
        logger.error("❌ Must specify one of: --collect-data, --train, or --full-pipeline")
        parser.print_help()
        sys.exit(1)

    if args.train and not args.training_data and not args.full_pipeline:
        logger.error("❌ --train requires --training-data unless using --full-pipeline")
        sys.exit(1)

    # Run selected mode
    async def run():
        if args.collect_data:
            await collect_training_data(args)
        elif args.train:
            await train_model(args, args.training_data)
        elif args.full_pipeline:
            await full_pipeline(args)

    # Execute
    try:
        asyncio.run(run())
        logger.info("🎉 Script completed successfully!")
    except KeyboardInterrupt:
        logger.info("⚠️ Script interrupted by user")
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()