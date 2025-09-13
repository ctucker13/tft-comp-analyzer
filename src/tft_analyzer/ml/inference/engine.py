"""
TFT ML Inference Engine
Handles model loading, prediction, and recommendation generation
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
import asyncio

from ..models.strategy_model import TFTStrategyModel, TFTSequenceModel, TFTModelEnsemble
from ..data.schemas import (
    TFTGameState, TFTModelPredictions, ScenarioSimulation,
    TFTRecommendationEngine, ActionType, CompType, RiskLevel
)


class TFTInferenceEngine:
    """
    Main inference engine for TFT strategy predictions
    """

    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        use_ensemble: bool = False
    ):
        self.device = torch.device(device)
        self.model = None
        self.feature_scaler = None
        self.use_ensemble = use_ensemble

        # Load model and preprocessors
        self._load_model(model_path)

        # Prediction caching for performance
        self._prediction_cache = {}
        self._cache_size_limit = 1000

    def _load_model(self, model_path: str) -> None:
        """Load trained model and preprocessors"""
        try:
            model_dir = Path(model_path)

            # Load model architecture config
            with open(model_dir / "config.json", "r") as f:
                config = json.load(f)

            # Initialize model
            if config["model_type"] == "strategy":
                self.model = TFTStrategyModel(
                    input_dim=config["input_dim"],
                    hidden_dim=config.get("hidden_dim", 256),
                    dropout=config.get("dropout", 0.3),
                    use_attention=config.get("use_attention", True)
                )
            elif config["model_type"] == "sequence":
                self.model = TFTSequenceModel(
                    input_dim=config["input_dim"],
                    d_model=config.get("d_model", 256),
                    nhead=config.get("nhead", 8),
                    num_layers=config.get("num_layers", 6)
                )

            # Load model weights
            state_dict = torch.load(model_dir / "model.pt", map_location=self.device)
            self.model.load_state_dict(state_dict)
            self.model.to(self.device)
            self.model.eval()

            # Load feature scaler if available
            scaler_path = model_dir / "scaler.json"
            if scaler_path.exists():
                with open(scaler_path, "r") as f:
                    scaler_data = json.load(f)
                    self.feature_scaler = scaler_data

            print(f"✅ Model loaded successfully from {model_path}")

        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise

    async def predict_strategy(self, game_state: TFTGameState) -> TFTModelPredictions:
        """
        Generate strategic predictions for a given game state

        Args:
            game_state: Current TFT game state

        Returns:
            Comprehensive predictions and recommendations
        """
        # Check cache first
        cache_key = self._get_cache_key(game_state)
        if cache_key in self._prediction_cache:
            return self._prediction_cache[cache_key]

        # Extract features
        features = self._extract_features(game_state)

        # Run inference
        with torch.no_grad():
            predictions = self.model(features)

        # Convert to structured predictions
        structured_predictions = self._process_predictions(predictions, game_state)

        # Cache result
        self._cache_prediction(cache_key, structured_predictions)

        return structured_predictions

    def _extract_features(self, game_state: TFTGameState) -> torch.Tensor:
        """Extract and normalize features from game state"""
        # Get base feature vector
        features = game_state.to_feature_vector()

        # Apply scaling if available
        if self.feature_scaler:
            features = self._apply_scaling(features)

        # Convert to tensor
        features_tensor = torch.tensor(features, dtype=torch.float32, device=self.device)

        # Add batch dimension
        return features_tensor.unsqueeze(0)

    def _apply_scaling(self, features: np.ndarray) -> np.ndarray:
        """Apply feature scaling using stored scaler parameters"""
        if self.feature_scaler and "mean" in self.feature_scaler:
            mean = np.array(self.feature_scaler["mean"])
            std = np.array(self.feature_scaler["std"])
            return (features - mean) / (std + 1e-8)
        return features

    def _process_predictions(
        self,
        raw_predictions: Dict[str, torch.Tensor],
        game_state: TFTGameState
    ) -> TFTModelPredictions:
        """Convert raw model outputs to structured predictions"""

        # Get action prediction
        action_probs = raw_predictions["action_probs"].cpu().numpy()[0]
        action_idx = np.argmax(action_probs)
        action_types = list(ActionType)
        recommended_action = action_types[action_idx]
        action_confidence = float(action_probs[action_idx])

        # Get composition prediction
        comp_probs = raw_predictions["comp_probs"].cpu().numpy()[0]
        comp_idx = np.argmax(comp_probs)
        comp_types = list(CompType)
        comp_type = comp_types[comp_idx]

        # Get risk assessment
        risk_probs = raw_predictions["risk_probs"].cpu().numpy()[0]
        risk_idx = np.argmax(risk_probs)
        risk_levels = list(RiskLevel)
        risk_level = risk_levels[risk_idx]

        # Extract regression outputs
        should_level_prob = float(raw_predictions["should_level_prob"].cpu().item())
        should_roll_prob = float(raw_predictions["should_roll_prob"].cpu().item())
        pivot_urgency = float(raw_predictions["pivot_urgency"].cpu().item())
        gold_target = int(raw_predictions["gold_target"].cpu().item())
        leveling_priority = float(raw_predictions["leveling_priority"].cpu().item())

        # Generate alternative actions
        alternative_actions = self._get_alternative_actions(action_probs, action_types)

        # Identify key factors
        key_factors = self._identify_key_factors(game_state, raw_predictions)

        return TFTModelPredictions(
            recommended_action=recommended_action,
            confidence=action_confidence,
            comp_type=comp_type,
            risk_level=risk_level,
            should_level_probability=should_level_prob,
            should_roll_probability=should_roll_prob,
            pivot_urgency=pivot_urgency,
            target_gold=gold_target,
            leveling_priority=leveling_priority,
            alternative_actions=alternative_actions,
            key_factors=key_factors
        )

    def _get_alternative_actions(
        self,
        action_probs: np.ndarray,
        action_types: List[ActionType]
    ) -> List[Dict[str, any]]:
        """Get top alternative actions with probabilities"""
        alternatives = []

        # Get top 3 actions
        top_indices = np.argsort(action_probs)[-3:][::-1]

        for idx in top_indices[1:]:  # Skip the top prediction
            alternatives.append({
                "action": action_types[idx].value,
                "probability": float(action_probs[idx]),
                "confidence": float(action_probs[idx])
            })

        return alternatives

    def _identify_key_factors(
        self,
        game_state: TFTGameState,
        predictions: Dict[str, torch.Tensor]
    ) -> List[str]:
        """Identify key factors influencing the prediction"""
        factors = []

        # Analyze game state for key factors
        if game_state.health <= 30:
            factors.append("Low health - need to stabilize")

        if game_state.gold >= 30:
            factors.append("High gold - consider rolling or leveling")

        if game_state.round >= 15 and game_state.level < 7:
            factors.append("Mid-game level timing critical")

        if game_state.win_streak >= 3:
            factors.append("Win streak - can afford to be greedy")

        if game_state.loss_streak >= 3:
            factors.append("Loss streak - need immediate power")

        # Add model-specific factors if available
        if hasattr(self.model, 'get_feature_importance'):
            # This would require additional implementation
            pass

        return factors[:5]  # Return top 5 factors

    async def simulate_scenarios(
        self,
        game_state: TFTGameState,
        actions: List[ActionType] = None
    ) -> List[ScenarioSimulation]:
        """
        Simulate different strategic scenarios

        Args:
            game_state: Current game state
            actions: Actions to simulate (default: all major actions)

        Returns:
            List of scenario simulations with expected outcomes
        """
        if actions is None:
            actions = [ActionType.LEVEL, ActionType.ROLL, ActionType.HOLD]

        scenarios = []

        for action in actions:
            scenario = await self._simulate_action_scenario(game_state, action)
            scenarios.append(scenario)

        # Sort by expected value
        scenarios.sort(key=lambda x: x.win_probability, reverse=True)

        return scenarios

    async def _simulate_action_scenario(
        self,
        game_state: TFTGameState,
        action: ActionType
    ) -> ScenarioSimulation:
        """Simulate a specific action scenario"""

        # Create modified game state based on action
        future_state = self._apply_action_to_state(game_state, action)

        # Get predictions for future state
        future_predictions = await self.predict_strategy(future_state)

        # Estimate outcomes
        expected_placement = self._estimate_placement(future_state, future_predictions)
        win_probability = max(0.0, (9 - expected_placement) / 8.0)  # Convert placement to win prob
        risk_score = self._calculate_risk_score(future_state, action)

        return ScenarioSimulation(
            strategy=action,
            expected_placement=expected_placement,
            win_probability=win_probability,
            risk_score=risk_score,
            health_projection=future_state.health,
            gold_projection=future_state.gold,
            board_strength_projection=self._estimate_board_strength(future_state),
            placement_confidence_interval=(expected_placement - 1.0, expected_placement + 1.0)
        )

    def _apply_action_to_state(self, game_state: TFTGameState, action: ActionType) -> TFTGameState:
        """Apply an action to create a future game state"""
        # Create a copy of the game state
        future_state = game_state.copy(deep=True)

        if action == ActionType.LEVEL:
            if future_state.gold >= self._level_cost(future_state.level):
                future_state.gold -= self._level_cost(future_state.level)
                future_state.level += 1
                future_state.experience = 0

        elif action == ActionType.ROLL:
            rolls = min(future_state.gold // 2, 10)  # Max 10 rolls
            future_state.gold -= rolls * 2
            # Would simulate shop rolls and potential upgrades

        elif action == ActionType.HOLD:
            # Holding doesn't change the state immediately
            pass

        return future_state

    def _level_cost(self, current_level: int) -> int:
        """Get cost to level up from current level"""
        level_costs = {1: 2, 2: 2, 3: 6, 4: 10, 5: 20, 6: 36, 7: 56, 8: 80}
        return level_costs.get(current_level, 100)

    def _estimate_placement(self, game_state: TFTGameState, predictions: TFTModelPredictions) -> float:
        """Estimate expected placement based on game state and predictions"""
        # Simple heuristic - would be replaced with more sophisticated model
        base_placement = 4.5

        # Adjust based on health
        if game_state.health > 60:
            base_placement -= 1.0
        elif game_state.health < 30:
            base_placement += 1.5

        # Adjust based on board strength
        board_strength = len(game_state.board) * game_state.level * 0.1
        base_placement -= (board_strength - 1.0)

        return max(1.0, min(8.0, base_placement))

    def _calculate_risk_score(self, game_state: TFTGameState, action: ActionType) -> float:
        """Calculate risk score for an action"""
        risk = 0.5  # Base risk

        if action == ActionType.LEVEL and game_state.gold < 20:
            risk += 0.3  # Risky to level with low gold

        if action == ActionType.ROLL and game_state.health > 60:
            risk += 0.2  # Risky to roll when healthy

        if game_state.health < 20:
            risk += 0.4  # Any action is risky with low health

        return max(0.0, min(1.0, risk))

    def _estimate_board_strength(self, game_state: TFTGameState) -> float:
        """Estimate board strength score"""
        if not game_state.board:
            return 0.0

        total_strength = 0.0
        for champion in game_state.board:
            strength = champion.cost * champion.tier * (1 + len(champion.items) * 0.2)
            total_strength += strength

        return total_strength / len(game_state.board)

    def _get_cache_key(self, game_state: TFTGameState) -> str:
        """Generate cache key for game state"""
        # Use a hash of key game state features
        key_features = (
            game_state.round,
            game_state.level,
            game_state.gold,
            game_state.health,
            len(game_state.board)
        )
        return str(hash(key_features))

    def _cache_prediction(self, key: str, prediction: TFTModelPredictions) -> None:
        """Cache prediction with size limit"""
        if len(self._prediction_cache) >= self._cache_size_limit:
            # Remove oldest entries
            oldest_key = next(iter(self._prediction_cache))
            del self._prediction_cache[oldest_key]

        self._prediction_cache[key] = prediction


class TFTRecommendationGenerator:
    """
    Generates comprehensive recommendations combining ML predictions with strategic reasoning
    """

    def __init__(self, inference_engine: TFTInferenceEngine):
        self.inference_engine = inference_engine

    async def generate_recommendations(
        self,
        game_state: TFTGameState,
        user_context: Optional[Dict] = None
    ) -> TFTRecommendationEngine:
        """
        Generate comprehensive recommendations

        Args:
            game_state: Current game state
            user_context: Additional user preferences/context

        Returns:
            Complete recommendation package
        """
        # Get ML predictions
        ml_predictions = await self.inference_engine.predict_strategy(game_state)

        # Simulate scenarios
        scenarios = await self.inference_engine.simulate_scenarios(game_state)

        # Generate detailed plan
        detailed_plan = self._create_detailed_plan(game_state, ml_predictions, scenarios)

        # Generate explanation
        explanation = self._generate_explanation(game_state, ml_predictions, scenarios)

        # Get key insights
        key_insights = self._extract_key_insights(game_state, ml_predictions, scenarios)

        return TFTRecommendationEngine(
            ml_predictions=ml_predictions,
            scenarios=scenarios,
            primary_recommendation=ml_predictions.recommended_action.value,
            detailed_plan=detailed_plan,
            overall_risk=ml_predictions.risk_level,
            contingency_plans=self._generate_contingency_plans(scenarios),
            explanation=explanation,
            key_insights=key_insights
        )

    def _create_detailed_plan(
        self,
        game_state: TFTGameState,
        predictions: TFTModelPredictions,
        scenarios: List[ScenarioSimulation]
    ) -> Dict[str, str]:
        """Create detailed round-by-round plan"""
        plan = {}

        current_round = game_state.round
        plan[str(current_round)] = predictions.recommended_action.value

        # Project next few rounds based on scenarios
        for i in range(1, 4):
            future_round = current_round + i
            if scenarios:
                best_scenario = scenarios[0]
                plan[str(future_round)] = f"Continue {best_scenario.strategy.value} strategy"

        return plan

    def _generate_explanation(
        self,
        game_state: TFTGameState,
        predictions: TFTModelPredictions,
        scenarios: List[ScenarioSimulation]
    ) -> str:
        """Generate human-readable explanation"""
        explanation_parts = [
            f"**Round {game_state.round} Recommendation: {predictions.recommended_action.value.title()}**",
            f"Confidence: {predictions.confidence:.1%}",
            "",
            f"**Strategic Context:**",
            f"- Health: {game_state.health}/100 ({'Critical' if game_state.health <= 20 else 'Stable' if game_state.health >= 50 else 'At Risk'})",
            f"- Economy: {game_state.gold} gold ({'Strong' if game_state.gold >= 30 else 'Weak' if game_state.gold <= 10 else 'Moderate'})",
            f"- Board: Level {game_state.level} with {len(game_state.board)} units",
            "",
            f"**Key Factors:**"
        ]

        for factor in predictions.key_factors:
            explanation_parts.append(f"- {factor}")

        if scenarios:
            explanation_parts.extend([
                "",
                f"**Alternative Strategies:**"
            ])
            for scenario in scenarios[1:3]:  # Show top 2 alternatives
                explanation_parts.append(
                    f"- {scenario.strategy.value.title()}: {scenario.win_probability:.1%} win rate"
                )

        return "\n".join(explanation_parts)

    def _extract_key_insights(
        self,
        game_state: TFTGameState,
        predictions: TFTModelPredictions,
        scenarios: List[ScenarioSimulation]
    ) -> List[str]:
        """Extract key strategic insights"""
        insights = []

        # Economic insights
        if predictions.target_gold > game_state.gold:
            insights.append(f"Target {predictions.target_gold} gold before next major decision")

        # Leveling insights
        if predictions.leveling_priority > 0.7:
            insights.append("Prioritize leveling for board strength")

        # Pivot insights
        if predictions.pivot_urgency > 0.6:
            insights.append(f"Consider pivoting to {predictions.comp_type.value}")

        # Risk insights
        if predictions.risk_level == RiskLevel.HIGH_RISK:
            insights.append("High-risk situation requires aggressive plays")

        return insights

    def _generate_contingency_plans(self, scenarios: List[ScenarioSimulation]) -> List[str]:
        """Generate backup plans based on scenarios"""
        plans = []

        if len(scenarios) >= 2:
            best = scenarios[0]
            backup = scenarios[1]

            plans.append(
                f"If {best.strategy.value} doesn't work, pivot to {backup.strategy.value}"
            )

        plans.append("If health drops below 20, prioritize immediate board strength")
        plans.append("If gold exceeds 50, consider aggressive leveling")

        return plans