#!/usr/bin/env python3
"""
TFT Agentic Model with LangGraph

An intelligent agent that can handle TFT conversations and automatically trigger
ML model tool calls when discussions involve compositions, meta analysis, or strategy.
"""

import json
import re
from typing import Dict, List, Optional, Any, Literal, TypedDict, Annotated
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

try:
    from ..tools.ml_recommendation_tool import get_tft_recommendation
    from ..tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from ..data.meta_data_manager import TFTMetaDataManager
    from ..models.llm_provider import LLMClient
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation
    from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
    from src.tft_analyzer.models.llm_provider import LLMClient
    from config.settings import Settings


# Define the agent state
class TFTAgentState(TypedDict):
    """State for the TFT Agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    conversation_context: Dict[str, Any]
    detected_intent: str
    game_state: Optional[Dict[str, Any]]
    tool_results: Dict[str, Any]
    needs_ml_analysis: bool
    needs_meta_analysis: bool


class TFTAgent:
    """Intelligent TFT agent with LangGraph workflow."""

    def __init__(self, provider: str = "anthropic", model: Optional[str] = None):
        """
        Initialize the TFT Agent.

        Args:
            provider: LLM provider ("anthropic" or "openai")
            model: Specific model to use
        """
        self.settings = Settings()
        self.provider = provider
        self.model = model or self._get_default_model()

        # Initialize LLM
        self._initialize_llm()

        # Initialize data manager
        self.meta_data_manager = TFTMetaDataManager()

        # Build the agent graph
        self.graph = self._build_graph()

    def _get_default_model(self) -> str:
        """Get default model for the provider."""
        if self.provider == "anthropic":
            return "claude-3-5-sonnet-20241022"
        elif self.provider == "openai":
            return "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _initialize_llm(self):
        """Initialize the LLM client."""
        if self.provider == "anthropic":
            api_key = self.settings.get_api_key_for_provider("anthropic")
            self.llm = ChatAnthropic(
                model=self.model,
                anthropic_api_key=api_key,
                temperature=0.1,
                max_tokens=2000
            )
        elif self.provider == "openai":
            api_key = self.settings.get_api_key_for_provider("openai")
            self.llm = ChatOpenAI(
                model=self.model,
                openai_api_key=api_key,
                temperature=0.1,
                max_tokens=2000
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Define tools
        tft_ml_tool = self._create_ml_recommendation_tool()
        tft_meta_tool = self._create_meta_analysis_tool()
        tft_tier_list_tool = self._create_tier_list_tool()

        # Create graph
        workflow = StateGraph(TFTAgentState)

        # Add nodes
        workflow.add_node("classifier", self._classify_conversation)
        workflow.add_node("game_state_extractor", self._extract_game_state)
        workflow.add_node("ml_analyzer", self._run_ml_analysis)
        workflow.add_node("meta_analyzer", self._run_meta_analysis)
        workflow.add_node("response_generator", self._generate_response)

        # Add edges
        workflow.add_edge(START, "classifier")

        # Conditional routing from classifier
        workflow.add_conditional_edges(
            "classifier",
            self._route_after_classification,
            {
                "extract_game_state": "game_state_extractor",
                "meta_analysis": "meta_analyzer",
                "direct_response": "response_generator"
            }
        )

        # From game state extractor to ML analyzer
        workflow.add_edge("game_state_extractor", "ml_analyzer")

        # From analyzers to response generator
        workflow.add_edge("ml_analyzer", "response_generator")
        workflow.add_edge("meta_analyzer", "response_generator")

        # End at response generator
        workflow.add_edge("response_generator", END)

        return workflow.compile()

    def _classify_conversation(self, state: TFTAgentState) -> TFTAgentState:
        """Classify the conversation intent and determine tool usage."""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""

        # Enhanced intent classification system
        classification_prompt = f"""
You are a TFT (Teamfight Tactics) conversation classifier. Analyze this message and determine the user's intent.

User message: "{last_message}"

Classify the intent as one of:

1. STRATEGIC_DECISION - User is asking for strategic advice about their current game state
   - Examples: "What should I do with 30 gold?", "I'm level 6, should I roll or level?"
   - Requires: Game state extraction + ML analysis

2. META_ANALYSIS - User is asking about meta compositions, tier lists, or what's strong
   - Examples: "What are the best comps?", "What's meta right now?", "Tier list?"
   - Requires: Meta analysis tool

3. COMPOSITION_QUESTION - User is asking about specific team compositions
   - Examples: "How do I play Star Guardian?", "Is reroll Gnar good?"
   - Requires: Meta analysis tool

