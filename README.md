# TFT Set 15: K.O. Coliseum Composition Analyzer

An AI-powered analysis tool for Teamfight Tactics (TFT) Set 15 that uses agentic workflows to identify optimal team compositions from high-tier player gameplay data. Features a modern Streamlit web interface with real-time analysis and interactive chat.

## ✨ Features

### 🎯 **TFT Set 15 Specialized**
- **K.O. Coliseum Analysis**: Specifically tuned for Set 15 mechanics and champions
- **Power Snax Integration**: Analyzes optimal power-up timing and usage
- **Multi-Tier Player Pool**: Sources data from Challenger, Grandmaster, and Master players
- **Winner-Focused**: Prioritizes players with high recent win rates for quality data

### 🤖 **Advanced AI Analysis**
- **Agentic LangGraph Workflow**: Multi-step analysis pipeline with specialized agents
- **Dual LLM Support**: Choose between Anthropic Claude or OpenAI GPT models
- **Real-time Processing**: Live analysis with progress tracking and status updates
- **Interactive Chat**: Ask specific questions about TFT meta, strategies, and compositions

### 🌐 **Professional Web Interface**
- **Modern Streamlit UI**: Clean, responsive design with dark theme
- **Live Progress Tracking**: Real-time status updates during analysis
- **Multiple Analysis Options**: Fresh data retrieval or quick cached regeneration
- **Export Functionality**: Download analysis reports as markdown files

