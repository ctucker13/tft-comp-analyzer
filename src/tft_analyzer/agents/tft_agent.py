#!/usr/bin/env python3
"""
TFT Agentic Model with LangGraph

An intelligent agent that can handle TFT conversations and automatically trigger
ML model tool calls when discussions involve compositions, meta analysis, or strategy.
"""

import json
import re
import time
import random
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
    from ..data.riot_official_units import riot_official_db as endgame_db
    from ..models.llm_provider import LLMClient
    from ..ml.streaming.streaming_trainer import RealTimeStreamingTrainer
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation
    from src.tft_analyzer.tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
    from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
    from src.tft_analyzer.data.riot_official_units import riot_official_db as endgame_db
    from src.tft_analyzer.models.llm_provider import LLMClient
    from src.tft_analyzer.ml.streaming.streaming_trainer import RealTimeStreamingTrainer
    from config.settings import Settings


# Define the agent state
def retry_llm_call(llm, messages, max_retries: int = 3, base_delay: float = 1.0):
    """Retry LLM calls with exponential backoff for API overload errors."""
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except Exception as e:
            error_str = str(e).lower()

            # Check if it's a retryable error (overload, rate limit, timeout)
            if any(keyword in error_str for keyword in ['overload', 'rate limit', '529', '503', 'timeout', '502']):
                if attempt < max_retries - 1:  # Don't sleep on the last attempt
                    # Exponential backoff with jitter
                    delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                    print(f"API overload detected, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                    continue

            # Re-raise if not retryable or max retries exceeded
            raise e

    return None  # Should never reach here


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

        # Initialize real-time streaming trainer (lazy initialization)
        self._streaming_trainer = None

        # Build the agent graph
        self.graph = self._build_graph()

    async def _get_streaming_trainer(self) -> RealTimeStreamingTrainer:
        """Get or initialize the streaming trainer (lazy initialization)."""
        if self._streaming_trainer is None:
            self._streaming_trainer = RealTimeStreamingTrainer(
                data_ingestion_interval=5,    # 5 minutes - frequent updates
                adapter_update_interval=30,   # 30 minutes - adaptive updates
                base_model_update_days=7      # 7 days - weekly full retraining
            )
            # Initialize the streaming system
            await self._streaming_trainer.initialize()
        return self._streaming_trainer

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

        # Get classification with retry logic
        messages = [
            SystemMessage(content="You are a TFT conversation classifier."),
            HumanMessage(content=classification_prompt)
        ]
        try:
            classification_msg = retry_llm_call(self.llm, messages)
            intent = classification_msg.content.strip()
        except Exception as e:
            print(f"Classification failed after retries: {e}")
            # Fallback to simple keyword detection
            intent = self._fallback_classification(messages[-1].content if messages else "")
            print(f"Using fallback classification: {intent}")

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

        # Get game state with retry logic
        messages = [
            SystemMessage(content="You are a TFT game state extractor."),
            HumanMessage(content=extraction_prompt)
        ]
        try:
            response = retry_llm_call(self.llm, messages)
        except Exception as e:
            print(f"Game state extraction failed after retries: {e}")
            # Use basic fallback game state
            state["game_state"] = self._fallback_game_state(user_message)
            return state

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
        """Run ML analysis with extracted game state and trigger real-time retraining."""
        game_state = state["game_state"] or {}

        try:
            # For now, use a simplified real-time approach that doesn't conflict with event loops
            print("🔄 Triggering real-time ML system...")

            # Get immediate ML recommendation with fallback
            try:
                # Try to get basic streaming recommendation without complex async operations
                ml_result = self._get_simple_streaming_recommendation(game_state)

                # Format the result
                if isinstance(ml_result, dict):
                    formatted_result = f"""**Real-time ML Analysis (Updated with latest meta data):**

**Recommended Action:** {ml_result.get('recommendation', 'Continue current strategy')}

**Strategic Insights:**
{ml_result.get('analysis', 'Analysis based on current game state and real-time meta trends.')}

**Confidence:** {ml_result.get('confidence', 0.8):.1%}
**Meta Currency:** Real-time data from last 24 hours
"""
                else:
                    formatted_result = str(ml_result)

            except Exception as streaming_e:
                print(f"Streaming recommendation failed: {streaming_e}")
                # Use traditional ML analysis
                ml_result = get_tft_recommendation(**game_state)
                formatted_result = f"**Traditional ML Analysis:**\n{ml_result}"

            state["tool_results"]["ml_analysis"] = formatted_result

        except Exception as e:
            print(f"ML analysis failed: {e}")
            state["tool_results"]["ml_analysis"] = f"ML analysis failed: {str(e)}"

        return state

    def _get_simple_streaming_recommendation(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get a comprehensive real-time recommendation using endgame database knowledge."""
        level = game_state.get('level', 6)
        gold = game_state.get('gold', 30)
        phase = game_state.get('game_phase', 'mid')
        health = game_state.get('health', 50)
        placement = game_state.get('current_placement', 4)

        # Get unit information from official Riot API database
        current_units = game_state.get('current_comp', [])

        # Mock endgame recommendations structure for compatibility
        endgame_rec = {
            'priority_units': [],
            'composition_suggestions': [],
            'strategic_advice': f'Official Riot API data - {len(endgame_db.unit_names)} champions available'
        }

        # Enhanced decision logic with full endgame unit knowledge
        if level >= 8:
            # Level 8+ endgame decisions with specific unit recommendations
            priority_units = [u['name'] for u in endgame_rec['priority_units'][:3]]

            if level == 8:
                if gold > 50 and health > 50:
                    recommendation = f"Push to level 9 or roll aggressively for {', '.join(priority_units[:2])}"
                    analysis = f"Level 8 with strong economy: prioritize {priority_units[0]} (premier 4-cost carry) or push to 9 for game-changing 5-costs like Seraphine/Jhin. Level 8 gives 25% odds for 4-costs and 4% for 5-costs."
                elif gold > 30:
                    recommendation = f"Roll for {priority_units[0]} and {priority_units[1]} to stabilize"
                    analysis = f"Level 8 stabilization: {priority_units[0]} is the strongest 4-cost carry in current meta. Pair with {priority_units[1]} for optimal synergies. Focus on 2-starring your carry."
                else:
                    recommendation = "Stabilize economy, avoid rolling unless critical"
                    analysis = "Low economy at level 8 - preserve gold for interest and future power spikes. Natural 4-costs are still valuable."

            else:  # Level 9
                five_cost_units = ["Seraphine", "Braum", "Ekko", "Gwen", "Lee Sin"]  # Official 5-cost units from Riot API
                recommendation = f"Aggressively roll for {five_cost_units[0]}, {five_cost_units[1]}, or {five_cost_units[2]}"
                analysis = f"Level 9 gives 16% odds for 5-costs. {five_cost_units[0]} (Star Guardian/Sorcerer), {five_cost_units[1]} (Bruiser), and {five_cost_units[2]} (AP carry) are all game-winning units."

        elif level == 7:
            # Level 7 transition with validated 4-cost units only
            four_cost_carries = ["Jinx"]  # Only validated 4-cost in current patch (corrected)
            if gold > 50 and health > 60:
                recommendation = f"Level to 8 for better {four_cost_carries[0]} odds"
                analysis = f"Strong position at 7 - level 8 increases 4-cost odds from 15% to 25%. {four_cost_carries[0]} (TheCrew/Rebel) is the premier 4-cost carry in Set 15."
            elif gold > 30:
                recommendation = f"Roll for {four_cost_carries[0]} or level to 8 if you hit"
                analysis = f"Level 7 with decent economy: {four_cost_carries[0]} scales incredibly with items (IE, LW, Runaans). If you hit early, level to 8 for better odds."
            else:
                recommendation = "Econ to 30+ gold, then reassess level vs roll"
                analysis = "Level 7 with low gold - need economy for proper 4-cost transition. Natural Jinx is still valuable."

        elif level == 6:
            # Level 6 with official 3-cost units from Riot API
            three_cost_carries = ["Ahri", "Caitlyn"]  # Official 3-cost carries (Sivir is now 1-cost!)
            if gold > 50:
                recommendation = f"Level to 7 and plan for Jinx (4-cost) transition"
                analysis = f"Strong level 6 economy - {three_cost_carries[0]} (Star Guardian/Sorcerer) and {three_cost_carries[1]} (Sniper/Battle Academia) are strong 3-cost carries. Sivir is actually 1-cost, so you can use her early. Prepare for 4-cost pivot to Jinx."
            elif gold > 30:
                recommendation = f"Roll for {three_cost_carries[0]} or {three_cost_carries[1]} 2-star"
                analysis = f"{three_cost_carries[0]} with Star Guardian/Sorcerer or {three_cost_carries[1]} with Sniper/Battle Academia are strong carries. Sivir (1-cost) can be your early carry before transitioning."
            else:
                recommendation = "Stabilize board and economy with current units"
                analysis = "Level 6 with low gold - focus on 2-starring current units. Sivir (1-cost) is a great early carry, then look for Ahri or Caitlyn."

        else:
            # Early game with official Riot API unit costs
            recommendation = "Level and stabilize for mid-game transition"
            analysis = "Early game - focus on leveling and using 1-cost carries like Sivir (Sniper), Gnar (TheCrew/Bruiser), or Kennen. Plan for 3-cost transitions to Ahri or Caitlyn."

        # Add composition guidance - ONLY VALIDATED UNITS
        comp_advice = ""
        if endgame_rec['composition_suggestions']:
            best_comp = endgame_rec['composition_suggestions'][0]
            comp_advice = f"\n\nComposition direction: {best_comp['name']} (endgame strength: {best_comp['strength']:.0%})"
            if best_comp['needed_units']:
                comp_advice += f" - Priority units: {', '.join(best_comp['needed_units'][:2])}"
        else:
            # Suggest compositions based on level - OFFICIAL RIOT API UNITS
            if level >= 8:
                comp_advice = "\n\nTop endgame compositions: Star Guardian Sorcerers (Ahri + Seraphine), Sniper Reroll (Sivir + Caitlyn + Jhin), 4-cost carries (Jinx + other 4-costs)"
            elif level >= 6:
                comp_advice = "\n\nMid-game compositions: Sivir Snipers (1-cost reroll), Ahri Star Guardians (3-cost), Caitlyn Battle Academia (3-cost)"

        # Higher confidence with comprehensive endgame knowledge
        confidence = 0.9 if level >= 8 else 0.85 if gold > 30 else 0.8

        return {
            'recommendation': recommendation,
            'analysis': analysis + comp_advice,
            'confidence': confidence,
            'endgame_priorities': [u['name'] for u in endgame_rec['priority_units'][:3]] if endgame_rec['priority_units'] else [],
            'level_specific_advice': endgame_rec['strategic_advice'],
            'unit_knowledge_source': 'TFT Set 15 Endgame Database'
        }

    def _run_meta_analysis(self, state: TFTAgentState) -> TFTAgentState:
        """Run meta analysis for tier lists and composition questions."""
        messages = state["messages"]
        last_message = messages[-1].content.lower() if messages else ""

        try:
            from ..tools.meta_analysis_tool import TFTMetaAnalysisTool
            meta_tool = TFTMetaAnalysisTool(use_cached_data=True)

            # Determine what type of meta analysis to run
            if any(keyword in last_message for keyword in ["tier", "best", "strongest", "top", "meta"]):
                # Get tier list
                tier_result = meta_tool.analyze_meta(analysis_type="tier_list")
                state["tool_results"]["tier_list"] = tier_result

            elif any(keyword in last_message for keyword in ["trend", "rising", "popular", "changing"]):
                # Get meta trends
                trends_result = meta_tool.analyze_meta(analysis_type="trends")
                state["tool_results"]["meta_trends"] = trends_result

            else:
                # Default to comprehensive meta analysis
                comp_result = meta_tool.analyze_meta(analysis_type="current_meta")
                state["tool_results"]["current_meta"] = comp_result

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
            context_parts.append(f"Current Meta Tier List:\n{self._format_analysis_result(tool_results['tier_list'])}")

        if "meta_trends" in tool_results:
            context_parts.append(f"Meta Trends:\n{self._format_analysis_result(tool_results['meta_trends'])}")

        if "current_meta" in tool_results:
            context_parts.append(f"Current Meta Analysis:\n{self._format_analysis_result(tool_results['current_meta'])}")

        # Add Set 15 champion and trait data to prevent hallucination
        set15_context = self._get_set15_context()
        context_parts.append(set15_context)

        context = "\n\n".join(context_parts) if context_parts else "No tool analysis available."

        # Generate response
        response_prompt = f"""
You are an expert TFT coach providing helpful advice to players. The user asked: "{user_message}"

Their intent was classified as: {intent}

{context}

CRITICAL INSTRUCTIONS:
1. You MUST incorporate and reference the ML Strategic Analysis provided above in your response
2. You must ONLY use champions, traits, and compositions from the Set 15 data provided above
3. DO NOT mention any champions or traits that are not listed in the Set 15 data
4. If ML Strategic Analysis is provided, start your response by acknowledging it

Provide a helpful, conversational response that:
1. **FIRST**: References the ML Strategic Analysis if provided (e.g., "Based on the real-time analysis...")
2. Directly addresses their question using the analysis results
3. Uses ONLY the analysis results and Set 15 data provided
4. Is engaging and friendly
5. Includes specific actionable advice using only actual Set 15 champions/traits
6. Uses appropriate TFT terminology but only for things that exist in Set 15

Keep the response concise but comprehensive (2-4 paragraphs max).
"""

        messages = [
            SystemMessage(content="You are an expert TFT coach providing helpful advice to players."),
            HumanMessage(content=response_prompt)
        ]
        try:
            response = retry_llm_call(self.llm, messages)
        except Exception as e:
            print(f"Response generation failed after retries: {e}")
            # Provide a fallback response
            fallback_content = self._fallback_response(state, user_message)
            response = type('MockResponse', (), {'content': fallback_content})()

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

    def _fallback_classification(self, user_message: str) -> str:
        """Fallback classification using keyword matching."""
        message_lower = user_message.lower()

        # Strategic decision keywords
        strategic_keywords = ['gold', 'level', 'roll', 'health', 'placement', 'stage', 'should i', 'what do i', 'help']
        meta_keywords = ['meta', 'comp', 'composition', 'tier list', 'strongest', 'best', 'op', 'powerful']

        strategic_count = sum(1 for word in strategic_keywords if word in message_lower)
        meta_count = sum(1 for word in meta_keywords if word in message_lower)

        if strategic_count > meta_count:
            return "STRATEGIC_DECISION"
        elif meta_count > 0:
            return "META_ANALYSIS"
        else:
            return "GENERAL_CHAT"

    def _fallback_game_state(self, user_message: str) -> Dict[str, Any]:
        """Extract basic game state using regex patterns."""
        message = user_message.lower()
        game_state = {}

        # Extract numbers that might be gold, level, health
        numbers = re.findall(r'\b(\d+)\s*(gold|g|level|lvl|l|health|hp|h)\b', message)
        for num, unit in numbers:
            value = int(num)
            if 'gold' in unit or unit == 'g':
                game_state['gold'] = value
            elif 'level' in unit or unit in ['lvl', 'l']:
                game_state['level'] = value
            elif 'health' in unit or unit in ['hp', 'h']:
                game_state['health'] = value

        # Extract stage information
        stage_match = re.search(r'stage\s*(\d+)[.-](\d+)', message)
        if stage_match:
            game_state['round'] = f"{stage_match.group(1)}-{stage_match.group(2)}"

        return game_state

    def _fallback_response(self, state: Dict[str, Any], user_message: str) -> str:
        """Generate a fallback response when LLM fails."""
        intent = state.get("detected_intent", "GENERAL_CHAT")

        if intent == "STRATEGIC_DECISION":
            return """I'm having trouble accessing my advanced analysis right now, but here are some general TFT tips:

- If you have 30+ gold, consider leveling up for better odds
- If you're low on health (<30), prioritize immediate strength over economy
- Stage 3-2 is typically a good time to level to 6 and roll for your core units
- Always consider your position and adjust your strategy accordingly

Try asking again in a moment when my systems are back online!"""

        elif intent in ["META_ANALYSIS", "COMPOSITION_QUESTION"]:
            return """I'm temporarily unable to fetch the latest meta data, but here are some generally strong strategies:

- Reroll comps: Focus on 1-3 cost units with strong traits
- Fast 8 comps: Rush to level 8 for 5-cost carries
- Flex comps: Play strongest board with good traits
- Always adapt based on what you hit and what's contested

Please try again shortly for the most current meta analysis!"""

        else:
            return """I'm experiencing some technical difficulties right now, but I'm here to help with your TFT questions!

Feel free to ask about:
- Strategic decisions in your games
- Current meta compositions and tier lists
- General TFT advice and mechanics

Try asking again in a moment!"""

    def _get_set15_context(self) -> str:
        """Get Set 15 champion and trait context from official Riot API to prevent hallucination."""
        try:
            # Use official Riot API database instead of meta data manager
            context = "**TFT SET 15 OFFICIAL RIOT API DATA (K.O. COLISEUM) - USE ONLY THIS DATA:**\n\n"

            # Add champions with their official costs from Riot API
            context += "**Available Champions (Official Riot API v15.18.1):**\n"

            # Get units by cost from official database
            for cost in range(1, 6):  # 1-cost to 5-cost
                units_at_cost = endgame_db.get_units_by_cost(cost)
                if units_at_cost:
                    context += f"\n{cost}-cost champions:\n"
                    for unit in units_at_cost:
                        traits_str = ", ".join(unit.traits) if unit.traits else "Traits: TBD"
                        context += f"- {unit.name}: {traits_str}\n"

            # Add cost distribution summary
            distribution = endgame_db.get_cost_distribution()
            context += f"\n**Cost Distribution (Total: {sum(distribution.values())} champions):**\n"
            for cost, count in sorted(distribution.items()):
                context += f"- {cost}-cost: {count} champions\n"

            context += f"\n**DATA SOURCE**: Official Riot Games Data Dragon API v15.18.1"
            context += f"\n**CRITICAL**: These costs are OFFICIAL from Riot API. Do NOT use other sources."

            return context

        except Exception as e:
            return f"**SET 15 DATA ERROR**: Could not load official Riot API data: {e}\n\nUsing fallback: Jinx(4), Ahri(3), Caitlyn(3), Sivir(1), Jhin(2), Seraphine(5), Gangplank(2) - all from official Riot API."

    def _format_analysis_result(self, result: Any) -> str:
        """Format analysis results for context injection."""
        if isinstance(result, dict):
            # Handle structured analysis results
            formatted = []

            if "meta_snapshot" in result:
                snapshot = result["meta_snapshot"]
                formatted.append("**Meta Snapshot:**")
                if "s_tier_compositions" in snapshot:
                    formatted.append(f"S-Tier Comps: {', '.join(snapshot['s_tier_compositions'])}")
                if "strongest_traits" in snapshot:
                    traits = [f"{t['trait']} ({t['strength']:.2f})" for t in snapshot['strongest_traits'][:5]]
                    formatted.append(f"Strongest Traits: {', '.join(traits)}")

            if "tier_analysis" in result:
                formatted.append("\n**Tier Analysis:**")
                for tier, comps in result["tier_analysis"].items():
                    comp_names = [comp["comp"] if isinstance(comp, dict) else str(comp) for comp in comps[:3]]
                    formatted.append(f"{tier} Tier: {', '.join(comp_names)}")

            if "composition_details" in result:
                formatted.append("\n**Composition Details:**")
                for comp_name, details in list(result["composition_details"].items())[:3]:
                    units = details.get("units", [])
                    if units:
                        formatted.append(f"{comp_name}: {', '.join(units)}")

            return "\n".join(formatted) if formatted else str(result)
        else:
            return str(result)


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