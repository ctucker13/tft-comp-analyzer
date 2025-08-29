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
    def __init__(self, llm_client: LLMClient, riot_api: RiotTFTAPI):
        self.llm = llm_client
        self.riot_api = riot_api
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        # Create the graph with the state structure
        workflow = StateGraph(AnalysisState)
        
        # Add nodes
        workflow.add_node("data_collector", self._collect_match_data)
        workflow.add_node("comp_extractor", self._extract_compositions)
        workflow.add_node("performance_analyzer", self._analyze_performance)
        workflow.add_node("meta_synthesizer", self._synthesize_meta)
        
        # Define the flow
        workflow.add_edge(START, "data_collector")
        workflow.add_edge("data_collector", "comp_extractor")
        workflow.add_edge("comp_extractor", "performance_analyzer")
        workflow.add_edge("performance_analyzer", "meta_synthesizer")
        workflow.add_edge("meta_synthesizer", END)
        
        return workflow.compile()
    
    async def _collect_match_data(self, state: AnalysisState) -> AnalysisState:
        print("Collecting match data...")
        try:
            players = await self.riot_api.get_challenger_players()
            print(f"Found {len(players)} challenger players")
            
            # Debug: Show first player
            if players:
                print(f"First player example: {players[0]}")
            
            match_data = []
            
            for i, player in enumerate(players[:3]):  # Limit for testing
                print(f"\nProcessing player {i+1}/3...")
                summoner_id = player.get("summonerId", "")
                print(f"Summoner ID: {summoner_id}")
                
                if summoner_id:
                    # Convert summonerId to PUUID
                    print("Getting PUUID...")
                    summoner_data = await self.riot_api.get_summoner_by_id(summoner_id)
                    puuid = summoner_data.get("puuid", "")
                    print(f"PUUID: {puuid}")
                    
                    if puuid:
                        print("Getting match history...")
                        matches = await self.riot_api.get_match_history(puuid, count=5)
                        print(f"Found {len(matches)} matches: {matches}")
                        
                        for j, match_id in enumerate(matches[:2]):
                            print(f"Getting details for match {j+1}: {match_id}")
                            match_details = await self.riot_api.get_match_details(match_id)
                            if match_details:
                                match_data.append(match_details)
                                print(f"Successfully added match details")
                            else:
                                print(f"No match details returned")
                else:
                    print(f"No summoner ID found for player: {player}")
            
            state["raw_matches"] = match_data
            print(f"\nFinal result: Collected {len(match_data)} matches from {len(players)} players")
        except Exception as e:
            print(f"Error collecting data: {e}")
            import traceback
            traceback.print_exc()
            state["raw_matches"] = []
        
        return state
    
    async def _extract_compositions(self, state: AnalysisState) -> AnalysisState:
        # Agent extracts and categorizes team compositions
        print("Extracting compositions...")
        
        prompt = """
        Analyze these TFT match results and extract the team compositions.
        For each composition, identify:
        1. Primary traits and synergies
        2. Key carry units
        3. Supporting units
        4. Final placement
        
        Match data: {matches}
        """
        
        messages = [
            {"role": "system", "content": "You are a TFT expert analyzing team compositions."},
            {"role": "user", "content": prompt.format(matches=str(state["raw_matches"])[:1000])}
        ]
        
        try:
            analysis = await self.llm.generate(messages)
            state["extracted_comps"] = analysis
        except Exception as e:
            print(f"Error extracting compositions: {e}")
            state["extracted_comps"] = "Error extracting compositions"
        
        return state
    
    async def _analyze_performance(self, state: AnalysisState) -> AnalysisState:
        # Agent analyzes which comps perform best
        print("Analyzing performance...")
        
        prompt = """
        Based on the extracted compositions, analyze performance patterns:
        1. Which compositions have the highest average placement?
        2. What traits appear most frequently in top 4 finishes?
        3. Are there any surprising underperforming meta comps?
        
        Composition data: {comps}
        """
        
        messages = [
            {"role": "system", "content": "You are a TFT strategist analyzing competitive performance."},
            {"role": "user", "content": prompt.format(comps=state["extracted_comps"])}
        ]
        
        try:
            performance_analysis = await self.llm.generate(messages)
            state["performance_analysis"] = performance_analysis
        except Exception as e:
            print(f"Error analyzing performance: {e}")
            state["performance_analysis"] = "Error analyzing performance"
        
        return state
    
    async def _synthesize_meta(self, state: AnalysisState) -> AnalysisState:
        # Agent creates final meta report
        print("Synthesizing meta report...")
        
        prompt = """
        Create a comprehensive meta report based on the analysis:
        1. Tier list of current best compositions
        2. Recommended comps for different skill levels
        3. Emerging trends and potential sleeper picks
        4. Specific positioning and itemization recommendations
        
        Performance analysis: {analysis}
        """
        
        messages = [
            {"role": "system", "content": "You are creating a strategic TFT guide for players."},
            {"role": "user", "content": prompt.format(analysis=state["performance_analysis"])}
        ]
        
        try:
            meta_report = await self.llm.generate(messages)
            state["final_report"] = meta_report
        except Exception as e:
            print(f"Error synthesizing meta: {e}")
            state["final_report"] = "Error creating meta report"
        
        return state