### 🔧 **Developer-Friendly**
- **Smart Caching**: Intelligent API response caching with configurable durations
- **Rate Limit Management**: Built-in protection against Riot API rate limits
- **Flexible Configuration**: Extensive environment variable customization
- **Development Mode**: Optional 24-hour match filtering and cache controls

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** with UV package manager
- **Riot Games Development API Key** ([Get one here](https://developer.riotgames.com/))
- **Anthropic API Key** ([Claude Console](https://console.anthropic.com/)) or **OpenAI API Key**

### Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/tft-comp-analyzer.git
cd tft-comp-analyzer

# Install dependencies with UV
uv sync

# Copy and configure environment
cp .env.example .env
```

### Configuration

Edit your `.env` file with your API keys:

```env
# Required API Keys
RIOT_API_KEY=your_riot_development_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
LLM_PROVIDER=anthropic

# Regional Settings
RIOT_REGION=euw1

# Set 15 Configuration
CURRENT_TFT_SET=15
CURRENT_PATCH=15.17
TFT_SET_NAME=K.O. Coliseum

# Analysis Preferences
REQUIRE_PATCH_15_3=false        # Include all Set 15 matches
USE_24H_FILTER=false            # Don't limit to last 24h
USE_CACHE=true                  # Enable caching for development
PRIORITIZE_WINNERS=true         # Focus on high-performing players
```

### Launch the Application

```bash
# Start the Streamlit web interface
uv run streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` to access the web interface.

## 📊 How It Works

### **Multi-Agent Workflow Pipeline**

1. **🎯 Data Collector Agent**
   - Fetches high-tier players (Challenger/Grandmaster/Master)
   - Analyzes recent performance to prioritize winners
   - Collects Set 15 match data with smart filtering

2. **🧠 Composition Extractor Agent**
   - Uses LLM to analyze team compositions from match data
   - Identifies successful carry units, trait combinations, and positioning
   - Extracts Power Snax usage patterns and timing

3. **📈 Performance Analyzer Agent**
   - Evaluates composition success rates and consistency
   - Analyzes economic patterns and game length impacts
   - Identifies meta trends and tier rankings

4. **📝 Meta Synthesizer Agent**
   - Generates comprehensive strategic guide
   - Creates tier lists and climbing recommendations
   - Provides Power Snax optimization advice

### **Smart Data Collection**

- **Winner-Focused Sampling**: Prioritizes players with high recent win rates
- **Multi-Tier Coverage**: Includes Challenger (top 300), Grandmaster (~700), Master (thousands)
- **Set 15 Filtering**: Ensures analysis only includes K.O. Coliseum matches
- **Rate Limit Protection**: Conservative API usage with intelligent delays

## 🖥️ Web Interface Features

### **📊 Meta Analysis Tab**
- **One-Click Analysis**: Generate comprehensive meta reports
- **Real-Time Progress**: Live status updates and progress bars  
- **Multiple Regeneration Options**:
  - 🔄 **Fresh Analysis**: Clear cache and get completely new data
  - ⚡ **Quick Regen**: Re-analyze existing data for different insights
- **Export Reports**: Download analysis as markdown files
- **Timestamp Tracking**: See when analysis was generated and method used

### **💬 TFT Chat Tab**
- **Interactive AI Expert**: Ask questions about current meta
- **Contextual Responses**: AI has access to your analysis data
- **Suggested Questions**: Get AI-generated relevant questions
- **Chat History**: Maintain conversation context

### **⚙️ Configuration Panel**
- **API Status Monitoring**: Real-time connection status
- **Patch Selection**: Choose specific patches for analysis
- **Cache Management**: View, clear, and control caching behavior
- **Development Settings**: 24-hour filters, cache controls

## 🗂️ Project Structure

```
tft-comp-analyzer/
├── src/tft_analyzer/
│   ├── agents/              # AI agent components (future expansion)
│   ├── chat/                # Interactive chat handler
│   ├── data/                # Riot API integration & data management
│   │   ├── riot_api.py      # Core API client with rate limiting
│   │   ├── patch_data_manager.py  # Patch data caching
│   │   └── dynamic_validation.py  # Content validation (optional)
│   ├── models/              # LLM provider abstractions
│   │   └── llm_provider.py  # Unified OpenAI/Anthropic interface
│   ├── utils/               # Utility functions
│   │   └── patch_detector.py # Auto-detect current TFT patch
│   └── workflows/           # LangGraph workflow orchestration
│       └── comp_analysis_workflow.py  # Main analysis pipeline
├── config/                  # Configuration management
│   └── settings.py         # Pydantic settings with env var support
├── streamlit_app.py        # Modern web interface
├── CLAUDE.md              # AI assistant instructions
└── pyproject.toml         # UV project configuration
```

## 🛠️ Advanced Configuration

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `RIOT_API_KEY` | Required | Riot Games Development API key |
| `ANTHROPIC_API_KEY` | Required | Anthropic Claude API key |
| `LLM_PROVIDER` | `anthropic` | AI provider (`anthropic` or `openai`) |
| `RIOT_REGION` | `euw1` | TFT region (`euw1`, `na1`, etc.) |
| `REQUIRE_PATCH_15_3` | `false` | Only analyze patch 15.3+ matches |
| `USE_24H_FILTER` | `false` | Limit to matches from last 24 hours |
| `USE_CACHE` | `true` | Enable API response caching |
| `PRIORITIZE_WINNERS` | `true` | Analyze recent performance for player selection |

### **Cache Configuration**

The application uses intelligent caching to optimize API usage:

- **Challenger Players**: 6 hours (changes infrequently)
- **Match History**: 2 hours (moderate update frequency)  
- **Match Details**: 72 hours (immutable once created)

Cache files are stored in `cache/riot_api/` and can be managed through the web interface.

### **Rate Limiting**

Built-in protection for Riot's Development API limits:
- **Conservative Delays**: 8 seconds between API calls
- **Request Tracking**: Monitors API usage patterns
- **Smart Fallbacks**: Graceful degradation when limits are approached

## 🔑 API Keys Setup

### **Riot Games API**
1. Visit [Riot Developer Portal](https://developer.riotgames.com/)
2. Sign in with your Riot Games account
3. Generate a **Development API Key** (free, expires every 24 hours)
4. For production use, apply for a **Production API Key**

### **Anthropic API (Recommended)**
1. Visit [Anthropic Console](https://console.anthropic.com/)
2. Create an account and add payment method
3. Generate an API key from the dashboard
4. Claude offers excellent strategic analysis capabilities

### **OpenAI API (Alternative)**
1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create account and add payment method
3. Generate API key from API section
4. GPT-4 provides good analytical capabilities

## 🐛 Development & Testing

### **Development Commands**

```bash
# Install with development dependencies
uv sync --extra dev

# Run linting and formatting
uv run black src/ config/
uv run ruff check src/ config/

# Run type checking
uv run mypy src/ config/

# Run tests
uv run pytest
```

### **Debugging Scripts**

The repository includes several debugging utilities:

```bash
# Test LLM provider connections
uv run python scripts/tests/test_anthropic.py

# Test Riot API rate limiting
uv run python scripts/tests/test_rate_limits.py

# Explore API response structure
uv run python scripts/debug/debug_api_structure.py
```

### **Cache Management**

```bash
# Clear all cache files
rm -rf cache/riot_api/

# View cache statistics
ls -la cache/riot_api/
```

## 📈 Performance Optimization

### **For Development API Keys**
- Limited to 100 requests per 2 minutes
- Targets 3 challenger players, 3 matches each
- Uses 8-second delays between calls
- Caching highly recommended

### **For Production API Keys**
- Much higher rate limits available
- Can analyze more players and matches
- Adjust `MAX_PLAYERS_TO_ANALYZE` in settings

### **Memory Usage**
- Typical usage: 100-200MB RAM
- Cache can grow to 50-100MB with heavy use
- Streamlit adds ~100MB base memory usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes with clear messages
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request with detailed description

### **Code Standards**
- **Black** formatting (line length: 88)
- **Ruff** linting with modern Python practices
- **Type hints** with mypy checking
- **Async/await** for all I/O operations

## 🛡️ Rate Limiting & Best Practices

### **Riot API Guidelines**
- Development keys: 100 requests per 2 minutes
- Always implement rate limiting and retries
- Cache responses when possible
- Respect the API terms of service

### **LLM API Optimization**
- Use appropriate token limits for different analysis types
- Implement caching for repeated queries
- Monitor usage and costs
- Handle rate limits gracefully

## 🔄 Recent Updates

### **v0.2.0 - Set 15 Specialization**
- ✅ Updated for TFT Set 15: K.O. Coliseum
- ✅ Added multi-tier player analysis (Challenger/GM/Master)
- ✅ Implemented winner-focused player prioritization
- ✅ Built modern Streamlit web interface
- ✅ Added interactive TFT chat functionality
- ✅ Removed validation false positives
- ✅ Enhanced caching and rate limiting

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This project is not affiliated with Riot Games, Inc. "Teamfight Tactics" and "League of Legends" are trademarks of Riot Games, Inc. This tool is for educational and analytical purposes only.

---

**🎯 Ready to dominate Set 15? Get strategic insights from the best players in the world! 🏆**