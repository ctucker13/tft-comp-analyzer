# TFT Agent Usage Examples

This document provides comprehensive examples of how to use the TFT agentic model for different types of conversations and strategic analysis.

## Quick Start

```bash
# Interactive demo
uv run python tft_agent_demo.py

# Show example conversations
uv run python tft_agent_demo.py --examples

# Direct usage in code
uv run python -c "from src.tft_analyzer.agents.tft_agent import chat_with_tft_agent; print(chat_with_tft_agent('What are the best comps right now?'))"
```

## Conversation Types and Agent Behavior

The TFT agent automatically classifies conversations and routes them to appropriate analysis tools:

### 1. Strategic Decisions → ML Analysis

**Intent**: When users ask about tactical decisions in their current game state.
**Tools Triggered**: Game state extraction + ML strategic analysis
**Example Conversations**:

```
User: "I'm at 30 gold, level 6, placement 5, what should I do?"
Agent: [Extracts game state] → [Runs ML analysis] → [Strategic recommendations]

User: "Should I roll or level up with 25 gold at stage 3-2?"
Agent: [Analyzes game phase] → [ML strategic analysis] → [Specific action advice]

User: "I have 15 health left, how should I play this out?"
Agent: [Considers low health scenario] → [ML analysis] → [Emergency strategy]
```

**Expected Agent Workflow**:
1. Classify as `STRATEGIC_DECISION`
2. Extract game parameters (gold, level, health, round, etc.)
3. Call ML recommendation tool with extracted parameters
4. Generate strategic response with specific actions

### 2. Meta Analysis → Tier Lists & Composition Data

**Intent**: When users ask about current meta, strong compositions, or tier lists.
**Tools Triggered**: Meta analysis tools (tier lists, composition data from MetaTFT)
**Example Conversations**:

```
User: "What are the strongest compositions right now?"
Agent: [Gets current meta tier list] → [Analyzes top comps] → [Tier list with explanations]

User: "Is Star Guardian good in the current meta?"
Agent: [Searches composition data] → [Evaluates specific comp] → [Meta positioning analysis]

User: "Give me the current tier list for patch 15.3"
Agent: [Fetches tier list data] → [Current meta analysis] → [Structured tier rankings]
```

**Expected Agent Workflow**:
1. Classify as `META_ANALYSIS` or `COMPOSITION_QUESTION`
2. Determine specific analysis type (tier list vs trends vs specific comp)
3. Call appropriate meta analysis tools
4. Generate comprehensive meta response

### 3. General TFT Chat → Direct Response

**Intent**: General discussion, game mechanics questions, or casual conversation.
**Tools Triggered**: None (direct LLM response)
**Example Conversations**:

```
User: "I love playing TFT, it's so much fun!"
Agent: [Direct engaging response about TFT enjoyment]

User: "How does the Power Up system work in Set 15?"
Agent: [Explains Set 15 Power Up mechanics]

User: "What's your favorite Set 15 feature?"
Agent: [Discusses Set 15 features conversationally]
```

**Expected Agent Workflow**:
1. Classify as `GENERAL_CHAT`
2. Route directly to response generator
3. Generate friendly, informative response without tool calls

## Advanced Usage Patterns

### Conversation Context

The agent maintains conversation history for context-aware responses:

```python
from src.tft_analyzer.agents.tft_agent import TFTAgent

agent = TFTAgent(provider="anthropic")

# First message
response1 = agent.process_message("What's meta right now?")

# Follow-up with context
response2 = agent.process_message("Which of those is best for beginners?",
                                  conversation_history=[
                                      {"role": "user", "content": "What's meta right now?"},
                                      {"role": "assistant", "content": response1}
                                  ])
```

### Provider Selection

```python
# Use Anthropic Claude (recommended)
agent_claude = TFTAgent(provider="anthropic", model="claude-3-5-sonnet-20241022")

# Use OpenAI GPT
agent_gpt = TFTAgent(provider="openai", model="gpt-4-turbo-preview")

# Quick chat function
from src.tft_analyzer.agents.tft_agent import chat_with_tft_agent
response = chat_with_tft_agent("I need help with my mid-game transition", provider="anthropic")
```

