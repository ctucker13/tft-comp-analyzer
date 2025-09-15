#!/usr/bin/env python3
"""
TFT Meta Analysis ML Model

Analyzes match data to identify meta compositions, trends, and performance patterns.
This model focuses on understanding the broader meta rather than individual strategic decisions.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta
import json

from ..data.schemas import CompType, GamePhase


class CompEmbedding(nn.Module):
    """Learns embeddings for different composition types based on unit combinations."""

    def __init__(self, num_units: int, embedding_dim: int = 64):
        super().__init__()
        self.unit_embeddings = nn.Embedding(num_units, embedding_dim)
        self.position_encodings = nn.Embedding(28, embedding_dim)  # 7x4 board positions
        self.tier_encodings = nn.Embedding(4, embedding_dim)  # 1-3 star + empty

    def forward(self, board_state: torch.Tensor) -> torch.Tensor:
        """
        Args:
            board_state: [batch_size, 28, 3] - (unit_id, tier, position)
        """
        unit_emb = self.unit_embeddings(board_state[:, :, 0])
        tier_emb = self.tier_encodings(board_state[:, :, 1])
        pos_emb = self.position_encodings(torch.arange(28).to(board_state.device))

        combined = unit_emb + tier_emb + pos_emb.unsqueeze(0)
        return combined.mean(dim=1)  # Average over board positions


class MetaTrendEncoder(nn.Module):
    """Encodes temporal patterns and meta trends."""

    def __init__(self, input_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True, num_layers=2)
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=8)

    def forward(self, sequence: torch.Tensor) -> torch.Tensor:
        """
        Args:
            sequence: [batch_size, seq_len, features] - Time series of match data
        """
        lstm_out, _ = self.lstm(sequence)

        # Apply self-attention to capture important time periods
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)

        return attn_out.mean(dim=1)  # Average over time steps


class TFTMetaAnalysisModel(nn.Module):
    """
    Meta analysis model for TFT composition trends and performance.

    Predicts:
    - Composition win rates and popularity trends
    - Meta tier rankings (S/A/B/C tiers)
    - Synergy strength analysis
    - Optimal item combinations per comp
    - Counter-pick recommendations
    """

    def __init__(
        self,
        num_units: int = 60,  # Approximate units in Set 15
        num_traits: int = 25,  # Set 15 traits
        num_items: int = 40,   # Completed items
        embedding_dim: int = 64,
        hidden_dim: int = 256,
        sequence_length: int = 50  # Number of recent matches to analyze
    ):
        super().__init__()

        self.comp_embeddings = CompEmbedding(num_units, embedding_dim)
        self.trend_encoder = MetaTrendEncoder(embedding_dim + num_traits + num_items, hidden_dim)

        # Meta analysis heads
        self.winrate_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, len(CompType))  # Win rate per comp type
        )

        self.popularity_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, len(CompType))  # Play rate per comp type
        )

        self.tier_ranking_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, len(CompType))  # Meta tier score per comp
        )

        self.synergy_strength_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, num_traits)  # Trait synergy strength
        )

        self.item_optimization_head = nn.Sequential(
            nn.Linear(hidden_dim + len(CompType), hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim // 2, num_items)  # Optimal items per comp
        )

        # Counter analysis head
        self.counter_matrix_head = nn.Sequential(
            nn.Linear(hidden_dim, len(CompType) * len(CompType)),
            nn.Sigmoid()  # Probability that comp A beats comp B
        )

    def forward(self, match_sequence: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass for meta analysis.

        Args:
            match_sequence: Dictionary containing:
                - board_states: [batch_size, seq_len, 28, 3]
                - trait_vectors: [batch_size, seq_len, num_traits]
                - item_vectors: [batch_size, seq_len, num_items]
                - comp_types: [batch_size, seq_len] - for conditioning

        Returns:
            Dictionary of meta analysis predictions
        """
        batch_size, seq_len = match_sequence['board_states'].shape[:2]

        # Encode compositions
        board_flat = match_sequence['board_states'].view(-1, 28, 3)
        comp_embeddings = self.comp_embeddings(board_flat)
        comp_embeddings = comp_embeddings.view(batch_size, seq_len, -1)

        # Combine with trait and item information
        combined_features = torch.cat([
            comp_embeddings,
            match_sequence['trait_vectors'],
            match_sequence['item_vectors']
        ], dim=-1)

        # Encode temporal trends
        trend_features = self.trend_encoder(combined_features)

        # Generate meta predictions
        predictions = {
            'win_rates': self.winrate_head(trend_features),
            'popularity': self.popularity_head(trend_features),
            'tier_rankings': self.tier_ranking_head(trend_features),
            'synergy_strengths': self.synergy_strength_head(trend_features)
        }

        # Item optimization (conditioned on comp type)
        if 'comp_types' in match_sequence:
            comp_onehot = F.one_hot(match_sequence['comp_types'][:, -1], len(CompType)).float()
            item_input = torch.cat([trend_features, comp_onehot], dim=-1)
            predictions['optimal_items'] = self.item_optimization_head(item_input)

        # Counter matrix
        counter_logits = self.counter_matrix_head(trend_features)
        predictions['counter_matrix'] = counter_logits.view(batch_size, len(CompType), len(CompType))

        return predictions

    def get_meta_tier_list(self, predictions: Dict[str, torch.Tensor]) -> Dict[str, List[str]]:
        """Convert model predictions to interpretable tier list."""
        tier_scores = predictions['tier_rankings'].mean(dim=0).cpu().numpy()
        win_rates = predictions['win_rates'].mean(dim=0).cpu().numpy()
        popularity = predictions['popularity'].mean(dim=0).cpu().numpy()

        # Combine metrics for final tier scoring
        combined_scores = 0.5 * tier_scores + 0.3 * win_rates + 0.2 * popularity

        comp_names = [comp.value for comp in CompType]
        comp_scores = list(zip(comp_names, combined_scores))
        comp_scores.sort(key=lambda x: x[1], reverse=True)

        # Create tier buckets
        num_comps = len(comp_scores)
        s_tier = comp_scores[:max(1, num_comps // 4)]
        a_tier = comp_scores[num_comps // 4:num_comps // 2]
        b_tier = comp_scores[num_comps // 2:3 * num_comps // 4]
        c_tier = comp_scores[3 * num_comps // 4:]

        return {
            'S': [comp[0] for comp in s_tier],
            'A': [comp[0] for comp in a_tier],
            'B': [comp[0] for comp in b_tier],
            'C': [comp[0] for comp in c_tier]
        }

    def analyze_meta_trends(self, historical_data: List[Dict]) -> Dict[str, any]:
        """Analyze meta trends over time."""
        trends = {
            'rising_comps': [],
            'falling_comps': [],
            'stable_meta': [],
            'patch_impact': {},
            'synergy_changes': {}
        }

        if len(historical_data) < 2:
            return trends

        # Compare recent vs older data
        recent_data = historical_data[-len(historical_data)//3:]  # Last third
        older_data = historical_data[:len(historical_data)//3]    # First third

        # Calculate trend changes
        for comp in CompType:
            recent_performance = np.mean([d.get('win_rates', {}).get(comp.value, 0) for d in recent_data])
            older_performance = np.mean([d.get('win_rates', {}).get(comp.value, 0) for d in older_data])

            change = recent_performance - older_performance

            if change > 0.05:  # 5% increase
                trends['rising_comps'].append({
                    'comp': comp.value,
                    'change': change,
                    'current_wr': recent_performance
                })
            elif change < -0.05:  # 5% decrease
                trends['falling_comps'].append({
                    'comp': comp.value,
                    'change': change,
                    'current_wr': recent_performance
                })
            else:
                trends['stable_meta'].append({
                    'comp': comp.value,
                    'win_rate': recent_performance
                })

        return trends


class MetaAnalysisDataProcessor:
    """Processes raw match data for meta analysis model."""

    def __init__(self):
        self.unit_to_id = {}  # Will be populated from match data
        self.trait_to_id = {}
        self.item_to_id = {}

    def process_matches_for_meta_analysis(self, matches: List[Dict]) -> Dict[str, torch.Tensor]:
        """Convert raw match data to model input format."""

        # Extract sequences of compositions from matches
        board_sequences = []
        trait_sequences = []
        item_sequences = []
        comp_type_sequences = []

        for match in matches:
            # Process each participant's final board state
            for participant in match.get('info', {}).get('participants', []):
                board_state = self._extract_board_state(participant)
                trait_vector = self._extract_trait_vector(participant)
                item_vector = self._extract_item_vector(participant)
                comp_type = self._infer_comp_type(participant)

                board_sequences.append(board_state)
                trait_sequences.append(trait_vector)
                item_sequences.append(item_vector)
                comp_type_sequences.append(comp_type)

        # Convert to tensors
        return {
            'board_states': torch.tensor(board_sequences, dtype=torch.long),
            'trait_vectors': torch.tensor(trait_sequences, dtype=torch.float),
            'item_vectors': torch.tensor(item_sequences, dtype=torch.float),
            'comp_types': torch.tensor(comp_type_sequences, dtype=torch.long)
        }

    def _extract_board_state(self, participant: Dict) -> np.ndarray:
        """Extract board state as unit positions and tiers."""
        board = np.zeros((28, 3), dtype=int)  # position, unit_id, tier

        units = participant.get('units', [])
        for i, unit in enumerate(units[:28]):  # Max 28 positions
            unit_id = self._get_unit_id(unit.get('character_id', ''))
            tier = unit.get('tier', 1)
            board[i] = [i, unit_id, tier]

        return board

    def _extract_trait_vector(self, participant: Dict) -> np.ndarray:
        """Extract trait activation levels."""
        trait_vector = np.zeros(25)  # Set 15 has ~25 traits

        traits = participant.get('traits', [])
        for trait in traits:
            trait_id = self._get_trait_id(trait.get('name', ''))
            if trait_id < 25:
                trait_vector[trait_id] = trait.get('tier_current', 0)

        return trait_vector

    def _extract_item_vector(self, participant: Dict) -> np.ndarray:
        """Extract item usage patterns."""
        item_vector = np.zeros(40)  # Approximate completed items

        units = participant.get('units', [])
        for unit in units:
            items = unit.get('itemNames', [])
            for item in items:
                item_id = self._get_item_id(item)
                if item_id < 40:
                    item_vector[item_id] += 1

        return item_vector

    def _infer_comp_type(self, participant: Dict) -> int:
        """Infer composition type from board state and traits."""
        traits = participant.get('traits', [])
        level = participant.get('level', 1)

        # Simple heuristics for comp classification
        active_traits = [t for t in traits if t.get('tier_current', 0) > 0]

        if level >= 8 and len(active_traits) <= 3:
            return CompType.FAST_8.value if hasattr(CompType.FAST_8, 'value') else 1
        elif level <= 6 and any(t.get('tier_current', 0) >= 3 for t in active_traits):
            return CompType.REROLL.value if hasattr(CompType.REROLL, 'value') else 0
        else:
            return CompType.FLEX.value if hasattr(CompType.FLEX, 'value') else 4

    def _get_unit_id(self, unit_name: str) -> int:
        """Get or create unit ID mapping."""
        if unit_name not in self.unit_to_id:
            self.unit_to_id[unit_name] = len(self.unit_to_id)
        return self.unit_to_id[unit_name]

    def _get_trait_id(self, trait_name: str) -> int:
        """Get or create trait ID mapping."""
        if trait_name not in self.trait_to_id:
            self.trait_to_id[trait_name] = len(self.trait_to_id)
        return self.trait_to_id[trait_name]

    def _get_item_id(self, item_name: str) -> int:
        """Get or create item ID mapping."""
        if item_name not in self.item_to_id:
            self.item_to_id[item_name] = len(self.item_to_id)
        return self.item_to_id[item_name]


if __name__ == "__main__":
    # Test the model architecture
    model = TFTMetaAnalysisModel()

    # Create dummy data
    batch_size, seq_len = 2, 10
    dummy_input = {
        'board_states': torch.randint(0, 60, (batch_size, seq_len, 28, 3)),
        'trait_vectors': torch.randn(batch_size, seq_len, 25),
        'item_vectors': torch.randn(batch_size, seq_len, 40),
        'comp_types': torch.randint(0, len(CompType), (batch_size, seq_len))
    }

    # Forward pass
    predictions = model(dummy_input)

    print("Meta Analysis Model Output Shapes:")
    for key, value in predictions.items():
        print(f"  {key}: {value.shape}")

    # Generate tier list
    tier_list = model.get_meta_tier_list(predictions)
    print(f"\nGenerated Tier List: {tier_list}")