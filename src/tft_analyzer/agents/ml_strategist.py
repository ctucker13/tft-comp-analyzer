"""
ML-Powered TFT Strategist Agent
Combines ML predictions with LLM explanations and reasoning
"""

from typing import Dict, List, Optional, Any
import asyncio
import json
from datetime import datetime

from ..ml.inference.engine import TFTInferenceEngine, TFTRecommendationGenerator
from ..ml.data.schemas import TFTGameState, TFTRecommendationEngine
from ..models.llm_provider import LLMClient
from ..data.riot_api import RiotTFTAPI


class GameStateParser:
    """Parses game state from various input formats"""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    async def parse_from_description(self, description: str) -> Optional[TFTGameState]:
        """Parse game state from natural language description"""
        prompt = f"""
        Parse this TFT game description into structured data.

        Description: {description}

        Extract and return in JSON format:
        {{
            "round": <current round number>,
            "level": <player level 1-9>,
            "gold": <current gold amount>,
            "health": <current health 0-100>,
            "win_streak": <win streak count>,
            "loss_streak": <loss streak count>,
            "board": [
                {{
                    "character_id": "<champion name>",
                    "tier": <star level 1-3>,
                    "position": {{"x": <0-6>, "y": <0-3>}},
                    "items": ["<item names>"],
                    "cost": <champion cost>
                }}
            ],
            "bench": ["<champion names on bench>"],
            "shop": ["<champions in shop>"],
            "phase": "<early/mid/late>"
        }}

        If information is not provided, use reasonable defaults.
        Only respond with valid JSON.
        """

        try:
            response = await self.llm.generate([
                {"role": "system", "content": "You are a TFT game state parser. Respond only with valid JSON."},
                {"role": "user", "content": prompt}
            ])

            # Parse JSON response
            game_data = json.loads(response.strip())

            # Convert to TFTGameState object
            return self._convert_to_game_state(game_data)

        except Exception as e:
            print(f"❌ Error parsing game state: {e}")
            return None

    def _convert_to_game_state(self, data: Dict) -> TFTGameState:
        """Convert parsed data to TFTGameState object"""
        from ..ml.data.schemas import ChampionState, Position, GamePhase

        # Convert board data
        board = []
        for champion_data in data.get("board", []):
            pos_data = champion_data.get("position", {"x": 0, "y": 0})
            position = Position(x=pos_data["x"], y=pos_data["y"])

            champion = ChampionState(
                character_id=champion_data["character_id"],
                tier=champion_data["tier"],
                position=position,
                items=champion_data.get("items", []),
                cost=champion_data.get("cost", 1)
            )
            board.append(champion)

        # Convert phase
        phase_str = data.get("phase", "mid").lower()
        if phase_str == "early":
            phase = GamePhase.EARLY
        elif phase_str == "late":
            phase = GamePhase.LATE
        else:
            phase = GamePhase.MID

        return TFTGameState(
            match_id="user_input",
            puuid="user",
            round=data.get("round", 10),
            timestamp=datetime.now(),
            level=data.get("level", 5),
            experience=0,
            gold=data.get("gold", 20),
            health=data.get("health", 60),
            win_streak=data.get("win_streak", 0),
            loss_streak=data.get("loss_streak", 0),
            board=board,
            bench=data.get("bench", []),
            shop=data.get("shop", []),
            phase=phase
        )