### Async Usage

```python
async def async_tft_chat():
    agent = TFTAgent()
    response = await agent.aprocess_message("What should I do with 50 gold at level 7?")
    return response

# Use in async context
import asyncio
response = asyncio.run(async_tft_chat())
```

## Testing Different Scenarios

### Strategic Decision Testing

Test the ML analysis pipeline with various game states:

```python
strategic_questions = [
    "I'm at 30 gold, level 6, placement 5, what should I do?",
    "Should I roll or level up with 25 gold at stage 3-2?",
    "I have 15 health left, round 4-1, how should I play?",
    "Level 7 with 40 gold, should I go 8 or roll down?",
    "I'm first place with 80 health, what's my strategy?",
]
```

### Meta Analysis Testing

Test the composition and tier list tools:

```python
meta_questions = [
    "What are the strongest compositions right now?",
    "Is reroll Gnar good this patch?",
    "Give me the current S-tier comps",
    "What comps counter Star Guardian?",
    "Which compositions are best for climbing?",
]
```

### Mixed Conversation Testing

Test conversation classification accuracy:

```python
mixed_questions = [
    "I love TFT but struggle with late game transitions",  # Should trigger strategic analysis
    "What's the difference between Power Ups and Artifacts?",  # General chat
    "Are there any OP comps I should abuse right now?",  # Meta analysis
    "Thanks for the help! TFT is getting easier to understand",  # General chat
]
```

## Integration Examples

### Streamlit Integration

```python
import streamlit as st
from src.tft_analyzer.agents.tft_agent import TFTAgent

if "agent" not in st.session_state:
    st.session_state.agent = TFTAgent(provider="anthropic")

user_input = st.text_input("Ask about TFT strategy:")
if user_input:
    response = st.session_state.agent.process_message(user_input)
    st.write(response)
```

### Discord Bot Integration

```python
import discord
from src.tft_analyzer.agents.tft_agent import TFTAgent

class TFTBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.agent = TFTAgent()

    async def on_message(self, message):
        if message.author == self.client.user:
            return

        if message.content.startswith("!tft "):
            query = message.content[5:]  # Remove "!tft "
            response = await self.agent.aprocess_message(query)
            await message.channel.send(response)
```

## Performance Considerations

### Tool Call Efficiency

The agent intelligently routes conversations to minimize unnecessary tool calls:

- **Strategic decisions**: Always triggers ML analysis (necessary for game state evaluation)
- **Meta questions**: Triggers tier list OR trends (not both unless needed)
- **General chat**: No tool calls (direct LLM response)

### Caching for Development

Enable caching to avoid repeated API calls during testing:

```bash
export USE_CACHE=true
uv run python tft_agent_demo.py
```

### Rate Limiting

The agent respects Riot API rate limits when fetching live data:

- 8-second delays between API calls
- Limited to 3 challenger players and 3 matches per player
- Automatic fallback to cached data when available

## Error Handling

The agent includes comprehensive error handling:

```python
# API failures fall back to cached data
response = agent.process_message("What's meta?")  # Will work even if APIs fail

# Invalid game states use reasonable defaults
response = agent.process_message("I'm at ??? gold, what do I do?")  # Handles missing info

# LLM failures provide user-friendly messages
response = agent.process_message("Strategic question")  # Graceful degradation
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you're running from project root with `uv run`
2. **API Key Issues**: Set `ANTHROPIC_API_KEY` or `OPENAI_API_KEY`
3. **Tool Call Failures**: Check Riot API key and internet connection
4. **Classification Issues**: Verify question format matches expected patterns

### Debug Mode

Enable detailed logging for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

agent = TFTAgent()
response = agent.process_message("Debug this conversation")
```

This comprehensive guide should help users understand and effectively use the TFT agentic model for various types of TFT strategic analysis and conversation.