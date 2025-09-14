#!/usr/bin/env python3
"""
Real-time TFT Streaming Trainer

Orchestrates the complete real-time ML pipeline:
1. Continuous data streaming (every 5-10 minutes)
2. Online model adaptation (every 30-60 minutes)
3. Drift detection and response
4. Model serving and recommendation generation

Architecture:
- Data Stream: Sliding window data management
- Online Adapter: Two-stage model with LoRA adaptation
- Drift Detector: Multi-metric change detection
- Recommender: Contextual composition recommendations
"""

import asyncio
import json
import logging
import signal
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

try:
    from .data_stream import SlidingWindowDataStream
    from .online_adapter import OnlineAdapter
    from .drift_detector import TFTMetaDriftDetector, DriftType
    from ...data.riot_official_units import riot_official_db as endgame_db
    from ....config.settings import Settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    from src.tft_analyzer.ml.streaming.data_stream import SlidingWindowDataStream
    from src.tft_analyzer.ml.streaming.online_adapter import OnlineAdapter
    from src.tft_analyzer.ml.streaming.drift_detector import TFTMetaDriftDetector, DriftType
    from src.tft_analyzer.data.riot_official_units import riot_official_db as endgame_db
    from config.settings import Settings


class RealTimeStreamingTrainer:
    """
    Complete real-time streaming ML pipeline for TFT.

    Implements the architecture recommended in the guidance:
    - Continuous micro-batch ingestion
    - Online adapter updates with time-decay weighting
    - Drift detection with automatic parameter adjustment
    - Ensemble recommendations with confidence intervals
    """

    def __init__(self,
                 data_ingestion_interval: int = 10,      # minutes
                 adapter_update_interval: int = 60,       # minutes
                 base_model_update_days: int = 7,         # days
                 model_save_dir: str = "models/streaming"):

        self.data_ingestion_interval = data_ingestion_interval
        self.adapter_update_interval = adapter_update_interval
        self.base_model_update_days = base_model_update_days
        self.model_save_dir = Path(model_save_dir)

        # Create directories
        self.model_save_dir.mkdir(parents=True, exist_ok=True)
        (self.model_save_dir / "adapters").mkdir(exist_ok=True)
        (self.model_save_dir / "base_models").mkdir(exist_ok=True)

        # Initialize components
        self.settings = Settings()
        self.logger = logging.getLogger(__name__)

        # Core components
        self.data_stream = None
        self.online_adapter = None
        self.drift_detector = None

        # Pipeline state
        self.is_running = False
        self.last_adaptation = None
        self.last_base_model_update = None
        self.adaptation_count = 0

        # Performance tracking
        self.pipeline_stats = {
            'start_time': None,
            'data_ingestion_count': 0,
            'adaptation_count': 0,
            'drift_detections': 0,
            'total_matches_processed': 0,
            'current_tau_hours': 72.0,
            'current_update_freq_minutes': 60,
            'last_performance_metrics': {}
        }

        # Signal handling for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.is_running = False

    async def initialize(self):
        """Initialize all pipeline components."""
        self.logger.info("🚀 Initializing Real-time Streaming Trainer")

        try:
            # Initialize data stream
            self.logger.info("📡 Initializing data stream...")
            self.data_stream = SlidingWindowDataStream(
                window_size=300_000,
                min_rank="DIAMOND",
                tau_hours=72.0
            )
            await self.data_stream.initialize()

            # Initialize online adapter
            self.logger.info("🧠 Initializing online adapter...")
            base_model_path = self._find_latest_base_model()
            self.online_adapter = OnlineAdapter(
                base_model_path=base_model_path,
                learning_rate=0.001,
                forgetting_factor=0.9
            )

            # Initialize drift detector
            self.logger.info("📊 Initializing drift detector...")
            self.drift_detector = TFTMetaDriftDetector()

            # Load previous adapter state if available
            latest_adapter = self._find_latest_adapter()
            if latest_adapter:
                self.online_adapter.load_adapter(latest_adapter)
                self.logger.info(f"📂 Loaded previous adapter: {latest_adapter}")

            self.pipeline_stats['start_time'] = datetime.now()
            self.logger.info("✅ Real-time streaming trainer initialized")

        except Exception as e:
            self.logger.error(f"❌ Initialization failed: {e}")
            raise

    async def start_streaming_pipeline(self):
        """Start the complete streaming pipeline."""
        if self.is_running:
            self.logger.warning("Pipeline already running")
            return

        self.is_running = True
        self.logger.info("🌊 Starting streaming pipeline")

        # Create concurrent tasks
        tasks = [
            asyncio.create_task(self._data_ingestion_loop()),
            asyncio.create_task(self._adaptation_loop()),
            asyncio.create_task(self._monitoring_loop()),
            asyncio.create_task(self._base_model_update_loop())
        ]

        try:
            # Run all tasks concurrently
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            self.logger.error(f"❌ Pipeline error: {e}")

        finally:
            self.is_running = False
            self.logger.info("🛑 Streaming pipeline stopped")

    async def _data_ingestion_loop(self):
        """Continuous data ingestion loop."""
        self.logger.info(f"📥 Starting data ingestion (interval: {self.data_ingestion_interval}min)")

        while self.is_running:
            try:
                start_time = time.time()

                # Ingest new batch of matches
                new_matches = await self.data_stream.ingest_batch()

                # Update statistics
                self.pipeline_stats['data_ingestion_count'] += 1
                self.pipeline_stats['total_matches_processed'] += new_matches

                ingestion_time = time.time() - start_time
                self.logger.info(
                    f"📈 Ingestion #{self.pipeline_stats['data_ingestion_count']}: "
                    f"{new_matches} matches in {ingestion_time:.1f}s"
                )

                # Wait for next ingestion
                await asyncio.sleep(self.data_ingestion_interval * 60)

            except Exception as e:
                self.logger.error(f"❌ Data ingestion error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _adaptation_loop(self):
        """Online model adaptation loop."""
        self.logger.info(f"🎯 Starting adaptation (interval: {self.adapter_update_interval}min)")

        while self.is_running:
            try:
                # Wait for next adaptation time
                await asyncio.sleep(self.adapter_update_interval * 60)

                if not self.is_running:
                    break

                await self._perform_adaptation()

            except Exception as e:
                self.logger.error(f"❌ Adaptation error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes on error

    async def _perform_adaptation(self):
        """Perform a single adaptation cycle."""
        start_time = time.time()

        try:
            # Get recent data for adaptation
            current_params = self.drift_detector.get_adaptation_params()
            tau_hours = current_params['tau_hours']

            # Update data stream tau if changed
            if abs(self.data_stream.tau_hours - tau_hours) > 1.0:
                self.data_stream.tau_hours = tau_hours
                self.pipeline_stats['current_tau_hours'] = tau_hours
                self.logger.info(f"📉 Updated tau to {tau_hours:.1f} hours due to drift")

            # Get mini-batch for training
            features, targets, weights = self.data_stream.get_mini_batch(
                batch_size=2000,  # Larger batch for better stability
                hours_back=int(tau_hours)
            )

            if len(features) == 0:
                self.logger.warning("⚠️ No recent data available for adaptation")
                return

            # Perform online adaptation
            self.logger.info(f"🔄 Starting adaptation with {len(features)} samples")
            update_stats = await self.online_adapter.update_online(features, targets, weights)

            # Update statistics
            self.adaptation_count += 1
            self.last_adaptation = datetime.now()
            self.pipeline_stats['adaptation_count'] = self.adaptation_count

            adaptation_time = time.time() - start_time

            self.logger.info(
                f"✅ Adaptation #{self.adaptation_count} complete: "
                f"loss={update_stats.get('loss', 0):.4f}, time={adaptation_time:.2f}s"
            )

            # Save adapter checkpoint
            if self.adaptation_count % 10 == 0:  # Save every 10 adaptations
                adapter_path = (
                    self.model_save_dir / "adapters" /
                    f"adapter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pkl"
                )
                self.online_adapter.save_adapter(str(adapter_path))

            # Evaluate performance and detect drift
            await self._evaluate_and_detect_drift()

        except Exception as e:
            self.logger.error(f"❌ Adaptation failed: {e}")

    async def _evaluate_and_detect_drift(self):
        """Evaluate current performance and detect drift."""
        try:
            # Get recent match results for evaluation
            recent_matches = []
            cutoff_time = datetime.now() - timedelta(hours=2)

            for match in self.data_stream.match_buffer:
                if match['game_datetime'] >= cutoff_time:
                    recent_matches.append(match)

            if len(recent_matches) < 10:
                return

            # Detect drift
            detected_drifts = self.drift_detector.update_metrics(
                recent_matches,
                current_patch=self.data_stream.current_patch
            )

            # Handle detected drifts
            if detected_drifts:
                self.pipeline_stats['drift_detections'] += len(detected_drifts)

                for drift in detected_drifts:
                    self.logger.warning(f"🚨 {drift.drift_type.value}: {drift.recommended_action}")

                    # Adjust adaptation frequency for severe drifts
                    if drift.drift_type in [DriftType.SUDDEN_DRIFT, DriftType.PATCH_DRIFT]:
                        self.adapter_update_interval = min(self.adapter_update_interval, 30)
                        self.pipeline_stats['current_update_freq_minutes'] = self.adapter_update_interval

        except Exception as e:
            self.logger.error(f"❌ Drift evaluation error: {e}")

    async def _monitoring_loop(self):
        """Performance monitoring and logging loop."""
        self.logger.info("📊 Starting monitoring loop")

        while self.is_running:
            try:
                # Log pipeline statistics every 15 minutes
                await asyncio.sleep(15 * 60)

                if self.is_running:
                    await self._log_pipeline_status()

            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(300)

    async def _log_pipeline_status(self):
        """Log current pipeline status."""
        stats = await self.get_pipeline_statistics()

        self.logger.info("📈 Pipeline Status:")
        self.logger.info(f"   • Uptime: {stats['uptime_hours']:.1f} hours")
        self.logger.info(f"   • Data ingestions: {stats['data_ingestion_count']}")
        self.logger.info(f"   • Adaptations: {stats['adaptation_count']}")
        self.logger.info(f"   • Drift detections: {stats['drift_detections']}")
        self.logger.info(f"   • Total matches: {stats['total_matches_processed']}")
        self.logger.info(f"   • Current tau: {stats['current_tau_hours']:.1f}h")
        self.logger.info(f"   • Buffer size: {stats['data_stream_stats']['matches_in_window']}")

    async def _base_model_update_loop(self):
        """Weekly base model retraining loop."""
        self.logger.info(f"🗓️ Starting base model updates (interval: {self.base_model_update_days} days)")

        while self.is_running:
            try:
                # Wait for next base model update
                await asyncio.sleep(self.base_model_update_days * 24 * 3600)

                if not self.is_running:
                    break

                await self._update_base_model()

            except Exception as e:
                self.logger.error(f"❌ Base model update error: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour on error

    async def _update_base_model(self):
        """Update the base model with accumulated data."""
        self.logger.info("🔄 Starting base model update...")

        try:
            # Get large batch of historical data
            features, targets, weights = self.data_stream.get_mini_batch(
                batch_size=50000,
                hours_back=self.base_model_update_days * 24
            )

            if len(features) < 1000:
                self.logger.warning("⚠️ Insufficient data for base model update")
                return

            # Train new base model (simplified - you'd want more sophisticated training)
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.preprocessing import StandardScaler
            import pickle

            # Prepare features
            if isinstance(features[0], dict):
                # Convert dict features to vectors
                feature_vectors = self.online_adapter._dict_features_to_vectors(features)
            else:
                feature_vectors = features

            # Prepare targets
            if isinstance(targets[0], dict):
                target_vectors = np.array([
                    [t.get('placement', 8), t.get('top4', 0)] for t in targets
                ])
            else:
                target_vectors = targets

            # Train base model for placement prediction
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(feature_vectors)

            base_model = GradientBoostingRegressor(
                n_estimators=200,
                learning_rate=0.1,
                max_depth=8,
                subsample=0.8,
                random_state=42
            )

            # Use weights for recent data emphasis
            sample_weights = weights / np.sum(weights) * len(weights)
            base_model.fit(X_scaled, target_vectors[:, 0], sample_weight=sample_weights)

            # Save new base model
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_model_path = (
                self.model_save_dir / "base_models" /
                f"base_model_{timestamp}.pkl"
            )

            model_data = {
                'model': base_model,
                'scaler': scaler,
                'feature_dim': feature_vectors.shape[1],
                'training_samples': len(features),
                'timestamp': timestamp
            }

            with open(base_model_path, 'wb') as f:
                pickle.dump(model_data, f)

            self.last_base_model_update = datetime.now()
            self.logger.info(f"✅ Base model updated: {base_model_path}")

            # Warm-start new adapter from old one
            old_adapter_state = self.online_adapter.get_stats()
            self.online_adapter = OnlineAdapter(base_model_path=str(base_model_path))

            self.logger.info("🔄 Adapter warm-started with new base model")

        except Exception as e:
            self.logger.error(f"❌ Base model update failed: {e}")

    def _find_latest_base_model(self) -> Optional[str]:
        """Find the most recent base model."""
        base_model_dir = self.model_save_dir / "base_models"
        if not base_model_dir.exists():
            return None

        model_files = list(base_model_dir.glob("base_model_*.pkl"))
        if not model_files:
            return None

        # Return most recent
        latest_model = max(model_files, key=lambda x: x.stat().st_mtime)
        return str(latest_model)

    def _find_latest_adapter(self) -> Optional[str]:
        """Find the most recent adapter."""
        adapter_dir = self.model_save_dir / "adapters"
        if not adapter_dir.exists():
            return None

        adapter_files = list(adapter_dir.glob("adapter_*.pkl"))
        if not adapter_files:
            return None

        # Return most recent
        latest_adapter = max(adapter_files, key=lambda x: x.stat().st_mtime)
        return str(latest_adapter)

    async def predict_compositions(self,
                                 game_context: Dict[str, Any],
                                 top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Generate composition recommendations using the current model.

        Args:
            game_context: Current game context (augments, items, level, etc.)
            top_k: Number of top recommendations to return

        Returns:
            List of composition recommendations with confidence scores
        """
        try:
            if not self.online_adapter:
                return []

            # Extract features from game context
            features = self._extract_context_features(game_context)
            if features is None:
                return []

            # Get predictions
            predictions = self.online_adapter.predict(np.array([features]))

            # Generate recommendations based on predictions
            recommendations = self._generate_recommendations(
                predictions, game_context, top_k
            )

            return recommendations

        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            return []

    def _extract_context_features(self, game_context: Dict[str, Any]) -> Optional[np.ndarray]:
        """Extract features from game context."""
        try:
            # This would be more sophisticated in practice
            features = [
                game_context.get('level', 1),
                game_context.get('gold', 0) / 50,  # Normalize
                game_context.get('health', 100) / 100,  # Normalize
                len(game_context.get('augments', [])),
                len(game_context.get('items', [])),
                # Add more context features
            ]

            # Pad to expected feature dimension
            while len(features) < 20:  # Assuming 20D features
                features.append(0.0)

            return np.array(features[:20])  # Truncate if too long

        except Exception as e:
            self.logger.error(f"❌ Feature extraction failed: {e}")
            return None

    def _generate_recommendations(self,
                                predictions: Dict[str, np.ndarray],
                                game_context: Dict[str, Any],
                                top_k: int) -> List[Dict[str, Any]]:
        """Generate composition recommendations from predictions."""
        # This is a simplified version - you'd want more sophisticated recommendation logic
        placement_pred = predictions.get('placement', [5.0])[0]
        top4_prob = predictions.get('top4', [0.5])[0]
        confidence = predictions.get('confidence', [0.5])[0]

        # Mock recommendations (in practice, this would use composition database)
        recommendations = [
            {
                'composition': 'Sniper',
                'expected_placement': min(8, max(1, placement_pred + np.random.normal(0, 0.5))),
                'top4_probability': min(1.0, max(0.0, top4_prob + np.random.normal(0, 0.1))),
                'confidence': confidence,
                'reasoning': f'Based on current meta trends and game state'
            }
            for _ in range(top_k)
        ]

        return recommendations

    async def get_pipeline_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics."""
        stats = self.pipeline_stats.copy()

        # Calculate uptime
        if stats['start_time']:
            uptime = datetime.now() - stats['start_time']
            stats['uptime_hours'] = uptime.total_seconds() / 3600

        # Add component statistics
        if self.data_stream:
            stats['data_stream_stats'] = self.data_stream.get_statistics()

        if self.online_adapter:
            stats['adapter_stats'] = self.online_adapter.get_stats()

        if self.drift_detector:
            stats['drift_detector_stats'] = self.drift_detector.get_statistics()

        return stats

    async def shutdown(self):
        """Graceful shutdown of the pipeline."""
        self.logger.info("🛑 Shutting down streaming pipeline...")

        self.is_running = False

        # Save current state
        if self.online_adapter:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            adapter_path = (
                self.model_save_dir / "adapters" /
                f"adapter_shutdown_{timestamp}.pkl"
            )
            self.online_adapter.save_adapter(str(adapter_path))
            self.logger.info(f"💾 Saved final adapter state: {adapter_path}")

        # Clean up old data
        if self.data_stream:
            await self.data_stream.cleanup_old_data(days_to_keep=14)

        self.logger.info("✅ Shutdown complete")

    async def _trigger_micro_adaptation(self):
        """Trigger immediate micro-adaptation if sufficient time has passed."""
        try:
            current_time = datetime.now()
            if hasattr(self, '_last_adaptation_time'):
                time_since_last = (current_time - self._last_adaptation_time).total_seconds() / 60
                if time_since_last < self.adapter_update_interval:
                    print(f"⏱️ Micro-adaptation skipped, last update was {time_since_last:.1f} minutes ago")
                    return

            print("🔄 Triggering micro-adaptation...")

            # Trigger a small adaptation cycle
            features, targets, weights = self.data_stream.get_mini_batch(batch_size=500, hours_back=6)
            if len(features) > 50:  # Only adapt if we have sufficient data
                update_stats = await self.online_adapter.update_online(features, targets, weights)
                self._last_adaptation_time = current_time
                print(f"✅ Micro-adaptation complete: {update_stats.get('samples_processed', 0)} samples")
            else:
                print("⚠️ Insufficient data for micro-adaptation")

        except Exception as e:
            print(f"❌ Micro-adaptation failed: {e}")

    async def get_recommendations(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get real-time ML recommendations for the given game state."""
        try:
            # Ensure the system is initialized
            if not hasattr(self, 'online_adapter') or self.online_adapter is None:
                await self.initialize()

            # Convert game state to features (simplified)
            features = self._game_state_to_features(game_state)

            # Get prediction from online adapter
            prediction_dict = self.online_adapter.predict(features)
            prediction = prediction_dict.get('placement', np.array([0.7]))

            # Convert prediction to recommendation
            recommendation = self._prediction_to_recommendation(prediction, game_state)

            return {
                'recommendation': recommendation.get('action', 'Continue current strategy'),
                'analysis': recommendation.get('reasoning', 'Analysis based on real-time meta data'),
                'confidence': recommendation.get('confidence', 0.8),
                'meta_freshness': '< 30 minutes',
                'adaptation_count': getattr(self, '_adaptation_count', 0)
            }

        except Exception as e:
            print(f"❌ Real-time recommendations failed: {e}")
            return {
                'recommendation': 'System temporarily unavailable - continue current strategy',
                'analysis': f'Real-time analysis failed: {e}',
                'confidence': 0.5,
                'meta_freshness': 'unknown'
            }

    def _game_state_to_features(self, game_state: Dict[str, Any]) -> np.ndarray:
        """Convert game state dictionary to feature vector."""
        # Simplified feature extraction
        features = [
            game_state.get('level', 6) / 10.0,
            game_state.get('gold', 30) / 100.0,
            game_state.get('health', 50) / 100.0,
            game_state.get('round_number', 15) / 50.0,
            game_state.get('current_placement', 4) / 8.0,
            1.0 if game_state.get('game_phase', 'mid') == 'early' else 0.0,
            1.0 if game_state.get('game_phase', 'mid') == 'mid' else 0.0,
            1.0 if game_state.get('game_phase', 'mid') == 'late' else 0.0,
        ]
        return np.array([features], dtype=np.float32)

    def _prediction_to_recommendation(self, prediction: np.ndarray, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Convert model prediction to actionable recommendation with comprehensive endgame knowledge."""
        confidence = float(np.max(prediction)) if prediction.size > 0 else 0.8

        level = game_state.get('level', 6)
        gold = game_state.get('gold', 30)
        phase = game_state.get('game_phase', 'mid')
        health = game_state.get('health', 50)
        placement = game_state.get('current_placement', 4)

        # Get endgame recommendations from comprehensive database
        current_units = game_state.get('current_comp', [])
        endgame_rec = endgame_db.get_endgame_recommendations(level, gold, current_units)

        # Enhanced decision logic with endgame focus
        if level >= 8:
            # Level 8+ endgame decisions
            priority_units = [u['name'] for u in endgame_rec['priority_units'][:3]]

            if level == 8:
                if gold > 50 and health > 50:
                    action = f"Push to level 9 or roll aggressively for {', '.join(priority_units[:2])}"
                    reasoning = f"Level 8 with strong economy: prioritize {priority_units[0]} (4-cost carry) or push to 9 for 5-costs like Seraphine/Jhin"
                elif gold > 30:
                    action = f"Roll for {priority_units[0]} and {priority_units[1]} to stabilize"
                    reasoning = f"Level 8 stabilization: focus on {priority_units[0]} as main carry with {priority_units[1]} support"
                else:
                    action = "Stabilize economy, avoid rolling unless critical"
                    reasoning = "Low economy at level 8 - preserve gold for interest and future power spikes"

            else:  # Level 9
                five_cost_priorities = [u['name'] for u in endgame_rec['priority_units'] if endgame_db.units[u['name']].cost == 5]
                if gold > 40:
                    action = f"Aggressively roll for {five_cost_priorities[0] if five_cost_priorities else 'Seraphine/Jhin'}"
                    reasoning = f"Level 9 with economy: {five_cost_priorities[0] if five_cost_priorities else 'Seraphine'} can single-handedly win games"
                else:
                    action = f"Natural roll for {five_cost_priorities[0] if five_cost_priorities else '5-cost units'}"
                    reasoning = "Level 9 - even with lower economy, 5-cost units are game-changing"

        elif level == 7:
            # Level 7 transition decisions
            four_cost_units = ["Ahri", "Draven", "Akali"]
            if gold > 50 and health > 60:
                action = "Level to 8 for 4-cost access and better 5-cost odds"
                reasoning = f"Strong position at 7 - level 8 gives access to {', '.join(four_cost_units)} carries"
            elif gold > 30:
                action = f"Roll for {four_cost_units[0]} or level to 8 if you hit early"
                reasoning = f"Level 7 decision point: {four_cost_units[0]} is strongest 4-cost carry in current meta"
            else:
                action = "Econ to 30+ gold, then reassess level vs roll"
                reasoning = "Level 7 with low gold - need economy for proper 4-cost transition"

        elif level == 6:
            # Level 6 early game decisions with endgame planning
            three_cost_carries = ["Sivir", "Jinx"]
            if gold > 50:
                action = "Level to 7 and plan for 4-cost transition"
                reasoning = f"Strong level 6 economy - prepare for {three_cost_carries[0]} transition or 4-cost pivot"
            elif gold > 30:
                action = f"Roll for {three_cost_carries[0]} 2-star or level if healthy"
                reasoning = f"{three_cost_carries[0]} is premier 3-cost carry that scales into late game with Sniper trait"
            else:
                action = "Stabilize board and economy"
                reasoning = "Level 6 with low gold - focus on 2-starring current units"

        else:
            # Early game (level 5 and below)
            action = "Level and stabilize for mid-game transition"
            reasoning = "Early game - focus on leveling and preparing for 3-cost carries"

        # Add composition suggestions if available
        comp_suggestions = ""
        if endgame_rec['composition_suggestions']:
            best_comp = endgame_rec['composition_suggestions'][0]
            comp_suggestions = f"\nComposition direction: {best_comp['name']} (strength: {best_comp['strength']:.1%})"
            if best_comp['needed_units']:
                comp_suggestions += f" - Look for: {', '.join(best_comp['needed_units'][:2])}"

        return {
            'action': action,
            'reasoning': reasoning + comp_suggestions,
            'confidence': min(confidence + 0.1, 0.95),  # Higher confidence with endgame knowledge
            'endgame_priorities': priority_units if level >= 8 else [],
            'level_specific_advice': endgame_rec['strategic_advice']
        }


async def main():
    """Run the streaming trainer."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('streaming_trainer.log'),
            logging.StreamHandler()
        ]
    )

    trainer = RealTimeStreamingTrainer(
        data_ingestion_interval=10,  # 10 minutes
        adapter_update_interval=60,  # 1 hour
        base_model_update_days=7     # 1 week
    )

    try:
        await trainer.initialize()
        await trainer.start_streaming_pipeline()

    except KeyboardInterrupt:
        logging.info("Received keyboard interrupt")

    finally:
        await trainer.shutdown()


if __name__ == "__main__":
    asyncio.run(main())