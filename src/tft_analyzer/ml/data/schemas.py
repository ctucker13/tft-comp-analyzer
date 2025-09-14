"""
TFT ML Data Schemas
Defines the data structures for ML training and inference
"""

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum
import numpy as np
from datetime import datetime


class GamePhase(str, Enum):
    EARLY = "early"  # Rounds 1-3-1
    MID = "mid"      # Rounds 3-2 to 5-1
    LATE = "late"    # Rounds 5-2+


class CompType(str, Enum):
    REROLL = "reroll"
    FAST_8 = "fast_8"
    SLOW_ROLL = "slow_roll"
    VERTICAL = "vertical"
    FLEX = "flex"
    HYPER_ROLL = "hyper_roll"


class ActionType(str, Enum):
    LEVEL = "level"
    ROLL = "roll"
    HOLD = "hold"
    PIVOT = "pivot"
    ALL_IN = "all_in"


class RiskLevel(str, Enum):
    SAFE = "safe"
    MEDIUM = "medium"
    HIGH_RISK = "high_risk"


class Position(BaseModel):
    x: int = Field(..., ge=0, le=6)  # 0-6 for 7 columns
    y: int = Field(..., ge=0, le=3)  # 0-3 for 4 rows


class ChampionState(BaseModel):
    character_id: str
    tier: int  # Star level (1, 2, 3)
    position: Position
    items: List[str] = []
    cost: int

    def to_feature_vector(self) -> List[float]:
        """Convert champion state to feature vector for ML"""
        return [
            self.cost,
            self.tier,
            self.position.x,
            self.position.y,
            len(self.items),
            # Add one-hot encoding for champion type in actual implementation
        ]


class TraitState(BaseModel):
    trait_name: str
    count: int
    active_tier: int  # 0 if not active, 1-4 for bronze/silver/gold/prismatic


class TFTGameState(BaseModel):
    """Complete game state at a specific point in time"""

    # Game Context
    match_id: str
    puuid: str
    round: int
    timestamp: datetime

    # Player State
    level: int
    experience: int  # XP towards next level
    gold: int
    health: int

    # Streak Information
    win_streak: int = 0
    loss_streak: int = 0

    # Board State
    board: List[ChampionState] = []
    bench: List[str] = []  # Champion IDs on bench
    traits: List[TraitState] = []

    # Shop State
    shop: List[str] = []  # Champion IDs in shop
    shop_locked: bool = False

    # Items
    item_components: List[str] = []
    completed_items: List[str] = []  # Items not on champions

    # Strategic Context
    lobby_strength: Optional[float] = None  # Relative power rating
    contested_units: Dict[str, int] = {}  # Unit -> count in lobby
    power_snax_used: int = 0

    # Game Phase
    phase: GamePhase

    def to_feature_vector(self) -> np.ndarray:
        """Convert game state to feature vector for ML model"""
        features = []

        # Basic game state
        features.extend([
            self.round,
            self.level,
            self.experience,
            self.gold,
            self.health,
            self.win_streak,
            self.loss_streak,
        ])

        # Board features
        board_power = sum(c.cost * c.tier for c in self.board)
        features.append(board_power)
        features.append(len(self.board))
        features.append(len(self.bench))

        # Economic features
        features.append(self.gold / max(1, self.round))  # Gold efficiency
        features.append(len(self.item_components))

        # Strategic features
        features.append(self.lobby_strength or 0.5)
        features.append(sum(self.contested_units.values()))
        features.append(self.power_snax_used)

        # Phase encoding (one-hot)
        phase_encoding = [0, 0, 0]
        if self.phase == GamePhase.EARLY:
            phase_encoding[0] = 1
        elif self.phase == GamePhase.MID:
            phase_encoding[1] = 1
        else:
            phase_encoding[2] = 1
        features.extend(phase_encoding)

        # Trait synergies (simplified - would need expansion)
        active_traits = len([t for t in self.traits if t.active_tier > 0])
        features.append(active_traits)

        return np.array(features, dtype=np.float32)


class TFTGameTransition(BaseModel):
    """Represents a state transition during a game"""

    before_state: TFTGameState
    action_taken: ActionType
    after_state: TFTGameState

    # Outcomes
    round_placement: int  # 1-8 placement this round
    damage_dealt: int
    damage_taken: int

    # Context
    action_was_optimal: Optional[bool] = None  # For supervised learning


class TFTGameOutcome(BaseModel):
    """Final game outcome for a player"""

    match_id: str
    puuid: str
    final_placement: int
    total_damage_dealt: int
    total_rounds_survived: int

    # Strategic analysis
    comp_type: Optional[CompType] = None
    transition_points: List[int] = []  # Rounds where major transitions occurred
    key_decisions: List[TFTGameTransition] = []


class MLTrainingLabel(BaseModel):
    """Labels for ML model training"""

    # Primary predictions
    optimal_action: ActionType
    comp_recommendation: CompType
    risk_level: RiskLevel

    # Detailed predictions
    should_level: bool
    should_roll: bool
    pivot_urgency: float = Field(..., ge=0, le=1)  # 0 = no pivot needed, 1 = urgent pivot

    # Positional recommendations
    position_changes: List[Dict[str, Position]] = []  # champion_id -> new_position

    # Economic predictions
    gold_target: int  # Target gold for next decision point
    experience_priority: float = Field(..., ge=0, le=1)


class TFTTrainingExample(BaseModel):
    """Complete training example for ML model"""

    game_state: TFTGameState
    labels: MLTrainingLabel

    # Context for training
    expert_reasoning: Optional[str] = None  # Human expert explanation
    confidence: float = Field(1.0, ge=0, le=1)  # How confident we are in labels


class TFTModelPredictions(BaseModel):
    """Output from ML model inference"""

    # Primary recommendations
    recommended_action: ActionType
    confidence: float = Field(..., ge=0, le=1)

    # Detailed predictions
    comp_type: CompType
    risk_level: RiskLevel

    # Specific advice
    should_level_probability: float
    should_roll_probability: float
    pivot_urgency: float

    # Economic guidance
    target_gold: int
    leveling_priority: float

    # Alternative strategies
    alternative_actions: List[Dict[str, Union[str, float]]] = []

    # Explanatory features
    key_factors: List[str] = []  # Most important factors in decision
    reasoning: Optional[str] = None


class ScenarioSimulation(BaseModel):
    """Results from simulating different strategies"""

    strategy: ActionType
    expected_placement: float
    win_probability: float
    risk_score: float

    # Detailed outcomes
    health_projection: int
    gold_projection: int
    board_strength_projection: float

    # Confidence intervals
    placement_confidence_interval: tuple[float, float]


class TFTRecommendationEngine(BaseModel):
    """Complete recommendation output combining ML and reasoning"""

    ml_predictions: TFTModelPredictions
    scenarios: List[ScenarioSimulation]

    # Final recommendations
    primary_recommendation: str
    detailed_plan: Dict[str, str]  # Round -> recommended action

    # Risk assessment
    overall_risk: RiskLevel
    contingency_plans: List[str]

    # User-facing explanation
    explanation: str
    key_insights: List[str]