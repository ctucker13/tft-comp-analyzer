#!/usr/bin/env python3
"""
Online Learning Adapter for Real-time TFT Training

Implements the two-stage model architecture:
1. Stable base model (updated weekly)
2. Lightweight online adapter (updated hourly)

Features:
- Time-decay weighted mini-batch updates
- Catastrophic forgetting protection
- LoRA-style adapter layers
- Automatic warm-starting from previous adapters
"""

import logging
import pickle
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from collections import deque

try:
    from .data_stream import SlidingWindowDataStream
    from ....config.settings import Settings
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
    from src.tft_analyzer.ml.streaming.data_stream import SlidingWindowDataStream
    from config.settings import Settings


class LoRAAdapter(nn.Module):
    """
    Low-Rank Adaptation (LoRA) layer for efficient fine-tuning.

    Instead of updating all model weights, we add trainable low-rank matrices
    that adapt the base model to recent data.
    """

    def __init__(self, in_features: int, out_features: int, rank: int = 8, alpha: float = 16):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scale = alpha / rank

        # Low-rank matrices (much smaller than full weight matrix)
        self.lora_A = nn.Parameter(torch.randn(in_features, rank) * 0.01)
        self.lora_B = nn.Parameter(torch.zeros(rank, out_features))

        # Original layer (frozen)
        self.original_weight = None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x @ W + x @ (A @ B) * scale
        original_output = torch.matmul(x, self.original_weight) if self.original_weight is not None else 0
        adapter_output = torch.matmul(torch.matmul(x, self.lora_A), self.lora_B) * self.scale
        return original_output + adapter_output

    def set_original_weight(self, weight: torch.Tensor):
        """Set the frozen original weight from base model."""
        self.original_weight = weight.detach()


