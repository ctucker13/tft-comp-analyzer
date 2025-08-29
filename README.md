# TFT Composition Analyzer

An AI-powered analysis tool for Teamfight Tactics (TFT) that uses agentic workflows to identify optimal team compositions from high-level gameplay data.

## Features

- **🤖 Agentic AI Workflow**: Uses LangGraph to orchestrate multi-step analysis
- **📊 TFT Data Integration**: Connects to Riot Games API for real match data
- **🧠 LLM Analysis**: Supports both OpenAI and Anthropic models for composition analysis
- **🌍 European Support**: Configured for EUW region with proper API routing
- **🎭 Mock Mode**: Develop and test without API keys using realistic mock data
- **⚡ Modern Python**: Built with UV package manager, Python 3.11+, and async/await

## Quick Start

### Prerequisites

- Python 3.11 or higher
- UV package manager
- Riot Games API key (optional for development)
- OpenAI or Anthropic API key (optional for development)

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tft-comp-analyzer.git
cd tft-comp-analyzer

# Install dependencies with UV
uv sync

# Copy environment file
cp .env.example .env
```

### Configuration

Create a `.env` file with your API keys:

```env
RIOT_API_KEY=your_riot_api_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_PROVIDER=anthropic
RIOT_REGION=euw1
```

**Note**: The app works in mock mode without real API keys for development!

### Run the Analysis

```bash
# Run the TFT composition analysis
uv run python -m src.tft_analyzer.main
```

## Project Structure

```
tft-comp-analyzer/
├── src/tft_analyzer/
│   ├── agents/           # AI agent components
│   ├── data/            # Riot API integration
│   ├── models/          # LLM provider abstractions
│   ├── workflows/       # LangGraph workflows
│   └── utils/           # Utility functions
├── config/              # Configuration management
├── tests/               # Test files
├── .env                 # Environment variables (not in git)
└── pyproject.toml       # UV project configuration
```

## Workflow Overview

1. **Data Collection**: Fetches challenger player data from Riot API
2. **Composition Extraction**: AI analyzes team compositions from match data
3. **Performance Analysis**: Evaluates composition success rates and patterns
4. **Meta Synthesis**: Generates strategic recommendations and tier lists

## API Keys Setup

### Riot Games API
1. Visit [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your Riot account
3. Generate a Development API Key (free, expires daily)

### Anthropic API
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Sign up and add a payment method
3. Generate an API key

## Development

The project supports mock mode for development without API keys:

```bash
# Force mock mode for testing
export RIOT_API_KEY=""
uv run python -m src.tft_analyzer.main
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Technologies Used

- **LangGraph**: Agentic AI workflow orchestration
- **Riot Games API**: TFT match and player data
- **Anthropic Claude / OpenAI GPT**: Natural language analysis
- **UV**: Fast Python package management
- **asyncio/aiohttp**: Async HTTP requests
- **Pydantic**: Configuration and data validation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This project is not affiliated with Riot Games. TFT and League of Legends are trademarks of Riot Games, Inc.