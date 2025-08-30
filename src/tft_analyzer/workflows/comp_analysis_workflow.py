import asyncio
from langgraph.graph import StateGraph, END, START
from typing import Dict, Any, List, TypedDict
from ..models.llm_provider import LLMClient
from ..data.riot_api import RiotTFTAPI

# Define the state structure
class AnalysisState(TypedDict):
    raw_matches: List[Dict[str, Any]]
    extracted_comps: str
    performance_analysis: str
    final_report: str

class CompAnalysisWorkflow:
    def __init__(self, llm_client: LLMClient, riot_api: RiotTFTAPI, settings):
        self.llm = llm_client
        self.riot_api = riot_api
        self.settings = settings
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        # Create the graph with the state structure
        workflow = StateGraph(AnalysisState)
        
        # Add nodes
        workflow.add_node("data_collector", self._collect_set15_match_data)
        workflow.add_node("comp_extractor", self._extract_set15_compositions)
        workflow.add_node("performance_analyzer", self._analyze_set15_performance)
        workflow.add_node("meta_synthesizer", self._synthesize_set15_meta)
        
        # Define the flow
        workflow.add_edge(START, "data_collector")
        workflow.add_edge("data_collector", "comp_extractor")
        workflow.add_edge("comp_extractor", "performance_analyzer")
        workflow.add_edge("performance_analyzer", "meta_synthesizer")
        workflow.add_edge("meta_synthesizer", END)
        
        return workflow.compile()
    
    async def _collect_set15_match_data(self, state: AnalysisState) -> AnalysisState:
        """Collect Set 15 match data - PUUID is directly available from challenger data"""
        print("Collecting Set 15 match data...")
        try:
            players = await self.riot_api.get_challenger_players()
            print(f"Found {len(players)} challenger players")
            
            set15_matches = []
            target_matches = self.settings.target_match_count
            successful_players = 0
            
            # Process fewer players to respect rate limits
            max_players = min(self.settings.max_players_to_analyze, 3)
            
            for i, player in enumerate(players[:max_players]):
                print(f"\nProcessing player {i+1}/{max_players}...")
                
                # PUUID is directly available from challenger data!
                puuid = player.get("puuid", "")
                league_points = player.get("leaguePoints", 0)
                wins = player.get("wins", 0)
                losses = player.get("losses", 0)
                
                if not puuid:
                    print("  No PUUID in challenger data, skipping...")
                    continue
                
                print(f"  Player: {league_points} LP ({wins}W/{losses}L) | PUUID: {puuid[:20]}...")
                
                if self.riot_api.is_mock_mode() or puuid.startswith("mock_"):
                    print("  Using mock data...")
                    matches = await self.riot_api.get_match_history(puuid, count=3)
                    
                    for match_id in matches:
                        match_details = await self.riot_api.get_match_details(match_id)
                        if match_details:
                            set15_matches.append(match_details)
                            print(f"  Added mock Set 15 match")
                    
                    successful_players += 1
                else:
                    # Real API call - skip the summoner lookup step entirely!
                    print(f"  Using PUUID directly from challenger data")
                    
                    # Get matches with rate limiting
                    matches = await self.riot_api.get_match_history(puuid, count=self.settings.max_matches_per_player)
                    print(f"  Found {len(matches)} recent matches")
                    
                    matches_processed = 0
                    for j, match_id in enumerate(matches):
                        if matches_processed >= 2:  # Limit to 2 matches per player for rate limits
                            break
                            
                        print(f"    Processing match {j+1}...")
                        match_details = await self.riot_api.get_match_details(match_id)
                        
                        # Only include Set 15 matches
                        if match_details and self.riot_api._is_set15_match(match_details):
                            set15_matches.append(match_details)
                            print(f"    Added Set 15 match: {match_id}")
                            matches_processed += 1
                        elif match_details:
                            set_num = match_details.get("info", {}).get("tft_set_number", "Unknown")
                            print(f"    Skipped Set {set_num} match")
                        else:
                            print(f"    No match details returned")
                        
                        # Stop if we have enough total data
                        if len(set15_matches) >= target_matches:
                            break
                    
                    successful_players += 1
                
                # Stop if we have enough data
                if len(set15_matches) >= target_matches:
                    print(f"  Reached target of {target_matches} matches")
                    break
                
                # Add longer delay between players for Development API key
                if i < max_players - 1:
                    delay = self.settings.api_delay_seconds
                    print(f"  Waiting {delay} seconds to respect rate limits...")
                    await asyncio.sleep(delay)
            
            state["raw_matches"] = set15_matches
            print(f"\nFinal Result: Collected {len(set15_matches)} Set 15 matches from {successful_players} players")
            
            if len(set15_matches) == 0:
                print("No Set 15 matches found - possible reasons:")
                print("   • Rate limiting prevented data collection")
                print("   • All recent matches are from older sets")
                print("   • Players haven't played Set 15 recently")
            elif len(set15_matches) < target_matches:
                print(f"Only found {len(set15_matches)}/{target_matches} target matches")
                print("   This is normal with Development API key rate limits")
            
        except Exception as e:
            print(f"Error collecting Set 15 data: {e}")
            import traceback
            traceback.print_exc()
            state["raw_matches"] = []
        
        return state
    
    async def _extract_set15_compositions(self, state: AnalysisState) -> AnalysisState:
        """Extract Set 15 specific compositions"""
        print("Extracting Set 15 compositions...")
        
        match_count = len(state["raw_matches"])
        print(f"Analyzing {match_count} Set 15 matches...")
        
        if match_count == 0:
            print("No match data to analyze, using fallback analysis")
            state["extracted_comps"] = "No Set 15 match data available for analysis"
            return state
        
        # Create a summary of match data for analysis
        match_summary = []
        for i, match in enumerate(state["raw_matches"][:5]):  # Limit to avoid token limits
            info = match.get("info", {})
            participants = info.get("participants", [])
            
            # Extract key composition info
            for participant in participants:
                placement = participant.get("placement", 0)
                traits = participant.get("traits", [])
                units = participant.get("units", [])
                
                if placement <= 4:  # Focus on successful comps
                    trait_names = [t.get("name", "") for t in traits if t.get("tier_current", 0) > 0]
                    unit_names = [u.get("name", "") for u in units]
                    
                    match_summary.append({
                        "placement": placement,
                        "traits": trait_names[:5],  # Top 5 traits
                        "units": unit_names[:8],    # Top 8 units
                    })
        
        prompt = f"""
        Analyze these TFT Set 15: K.O. Coliseum match results from Patch 15.17.
        
        Set 15 Context:
        - Power Snax system: 2 power-ups per game (rounds 1-3 and 3-6)
        - Role system: Tank, Fighter, Marksman, Caster, Assassin, Specialist
        - 3-star 5-costs have CC immunity and 20 mana regen
        - Longer games (40+ rounds common)
        - 3 augments per game
        
        Match Data Summary ({len(match_summary)} successful compositions):
        {match_summary}
        
        For each composition pattern, identify:
        1. Primary trait combinations and synergy strengths
        2. Key carry units and optimal itemization
        3. Role-based team structure and positioning
        4. Power Snax optimization opportunities
        5. Placement consistency and win conditions
        
        Focus on actionable patterns from this real Set 15 data.
        """
        
        messages = [
            {"role": "system", "content": "You are analyzing real TFT Set 15 match data to identify successful team compositions. Focus on practical patterns and meta insights."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            analysis = await self.llm.generate(messages, max_tokens=1500)
            state["extracted_comps"] = analysis
            print("Completed composition extraction")
        except Exception as e:
            print(f"Error extracting Set 15 compositions: {e}")
            state["extracted_comps"] = "Error extracting compositions"
        
        return state
    
    async def _analyze_set15_performance(self, state: AnalysisState) -> AnalysisState:
        """Analyze Set 15 performance patterns"""
        print("Analyzing Set 15 performance...")
        
        prompt = f"""
        Based on the Set 15 compositions extracted, analyze performance patterns:
        
        Composition Analysis: {state["extracted_comps"]}
        
        Performance Questions:
        1. Which trait combinations show the highest consistency?
        2. What carry units are most reliable in the current meta?
        3. How do Power Snax choices affect final placement?
        4. Which role combinations provide the best frontline/backline balance?
        5. What economic patterns lead to successful Set 15 games?
        
        Provide data-driven insights about what makes compositions successful in Set 15.
        """
        
        messages = [
            {"role": "system", "content": "You are analyzing TFT Set 15 performance data to identify success patterns and meta trends."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            performance_analysis = await self.llm.generate(messages, max_tokens=1500)
            state["performance_analysis"] = performance_analysis
            print("Completed performance analysis")
        except Exception as e:
            print(f"Error analyzing Set 15 performance: {e}")
            state["performance_analysis"] = "Error analyzing performance"
        
        return state
    
    async def _synthesize_set15_meta(self, state: AnalysisState) -> AnalysisState:
        """Create Set 15 specific meta report"""
        print("Synthesizing Set 15 meta report...")
        
        prompt = f"""
        Create a TFT Set 15 meta guide based on the analysis:

        Performance Analysis: {state["performance_analysis"]}
        Composition Analysis: {state["extracted_comps"]}
        
        Create sections for:
        
        ## PATCH 15.17 META TIER LIST
        Rank the strongest compositions with brief descriptions
        
        ## POWER SNAX GUIDE
        Optimal champions and timing for power-ups
        
        ## POSITIONING STRATEGIES
        Role-based positioning for maximum effectiveness
        
        ## CLIMBING RECOMMENDATIONS
        Specific advice for ranking up in current meta
        
        Keep recommendations practical and focused on current Set 15 mechanics.
        """
        
        messages = [
            {"role": "system", "content": "You are creating a strategic TFT Set 15 guide. Focus on actionable advice for the current meta."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            meta_report = await self.llm.generate(messages, max_tokens=2000)
            state["final_report"] = meta_report
            print("Completed meta synthesis")
        except Exception as e:
            print(f"Error synthesizing Set 15 meta: {e}")
            state["final_report"] = "Error creating meta report"
        
        return state