class OnlineAdapter:
    """
    Online learning adapter for real-time TFT model updates.

    Two-stage architecture:
    1. Base model (stable, updated weekly)
    2. Adapter (lightweight, updated hourly)
    """

    def __init__(self,
                 base_model_path: Optional[str] = None,
                 learning_rate: float = 0.001,
                 forgetting_factor: float = 0.9,
                 replay_buffer_size: int = 10000):

        self.learning_rate = learning_rate
        self.forgetting_factor = forgetting_factor
        self.replay_buffer_size = replay_buffer_size

        # Initialize logger
        self.logger = logging.getLogger(__name__)

        # Model components
        self.base_model = None
        self.adapter_layers = {}
        self.feature_scaler = StandardScaler()

        # Training state
        self.optimizer = None
        self.replay_buffer = deque(maxlen=replay_buffer_size)
        self.update_count = 0
        self.last_update = None

        # Performance tracking
        self.performance_history = deque(maxlen=100)
        self.adaptation_stats = {
            'updates_performed': 0,
            'avg_loss': 0.0,
            'recent_accuracy': 0.0,
            'adaptation_time': 0.0
        }

        # Load or initialize base model
        if base_model_path and Path(base_model_path).exists():
            self.load_base_model(base_model_path)
        else:
            self.initialize_lightweight_model()

    def initialize_lightweight_model(self):
        """Initialize a lightweight base model for bootstrapping."""
        self.logger.info("🔧 Initializing lightweight base model...")

        # Simple gradient boosting model as base
        self.base_model = GradientBoostingRegressor(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )

        # Feature dimensions (will be determined from first batch)
        self.feature_dim = None
        self.output_dim = 2  # placement and top4 probability

        self.logger.info("✅ Lightweight model initialized")

    def load_base_model(self, model_path: str):
        """Load a pre-trained base model."""
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)

            self.base_model = model_data['model']
            self.feature_scaler = model_data.get('scaler', StandardScaler())
            self.feature_dim = model_data.get('feature_dim')

            self.logger.info(f"✅ Loaded base model from {model_path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to load base model: {e}")
            self.initialize_lightweight_model()

    def create_adapter_layers(self, feature_dim: int):
        """Create LoRA adapter layers."""
        if feature_dim == self.feature_dim:
            return  # Already created

        self.feature_dim = feature_dim

        # Create lightweight adaptation layers
        self.adapter_layers = nn.ModuleDict({
            'placement_adapter': LoRAAdapter(feature_dim, 64, rank=8),
            'top4_adapter': LoRAAdapter(64, 1, rank=4)
        })

        # Initialize optimizer for adapter parameters only
        adapter_params = list(self.adapter_layers.parameters())
        self.optimizer = optim.AdamW(adapter_params, lr=self.learning_rate, weight_decay=0.01)

        self.logger.info(f"🎯 Created adapter layers for {feature_dim}D features")

    async def update_online(self,
                          features: np.ndarray,
                          targets: np.ndarray,
                          weights: np.ndarray) -> Dict[str, float]:
        """
        Perform online update with mini-batch of recent data.

        Args:
            features: Feature matrix [N, D]
            targets: Target values [N, 2] (placement, top4)
            weights: Time-decay weights [N]

        Returns:
            Update statistics
        """
        start_time = time.time()

        if len(features) == 0:
            return {'loss': 0.0, 'samples': 0}

        try:
            # Initialize adapters if needed
            if self.feature_dim is None:
                self.create_adapter_layers(features.shape[1])

            # Prepare data
            X_scaled = self._prepare_features(features)
            y = self._prepare_targets(targets)

            # Add to replay buffer (for catastrophic forgetting protection)
            self._update_replay_buffer(X_scaled, y, weights)

            # Perform adaptation
            loss = await self._adapt_with_replay(X_scaled, y, weights)

            # Update statistics
            self.update_count += 1
            self.last_update = datetime.now()
            adaptation_time = time.time() - start_time

            self.adaptation_stats.update({
                'updates_performed': self.update_count,
                'avg_loss': loss,
                'adaptation_time': adaptation_time
            })

            self.logger.info(
                f"📈 Online update #{self.update_count}: "
                f"loss={loss:.4f}, samples={len(features)}, time={adaptation_time:.2f}s"
            )

            return {
                'loss': loss,
                'samples': len(features),
                'adaptation_time': adaptation_time,
                'update_count': self.update_count
            }

        except Exception as e:
            self.logger.error(f"❌ Online update failed: {e}")
            return {'loss': float('inf'), 'samples': 0}

    def _prepare_features(self, features: np.ndarray) -> np.ndarray:
        """Prepare and normalize features."""
        # If features are dicts, convert to vectors
        if isinstance(features[0], dict):
            features = self._dict_features_to_vectors(features)

        # Normalize features
        if hasattr(self.feature_scaler, 'mean_'):  # Already fitted
            X_scaled = self.feature_scaler.transform(features)
        else:  # First batch, fit scaler
            X_scaled = self.feature_scaler.fit_transform(features)

        return X_scaled

    def _prepare_targets(self, targets: np.ndarray) -> np.ndarray:
        """Prepare target values."""
        if isinstance(targets[0], dict):
            # Convert dict targets to array
            placement = np.array([t.get('placement', 8) for t in targets])
            top4 = np.array([t.get('top4', 0) for t in targets])
            return np.column_stack([placement, top4])

        return targets

    def _dict_features_to_vectors(self, features: List[Dict]) -> np.ndarray:
        """Convert dictionary features to fixed-size vectors."""
        # This is a simplified version - you'd want more sophisticated feature engineering
        feature_vectors = []

        for feature_dict in features:
            vector = [
                feature_dict.get('level', 1),
                feature_dict.get('total_damage_to_players', 0) / 10000,  # Normalize
                feature_dict.get('hours_since_patch', 24) / 24,  # Normalize
                len(feature_dict.get('augments', [])),
                len(feature_dict.get('units', [])),
                # Add more feature extraction as needed
            ]

            # Add trait features (simplified)
            traits = feature_dict.get('traits', {})
            for trait_name in ['Sniper', 'Star Guardian', 'TheCrew', 'Bruiser', 'Sorcerer']:
                trait_data = traits.get(f'trait_{trait_name}', {})
                vector.extend([
                    trait_data.get('num_units', 0),
                    trait_data.get('tier', 0)
                ])

            feature_vectors.append(vector)

        return np.array(feature_vectors)

    def _update_replay_buffer(self, X: np.ndarray, y: np.ndarray, weights: np.ndarray):
        """Update replay buffer for catastrophic forgetting protection."""
        for i in range(len(X)):
            self.replay_buffer.append({
                'features': X[i],
                'targets': y[i],
                'weight': weights[i],
                'timestamp': datetime.now()
            })

    async def _adapt_with_replay(self, X_new: np.ndarray, y_new: np.ndarray, weights_new: np.ndarray) -> float:
        """Adapt model with new data + replay buffer samples."""
        if not self.adapter_layers:
            return 0.0

        # Combine new data with replay buffer (80% new, 20% replay)
        replay_size = min(len(self.replay_buffer), int(len(X_new) * 0.25))

        if replay_size > 0:
            replay_samples = list(self.replay_buffer)[-replay_size:]
            X_replay = np.array([s['features'] for s in replay_samples])
            y_replay = np.array([s['targets'] for s in replay_samples])
            weights_replay = np.array([s['weight'] * 0.5 for s in replay_samples])  # Reduce replay weight

            X_combined = np.vstack([X_new, X_replay])
            y_combined = np.vstack([y_new, y_replay])
            weights_combined = np.concatenate([weights_new, weights_replay])
        else:
            X_combined, y_combined, weights_combined = X_new, y_new, weights_new

        # Convert to tensors
        X_tensor = torch.FloatTensor(X_combined)
        y_tensor = torch.FloatTensor(y_combined)
        weight_tensor = torch.FloatTensor(weights_combined)

        # Forward pass through adapter
        self.optimizer.zero_grad()

        # Simple adapter forward pass
        adapted_features = X_tensor
        for name, layer in self.adapter_layers.items():
            if 'placement' in name:
                placement_pred = layer(adapted_features)
            elif 'top4' in name:
                top4_pred = layer(placement_pred)

        # Calculate weighted loss
        placement_loss = torch.nn.functional.mse_loss(
            placement_pred.squeeze(), y_tensor[:, 0], reduction='none'
        )
        top4_loss = torch.nn.functional.binary_cross_entropy_with_logits(
            top4_pred.squeeze(), y_tensor[:, 1], reduction='none'
        )

        # Apply time-decay weights
        weighted_loss = (placement_loss + top4_loss) * weight_tensor
        total_loss = weighted_loss.mean()

        # Backward pass
        total_loss.backward()
        torch.nn.utils.clip_grad_norm_(self.adapter_layers.parameters(), max_norm=1.0)
        self.optimizer.step()

        return total_loss.item()

    def predict(self, features: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Make predictions using base model + adapter.

        Args:
            features: Feature matrix [N, D]

        Returns:
            Predictions dict with 'placement' and 'top4' arrays
        """
        try:
            X_scaled = self._prepare_features(features)

            # Base model prediction
            if hasattr(self.base_model, 'predict'):
                base_pred = self.base_model.predict(X_scaled)
            else:
                base_pred = np.zeros((len(X_scaled), 2))

            # Adapter adjustment
            if self.adapter_layers and len(self.adapter_layers) > 0:
                X_tensor = torch.FloatTensor(X_scaled)

                with torch.no_grad():
                    adapted_features = X_tensor
                    for name, layer in self.adapter_layers.items():
                        if 'placement' in name:
                            placement_adj = layer(adapted_features).numpy()
                        elif 'top4' in name and 'placement_adj' in locals():
                            top4_adj = torch.sigmoid(layer(torch.FloatTensor(placement_adj))).numpy()

                # Combine base prediction with adapter adjustment
                if 'placement_adj' in locals():
                    placement_pred = base_pred[:, 0] + placement_adj.squeeze() * 0.1  # Small adjustment
                else:
                    placement_pred = base_pred[:, 0] if base_pred.ndim > 1 else base_pred

                if 'top4_adj' in locals():
                    top4_pred = np.clip(top4_adj.squeeze(), 0, 1)
                else:
                    top4_pred = (placement_pred <= 4).astype(float)

            else:
                placement_pred = base_pred[:, 0] if base_pred.ndim > 1 else base_pred
                top4_pred = (placement_pred <= 4).astype(float)

            return {
                'placement': placement_pred,
                'top4': top4_pred,
                'confidence': np.ones_like(placement_pred) * 0.8  # Placeholder
            }

        except Exception as e:
            self.logger.error(f"❌ Prediction failed: {e}")
            n_samples = len(features)
            return {
                'placement': np.full(n_samples, 5.0),  # Average placement
                'top4': np.full(n_samples, 0.5),       # 50% top4 rate
                'confidence': np.full(n_samples, 0.1)  # Low confidence
            }

    def save_adapter(self, path: str):
        """Save the current adapter state."""
        adapter_data = {
            'adapter_layers': self.adapter_layers,
            'feature_scaler': self.feature_scaler,
            'feature_dim': self.feature_dim,
            'update_count': self.update_count,
            'stats': self.adaptation_stats,
            'timestamp': datetime.now().isoformat()
        }

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'wb') as f:
            pickle.dump(adapter_data, f)

        self.logger.info(f"💾 Saved adapter to {path}")

    def load_adapter(self, path: str):
        """Load a saved adapter state."""
        try:
            with open(path, 'rb') as f:
                adapter_data = pickle.load(f)

            self.adapter_layers = adapter_data['adapter_layers']
            self.feature_scaler = adapter_data['feature_scaler']
            self.feature_dim = adapter_data['feature_dim']
            self.update_count = adapter_data.get('update_count', 0)
            self.adaptation_stats = adapter_data.get('stats', {})

            # Recreate optimizer
            if self.adapter_layers:
                adapter_params = list(self.adapter_layers.parameters())
                self.optimizer = optim.AdamW(adapter_params, lr=self.learning_rate)

            self.logger.info(f"✅ Loaded adapter from {path}")

        except Exception as e:
            self.logger.error(f"❌ Failed to load adapter: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get current adaptation statistics."""
        return {
            **self.adaptation_stats,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'replay_buffer_size': len(self.replay_buffer),
            'feature_dim': self.feature_dim,
            'has_base_model': self.base_model is not None,
            'has_adapter': len(self.adapter_layers) > 0 if self.adapter_layers else False
        }


async def main():
    """Test the online adapter."""
    adapter = OnlineAdapter()

    # Create dummy data
    features = np.random.randn(100, 10)
    targets = np.random.randint(1, 9, (100, 2))
    weights = np.exp(-np.random.exponential(1, 100))

    print("🧪 Testing online adapter...")
    print(f"Initial stats: {adapter.get_stats()}")

    # Test adaptation
    update_stats = await adapter.update_online(features, targets, weights)
    print(f"Update stats: {update_stats}")

    # Test prediction
    predictions = adapter.predict(features[:10])
    print(f"Predictions: {predictions['placement'][:5]}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())