4. GENERAL_CHAT - General TFT discussion, theory, or non-strategic questions
   - Examples: "I love this patch", "TFT is fun", "How does this trait work?"
   - Requires: Direct response

Respond with ONLY the classification: STRATEGIC_DECISION, META_ANALYSIS, COMPOSITION_QUESTION, or GENERAL_CHAT
"""

        # Get classification
        messages = [
            SystemMessage(content="You are a TFT conversation classifier."),
            HumanMessage(content=classification_prompt)
        ]
        classification_msg = self.llm.invoke(messages)
        intent = classification_msg.content.strip()

        # Set flags based on intent
        needs_ml = intent == "STRATEGIC_DECISION"
        needs_meta = intent in ["META_ANALYSIS", "COMPOSITION_QUESTION"]

        state["detected_intent"] = intent
        state["needs_ml_analysis"] = needs_ml
        state["needs_meta_analysis"] = needs_meta

        return state

    def _route_after_classification(self, state: TFTAgentState) -> str:
        """Route to appropriate node based on classification."""
        intent = state["detected_intent"]

        if intent == "STRATEGIC_DECISION":
            return "extract_game_state"
        elif intent in ["META_ANALYSIS", "COMPOSITION_QUESTION"]:
            return "meta_analysis"
        else:
            return "direct_response"

    def _extract_game_state(self, state: TFTAgentState) -> TFTAgentState:
        """Extract game state parameters from the conversation."""
        messages = state["messages"]
        last_message = messages[-1].content if messages else ""

        extraction_prompt = f"""
Extract TFT game state parameters from this message. If information is not provided, use reasonable defaults.

User message: "{last_message}"

Extract and return a JSON object with these parameters:
{{
    "current_placement": int (1-8, default: 4),
    "gold": int (default: 30),
    "health": int (default: 50),
    "level": int (1-10, default: 6),
    "round_number": int (default: 15),
    "stage": int (1-6, default: 3),
    "game_phase": "early" | "mid" | "late" (default: "mid"),
    "units_count": int (default: 6),
    "traits": {{}} (empty object if not specified)
}}

Only include parameters that are mentioned or can be reasonably inferred.
Return ONLY the JSON object, no other text.
"""

        # Get game state
        messages = [
            SystemMessage(content="You are a TFT game state extractor."),
            HumanMessage(content=extraction_prompt)
        ]
        response = self.llm.invoke(messages)

        try:
            game_state = json.loads(response.content)
        except json.JSONDecodeError:
            # Fallback to defaults
            game_state = {
                "current_placement": 4,
                "gold": 30,
                "health": 50,
                "level": 6,
                "round_number": 15,
                "stage": 3,
                "game_phase": "mid",
                "units_count": 6,
                "traits": {}
            }

        state["game_state"] = game_state
        return state

    def _run_ml_analysis(self, state: TFTAgentState) -> TFTAgentState:
        """Run ML analysis with extracted game state."""
        game_state = state["game_state"] or {}

        try:
            # Get ML recommendation
            ml_result = get_tft_recommendation(**game_state)
            state["tool_results"]["ml_analysis"] = ml_result
        except Exception as e:
            state["tool_results"]["ml_analysis"] = f"ML analysis failed: {str(e)}"

        return state

    def _run_meta_analysis(self, state: TFTAgentState) -> TFTAgentState:
        """Run meta analysis for tier lists and composition questions."""
        messages = state["messages"]
        last_message = messages[-1].content.lower() if messages else ""

        try:
            # Determine what type of meta analysis to run
            if any(keyword in last_message for keyword in ["tier", "best", "strongest", "top", "meta"]):
                # Get tier list
                tier_result = get_meta_tier_list(refresh_data=False)
                state["tool_results"]["tier_list"] = tier_result

            if any(keyword in last_message for keyword in ["trend", "rising", "popular", "changing"]):
                # Get meta trends
                trends_result = get_meta_trends(refresh_data=False)
                state["tool_results"]["meta_trends"] = trends_result

            # If no specific tools were triggered, get tier list as default
            if not state["tool_results"]:
                tier_result = get_meta_tier_list(refresh_data=False)
                state["tool_results"]["tier_list"] = tier_result

        except Exception as e:
            state["tool_results"]["meta_analysis"] = f"Meta analysis failed: {str(e)}"

        return state

    def _generate_response(self, state: TFTAgentState) -> TFTAgentState:
        """Generate the final response based on analysis results."""
        messages = state["messages"]
        intent = state["detected_intent"]
        tool_results = state["tool_results"]
        user_message = messages[-1].content if messages else ""

        # Build context for response generation
        context_parts = []

        if "ml_analysis" in tool_results:
            context_parts.append(f"ML Strategic Analysis:\n{tool_results['ml_analysis']}")

        if "tier_list" in tool_results:
            context_parts.append(f"Current Meta Tier List:\n{tool_results['tier_list']}")

        if "meta_trends" in tool_results:
            context_parts.append(f"Meta Trends:\n{tool_results['meta_trends']}")

        context = "\n\n".join(context_parts) if context_parts else "No tool analysis available."

        # Generate response
        response_prompt = f"""
