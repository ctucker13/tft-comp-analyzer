"""Pydantic models for API requests and responses."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ChatRequest(BaseModel):
    """Chat message request model."""
    message: str = Field(..., description="User message", min_length=1, max_length=1000)
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    provider: str = Field("anthropic", description="LLM provider (anthropic/openai)")


class ChatResponse(BaseModel):
    """Chat message response model."""
    response: str = Field(..., description="AI response")
    conversation_id: str = Field(..., description="Conversation ID")
    intent: Optional[str] = Field(None, description="Detected intent")
    tool_used: Optional[str] = Field(None, description="Tool that was triggered")


class MLRecommendationRequest(BaseModel):
    """ML recommendation request model."""
    gold: int = Field(..., description="Current gold amount", ge=0, le=100)
    level: int = Field(..., description="Current level", ge=1, le=11)
    stage: int = Field(..., description="Current stage", ge=1, le=7)
    health: int = Field(100, description="Current health", ge=0, le=100)
    round_number: Optional[int] = Field(None, description="Current round number")


class MLRecommendationResponse(BaseModel):
    """ML recommendation response model."""
    recommendation: str = Field(..., description="Strategic recommendation")
    confidence: float = Field(..., description="Confidence score", ge=0, le=1)
    game_phase: str = Field(..., description="Current game phase")
    priority_units: List[str] = Field(default_factory=list, description="Recommended units")


class ChampionFilter(BaseModel):
    """Champion filter parameters."""
    name: Optional[str] = Field(None, description="Champion name filter")
    cost: Optional[int] = Field(None, description="Cost filter", ge=1, le=5)
    trait: Optional[str] = Field(None, description="Trait filter")


class ChampionInfo(BaseModel):
    """Champion information model."""
    name: str = Field(..., description="Champion name")
    cost: int = Field(..., description="Champion cost")
    traits: List[str] = Field(..., description="Champion traits")
    type: str = Field("Champion", description="Unit type")


class TierFilter(str, Enum):
    """Tier filter enum."""
    S_PLUS = "S+"
    S = "S"
    A = "A"
    B = "B"
    C = "C"


class CompositionInfo(BaseModel):
    """Composition information model."""
    name: str = Field(..., description="Composition name")
    tier: str = Field(..., description="Tier ranking")
    win_rate: float = Field(..., description="Win rate", ge=0, le=1)
    avg_placement: float = Field(..., description="Average placement", ge=1, le=8)
    play_rate: float = Field(..., description="Play rate", ge=0, le=1)
    primary_trait: str = Field(..., description="Primary trait")
    key_champions: List[str] = Field(default_factory=list, description="Key champions")


class MetaResponse(BaseModel):
    """Meta analysis response model."""
    tier_lists: Dict[str, List[CompositionInfo]] = Field(default_factory=dict, description="Tier lists")
    trends: Optional[str] = Field(None, description="Trend analysis")
    last_updated: str = Field(..., description="Last update timestamp")
    data_source: str = Field(..., description="Data source information")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="API status")
    timestamp: str = Field(..., description="Data timestamp")
    champions: int = Field(..., description="Number of champions")
    traits: int = Field(..., description="Number of traits")
    compositions: int = Field(..., description="Number of compositions")
    api_keys: Dict[str, bool] = Field(..., description="API key availability")