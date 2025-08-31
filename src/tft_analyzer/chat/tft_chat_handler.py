"""
TFT Chat Handler - Provides conversational interface with Riot API data context
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from ..models.llm_provider import LLMClient
    from ..data.riot_api import RiotTFTAPI
    from ..utils.patch_detector import TFTPatchDetector
except ImportError:
    from src.tft_analyzer.models.llm_provider import LLMClient
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from src.tft_analyzer.utils.patch_detector import TFTPatchDetector


class TFTChatHandler:
    """Handles chat interactions with TFT context from Riot API data"""
    
    def __init__(self, llm_client: LLMClient, riot_api: RiotTFTAPI, settings):
        self.llm = llm_client
        self.riot_api = riot_api
        self.settings = settings
        self._cached_context = None
        self._context_timestamp = None
        self._cache_duration = 300  # 5 minutes
        
    async def get_fresh_tft_context(self) -> Dict[str, Any]:
        """Get fresh TFT context data from Riot API"""
        print("Fetching fresh TFT context...")
        
        try:
            # Get current patch info
            patch_detector = TFTPatchDetector()
            patch_info = await patch_detector.get_current_patch_info()
            
            # Get challenger player data for meta context
            players = await self.riot_api.get_challenger_players()
            
            # Get sample match data for composition context
            sample_matches = []
            if players:
                # Get match data from top 3 players
                for player in players[:3]:
                    puuid = player.get("puuid", "")
                    if puuid:
                        matches = await self.riot_api.get_match_history(puuid, count=2)
                        for match_id in matches:
                            match_details = await self.riot_api.get_match_details(match_id)
                            if match_details and self.riot_api._is_set15_match(match_details):
                                sample_matches.append(match_details)
                                break  # Only get one Set 15 match per player
                    
                    if len(sample_matches) >= 3:  # Limit to avoid too much data
                        break
                        
                    # Rate limiting
                    await asyncio.sleep(2)
            
            # Build context summary
            context = {
                "patch_info": patch_info,
                "challenger_count": len(players),
                "sample_matches_count": len(sample_matches),
                "recent_compositions": self._extract_compositions_summary(sample_matches),
                "meta_trends": self._extract_meta_trends(sample_matches),
                "timestamp": datetime.now().isoformat()
            }
            
            return context
            
        except Exception as e:
            print(f"Error fetching TFT context: {e}")
            # Return minimal context with patch info
            try:
                patch_detector = TFTPatchDetector()
                patch_info = await patch_detector.get_current_patch_info()
                return {
                    "patch_info": patch_info,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            except:
                return {
                    "patch_info": {"patch": "15.17", "set_number": 15, "set_name": "K.O. Coliseum"},
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    def _extract_compositions_summary(self, matches: List[Dict]) -> List[Dict]:
        """Extract composition summaries from match data"""
        compositions = []
        
        for match in matches:
            info = match.get("info", {})
            participants = info.get("participants", [])
            
            for participant in participants:
                placement = participant.get("placement", 0)
                if placement <= 4:  # Focus on successful comps
                    traits = participant.get("traits", [])
                    units = participant.get("units", [])
                    
                    active_traits = [t.get("name", "") for t in traits if t.get("tier_current", 0) > 0]
                    key_units = [u.get("name", "") for u in units if u.get("tier", 0) >= 2]  # 2+ star units
                    
                    compositions.append({
                        "placement": placement,
                        "traits": active_traits[:4],  # Top 4 traits
                        "key_units": key_units[:6],   # Top 6 key units
                    })
        
        return compositions[:10]  # Limit to avoid too much data
    
    def _extract_meta_trends(self, matches: List[Dict]) -> Dict[str, Any]:
        """Extract meta trends from match data"""
        if not matches:
            return {"note": "No recent match data available"}
        
        trait_frequency = {}
        unit_frequency = {}
        
        for match in matches:
            info = match.get("info", {})
            participants = info.get("participants", [])
            
            for participant in participants:
                placement = participant.get("placement", 0)
                if placement <= 4:  # Only count successful placements
                    # Count traits
                    traits = participant.get("traits", [])
                    for trait in traits:
                        if trait.get("tier_current", 0) > 0:
                            name = trait.get("name", "")
                            trait_frequency[name] = trait_frequency.get(name, 0) + 1
                    
                    # Count units
                    units = participant.get("units", [])
                    for unit in units:
                        name = unit.get("name", "")
                        unit_frequency[name] = unit_frequency.get(name, 0) + 1
        
        # Get top trends
        top_traits = sorted(trait_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        top_units = sorted(unit_frequency.items(), key=lambda x: x[1], reverse=True)[:8]
        
        return {
            "popular_traits": [trait[0] for trait in top_traits],
            "popular_units": [unit[0] for unit in top_units],
            "matches_analyzed": len(matches)
        }
    
    async def get_cached_context(self) -> Dict[str, Any]:
        """Get cached context or fetch fresh if expired"""
        now = datetime.now()
        
        if (self._cached_context is None or 
            self._context_timestamp is None or 
            (now - self._context_timestamp).seconds > self._cache_duration):
            
            self._cached_context = await self.get_fresh_tft_context()
            self._context_timestamp = now
        
        return self._cached_context
    
    async def handle_chat_message(self, user_message: str, chat_history: List[Dict] = None) -> str:
        """Handle a chat message with TFT context"""
        
        # Get current TFT context
        context = await self.get_cached_context()
        
        # Build context string for the LLM
        context_str = self._build_context_string(context)
        
        # Build the conversation
        messages = [
            {
                "role": "system", 
                "content": f"""You are a TFT (Teamfight Tactics) expert assistant with access to real-time data from the Riot Games API. 

