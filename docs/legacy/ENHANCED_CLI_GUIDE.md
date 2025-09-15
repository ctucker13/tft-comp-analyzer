# 🎮 Enhanced TFT CLI Guide

The TFT Composition Analyzer now features a beautiful, modern CLI interface powered by the Rich Python library!

## ✨ Features

### 🎨 Visual Enhancements
- **Rich Colors & Typography**: Beautiful colored output with professional styling
- **Interactive Tables**: Organized data display with borders and colors
- **Panels & Boxes**: Content organized in attractive panels
- **Progress Bars**: Visual feedback for long-running operations
- **Status Indicators**: Emojis and color-coded status messages
- **Smart Prompts**: Input validation and helpful defaults

### 🤖 AI-Powered Analysis
- **Strategic Chat**: Natural language game state analysis
- **Parameter Mode**: Manual input for precise analysis
- **Meta Analysis**: Current tier lists and trending strategies
- **Unit Database**: Browse all 65 official Set 15 champions

### 📊 Real-time Data
- **Official Riot API**: All unit costs and data from Riot Games
- **Live Updates**: Real-time ML model training and recommendations
- **Session Tracking**: Monitor your usage and query history

## 🚀 Getting Started

### Quick Start
```bash
# Launch enhanced CLI
uv run python src/tft_analyzer/enhanced_cli.py

# Direct to chat mode
uv run python src/tft_analyzer/enhanced_cli.py --chat

# Single query
uv run python src/tft_analyzer/enhanced_cli.py --query "I'm level 8 with 50 gold, what should I do?"
```

### Main Menu Options

| Option | Icon | Description | Usage |
|--------|------|-------------|-------|
| **ML Strategy Chat** | 🤖 | Natural language analysis | Best for general questions |
| **Parameter Analysis** | 📊 | Manual input mode | Precise game state analysis |
| **Meta Tier Lists** | 🏆 | Current strongest comps | Meta overview |
| **Meta Trends** | 📈 | Rising/falling strategies | Trend analysis |
| **Unit Database** | 🎯 | Browse champions | Unit lookup |
| **System Info** | ⚙️ | View system status | Diagnostics |
| **Help & Examples** | ❓ | Usage guide | Documentation |

## 💬 Chat Mode Examples

### Strategic Decisions
```
"I'm at 30 gold, 45 health, level 6, placement 5, what should I do?"
"Should I roll or level to 8 with 50 gold?"
"I'm low health in 7th place, help me stabilize"
```

### Composition Questions
```
"What's the best Star Guardian build?"
"How do I play Sivir reroll effectively?"
"What items should I put on Jinx?"
```

### Meta Questions
```
"What comps are strongest right now?"
"What's trending in the meta?"
"Is reroll better than fast 8 this patch?"
```

## 📊 Parameter Mode

Perfect for analyzing specific scenarios:

- **Placement**: Current rank (1-8)
- **Gold**: Available gold amount
- **Health**: Current HP
- **Level**: Player level (1-10)
- **Round**: Current round number
- **Stage**: Game stage (1-6)
- **Units**: Units on board count
- **Phase**: early/mid/late

Each parameter shows helpful status indicators:
- 🥇 Winning / ✅ Safe / ⚠️ Danger / 🆘 Critical (placement)
- 💰 Rich / 💵 Stable / 🪙 Low / 💸 Broke (gold)
- 💚 Healthy / 💛 Stable / 🧡 Danger / ❤️ Critical (health)

## 🎯 Unit Database

Browse all 65 official Set 15 champions:

### Cost Distribution
- **1-cost**: 14 champions (Sivir, Gnar, etc.)
- **2-cost**: 13 champions (Jhin, Gangplank, etc.)
- **3-cost**: 16 champions (Ahri, Caitlyn, etc.)
- **4-cost**: 13 champions (Jinx, Akali, etc.)
- **5-cost**: 9 champions (Seraphine, Braum, etc.)

### Champion Details
Get detailed information for any champion:
- Official cost from Riot API
- Trait assignments (when available)
- Riot ID and API name
- Data source verification

## ⚡ Key Features

### Rich Visual Elements
- **Tables**: Organized data with borders and colors
- **Panels**: Boxed content with titles and styling
- **Progress Bars**: Visual feedback during analysis
- **Status Icons**: Emojis for quick status recognition
- **Color Coding**: Green for success, red for errors, yellow for warnings

### Interactive Experience
- **Smart Prompts**: Input validation and helpful defaults
- **Menu Navigation**: Easy keyboard navigation
- **Session Tracking**: Monitor queries and usage time
- **Error Handling**: Graceful error messages with Rich formatting

### Professional Styling
- **Gold Theme**: Premium gold and blue color scheme
- **Consistent Layout**: Organized, readable interface
- **Typography**: Bold headings and clear text hierarchy
- **Responsive**: Adapts to terminal width

## 🔧 Command Line Options

```bash
# Interactive enhanced menu (default)
uv run python src/tft_analyzer/enhanced_cli.py

# Start directly in chat mode
uv run python src/tft_analyzer/enhanced_cli.py --chat

# Single query mode (non-interactive)
uv run python src/tft_analyzer/enhanced_cli.py --query "your question here"

# Help
uv run python src/tft_analyzer/enhanced_cli.py --help
```

## 🎨 Visual Examples

The enhanced CLI includes:
- Beautiful ASCII art banners
- Color-coded status indicators
- Interactive tables with data
- Professional panel layouts
- Progress bars for operations
- Rich typography and formatting

## 🔄 Migration from Old CLI

The original CLI (`cli.py`) is still available, but the enhanced version provides:
- Much better visual experience
- Improved usability and navigation
- Professional appearance
- Better error handling and feedback
- More intuitive interface

## 🤝 Tips & Tricks

1. **Chat Mode**: Use natural language - the AI understands context
2. **Parameter Mode**: Great for testing specific scenarios
3. **Unit Database**: Look up exact costs before making decisions
4. **Session Stats**: Track your usage with the stats command
5. **Help**: Type 'help' in chat mode for quick examples

## 🎯 Official Data

All data is sourced from:
- **Riot Games Data Dragon API v15.18.1**
- **65 official Set 15 champions**
- **Real-time updates every 5 minutes**
- **Validated unit costs and traits**

The enhanced CLI represents a major upgrade in user experience while maintaining all the powerful analysis capabilities of the TFT Composition Analyzer!