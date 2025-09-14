"""
Enhanced TFT Data Collector for ML Training
Collects detailed game state transitions and outcomes
"""

import asyncio
import json
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path

from .schemas import (
    TFTGameState, TFTGameTransition, TFTGameOutcome,
    ChampionState, TraitState, Position, GamePhase,
    ActionType, CompType
)
from ...data.riot_api import RiotTFTAPI
from ...utils.patch_detector import TFTPatchDetector


class TFTMLDataCollector:
    """Enhanced data collector for ML training data"""

    def __init__(self, riot_api: RiotTFTAPI, output_dir: str = "data/raw"):
        self.riot_api = riot_api
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Data quality filters
        self.min_game_length = 15  # Minimum rounds for valid game
        self.target_ranks = ["CHALLENGER", "GRANDMASTER", "MASTER"]

    async def collect_training_data(
        self,
        target_games: int = 1000,
        max_players: int = 100,
        days_back: int = 7
    ) -> Dict[str, int]:
        """
        Collect comprehensive training data

        Args:
            target_games: Number of complete games to collect
            max_players: Maximum players to analyze
            days_back: Days to look back for matches

        Returns:
            Dictionary with collection statistics
        """
        print(f"🎯 Starting ML data collection: {target_games} games from {max_players} players")

        stats = {
            "players_processed": 0,
            "games_collected": 0,
            "game_states_extracted": 0,
            "transitions_captured": 0,
            "failed_games": 0
        }

        # Get high-tier players
        players = await self._get_target_players(max_players)
        print(f"📊 Found {len(players)} high-tier players")

        games_collected = 0
        for i, player in enumerate(players):
            if games_collected >= target_games:
                break

            print(f"👤 Processing player {i+1}/{len(players)}: {player.get('summonerName', 'Unknown')}")

            try:
                player_games = await self._collect_player_games(
                    player["puuid"], days_back=days_back
                )

                for game_data in player_games:
                    if games_collected >= target_games:
                        break

                    game_outcome = await self._process_complete_game(game_data)
                    if game_outcome:
                        await self._save_game_data(game_outcome)
                        games_collected += 1
                        stats["games_collected"] = games_collected

                        if games_collected % 10 == 0:
                            print(f"✅ Collected {games_collected}/{target_games} games")

                stats["players_processed"] += 1

            except Exception as e:
                print(f"❌ Error processing player: {e}")
                continue

            # Rate limiting
            await asyncio.sleep(2)

        print(f"🎉 Data collection complete! Collected {games_collected} games")
        return stats

    async def _get_target_players(self, max_players: int) -> List[Dict]:
        """Get high-quality players for training data"""
        all_players = []

        # Get players from multiple tiers
        tiers = ["challenger", "grandmaster", "master"]
        for tier in tiers:
            try:
                if tier == "challenger":
                    players = await self.riot_api.get_challenger_players()
                elif tier == "grandmaster":
                    players = await self.riot_api.get_grandmaster_players()
                else:  # master
                    players = await self.riot_api.get_master_players()

                # Add tier information
                for player in players:
                    player["tier"] = tier.upper()

                all_players.extend(players)
                print(f"📈 Added {len(players)} {tier} players")

                await asyncio.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"⚠️ Failed to get {tier} players: {e}")

        # Sort by LP and take the best players
        all_players.sort(key=lambda x: x.get("leaguePoints", 0), reverse=True)
        return all_players[:max_players]

    async def _collect_player_games(self, puuid: str, days_back: int = 7) -> List[Dict]:
        """Collect detailed game data for a player"""
        # Get match history
        match_ids = await self.riot_api.get_match_history(puuid, count=20)

        games = []
        for match_id in match_ids[:10]:  # Limit for rate limiting
            try:
                match_details = await self.riot_api.get_match_details(match_id, debug=False)
                if match_details and self._is_valid_training_game(match_details):
                    games.append(match_details)

                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"⚠️ Failed to get match {match_id}: {e}")

        return games

    def _is_valid_training_game(self, match_data: Dict) -> bool:
        """Check if game is suitable for training data"""
        info = match_data.get("info", {})

        # Check Set 15
        if info.get("tft_set_number") != 15:
            return False

        # Check game length
        game_length = info.get("game_length", 0)
        if game_length < self.min_game_length * 60 * 1000:  # 15+ minutes
            return False

        # Check participant count
        participants = info.get("participants", [])
        if len(participants) != 8:
            return False

        return True

    async def _process_complete_game(self, match_data: Dict) -> Optional[TFTGameOutcome]:
        """Process a complete game and extract training data"""
        try:
            info = match_data.get("info", {})
            participants = info.get("participants", [])

            game_outcomes = []
            for participant in participants:
                outcome = await self._extract_game_outcome(participant, info)
                if outcome:
                    game_outcomes.append(outcome)

            # Save all outcomes for this match
            if game_outcomes:
                return {
                    "match_id": match_data["metadata"]["match_id"],
                    "game_datetime": info.get("game_datetime"),
                    "participants": game_outcomes,
                    "game_version": info.get("game_version"),
                    "set_number": info.get("tft_set_number")
                }

        except Exception as e:
            print(f"❌ Error processing game: {e}")

        return None

    async def _extract_game_outcome(self, participant: Dict, game_info: Dict) -> Optional[TFTGameOutcome]:
        """Extract outcome data from a participant"""
        try:
            # Basic outcome information
            outcome = TFTGameOutcome(
                match_id=game_info.get("match_id", ""),
                puuid=participant.get("puuid", ""),
                final_placement=participant.get("placement", 8),
                total_damage_dealt=participant.get("total_damage_to_players", 0),
                total_rounds_survived=len(participant.get("traits", []))  # Approximate
            )

            # Analyze composition type
            outcome.comp_type = self._classify_comp_type(participant)

            # Extract key decision points (would need timeline data)
            outcome.transition_points = self._identify_transition_points(participant)

            return outcome

        except Exception as e:
            print(f"⚠️ Error extracting outcome: {e}")
            return None

    def _classify_comp_type(self, participant: Dict) -> CompType:
        """Classify the composition type based on final board"""
        units = participant.get("units", [])
        traits = participant.get("traits", [])

        # Simple heuristics for comp classification
        total_cost = sum(unit.get("tier", 1) * self._get_champion_cost(unit.get("character_id", "")) for unit in units)
        three_star_count = sum(1 for unit in units if unit.get("tier", 1) == 3)
        max_cost_unit = max((self._get_champion_cost(unit.get("character_id", "")) for unit in units), default=1)

        if three_star_count >= 2 and max_cost_unit <= 3:
            return CompType.REROLL
        elif max_cost_unit >= 4 and total_cost > 30:
            return CompType.FAST_8
        elif len(traits) >= 3:
            return CompType.VERTICAL
        else:
            return CompType.FLEX

    def _get_champion_cost(self, character_id: str) -> int:
        """Get champion cost (simplified - would use actual data)"""
        # This would be replaced with actual champion cost data
        cost_mapping = {
            # This would be populated with actual Set 15 champion costs
            "TFT15_": 1,  # Default cost
        }

        # Simple heuristic based on character ID
        if "5cost" in character_id.lower():
            return 5
        elif "4cost" in character_id.lower():
            return 4
        elif "3cost" in character_id.lower():
            return 3
        elif "2cost" in character_id.lower():
            return 2
        else:
            return 1

    def _identify_transition_points(self, participant: Dict) -> List[int]:
        """Identify key transition rounds (placeholder)"""
        # This would require timeline data from the API
        # For now, return common transition points
        return [9, 15, 21]  # Typical level 5, 7, 8 transition points

    async def _save_game_data(self, game_data: Dict) -> None:
        """Save collected game data to file"""
        match_id = game_data["match_id"]
        timestamp = datetime.now().isoformat()

        filename = f"game_{match_id}_{timestamp.replace(':', '-')}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(game_data, f, indent=2, default=str)

    async def generate_training_examples(self, input_dir: str = "data/raw") -> int:
        """Convert raw game data into ML training examples"""
        print("🔄 Converting raw data to training examples...")

        input_path = Path(input_dir)
        output_path = Path("data/processed")
        output_path.mkdir(parents=True, exist_ok=True)

        game_files = list(input_path.glob("game_*.json"))
        training_examples = []

        for file_path in game_files:
            try:
                with open(file_path, 'r') as f:
                    game_data = json.load(f)

                examples = self._create_training_examples_from_game(game_data)
                training_examples.extend(examples)

            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

        # Save training examples
        output_file = output_path / f"training_examples_{datetime.now().isoformat().replace(':', '-')}.json"
        with open(output_file, 'w') as f:
            json.dump([ex.dict() for ex in training_examples], f, indent=2, default=str)

        print(f"✅ Generated {len(training_examples)} training examples")
        return len(training_examples)

    def _create_training_examples_from_game(self, game_data: Dict) -> List:
        """Create training examples from game data (placeholder)"""
        # This would implement the logic to create training examples
        # from the game state transitions and outcomes
        examples = []

        # For each participant, create examples at key decision points
        for participant in game_data.get("participants", []):
            # This would extract game states and create labels based on
            # the final outcome and strategic analysis
            pass

        return examples