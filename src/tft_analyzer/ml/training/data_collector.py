"""
Training data collection pipeline for TFT ML model.

This module handles collection and preparation of TFT match data for model training,
including feature extraction from game states and outcome labeling.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel, field_validator

try:
    from ..data.schemas import TFTGameState, TFTModelPredictions
    from ...data.riot_api import RiotTFTAPI
    from config.settings import Settings
except ImportError:
    from src.tft_analyzer.ml.data.schemas import TFTGameState, TFTModelPredictions
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from config.settings import Settings


class TrainingDataPoint(BaseModel):
    """Single training data point with features and labels."""

    # Game identification
    match_id: str
    puuid: str
    game_datetime: datetime
    patch: str

    # Input features (game state)
    features: Dict

    # Output labels (what we want to predict)
    placement: int  # 1-8 final placement
    actions_taken: List[str]  # Actions taken this round
    comp_type: str  # Fast 8, reroll, etc.
    items_built: List[str]  # Items crafted
    level_up_round: Optional[int]  # When leveled up
    risk_level: float  # 0-1 risk assessment

    # Context for learning
    round_number: int
    stage: int
    player_level: int
    gold: int
    health: int

    @field_validator('round_number', 'stage', 'player_level', 'gold', 'health', 'placement', mode='before')
    @classmethod
    def convert_float_to_int(cls, v):
        """Convert float values to integers (common in Riot API responses)."""
        if isinstance(v, float):
            return int(round(v))
        return v

    @field_validator('level_up_round', mode='before')
    @classmethod
    def convert_optional_float_to_int(cls, v):
        """Convert optional float values to integers."""
        if v is None:
            return v
        if isinstance(v, float):
            return int(round(v))
        return v


class TFTTrainingDataCollector:
    """Collects and processes TFT match data for ML model training."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.riot_client = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=True)
        self.logger = logging.getLogger(__name__)

        # Training data storage
        self.data_dir = Path("data/training")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    async def collect_training_data(
        self,
        num_matches: int = 100,
        min_rank: str = "MASTER",
        days_back: int = 7
    ) -> List[TrainingDataPoint]:
        """
        Collect training data from high-rank matches.

        Args:
            num_matches: Target number of matches to collect
            min_rank: Minimum rank tier (CHALLENGER, GRANDMASTER, MASTER)
            days_back: How many days back to look for matches

        Returns:
            List of training data points
        """
        self.logger.info(f"Starting training data collection: {num_matches} matches")

        # Get high-tier players
        players = await self._get_training_players(min_rank)
        self.logger.info(f"Found {len(players)} players for training data")

        # Collect matches from these players
        training_data = []
        matches_collected = 0

        for player in players:
            if matches_collected >= num_matches:
                break

            try:
                player_matches = await self._collect_player_training_data(
                    player["puuid"],
                    days_back
                )
                training_data.extend(player_matches)
                matches_collected += len(player_matches)

                player_name = player.get('summonerName', player.get('puuid', 'Unknown')[:8] + '...')
                self.logger.info(
                    f"Collected {len(player_matches)} matches from {player_name} "
                    f"({matches_collected}/{num_matches})"
                )

                # Rate limiting
                await asyncio.sleep(1)

            except Exception as e:
                self.logger.error(f"Error collecting data for player {player['puuid']}: {e}")
                continue

        self.logger.info(f"Training data collection complete: {len(training_data)} data points")
        return training_data

    async def _get_training_players(self, min_rank: str) -> List[Dict]:
        """Get high-tier players for training data collection."""
        players = []

        try:
            if min_rank in ["CHALLENGER", "GRANDMASTER", "MASTER"]:
                challenger_players = await self.riot_client.get_challenger_players()
                players.extend(challenger_players[:20])  # Top 20 challenger

            if min_rank in ["GRANDMASTER", "MASTER"]:
                gm_players = await self.riot_client.get_grandmaster_players()
                players.extend(gm_players[:30])  # Top 30 GM

            if min_rank == "MASTER":
                master_players = await self.riot_client.get_master_players()
                players.extend(master_players[:50])  # Top 50 master

        except Exception as e:
            self.logger.error(f"Error fetching players: {e}")

        return players

    async def _collect_player_training_data(
        self,
        puuid: str,
        days_back: int
    ) -> List[TrainingDataPoint]:
        """Collect training data from a single player's matches."""
        training_data = []

        try:
            # Get match history
            match_ids = await self.riot_client.get_match_history(puuid, count=20)

            for match_id in match_ids[:10]:  # Limit to 10 matches per player
                try:
                    match_data = await self.riot_client.get_match_details(match_id)

                    # Filter for Set 15 and recent matches
                    if not self._is_valid_training_match(match_data, days_back):
                        continue

                    # Extract training data points from this match
                    match_training_data = self._extract_training_data_from_match(
                        match_data, puuid
                    )
                    training_data.extend(match_training_data)

                    await asyncio.sleep(0.5)  # Rate limiting

                except Exception as e:
                    self.logger.error(f"Error processing match {match_id}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error getting match history for {puuid}: {e}")

        return training_data

    def _is_valid_training_match(self, match_data: Dict, days_back: int) -> bool:
        """Check if match is suitable for training data."""
        try:
            # Check if Set 15
            if match_data.get("info", {}).get("tft_set_number") != 15:
                return False

            # Check if recent enough
            game_creation = match_data.get("info", {}).get("game_creation", 0)
            if game_creation:
                game_date = datetime.fromtimestamp(game_creation / 1000)
                cutoff_date = datetime.now() - timedelta(days=days_back)
                if game_date < cutoff_date:
                    return False

            # Check if ranked
            queue_id = match_data.get("info", {}).get("queue_id")
            if queue_id != 1100:  # TFT Ranked queue
                return False

            return True

        except Exception:
            return False

    def _extract_training_data_from_match(
        self,
        match_data: Dict,
        target_puuid: str
    ) -> List[TrainingDataPoint]:
        """Extract training data points from a single match."""
        training_data = []

        try:
            participants = match_data.get("info", {}).get("participants", [])
            target_participant = None

            # Find target player
            for participant in participants:
                if participant.get("puuid") == target_puuid:
                    target_participant = participant
                    break

            if not target_participant:
                return training_data

            # Extract key information
            placement = target_participant.get("placement", 8)
            traits = target_participant.get("traits", [])
            units = target_participant.get("units", [])

            # Create training data point
            training_point = TrainingDataPoint(
                match_id=match_data.get("metadata", {}).get("match_id", ""),
                puuid=target_puuid,
                game_datetime=datetime.fromtimestamp(
                    match_data.get("info", {}).get("game_creation", 0) / 1000
                ),
                patch=match_data.get("info", {}).get("game_version", "15.3"),
                features=self._extract_features(target_participant, participants),
                placement=placement,
                actions_taken=self._extract_actions(target_participant),
                comp_type=self._classify_comp_type(traits, units),
                items_built=self._extract_items(units),
                level_up_round=self._extract_level_timing(target_participant),
                risk_level=self._calculate_risk_level(placement, target_participant),
                round_number=match_data.get("info", {}).get("game_length", 0),
                stage=self._calculate_stage(match_data.get("info", {}).get("game_length", 0)),
                player_level=target_participant.get("level", 1),
                gold=target_participant.get("gold_left", 0),
                health=100 - target_participant.get("players_eliminated", 0)  # Convert eliminated count to health
            )

            training_data.append(training_point)

        except Exception as e:
            self.logger.error(f"Error extracting training data: {e}")

        return training_data

    def _extract_features(self, participant: Dict, all_participants: List[Dict]) -> Dict:
        """Extract feature vector from game state."""
        features = {
            # Player state
            "level": participant.get("level", 1),
            "gold": participant.get("gold_left", 0),
            "health": 100 - participant.get("players_eliminated", 0),

            # Board state
            "units_count": len(participant.get("units", [])),
            "trait_count": len([t for t in participant.get("traits", []) if t.get("tier_current", 0) > 0]),

            # Relative position
            "current_placement": self._estimate_current_placement(participant, all_participants),
        }

        # Add trait features
        traits = participant.get("traits", [])
        for trait in traits:
            trait_name = trait.get("name", "")
            trait_tier = trait.get("tier_current", 0)
            if trait_tier > 0:
                features[f"trait_{trait_name}"] = trait_tier

        return features

    def _extract_actions(self, participant: Dict) -> List[str]:
        """Extract actions taken by player."""
        actions = []

        # Simplified action extraction
        level = participant.get("level", 1)
        if level >= 8:
            actions.append("level_8_plus")

        units = participant.get("units", [])
        three_star_units = [u for u in units if u.get("tier", 1) == 3]
        if three_star_units:
            actions.append("three_star_unit")

        return actions

    def _classify_comp_type(self, traits: List[Dict], units: List[Dict]) -> str:
        """Classify the composition type based on multiple factors."""
        if not units:
            return "unknown"

        # Get unit costs and tiers
        unit_costs = [u.get("rarity", 1) for u in units]
        unit_tiers = [u.get("tier", 1) for u in units]

        # Count units by cost
        cost_counts = {}
        for cost in unit_costs:
            cost_counts[cost] = cost_counts.get(cost, 0) + 1

        # Count 3-star units
        three_star_count = sum(1 for tier in unit_tiers if tier == 3)

        # Count high-cost units (4+ cost)
        high_cost_count = sum(1 for cost in unit_costs if cost >= 4)

        # Classification logic
        if three_star_count >= 2:
            return "reroll"
        elif three_star_count >= 1 and cost_counts.get(1, 0) >= 3:
            return "reroll"
        elif high_cost_count >= 3:
            return "fast_8"
        elif cost_counts.get(5, 0) >= 2:
            return "fast_9"
        elif high_cost_count >= 1 and cost_counts.get(2, 0) + cost_counts.get(3, 0) >= 4:
            return "midrange"
        elif cost_counts.get(1, 0) + cost_counts.get(2, 0) >= 5:
            return "econ_reroll"
        else:
            return "flex"

    def _extract_items(self, units: List[Dict]) -> List[str]:
        """Extract items built."""
        items = []
        for unit in units:
            unit_items = unit.get("items", [])
            items.extend([str(item) for item in unit_items])
        return items

    def _extract_level_timing(self, participant: Dict) -> Optional[int]:
        """Extract when player leveled up (simplified)."""
        return participant.get("level", 1)  # Placeholder

    def _calculate_risk_level(self, placement: int, participant: Dict) -> float:
        """Calculate risk level based on outcome."""
        # Higher risk for worse placement
        return (8 - placement) / 7.0

    def _calculate_stage(self, game_length: int) -> int:
        """Calculate game stage from length."""
        # Simplified stage calculation
        return min(7, max(1, game_length // 300))

    def _estimate_current_placement(self, participant: Dict, all_participants: List[Dict]) -> int:
        """Estimate current placement during game."""
        # Simplified estimation based on health
        health = 100 - participant.get("players_eliminated", 0)
        healths = [100 - p.get("players_eliminated", 0) for p in all_participants]
        healths.sort(reverse=True)

        try:
            return healths.index(health) + 1
        except ValueError:
            return 4  # Default middle placement

    def save_training_data(self, training_data: List[TrainingDataPoint], filename: str):
        """Save training data to disk."""
        filepath = self.data_dir / f"{filename}.json"

        data_dicts = [point.dict() for point in training_data]

        with open(filepath, 'w') as f:
            json.dump(data_dicts, f, indent=2, default=str)

        self.logger.info(f"Saved {len(training_data)} training data points to {filepath}")

    def load_training_data(self, filename: str) -> List[TrainingDataPoint]:
        """Load training data from disk."""
        filepath = self.data_dir / f"{filename}.json"

        if not filepath.exists():
            return []

        with open(filepath, 'r') as f:
            data_dicts = json.load(f)

        training_data = []
        for data_dict in data_dicts:
            try:
                # Convert datetime strings back to datetime objects
                if isinstance(data_dict.get("game_datetime"), str):
                    data_dict["game_datetime"] = datetime.fromisoformat(
                        data_dict["game_datetime"].replace("Z", "+00:00")
                    )

                training_data.append(TrainingDataPoint(**data_dict))
            except Exception as e:
                self.logger.error(f"Error loading training data point: {e}")
                continue

        self.logger.info(f"Loaded {len(training_data)} training data points from {filepath}")
        return training_data


async def main():
    """Test data collection."""
    settings = Settings()
    collector = TFTTrainingDataCollector(settings)

    # Collect small sample for testing
    training_data = await collector.collect_training_data(num_matches=5)

    print(f"Collected {len(training_data)} training data points")
    for i, point in enumerate(training_data[:3]):
        print(f"Point {i}: Match {point.match_id}, Placement {point.placement}")

    # Save data
    collector.save_training_data(training_data, "sample_training_data")


if __name__ == "__main__":
    asyncio.run(main())