You are an expert TFT coach providing helpful advice to players. The user asked: "{user_message}"

Their intent was classified as: {intent}

{context}

Provide a helpful, conversational response that:
1. Directly addresses their question
2. Uses the analysis results when available
3. Is engaging and friendly
4. Includes specific actionable advice
5. Uses appropriate TFT terminology

Keep the response concise but comprehensive (2-4 paragraphs max).
"""

        messages = [
            SystemMessage(content="You are an expert TFT coach providing helpful advice to players."),
            HumanMessage(content=response_prompt)
        ]
        response = self.llm.invoke(messages)

        # Add response to messages
        state["messages"].append(AIMessage(content=response.content))

        return state

    def _create_ml_recommendation_tool(self):
        """Create ML recommendation tool for LangGraph."""
        @tool
        def tft_ml_recommendation(
            current_placement: int = 4,
            gold: int = 30,
            health: int = 50,
            level: int = 6,
            round_number: int = 15,
            stage: int = 3,
            game_phase: str = "mid",
            units_count: int = 6
        ) -> str:
            """Get ML-based TFT strategic recommendations."""
            return get_tft_recommendation(
                current_placement=current_placement,
                gold=gold,
                health=health,
                level=level,
                round_number=round_number,
                stage=stage,
                game_phase=game_phase,
                units_count=units_count
            )

        return tft_ml_recommendation

    def _create_meta_analysis_tool(self):
        """Create meta analysis tool for LangGraph."""
        @tool
        def tft_meta_trends() -> str:
            """Get current TFT meta trends and analysis."""
            return get_meta_trends(refresh_data=False)

        return tft_meta_trends

    def _create_tier_list_tool(self):
        """Create tier list tool for LangGraph."""
        @tool
        def tft_tier_list() -> str:
            """Get current TFT composition tier list."""
            return get_meta_tier_list(refresh_data=False)

        return tft_tier_list

    def process_message(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """
        Process a user message through the agentic workflow.

        Args:
            user_message: User's input message
            conversation_history: Previous conversation context

        Returns:
            Agent's response
        """
        # Initialize state
        messages = []

        # Add conversation history
        if conversation_history:
            for msg in conversation_history:
                if msg.get("role") == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg.get("role") == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        # Add current message
        messages.append(HumanMessage(content=user_message))

        initial_state = TFTAgentState(
            messages=messages,
            conversation_context={
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message
            },
            detected_intent="",
            game_state=None,
            tool_results={},
            needs_ml_analysis=False,
            needs_meta_analysis=False
        )

        # Run the workflow
        result = self.graph.invoke(initial_state)

        # Extract response
        final_messages = result["messages"]
        if final_messages and isinstance(final_messages[-1], AIMessage):
            return final_messages[-1].content
        else:
            return "I'm sorry, I couldn't generate a proper response. Please try asking about TFT strategy or compositions."

    async def aprocess_message(self, user_message: str, conversation_history: List[Dict] = None) -> str:
        """
        Async version of process_message.

        Args:
            user_message: User's input message
            conversation_history: Previous conversation context

        Returns:
            Agent's response
        """
        # For now, delegate to sync version
        # In future, can be enhanced with async LLM calls
        return self.process_message(user_message, conversation_history)


# Convenience functions for easy usage
def create_tft_agent(provider: str = "anthropic", model: Optional[str] = None) -> TFTAgent:
    """Create a TFT agent with specified provider."""
    return TFTAgent(provider=provider, model=model)


def chat_with_tft_agent(message: str, provider: str = "anthropic") -> str:
    """Quick chat function with TFT agent."""
    agent = create_tft_agent(provider=provider)
    return agent.process_message(message)


if __name__ == "__main__":
    # Example usage
    agent = create_tft_agent("anthropic")

    # Test different types of conversations
    test_messages = [
        "I'm at 30 gold, level 6, placement 5, what should I do?",
        "What are the strongest compositions right now?",
        "Is Star Guardian good in the current meta?",
        "I love playing TFT, it's so much fun!"
    ]

    print("🤖 TFT Agent Test")
    print("=" * 40)

    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. User: {message}")
        response = agent.process_message(message)
        print(f"   Agent: {response[:200]}..." if len(response) > 200 else f"   Agent: {response}")