from pydantic_settings import BaseSettings
from pydantic import Field
from enum import Enum
from typing import Optional

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    
    # API Keys - Updated field names to match environment variables
    riot_api_key: str = Field(..., env="RIOT_API_KEY", description="Riot Games API key")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY", description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY", description="Anthropic API key")
    
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
    max_players_to_analyze: int = Field(3, description="Max players (increased to 3 for better data)")
    days_back_for_matches: int = Field(7, description="Only analyze matches from last N days")
    min_set_number: int = Field(15, description="Minimum set number to include in analysis")
    target_match_count: int = Field(10, description="Target number of Set 15 matches (low for dev key)")
    api_delay_seconds: int = Field(8, description="Seconds between API calls for dev key")
    
    def get_api_key_for_provider(self, provider: LLMProvider) -> Optional[str]:
        """Get the appropriate API key for the given provider"""
        if provider == LLMProvider.OPENAI:
            return self.openai_api_key
        elif provider == LLMProvider.ANTHROPIC:
            return self.anthropic_api_key
        return None
    
    def get_model_for_provider(self, provider: LLMProvider) -> str:
        """Get the appropriate model for the given provider"""
        if provider == LLMProvider.OPENAI:
            return self.openai_model
        elif provider == LLMProvider.ANTHROPIC:
            return self.anthropic_model
        return "unknown-model"
    
    def validate_api_keys(self) -> dict:
        """Validate which API keys are properly configured"""
        validation = {
            "riot": bool(self.riot_api_key and not self.riot_api_key.startswith("your_")),
            "openai": bool(self.openai_api_key and self.openai_api_key.startswith("sk-")),
            "anthropic": bool(self.anthropic_api_key and self.anthropic_api_key.startswith("sk-ant-"))
        }
        return validation
    
    def debug_info(self) -> dict:
        """Get debug information about configuration"""
        return {
            "provider": self.llm_provider,
            "model": self.get_model_for_provider(self.llm_provider),
            "api_key_present": bool(self.get_api_key_for_provider(self.llm_provider)),
            "riot_region": self.riot_region,
            "current_set": self.current_tft_set,
            "current_patch": self.current_patch,
            "api_keys_valid": self.validate_api_keys()
        }