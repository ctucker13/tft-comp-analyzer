"""
TFT Strategy ML Model Architecture
Multi-task learning model for TFT strategic decision making
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional
import numpy as np

from ..data.schemas import ActionType, CompType, RiskLevel


class TFTFeatureEncoder(nn.Module):
    """Encodes TFT game state features into dense representation"""

    def __init__(self, input_dim: int, hidden_dim: int = 256, dropout: float = 0.3):
        super().__init__()

        self.feature_layers = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(dropout),

            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim),
            nn.Dropout(dropout),

            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(hidden_dim // 2),
            nn.Dropout(dropout / 2),
        )

        self.output_dim = hidden_dim // 2

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.feature_layers(x)


class AttentionHead(nn.Module):
    """Attention mechanism for focusing on important features"""

    def __init__(self, input_dim: int, attention_dim: int = 64):
        super().__init__()

        self.attention = nn.Sequential(
            nn.Linear(input_dim, attention_dim),
            nn.Tanh(),
            nn.Linear(attention_dim, 1),
            nn.Softmax(dim=1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attention_weights = self.attention(x)
        return torch.sum(x * attention_weights, dim=1)


class TFTStrategyModel(nn.Module):
    """
    Multi-task learning model for TFT strategic decisions

    Predicts:
    - Optimal action (level/roll/hold/pivot)
    - Composition type recommendation
    - Risk level assessment
    - Continuous values (gold target, leveling priority, etc.)
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int = 256,
        dropout: float = 0.3,
        use_attention: bool = True
    ):
        super().__init__()

        self.encoder = TFTFeatureEncoder(input_dim, hidden_dim, dropout)
        encoded_dim = self.encoder.output_dim

        # Attention mechanism (optional)
        self.use_attention = use_attention
        if use_attention:
            self.attention = AttentionHead(encoded_dim)
            final_dim = encoded_dim
        else:
            final_dim = encoded_dim

        # Task-specific prediction heads
        self.action_head = self._create_classification_head(
            final_dim, len(ActionType), "action_prediction"
        )

        self.comp_head = self._create_classification_head(
            final_dim, len(CompType), "comp_prediction"
        )

        self.risk_head = self._create_classification_head(
            final_dim, len(RiskLevel), "risk_prediction"
        )

        # Regression heads for continuous predictions
        self.regression_head = nn.Sequential(
            nn.Linear(final_dim, final_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout / 2),
            nn.Linear(final_dim // 2, 5)  # [should_level, should_roll, pivot_urgency, gold_target, leveling_priority]
        )

        # Value estimation head (for RL-style training)
        self.value_head = nn.Sequential(
            nn.Linear(final_dim, final_dim // 4),
            nn.ReLU(),
            nn.Linear(final_dim // 4, 1)  # Expected placement (1-8)
        )

    def _create_classification_head(self, input_dim: int, num_classes: int, name: str) -> nn.Module:
        """Create a classification head with dropout and batch norm"""
        return nn.Sequential(
            nn.Linear(input_dim, input_dim // 2),
            nn.ReLU(),
            nn.BatchNorm1d(input_dim // 2),
            nn.Dropout(0.2),
            nn.Linear(input_dim // 2, num_classes)
        )

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through the model

        Args:
            x: Input features [batch_size, input_dim]

        Returns:
            Dictionary of predictions for each task
        """
        # Encode features
        encoded = self.encoder(x)

        # Apply attention if enabled
        if self.use_attention:
            # For attention, we need to reshape if necessary
            if len(encoded.shape) == 2:
                encoded = encoded.unsqueeze(1)  # Add sequence dimension
            attended = self.attention(encoded)
            final_features = attended
        else:
            final_features = encoded

        # Get predictions from each head
        predictions = {
            'action_logits': self.action_head(final_features),
            'comp_logits': self.comp_head(final_features),
            'risk_logits': self.risk_head(final_features),
            'regression_outputs': self.regression_head(final_features),
            'value_estimate': self.value_head(final_features)
        }

        # Apply softmax to classification outputs for probabilities
        predictions['action_probs'] = F.softmax(predictions['action_logits'], dim=-1)
        predictions['comp_probs'] = F.softmax(predictions['comp_logits'], dim=-1)
        predictions['risk_probs'] = F.softmax(predictions['risk_logits'], dim=-1)

        # Apply sigmoid to regression outputs that should be in [0, 1]
        regression = predictions['regression_outputs']
        predictions['should_level_prob'] = torch.sigmoid(regression[:, 0])
        predictions['should_roll_prob'] = torch.sigmoid(regression[:, 1])
        predictions['pivot_urgency'] = torch.sigmoid(regression[:, 2])
        predictions['gold_target'] = regression[:, 3]  # Can be any positive value
        predictions['leveling_priority'] = torch.sigmoid(regression[:, 4])

        return predictions

    def get_feature_importance(self, x: torch.Tensor) -> torch.Tensor:
        """
        Get feature importance using gradient-based attribution

        Args:
            x: Input features [batch_size, input_dim]

        Returns:
            Feature importance scores [batch_size, input_dim]
        """
        x.requires_grad_(True)
        predictions = self.forward(x)

        # Use the action prediction as the target for attribution
        action_probs = predictions['action_probs']
        max_action_prob = torch.max(action_probs, dim=1)[0]

        # Compute gradients
        gradients = torch.autograd.grad(
            outputs=max_action_prob.sum(),
            inputs=x,
            create_graph=False,
            retain_graph=False
        )[0]

        # Return absolute gradients as importance scores
        return torch.abs(gradients)


class TFTSequenceModel(nn.Module):
    """
    Alternative transformer-based model for sequential decision making
    Treats the game as a sequence of states and predicts next best action
    """

    def __init__(
        self,
        input_dim: int,
        d_model: int = 256,
        nhead: int = 8,
        num_layers: int = 6,
        max_sequence_length: int = 50
    ):
        super().__init__()

        self.d_model = d_model
        self.input_projection = nn.Linear(input_dim, d_model)

        # Positional encoding for sequence
        self.pos_encoding = nn.Parameter(
            torch.randn(max_sequence_length, d_model) * 0.1
        )

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=0.1,
            activation='relu',
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_layers
        )

        # Output heads
        self.action_head = nn.Linear(d_model, len(ActionType))
        self.value_head = nn.Linear(d_model, 1)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass for sequence model

        Args:
            x: Input sequence [batch_size, seq_len, input_dim]
            mask: Padding mask [batch_size, seq_len]

        Returns:
            Predictions for each timestep
        """
        batch_size, seq_len, _ = x.shape

        # Project input to model dimension
        x = self.input_projection(x)

        # Add positional encoding
        if seq_len <= self.pos_encoding.size(0):
            x = x + self.pos_encoding[:seq_len].unsqueeze(0)

        # Apply transformer
        transformer_output = self.transformer(x, src_key_padding_mask=mask)

        # Get predictions
        action_logits = self.action_head(transformer_output)
        value_estimates = self.value_head(transformer_output)

        return {
            'action_logits': action_logits,
            'action_probs': F.softmax(action_logits, dim=-1),
            'value_estimates': value_estimates.squeeze(-1)
        }


class TFTModelEnsemble(nn.Module):
    """
    Ensemble of multiple TFT models for improved predictions
    """

    def __init__(self, models: list):
        super().__init__()
        self.models = nn.ModuleList(models)

    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through ensemble

        Args:
            x: Input features

        Returns:
            Averaged predictions from all models
        """
        predictions = []

        for model in self.models:
            pred = model(x)
            predictions.append(pred)

        # Average predictions
        ensemble_pred = {}
        for key in predictions[0].keys():
            if 'logits' in key or 'probs' in key:
                ensemble_pred[key] = torch.stack([p[key] for p in predictions]).mean(dim=0)
            else:
                ensemble_pred[key] = torch.stack([p[key] for p in predictions]).mean(dim=0)

        return ensemble_pred

    def get_prediction_variance(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Get prediction variance for uncertainty estimation

        Args:
            x: Input features

        Returns:
            Variance of predictions across ensemble members
        """
        predictions = []

        for model in self.models:
            with torch.no_grad():
                pred = model(x)
                predictions.append(pred)

        variance = {}
        for key in predictions[0].keys():
            if 'probs' in key:
                stacked = torch.stack([p[key] for p in predictions])
                variance[key] = torch.var(stacked, dim=0)

        return variance