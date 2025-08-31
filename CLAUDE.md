# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TFT Composition Analyzer is an AI-powered analysis tool for Teamfight Tactics (TFT) Set 15: K.O. Coliseum. The application uses LangGraph workflows to orchestrate multi-step analysis of challenger gameplay data from the Riot Games API, then leverages LLMs to identify optimal team compositions and meta trends.

## Architecture

### Core Components

- **LangGraph Workflow**: Multi-step agentic analysis using StateGraph with defined flow:
  1. `data_collector` → fetches challenger player data and match history
  2. `comp_extractor` → analyzes compositions using LLM
  3. `performance_analyzer` → evaluates success patterns
  4. `meta_synthesizer` → generates strategic recommendations

- **LLM Provider Abstraction**: Unified interface supporting both OpenAI and Anthropic models
  - Located in `src/tft_analyzer/models/llm_provider.py`
  - Handles API key validation and model selection

- **Riot API Integration**: Async client for TFT data with rate limiting
  - Located in `src/tft_analyzer/data/riot_api.py`
  - Includes Set 15 filtering and patch detection
  - Requires valid Riot API key (no mock data fallbacks)

- **Configuration Management**: Pydantic-based settings with environment variable loading
  - Located in `config/settings.py`
  - Handles API keys, model selection, and analysis parameters

### Data Flow

The application follows this workflow:
1. Auto-detects current TFT patch using `TFTPatchDetector`
2. Fetches challenger player data (PUUIDs directly available)
3. Collects recent match history for Set 15 games only
4. Extracts compositions using LLM analysis of match data
5. Analyzes performance patterns and success factors
6. Synthesizes meta recommendations and tier lists

## Common Development Commands

### Installation and Setup
```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --extra dev

# Copy environment configuration
cp .env.example .env
```

### Running the Application
```bash
# Main application entry point
uv run python -m src.tft_analyzer.main

# Force mock mode (no API keys required)
export RIOT_API_KEY="" && uv run python -m src.tft_analyzer.main
```

### Testing and Development
```bash
# Run linting
uv run black src/ config/
uv run ruff check src/ config/

# Run type checking
uv run mypy src/ config/

# Run tests
uv run pytest

# Run async tests specifically
uv run pytest -v tests/ -k async
```

### Debugging Scripts
The repository includes several debugging utilities:
- `scripts/tests/test_anthropic.py` - Test LLM provider connections
- `scripts/tests/test_rate_limits.py` - Test Riot API rate limiting
- `scripts/debug/debug_api_structure.py` - Explore API response structure
- `scripts/debug/simple_working_test.py` - Basic functionality verification
- `scripts/test_patch_filtering.py` - Test patch 15.3+ and 24h filtering

## Key Configuration

### Environment Variables
- `RIOT_API_KEY`: Riot Games Development API key (expires daily)
- `ANTHROPIC_API_KEY`: Anthropic API key (preferred LLM provider)
- `OPENAI_API_KEY`: OpenAI API key (alternative LLM provider)
- `LLM_PROVIDER`: "anthropic" or "openai"
- `RIOT_REGION`: "euw1" (Europe West)
- `REQUIRE_PATCH_15_3`: "true" to only analyze patch 15.3+ matches (default: true)
- `USE_24H_FILTER`: "true" to only get matches from last 24 hours (default: false)
- `USE_CACHE`: "true" to enable API response caching for development (default: false)

### Development Settings
The application is optimized for Development API key constraints:
- Rate limits: 8-second delays between API calls
- Limited players: 3 challenger players maximum
- Limited matches: 3 matches per player, 2 processed for Set 15
- Target data: 10 Set 15 matches total
- **Patch filtering**: Only analyzes matches from patch 15.3+ (released 2025/08/26)
- **Optional 24h filtering**: Can limit to matches from last 24 hours only
- **API Caching**: Optional caching system to avoid rate limits during development

### Caching System
For development convenience, the application includes an optional caching system:
- **Cache Location**: `cache/riot_api/` directory
- **Cache Duration**: Challenger players (1h), Match history (30m), Match details (24h)
- **Streamlit Controls**: Enable/disable caching and clear cache via UI
- **Smart Expiration**: Automatically ignores expired cache files
- **Filter Preservation**: Cached data still respects Set 15 and patch 15.3+ filtering

### Set 15 Specifics
Current configuration targets:
- **Set Number**: 15 (K.O. Coliseum)
- **Current Patch**: 15.3+ (released 2025/08/26)
- **Key Features**: Power Snax system, Role-based gameplay, 3-star 5-cost mechanics
- **Match Filtering**: Only analyzes matches from Set 15, patch 15.3+
- **Date Filtering**: Only includes matches from 2025/08/26 onwards
- **Time Filtering**: Optional 24-hour window for most recent matches

## Import Structure

The codebase uses dual import patterns to handle both development and installed package scenarios:
```python
try:
    # Relative imports for package structure
    from .models.llm_provider import LLMClient
except ImportError:
    # Absolute imports for direct execution
    from src.tft_analyzer.models.llm_provider import LLMClient
```

## Error Handling

The application includes comprehensive error handling for:
- API rate limiting and connection failures
- Missing or invalid API keys (raises clear error messages)
- Set filtering (skips non-Set 15 matches)
- Patch filtering (skips pre-15.3 matches)
- LLM request failures with retry logic

## Testing

The application requires a valid Riot API key for all operations. For testing LLM functionality without API access:
- Use `scripts/test_llm_with_mock_data.py` for LLM provider testing with mock Set 15 data
- Mock data is only available in the separate test script, not in the main application