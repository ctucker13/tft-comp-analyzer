#!/usr/bin/env python3
"""
TFT ML Chat Interface

Provides a conversational interface for getting ML-based TFT recommendations.
Users can describe their game state in natural language and get strategic advice.
"""

import re
from typing import Dict, Optional, Any
from ..tools.ml_recommendation_tool import get_tft_recommendation
from ..tools.meta_analysis_tool import get_meta_tier_list, get_meta_trends
from ..models.llm_provider import LLMClient

try:
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from config.settings import Settings


class TFTMLChatInterface:
    """Conversational interface for TFT ML recommendations."""

    def __init__(self):
        self.default_params = {
            'current_placement': 4,
            'gold': 30,
            'health': 50,
            'level': 6,
            'round_number': 15,
            'stage': 3,
            'traits': {},
            'units_count': 6,
            'game_phase': 'mid'
        }

        # Initialize LLM client
        try:
            self.settings = Settings()
            api_key = self.settings.get_api_key_for_provider(self.settings.llm_provider)
            model = self.settings.get_model_for_provider(self.settings.llm_provider)
            self.llm_client = LLMClient(
                provider=self.settings.llm_provider,
                model=model,
                api_key=api_key
            )
        except Exception as e:
            print(f"Warning: Could not initialize LLM client: {e}")
            self.llm_client = None

    def process_query(self, user_input: str) -> str:
        """
        Process a natural language query about TFT strategy using LLM + ML models.

        Args:
            user_input: User's description of their game state or question

        Returns:
            Conversational response with ML-based recommendations
        """
        if not self.llm_client:
            # Fallback to original rule-based processing
            return self._process_query_fallback(user_input)

        # Use LLM to understand the query and get ML recommendations
        return self._process_query_with_llm(user_input)

    def _process_query_with_llm(self, user_input: str) -> str:
        """Process query using LLM for conversation handling + ML for recommendations."""
        try:
            # First, determine query type and extract parameters using LLM
            analysis_prompt = f"""
You are analyzing a TFT (Teamfight Tactics) player's query to determine:
1. Is this a meta analysis query (asking about tier lists, best comps, what's strong in the meta)?
2. If not, extract game state parameters for strategic decision making

User query: "{user_input}"

Please respond in JSON format:
{{
    "query_type": "meta" or "strategy",
    "extracted_params": {{
        "current_placement": number (1-8, default 4),
        "gold": number (default 30),
        "health": number (default 50),
        "level": number (1-10, default 6),
        "round_number": number (default 15),
        "stage": number (1-6, default 3),
        "game_phase": "early" or "mid" or "late" (default "mid"),
        "units_count": number (default 6)
    }},
    "user_intent": "Brief description of what the user is asking"
}}

Only include parameters that are explicitly mentioned or can be clearly inferred from the query.
"""

            # Get LLM analysis
            analysis_response = self.llm_client.generate_response(analysis_prompt)

            try:
                import json
                analysis = json.loads(analysis_response)
                query_type = analysis.get("query_type", "strategy")
                extracted_params = analysis.get("extracted_params", {})
                user_intent = analysis.get("user_intent", "Strategic advice")
            except (json.JSONDecodeError, KeyError) as e:
                # Fallback to rule-based parsing
                return self._process_query_fallback(user_input)

            # Get the appropriate ML recommendation
            if query_type == "meta":
                ml_result = self._handle_meta_query(user_input.lower())
            else:
                # Merge with defaults and get ML recommendation
                final_params = {**self.default_params, **extracted_params}
                ml_result = get_tft_recommendation(**final_params)

            # Use LLM to create a conversational response
            conversation_prompt = f"""
You are a friendly, expert TFT coach having a conversation with a player. They asked: "{user_input}"

Their intent: {user_intent}

Here's the ML analysis result:
{ml_result}

Please create a conversational, well-formatted response that:

**FORMATTING REQUIREMENTS:**
- Use clear section headers with emojis (🎯, 📈, 🛡️, ⚔️, 💡)
- Use bullet points and numbered lists for better readability
- Use **bold text** for key recommendations and important stats
- Use proper spacing between sections
- Structure information in logical blocks
- Make numbers and percentages stand out

**CONTENT REQUIREMENTS:**
1. Acknowledge their specific question warmly
2. Present the main recommendation clearly with reasoning
3. Break down complex advice into digestible sections
4. Include specific details like:
   - **Complete unit lineup** (all 8 units when applicable)
   - **Optimal items** for each carry
   - **Positioning guidelines**
   - **Power Up recommendations** for key units
   - **Economic advice** (when to level, roll, save)
5. Provide actionable next steps
6. Keep it comprehensive but well-organized

Make it feel like advice from an expert coach who cares about clear communication and helping you succeed.
"""

            # Get conversational response
            final_response = self.llm_client.generate_response(conversation_prompt)
            return final_response

        except Exception as e:
            # Fallback to original processing on any error
            return self._process_query_fallback(user_input)

    def _process_query_fallback(self, user_input: str) -> str:
        """Original rule-based query processing as fallback."""
        user_lower = user_input.lower()

        # Check if this is a meta analysis query
        if self._is_meta_query(user_lower):
            return self._handle_meta_query(user_lower)

        # Otherwise, handle as strategic decision query
        params = self._parse_game_state(user_input)
        final_params = {**self.default_params, **params}

        return get_tft_recommendation(**final_params)

    def _parse_game_state(self, text: str) -> Dict[str, Any]:
        """Extract game state parameters from natural language text."""
        params = {}
        text_lower = text.lower()

        # Parse placement
        placement_match = re.search(r'(?:placement|place|position|rank)(?:\s+is)?\s+(\d+)', text_lower)
        if placement_match:
            params['current_placement'] = int(placement_match.group(1))

        # Parse gold
        gold_match = re.search(r'(\d+)\s*gold|gold(?:\s+is)?\s*(\d+)', text_lower)
        if gold_match:
            params['gold'] = int(gold_match.group(1) or gold_match.group(2))

        # Parse health
        health_match = re.search(r'(\d+)\s*(?:hp|health)|(?:hp|health)(?:\s+is)?\s*(\d+)', text_lower)
        if health_match:
            params['health'] = int(health_match.group(1) or health_match.group(2))

        # Parse level
        level_match = re.search(r'level\s*(\d+)|(\d+)\s*level', text_lower)
        if level_match:
            params['level'] = int(level_match.group(1) or level_match.group(2))

        # Parse round/stage
        round_match = re.search(r'round\s*(\d+)', text_lower)
        if round_match:
            params['round_number'] = int(round_match.group(1))

        stage_match = re.search(r'stage\s*(\d+)', text_lower)
        if stage_match:
            params['stage'] = int(stage_match.group(1))

        # Parse game phase
        if any(word in text_lower for word in ['early', 'start', 'beginning']):
            params['game_phase'] = 'early'
        elif any(word in text_lower for word in ['late', 'end', 'final']):
            params['game_phase'] = 'late'
        elif any(word in text_lower for word in ['mid', 'middle']):
            params['game_phase'] = 'mid'

        # Parse units count
        units_match = re.search(r'(\d+)\s*units|units(?:\s+is)?\s*(\d+)', text_lower)
        if units_match:
            params['units_count'] = int(units_match.group(1) or units_match.group(2))

        # Parse traits (simple detection)
        traits = {}
        trait_keywords = {
            'reroll': ['reroll', 're-roll', 'roll down'],
            'fast_8': ['fast 8', 'fast eight', 'fast-8', 'level 8'],
            'flex': ['flex', 'flexible', 'pivot'],
            'slow_roll': ['slow roll', 'slow-roll', 'slowroll'],
            'vertical': ['vertical', 'vert'],
            'hyper_roll': ['hyper roll', 'hyperroll', 'hyper-roll']
        }

        for trait, keywords in trait_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    traits[trait] = 1
                    break

        if traits:
            params['traits'] = traits

        return params

    def _is_meta_query(self, text: str) -> bool:
        """Check if the query is asking for meta analysis."""
        meta_keywords = [
            'meta', 'tier list', 'what\'s good', 'best comp', 'strongest',
            'trending', 'popular', 'op comp', 'what to play', 'tier',
            'meta comps', 'current meta', 'patch meta', 'what\'s strong'
        ]
        return any(keyword in text for keyword in meta_keywords)

    def _handle_meta_query(self, text: str) -> str:
        """Handle meta analysis queries."""
        # Determine type of meta query
        if any(word in text for word in ['trend', 'rising', 'falling', 'changing']):
            return self._get_meta_trends_response()
        elif any(word in text for word in ['tier', 'best', 'strongest', 'op', 'good']):
            return self._get_tier_list_response()
        else:
            # Default to tier list for general meta queries
            return self._get_tier_list_response()

    def _get_tier_list_response(self) -> str:
        """Get tier list response."""
        try:
            return get_meta_tier_list(refresh_data=False)
        except Exception as e:
            return f"❌ Unable to get tier list: {str(e)}\n\nTry asking about your specific game state instead!"

    def _get_meta_trends_response(self) -> str:
        """Get meta trends response."""
        try:
            return get_meta_trends(refresh_data=False)
        except Exception as e:
            return f"❌ Unable to get meta trends: {str(e)}\n\nTry asking about your specific game state instead!"

    def get_example_queries(self) -> list[str]:
        """Get example queries users can try."""
        return [
            # Strategic decision queries
            "I'm at 30 gold, 45 health, level 6, placement 5, what should I do?",
            "Stage 3, 25 gold, need to pivot from my current comp",
            "Late game, 15 health, level 8, should I reroll or go fast 8?",
            "Early game with 50 gold, when should I level?",
            "I'm in 7th place with low health, help me stabilize",
            # Meta analysis queries
            "What's the current meta tier list?",
            "What comps are trending right now?",
            "What are the best comps to play?",
            "Show me the strongest compositions",
            "What's the current patch meta?"
        ]


def chat_with_tft_ml(query: str) -> str:
    """
    Chat interface for TFT ML recommendations.

    Ask questions about your TFT game state in natural language and get
    ML-powered strategic advice.

    Args:
        query: Your question or description of the game state

    Returns:
        Strategic recommendation based on ML analysis
    """
    interface = TFTMLChatInterface()
    return interface.process_query(query)


if __name__ == "__main__":
    # Interactive testing
    interface = TFTMLChatInterface()

    print("🎯 TFT ML Chat Interface")
    print("Describe your game state and get ML-powered recommendations!\n")

    print("Example queries:")
    for example in interface.get_example_queries():
        print(f"• {example}")

    print("\nTry it out:")

    while True:
        try:
            user_input = input("\n> ").strip()
            if user_input.lower() in ['quit', 'exit', 'q']:
                break

            if not user_input:
                print("Please describe your game state or ask a question.")
                continue

            response = interface.process_query(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")