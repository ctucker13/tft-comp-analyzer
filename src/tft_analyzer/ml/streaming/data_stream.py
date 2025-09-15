#!/usr/bin/env python3
"""
Real-time TFT Data Streaming Pipeline

Implements a sliding window data management system with:
- Continuous match ingestion from Riot API
- Time-decay weighting for recency awareness
- Sliding window data retention (last 200k-500k matches)
- Mini-batch preparation for streaming updates
"""

import asyncio
import json
import logging
import sqlite3
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

try:
    from ...data.riot_api import RiotTFTAPI
    from ...data.patch_detector import TFTPatchDetector
    from ..data.schemas import TFTGameState
    from ....config.settings import Settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from src.tft_analyzer.data.patch_detector import TFTPatchDetector
    from src.tft_analyzer.ml.data.schemas import TFTGameState
    from config.settings import Settings


class SlidingWindowDataStream:
    """
    Manages a sliding window of TFT match data for real-time training.

    Key features:
    - Continuous data ingestion every 5-10 minutes
    - Sliding window of last 200k-500k matches
    - Time-decay weighting (exp(-Δt/τ))
    - Patch-aware filtering and weighting
    - Mini-batch preparation for streaming updates
    """

    def __init__(self,
                 window_size: int = 300_000,  # Last 300k matches
                 min_rank: str = "DIAMOND",   # Diamond+ only
                 tau_hours: float = 72.0,     # 3-day time decay
                 db_path: str = "data/streaming/matches.db"):

        self.window_size = window_size
        self.min_rank = min_rank
        self.tau_hours = tau_hours
        self.db_path = Path(db_path)

        # Create directory
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.settings = Settings()
        self.riot_api = RiotTFTAPI(self.settings)
        self.patch_detector = TFTPatchDetector()
        self.logger = logging.getLogger(__name__)

        # In-memory sliding window for fast access
        self.match_buffer = deque(maxlen=self.window_size)
        self.last_ingestion = None
        self.current_patch = None

        # Statistics tracking
        self.stats = {
            'total_ingested': 0,
            'matches_in_window': 0,
            'last_update': None,
            'patches_seen': set(),
            'ingestion_errors': 0
        }

        # Initialize database
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    game_datetime TIMESTAMP,
                    patch TEXT,
                    participants BLOB,
                    raw_data BLOB,
                    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    weight REAL DEFAULT 1.0
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_game_datetime
                ON matches(game_datetime)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_patch_time
                ON matches(patch, game_datetime)
            """)

    async def initialize(self):
        """Initialize the streaming pipeline."""
        self.logger.info("🚀 Initializing real-time data stream...")

        # Detect current patch
        self.current_patch = await self.patch_detector.get_current_patch()
        self.logger.info(f"📍 Current patch: {self.current_patch}")

        # Load existing data from database
        await self._load_existing_data()

        self.logger.info(f"✅ Stream initialized with {len(self.match_buffer)} matches in buffer")

    async def _load_existing_data(self):
        """Load recent matches from database into memory buffer."""
        cutoff_time = datetime.now() - timedelta(days=7)  # Last 7 days

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT match_id, game_datetime, patch, participants, raw_data
                FROM matches
                WHERE game_datetime > ?
                ORDER BY game_datetime DESC
                LIMIT ?
            """, (cutoff_time, self.window_size))

            rows = cursor.fetchall()

        # Load into buffer (newest first, then reverse for chronological order)
        loaded_matches = []
        for row in reversed(rows):  # Reverse to get chronological order
            match_data = {
                'match_id': row[0],
                'game_datetime': datetime.fromisoformat(row[1]),
                'patch': row[2],
                'participants': json.loads(row[3]),
                'raw_data': json.loads(row[4])
            }
            loaded_matches.append(match_data)

        self.match_buffer.extend(loaded_matches)
        self.stats['matches_in_window'] = len(self.match_buffer)

        self.logger.info(f"📂 Loaded {len(loaded_matches)} matches from database")

    async def start_streaming(self, interval_minutes: int = 10):
        """
        Start continuous data streaming.

        Args:
            interval_minutes: How often to ingest new data
        """
        self.logger.info(f"🌊 Starting data stream (interval: {interval_minutes}min)")

        while True:
            try:
                await self.ingest_batch()
                await asyncio.sleep(interval_minutes * 60)

            except Exception as e:
                self.logger.error(f"❌ Streaming error: {e}")
                self.stats['ingestion_errors'] += 1
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def ingest_batch(self) -> int:
        """
        Ingest a batch of new matches.

        Returns:
            Number of new matches ingested
        """
        start_time = time.time()

        try:
            # Get high-rank players
            players = await self._get_streaming_players()
            new_matches = 0

            # Collect recent matches from these players
            for player in players[:50]:  # Limit to 50 players per batch
                try:
                    player_matches = await self._collect_player_matches(player['puuid'])
                    new_matches += player_matches

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    self.logger.debug(f"Error collecting from player {player['puuid']}: {e}")
                    continue

            # Update statistics
            self.stats['total_ingested'] += new_matches
            self.stats['matches_in_window'] = len(self.match_buffer)
            self.stats['last_update'] = datetime.now()

            elapsed = time.time() - start_time
            self.logger.info(f"📥 Ingested {new_matches} matches in {elapsed:.1f}s")

            return new_matches

        except Exception as e:
            self.logger.error(f"❌ Batch ingestion failed: {e}")
            return 0

    async def _get_streaming_players(self) -> List[Dict]:
        """Get high-rank players for streaming data collection."""
        players = []

        try:
            # Focus on top players for highest quality data
            challenger = await self.riot_api.get_challenger_players()
            grandmaster = await self.riot_api.get_grandmaster_players()

            players.extend(challenger[:30])  # Top 30 challenger
            players.extend(grandmaster[:70])  # Top 70 GM

        except Exception as e:
            self.logger.warning(f"Error fetching players: {e}")

        return players

    async def _collect_player_matches(self, puuid: str) -> int:
        """Collect recent matches from a single player."""
        new_matches = 0

        try:
            # Get recent match history
            match_ids = await self.riot_api.get_match_history(puuid, count=10)

            for match_id in match_ids[:3]:  # Limit to 3 most recent
                if await self._process_match(match_id):
                    new_matches += 1

        except Exception as e:
            self.logger.debug(f"Error collecting matches for {puuid}: {e}")

        return new_matches

    async def _process_match(self, match_id: str) -> bool:
        """
        Process and store a single match.

        Returns:
            True if match was new and stored
        """
        try:
            # Check if we already have this match
            if any(m['match_id'] == match_id for m in self.match_buffer):
                return False

            # Get match details
            match_data = await self.riot_api.get_match_details(match_id)

            if not self._is_valid_streaming_match(match_data):
                return False

            # Extract key information
            game_datetime = datetime.fromtimestamp(
                match_data['info']['game_creation'] / 1000
            )

            patch = match_data['info'].get('game_version', self.current_patch)
            participants = match_data['info']['participants']

            # Create match record
            match_record = {
                'match_id': match_id,
                'game_datetime': game_datetime,
                'patch': patch,
                'participants': participants,
                'raw_data': match_data
            }

            # Add to sliding window buffer
            self.match_buffer.append(match_record)

            # Store in database
            await self._store_match_db(match_record)

            # Track patches
            self.stats['patches_seen'].add(patch)

            return True

        except Exception as e:
            self.logger.debug(f"Error processing match {match_id}: {e}")
            return False

    def _is_valid_streaming_match(self, match_data: Dict) -> bool:
        """Check if match is suitable for streaming pipeline."""
        try:
            info = match_data.get('info', {})

            # Must be Set 15
            if info.get('tft_set_number') != 15:
                return False

            # Must be ranked
            if info.get('queue_id') != 1100:
                return False

            # Must be recent (last 24 hours for real-time)
            game_creation = info.get('game_creation', 0)
            if game_creation:
                game_date = datetime.fromtimestamp(game_creation / 1000)
                if (datetime.now() - game_date).total_seconds() > 24 * 3600:
                    return False

            # Must be full lobby
            if len(info.get('participants', [])) != 8:
                return False

            return True

        except Exception:
            return False

    async def _store_match_db(self, match_record: Dict):
        """Store match in persistent database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO matches
                (match_id, game_datetime, patch, participants, raw_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                match_record['match_id'],
                match_record['game_datetime'].isoformat(),
                match_record['patch'],
                json.dumps(match_record['participants']),
                json.dumps(match_record['raw_data'])
            ))

    def get_mini_batch(self,
                      batch_size: int = 1000,
                      hours_back: int = 24) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Get a mini-batch of recent matches with time-decay weights.

        Args:
            batch_size: Number of matches to include
            hours_back: How many hours back to look

        Returns:
            (features, targets, weights) arrays
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        # Filter for recent matches
        recent_matches = [
            match for match in self.match_buffer
            if match['game_datetime'] >= cutoff_time
        ]

        if len(recent_matches) == 0:
            return np.array([]), np.array([]), np.array([])

        # Sort by time (most recent first) and take batch_size
        recent_matches.sort(key=lambda x: x['game_datetime'], reverse=True)
        batch_matches = recent_matches[:batch_size]

        # Extract features and targets
        features = []
        targets = []
        weights = []

        now = datetime.now()

        for match in batch_matches:
            # Calculate time-decay weight
            time_diff_hours = (now - match['game_datetime']).total_seconds() / 3600
            weight = np.exp(-time_diff_hours / self.tau_hours)

            # Extract features and targets from match
            match_features, match_targets = self._extract_features_targets(match)

            features.extend(match_features)
            targets.extend(match_targets)
            weights.extend([weight] * len(match_features))

        return np.array(features), np.array(targets), np.array(weights)

    def _extract_features_targets(self, match: Dict) -> Tuple[List, List]:
        """Extract features and targets from a single match."""
        features = []
        targets = []

        participants = match['participants']
        patch = match['patch']
        game_time = match['game_datetime']

        for participant in participants:
            try:
                # Features: patch, time since patch, traits, units, items, etc.
                feature_vector = {
                    'patch': patch,
                    'hours_since_patch': self._hours_since_patch_release(patch, game_time),
                    'placement': participant.get('placement', 8),
                    'level': participant.get('level', 1),
                    'total_damage_to_players': participant.get('total_damage_to_players', 0),
                    'time_eliminated': participant.get('time_eliminated', 0),
                    'last_round': participant.get('last_round', 1),

                    # Traits
                    'traits': self._encode_traits(participant.get('traits', [])),

                    # Units and items
                    'units': self._encode_units(participant.get('units', [])),

                    # Augments
                    'augments': participant.get('augments', []),
                }

                # Target: placement (for regression) or top4 (for classification)
                placement = participant.get('placement', 8)
                top4 = 1 if placement <= 4 else 0

                features.append(feature_vector)
                targets.append({'placement': placement, 'top4': top4})

            except Exception as e:
                self.logger.debug(f"Error extracting features: {e}")
                continue

        return features, targets

    def _hours_since_patch_release(self, patch: str, game_time: datetime) -> float:
        """Calculate hours since patch release (approximate)."""
        # This would ideally use actual patch release dates
        # For now, use a simple heuristic
        return 24.0  # Placeholder

    def _encode_traits(self, traits: List[Dict]) -> Dict:
        """Encode trait information."""
        trait_dict = {}
        for trait in traits:
            name = trait.get('name', '')
            num_units = trait.get('num_units', 0)
            tier_current = trait.get('tier_current', 0)

            trait_dict[f'trait_{name}'] = {
                'num_units': num_units,
                'tier': tier_current
            }

        return trait_dict

    def _encode_units(self, units: List[Dict]) -> List[Dict]:
        """Encode unit and item information."""
        unit_data = []
        for unit in units:
            unit_info = {
                'character_id': unit.get('character_id', ''),
                'tier': unit.get('tier', 1),  # Star level
                'items': unit.get('items', []),
                'rarity': unit.get('rarity', 0),
            }
            unit_data.append(unit_info)

        return unit_data

    def get_statistics(self) -> Dict[str, Any]:
        """Get streaming statistics."""
        return {
            **self.stats,
            'window_size': self.window_size,
            'tau_hours': self.tau_hours,
            'current_patch': self.current_patch,
            'buffer_utilization': len(self.match_buffer) / self.window_size,
            'patches_seen': list(self.stats['patches_seen'])
        }

    async def cleanup_old_data(self, days_to_keep: int = 14):
        """Clean up old data from database."""
        cutoff_time = datetime.now() - timedelta(days=days_to_keep)

        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute("""
                DELETE FROM matches WHERE game_datetime < ?
            """, (cutoff_time,))

            deleted_count = result.rowcount

        self.logger.info(f"🧹 Cleaned up {deleted_count} old matches from database")

        return deleted_count


async def main():
    """Test the streaming data pipeline."""
    stream = SlidingWindowDataStream(
        window_size=10000,  # Smaller for testing
        tau_hours=24.0
    )

    await stream.initialize()

    print("🧪 Testing streaming pipeline...")
    print(f"Initial stats: {stream.get_statistics()}")

    # Test batch ingestion
    new_matches = await stream.ingest_batch()
    print(f"Ingested {new_matches} new matches")

    # Test mini-batch creation
    features, targets, weights = stream.get_mini_batch(batch_size=100)
    print(f"Mini-batch: {len(features)} samples with weights {weights[:5]}")


if __name__ == "__main__":
    asyncio.run(main())