Current TFT Context:
{context_str}

Guidelines:
- Use the provided context to give accurate, data-driven advice
- Focus on Set 15: K.O. Coliseum mechanics and meta
- Reference actual challenger gameplay patterns when available
- Be conversational but informative
- If asked about specific compositions, reference the recent match data
- Always mention the current patch when giving meta advice"""
            }
        ]
        
        # Add chat history if provided
        if chat_history:
            messages.extend(chat_history[-10:])  # Keep last 10 messages for context
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = await self.llm.generate(messages, max_tokens=1000)
            return response
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    def _build_context_string(self, context: Dict[str, Any]) -> str:
        """Build a context string for the LLM"""
        lines = []
        
        # Patch information
        patch_info = context.get("patch_info", {})
        lines.append(f"Current Patch: {patch_info.get('patch', 'Unknown')}")
        lines.append(f"Set: {patch_info.get('set_number', 'Unknown')} - {patch_info.get('set_name', 'Unknown')}")
        
        # Meta trends
        meta_trends = context.get("meta_trends", {})
        if "popular_traits" in meta_trends:
            lines.append(f"Popular Traits: {', '.join(meta_trends['popular_traits'])}")
        if "popular_units" in meta_trends:
            lines.append(f"Popular Units: {', '.join(meta_trends['popular_units'])}")
        
        # Recent compositions
        compositions = context.get("recent_compositions", [])
        if compositions:
            lines.append(f"\nRecent Successful Compositions ({len(compositions)} samples):")
            for i, comp in enumerate(compositions[:5]):  # Show top 5
                traits_str = ", ".join(comp.get("traits", []))
                lines.append(f"  #{comp.get('placement', '?')}: {traits_str}")
        
        # Data freshness
        timestamp = context.get("timestamp", "")
        if timestamp:
            lines.append(f"\nData updated: {timestamp}")
        
        # Error info
        if "error" in context:
            lines.append(f"\nNote: Using cached/limited data due to: {context['error']}")
        
        return "\n".join(lines)
    
    async def suggest_questions(self) -> List[str]:
        """Suggest relevant questions based on current context"""
        context = await self.get_cached_context()
        
        suggestions = [
            "What are the strongest comps in the current meta?",
            "How should I play the early game in Set 15?",
            "What Power Snax should I prioritize?",
            "Which units are the best carries right now?",
            "How has the meta changed in recent patches?"
        ]
        
        # Add context-specific suggestions
        meta_trends = context.get("meta_trends", {})
        popular_traits = meta_trends.get("popular_traits", [])
        
        if popular_traits:
            suggestions.extend([
                f"How do I play {popular_traits[0]} comps?",
                f"What items work best with {popular_traits[1] if len(popular_traits) > 1 else popular_traits[0]}?"
            ])
        
        return suggestions[:7]  # Return top 7 suggestions