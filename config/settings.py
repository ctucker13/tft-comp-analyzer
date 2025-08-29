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
    
    # LLM Configuration
    llm_provider: LLMProvider = Field(LLMProvider.OPENAI, description="LLM provider to use")
    openai_model: str = Field("gpt-4-turbo-preview", description="OpenAI model name")
    anthropic_model: str = Field("claude-3-sonnet-20240229", description="Anthropic model name")
    
    # TFT Configuration - Updated for Europe
    riot_region: str = Field("euw1", description="Riot API platform (changed to Europe West)")
    max_matches_per_player: int = Field(20, description="Max matches to analyze per player")
    max_players_to_analyze: int = Field(50, description="Max players to analyze")