"""Chat API endpoints for TFT strategic advice."""

from fastapi import APIRouter, HTTPException
from typing import List
import uuid
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.agents.tft_agent import create_tft_agent
from ..models import ChatRequest, ChatResponse

router = APIRouter()

# In-memory conversation storage (in production, use Redis/database)
conversations = {}


def get_fallback_response(message: str) -> str:
    """Provide fallback responses when the AI agent fails."""
    message_lower = message.lower()

    # Strategic decision patterns
    if any(word in message_lower for word in ["gold", "level", "roll", "should"]):
        return """I'm having trouble accessing my full analysis capabilities right now, but here's some general TFT advice:

**Economic Decision Making:**
- If you have 30+ gold: Consider leveling to strengthen your board
- If you're below 20 gold: Usually better to save and stabilize
- Rolling is best when you're close to completing key 3-star units or need urgent upgrades

**General Strategy:**
- Prioritize board strength early, economy mid-game, and positioning late
- Look for strong item holders and plan your composition around them
- Don't force compositions - play your strongest board with good synergies

*Note: My advanced AI analysis is temporarily unavailable. Please try again later for detailed strategic recommendations.*"""

    # Meta analysis patterns
    elif any(word in message_lower for word in ["meta", "tier", "comp", "strong", "best"]):
        return """I'm currently unable to access live meta data, but here are some generally strong Set 15 compositions:

**S-Tier Compositions:**
- **Mighty Mech Reroll**: Focus on 3-star Gnar and mech synergies
- **Star Guardian**: High-cost carries with guardian frontline
- **Soul Fighter**: Balanced comp with strong mid-game scaling

**Key Set 15 Mechanics:**
- Power Snax provide unique combat bonuses
- Role-based gameplay emphasizes positioning
- 3-star 5-cost champions are very powerful this set

**General Meta Advice:**
- Flexible play often beats forcing one composition
- Strong economy leads to better end-game positioning
- Items and augments can shift optimal strategies

*Note: For current tier lists and trends, please try again when my data access is restored.*"""

    # General or greeting patterns
    else:
        return """Hello! I'm your TFT strategic advisor, though I'm currently running in limited mode.

I can help with:
- Strategic decision making (gold management, when to roll/level)
- Composition advice and synergy planning
- Meta analysis and tier list discussions
- Item prioritization and positioning

While my full AI analysis is temporarily unavailable, I'm still here to assist with TFT strategy questions. Please try asking again, or feel free to ask about specific game situations!

*Advanced features will be restored once my backend systems are fully operational.*"""


@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the TFT AI agent and get strategic advice.

    - **message**: Your strategic question or game state
    - **provider**: LLM provider (anthropic/openai)
    - **conversation_id**: Optional conversation ID for context
    """
    try:
        # Generate conversation ID if not provided
        conversation_id = request.conversation_id or str(uuid.uuid4())

        # Get or create conversation history
        if conversation_id not in conversations:
            conversations[conversation_id] = []

        conversation_history = conversations[conversation_id]

        try:
            # Create TFT agent
            agent = create_tft_agent(provider=request.provider)

            # Get AI response
            response = agent.process_message(request.message, conversation_history)

            # Try to extract intent and tool information from the agent
            intent = getattr(agent, 'last_intent', None) if hasattr(agent, 'last_intent') else None
            tool_used = getattr(agent, 'last_tool', None) if hasattr(agent, 'last_tool') else None

        except Exception as agent_error:
            print(f"Agent failed, providing fallback response: {agent_error}")
            # Provide fallback response when agent fails
            response = get_fallback_response(request.message)
            intent = "fallback"
            tool_used = "fallback_responses"

        # Update conversation history
        conversations[conversation_id].append({
            "user": request.message,
            "assistant": response
        })

        # Limit conversation history to last 10 exchanges
        if len(conversations[conversation_id]) > 10:
            conversations[conversation_id] = conversations[conversation_id][-10:]

        return ChatResponse(
            response=response,
            conversation_id=conversation_id,
            intent=intent,
            tool_used=tool_used
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history by ID."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id]
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation."""
    if conversation_id in conversations:
        del conversations[conversation_id]
        return {"message": "Conversation deleted"}
    else:
        raise HTTPException(status_code=404, detail="Conversation not found")


@router.get("/examples")
async def get_example_questions():
    """Get example strategic questions for the chat interface."""
    return {
        "examples": [
            {
                "category": "Strategic Decisions",
                "questions": [
                    "I'm at 30 gold, level 6, what should I do?",
                    "Should I roll for Lee Sin or save for level 8?",
                    "I have Star Guardian start, how do I transition?",
                    "When should I pivot from my current board?"
                ]
            },
            {
                "category": "Meta Analysis",
                "questions": [
                    "What are the best comps right now?",
                    "What are the current meta trends?",
                    "Which compositions are rising in popularity?",
                    "What's the strongest trait this patch?"
                ]
            },
            {
                "category": "Composition Help",
                "questions": [
                    "How do I play Mighty Mech compositions?",
                    "Is reroll Gnar still good?",
                    "What items should I build on Lee Sin?",
                    "How does Soul Fighter synergy work?"
                ]
            }
        ]
    }