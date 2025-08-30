from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum
from typing import Optional

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    # API Keys
    riot_api_key: str = Field(..., description="Riot Games API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    
    # LLM Configuration - Updated models
    llm_provider: LLMProvider = Field(LLMProvider.ANTHROPIC, description="LLM provider to use")
    openai_model: str = Field("gpt-4o", description="OpenAI model name")
    anthropic_model: str = Field("claude-sonnet-4-20250514", description="Current Anthropic model")
    
    # TFT Configuration - Updated for Europe
    riot_region: str = Field("euw1", description="Riot API platform (Europe West)")
     
    # TFT Set 15 Configuration - Updated with real data
    current_tft_set: int = Field(15, description="Current TFT set number")
    current_patch: str = Field("15.17", description="Current TFT patch - updated from API")
    tft_set_name: str = Field("K.O. Coliseum", description="Current TFT set name")
    
    # Analysis Configuration - Conservative for Development API key
    max_matches_per_player: int = Field(3, description="Max matches per player (low for dev key)")
    max_players_to_analyze: int = Field(2, description="Max players (very low for dev key)")
    days_back_for_matches: int = Field(7, description="Only analyze matches from last N days")
    min_set_number: int = Field(15, description="Minimum set number to include in analysis")
    target_match_count: int = Field(10, description="Target number of Set 15 matches (low for dev key)")
    api_delay_seconds: int = Field(8, description="Seconds between API calls for dev key")