class MLStrategistAgent:
    """
    Advanced TFT strategist that combines ML predictions with LLM reasoning
    """

    def __init__(
        self,
        inference_engine: TFTInferenceEngine,
        llm_client: LLMClient,
        riot_api: Optional[RiotTFTAPI] = None
    ):
        self.inference_engine = inference_engine
        self.llm = llm_client
        self.riot_api = riot_api

        self.recommendation_generator = TFTRecommendationGenerator(inference_engine)
        self.game_state_parser = GameStateParser(llm_client)

        # Conversation memory
        self.conversation_history = []

    async def handle_strategy_query(
        self,
        user_input: str,
        game_state: Optional[TFTGameState] = None
    ) -> Dict[str, Any]:
        """
        Handle user queries about TFT strategy

        Args:
            user_input: User's question or request
            game_state: Optional current game state

        Returns:
            Comprehensive response with ML predictions and explanations
        """
        # Parse intent and extract game state if needed
        if game_state is None:
            game_state = await self._extract_game_state_from_input(user_input)

        if game_state is None:
            return await self._handle_general_query(user_input)

        # Get ML recommendations
        recommendations = await self.recommendation_generator.generate_recommendations(game_state)

        # Generate contextual explanation using LLM
        explanation = await self._generate_contextual_explanation(
            user_input, game_state, recommendations
        )

        # Create response
        response = {
            "type": "strategy_recommendation",
            "ml_predictions": recommendations.ml_predictions.dict(),
            "scenarios": [s.dict() for s in recommendations.scenarios],
            "primary_recommendation": recommendations.primary_recommendation,
            "explanation": explanation,
            "key_insights": recommendations.key_insights,
            "confidence": recommendations.ml_predictions.confidence,
            "game_state": game_state.dict()
        }

        # Update conversation history
        self._update_conversation_history(user_input, response)

        return response

    async def _extract_game_state_from_input(self, user_input: str) -> Optional[TFTGameState]:
        """Extract game state from user input if present"""
        # Check if user input contains game state information
        game_state_indicators = [
            "round", "level", "gold", "health", "board", "shop",
            "I have", "my board", "currently", "game state"
        ]

        if any(indicator in user_input.lower() for indicator in game_state_indicators):
            return await self.game_state_parser.parse_from_description(user_input)

        return None

    async def _handle_general_query(self, user_input: str) -> Dict[str, Any]:
        """Handle general TFT questions without specific game state"""

        # Check if this is a meta/strategy question
        if await self._is_meta_query(user_input):
            # Get recent meta analysis if available
            meta_context = await self._get_meta_context()

            prompt = f"""
            Answer this TFT strategy question using your knowledge of Set 15: K.O. Coliseum.

            User Question: {user_input}

            {meta_context}

            Provide a comprehensive answer covering:
            1. Direct answer to the question
            2. Strategic context and reasoning
            3. Specific examples from Set 15
            4. Alternative approaches if applicable

            Be specific about champion names, trait synergies, and positioning.
            """
        else:
            prompt = f"""
            Answer this TFT question: {user_input}

            Focus on Set 15: K.O. Coliseum mechanics, champions, and strategies.
            Provide clear, actionable advice.
            """

        explanation = await self.llm.generate([
            {"role": "system", "content": "You are an expert TFT strategist specializing in Set 15. Provide detailed, accurate advice."},
            {"role": "user", "content": prompt}
        ])

        return {
            "type": "general_advice",
            "explanation": explanation,
            "requires_game_state": False
        }

    async def _is_meta_query(self, user_input: str) -> bool:
        """Check if query is about meta/strategy"""
        meta_keywords = [
            "meta", "comp", "build", "strategy", "best", "tier list",
            "strong", "op", "optimal", "should i", "what comp",
            "reroll", "fast 8", "leveling", "positioning"
        ]

        return any(keyword in user_input.lower() for keyword in meta_keywords)

    async def _get_meta_context(self) -> str:
        """Get recent meta analysis context"""
        # This would integrate with your existing meta analysis
        # For now, return a placeholder
        return """
        Recent Set 15 Meta Context:
        - Power Snax system creates longer games
        - 3-star 5-costs are viable win conditions
        - Trait diversity is important for flexibility
        """

    async def _generate_contextual_explanation(
        self,
        user_input: str,
        game_state: TFTGameState,
        recommendations: TFTRecommendationEngine
    ) -> str:
        """Generate LLM explanation of ML recommendations"""

        # Format ML predictions for LLM
        ml_summary = f"""
        ML Model Recommendations:
        - Primary Action: {recommendations.primary_recommendation} (confidence: {recommendations.ml_predictions.confidence:.1%})
        - Composition Type: {recommendations.ml_predictions.comp_type.value}
        - Risk Level: {recommendations.ml_predictions.risk_level.value}
        - Should Level: {recommendations.ml_predictions.should_level_probability:.1%}
        - Should Roll: {recommendations.ml_predictions.should_roll_probability:.1%}
        - Pivot Urgency: {recommendations.ml_predictions.pivot_urgency:.1%}
        - Target Gold: {recommendations.ml_predictions.target_gold}

        Top Scenarios:
        """

        for i, scenario in enumerate(recommendations.scenarios[:3]):
            ml_summary += f"""
        {i+1}. {scenario.strategy.value}: {scenario.win_probability:.1%} win rate, placement {scenario.expected_placement:.1f}
            """

        prompt = f"""
        Explain these ML predictions for TFT strategy in response to the user's question.

        User Question: {user_input}

        Game State:
        - Round {game_state.round}, Level {game_state.level}
        - {game_state.gold} gold, {game_state.health} health
        - Board: {len(game_state.board)} units
        - Win/Loss Streak: +{game_state.win_streak}/-{game_state.loss_streak}

        {ml_summary}

        Key Factors: {', '.join(recommendations.ml_predictions.key_factors)}

        Provide a clear, strategic explanation that:
        1. Directly answers the user's question
        2. Explains why the ML model recommends this action
        3. Discusses the strategic reasoning behind the prediction
        4. Mentions key factors and risks
        5. Provides specific next steps

        Make it conversational and educational, explaining both what to do and why.
        """

        return await self.llm.generate([
            {
                "role": "system",
                "content": "You are an expert TFT coach explaining ML-generated strategy recommendations. Be clear, educational, and actionable."
            },
            {"role": "user", "content": prompt}
        ])

    def _update_conversation_history(self, user_input: str, response: Dict[str, Any]) -> None:
        """Update conversation history for context"""
        self.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "response_type": response["type"],
            "recommendation": response.get("primary_recommendation")
        })

        # Keep only recent history
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]

    async def get_suggested_questions(self) -> List[str]:
        """Generate relevant questions user might ask"""
        prompt = """
        Generate 5 relevant questions a TFT player might ask about strategy, based on current Set 15 meta.

        Focus on practical, actionable questions about:
        - Composition strategies
        - Economic decisions
        - Leveling timing
        - Item prioritization
        - Positioning

        Make them specific to Set 15 mechanics and champions.
        Return as a simple list, one question per line.
        """

        response = await self.llm.generate([
            {"role": "system", "content": "Generate helpful TFT strategy questions for Set 15."},
            {"role": "user", "content": prompt}
        ])

        # Parse response into list
        questions = [q.strip() for q in response.strip().split('\n') if q.strip()]
        return questions[:5]

    async def analyze_game_screenshot(self, image_path: str) -> Dict[str, Any]:
        """Analyze game state from screenshot (future feature)"""
        # This would use computer vision to extract game state
        # For now, return placeholder
        return {
            "type": "screenshot_analysis",
            "status": "not_implemented",
            "message": "Screenshot analysis will be available in future version"
        }

    async def get_conversation_summary(self) -> str:
        """Get summary of recent conversation"""
        if not self.conversation_history:
            return "No recent conversation history."

        recent_questions = [entry["user_input"] for entry in self.conversation_history[-3:]]

        prompt = f"""
        Summarize this TFT strategy conversation:

        Recent questions:
        {chr(10).join(f"- {q}" for q in recent_questions)}

        Provide a brief summary of the main topics discussed and any key recommendations given.
        """

        return await self.llm.generate([
            {"role": "system", "content": "Summarize TFT strategy conversations concisely."},
            {"role": "user", "content": prompt}
        ])