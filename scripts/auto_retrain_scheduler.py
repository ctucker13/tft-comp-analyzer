#!/usr/bin/env python3
"""
Automated TFT Model Retraining Scheduler

This script can run continuously to automatically retrain the model
at specified intervals using fresh 24-hour data.

Usage:
    python scripts/auto_retrain_scheduler.py --interval 6  # Retrain every 6 hours
    python scripts/auto_retrain_scheduler.py --interval 4 --rank CHALLENGER  # Every 4 hours, challenger only
    python scripts/auto_retrain_scheduler.py --once  # Run once now
"""

import asyncio
import argparse
import logging
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from quick_retrain import quick_retrain

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_retrain.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AutoRetrainScheduler:
    """Automated retraining scheduler."""

    def __init__(self, interval_hours: int = 6, num_matches: int = 120, min_rank: str = "MASTER"):
        self.interval_hours = interval_hours
        self.num_matches = num_matches
        self.min_rank = min_rank
        self.running = True
        self.last_retrain = None

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def run_scheduler(self):
        """Main scheduler loop."""
        logger.info("🤖 TFT Auto-Retrain Scheduler Started")
        logger.info(f"⏱️ Retraining interval: {self.interval_hours} hours")
        logger.info(f"🎯 Target matches: {self.num_matches}")
        logger.info(f"🏆 Minimum rank: {self.min_rank}")
        logger.info("Press Ctrl+C to stop")
        print()

        retrain_count = 0

        while self.running:
            try:
                # Calculate next retrain time
                if self.last_retrain:
                    next_retrain = self.last_retrain + timedelta(hours=self.interval_hours)
                    now = datetime.now()

                    if now < next_retrain:
                        wait_seconds = (next_retrain - now).total_seconds()
                        logger.info(f"⏳ Next retrain in {wait_seconds/3600:.1f} hours at {next_retrain.strftime('%H:%M:%S')}")

                        # Wait with periodic status updates
                        while wait_seconds > 0 and self.running:
                            sleep_time = min(wait_seconds, 300)  # Check every 5 minutes
                            await asyncio.sleep(sleep_time)
                            wait_seconds -= sleep_time

                            if wait_seconds > 0:
                                logger.info(f"⏳ {wait_seconds/3600:.1f} hours until next retrain")

                if not self.running:
                    break

                # Perform retrain
                retrain_count += 1
                logger.info(f"🔄 Starting retrain #{retrain_count}")

                success = await quick_retrain(self.num_matches, self.min_rank)

                if success:
                    logger.info(f"✅ Retrain #{retrain_count} successful!")
                    self.last_retrain = datetime.now()
                else:
                    logger.error(f"❌ Retrain #{retrain_count} failed")

                # Brief pause before next cycle
                if self.running:
                    await asyncio.sleep(60)  # 1 minute buffer

            except Exception as e:
                logger.error(f"❌ Scheduler error: {e}")
                logger.info("⏳ Waiting 10 minutes before retry...")
                await asyncio.sleep(600)

        logger.info("🛑 Auto-Retrain Scheduler Stopped")
        logger.info(f"📊 Total retrains completed: {retrain_count}")

    async def run_once(self):
        """Run retrain once and exit."""
        logger.info("🔄 Running single retrain...")

        success = await quick_retrain(self.num_matches, self.min_rank)

        if success:
            logger.info("✅ Single retrain successful!")
            return True
        else:
            logger.error("❌ Single retrain failed")
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="TFT Auto-Retrain Scheduler")

    parser.add_argument("--interval", type=int, default=6, help="Retrain interval in hours (default: 6)")
    parser.add_argument("--matches", type=int, default=120, help="Number of matches to collect (default: 120)")
    parser.add_argument("--rank", choices=["CHALLENGER", "GRANDMASTER", "MASTER"], default="MASTER", help="Minimum rank tier")
    parser.add_argument("--once", action="store_true", help="Run retrain once and exit")

    args = parser.parse_args()

    scheduler = AutoRetrainScheduler(
        interval_hours=args.interval,
        num_matches=args.matches,
        min_rank=args.rank
    )

    if args.once:
        success = await scheduler.run_once()
        sys.exit(0 if success else 1)
    else:
        await scheduler.run_scheduler()


if __name__ == "__main__":
    asyncio.run(main())