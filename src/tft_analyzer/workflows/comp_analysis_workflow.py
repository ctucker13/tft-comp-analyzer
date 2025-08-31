import asyncio
from datetime import datetime
from langgraph.graph import StateGraph, END, START
from typing import Dict, Any, List, TypedDict
from ..models.llm_provider import LLMClient
from ..data.riot_api import RiotTFTAPI
from ..data.dynamic_validation import ValidationManager
from ..data.set15_validation import (
    validate_analysis_text, 
    get_set15_validation_prompt
)

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
        self.validation_manager = ValidationManager()
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
        """Collect Set 15 match data from high-tier players (Challenger, Grandmaster, Master)"""
        print("Collecting Set 15 match data from high-tier players...")
        try:
            # Get players from multiple tiers for more diverse data
            include_tiers = getattr(self.settings, 'include_tiers', ['challenger', 'grandmaster', 'master'])
            players = await self.riot_api.get_high_tier_players(include_tiers=include_tiers)
            print(f"Found {len(players)} high-tier players across multiple tiers")
            
            # Optionally prioritize players who are winning more games
            prioritize_winners = getattr(self.settings, 'prioritize_winners', True)
            if prioritize_winners and len(players) > 5:
                print("🏆 Analyzing recent performance to prioritize winning players...")
                players = await self.riot_api.get_winning_players_from_recent_matches(players)
                print(f"Prioritized {len(players)} players based on recent win rates")
            
            set15_matches = []
            target_matches = self.settings.target_match_count
            successful_players = 0
            
            # Process fewer players to respect rate limits
            max_players = min(self.settings.max_players_to_analyze, 3)
            
            for i, player in enumerate(players[:max_players]):
                print(f"\nProcessing player {i+1}/{max_players}...")
                
                # PUUID is directly available from high-tier player data!
                puuid = player.get("puuid", "")
                league_points = player.get("leaguePoints", 0)
                wins = player.get("wins", 0)
                losses = player.get("losses", 0)
                tier = player.get("tier", "UNKNOWN")
                rank = player.get("rank", "")
                
                if not puuid:
                    print(f"  No PUUID in {tier} data, skipping...")
                    continue
                
                print(f"  Player: {tier} {rank} - {league_points} LP ({wins}W/{losses}L) | PUUID: {puuid[:20]}...")
                
                # Get matches with rate limiting - optionally filter to last 24 hours
                use_24h_filter = getattr(self.settings, 'use_24h_filter', False)
                matches = []
                
                if use_24h_filter:
                    matches = await self.riot_api.get_match_history(puuid, count=self.settings.max_matches_per_player, hours_back=24)
                    print(f"  Found {len(matches)} matches from last 24 hours")
                    
                    # If no matches in 24h, fall back to 7-day timeframe
                    if len(matches) == 0:
                        print("  No matches in 24h, trying last 7 days...")
                        matches = await self.riot_api.get_match_history(puuid, count=self.settings.max_matches_per_player, hours_back=168)  # 7 days = 168 hours
                        print(f"  Found {len(matches)} matches in last 7 days")
                        
                        # If still no matches in 7 days, try without time filter (default recent matches)
                        if len(matches) == 0:
                            print("  No matches in 7 days, trying all recent matches...")
                            matches = await self.riot_api.get_match_history(puuid, count=self.settings.max_matches_per_player)
                            print(f"  Found {len(matches)} recent matches (no time limit)")
                else:
                    matches = await self.riot_api.get_match_history(puuid, count=self.settings.max_matches_per_player)
                    print(f"  Found {len(matches)} recent matches")
                
                matches_processed = 0
                
                for j, match_id in enumerate(matches):
                    if matches_processed >= 5:  # Increased from 2 to 5 matches per player
                        break
                        
                    print(f"    Processing match {j+1}...")
                    # Filter for Set 15 and patch 15.3+
                    require_patch_15_3 = getattr(self.settings, 'require_patch_15_3', True)
                    match_details = await self.riot_api.get_match_details(match_id, require_patch_15_3=require_patch_15_3)
                    
                    # Only include valid matches (already filtered by get_match_details)
                    if match_details:
                        set15_matches.append(match_details)
                        info = match_details.get("info", {})
                        game_version = info.get("game_version", "Unknown")
                        set_number = info.get("tft_set_number", "Unknown")
                        game_datetime = info.get("game_datetime", 0)
                        match_date = datetime.fromtimestamp(game_datetime / 1000).strftime('%Y-%m-%d') if game_datetime else "Unknown"
                        print(f"    ✅ Added Set {set_number} match: {match_id} (version: {game_version}, date: {match_date})")
                        matches_processed += 1
                    else:
                        print("    ⏭️ Skipped match (not Set 15 or filtered out)")
                    
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
                print("   • All recent matches are from older sets or patches")
                print("   • Players haven't played Set 15 patch 15.3+ recently")
                print("   • API key may be invalid or expired")
                use_24h_filter = getattr(self.settings, 'use_24h_filter', False)
                if use_24h_filter:
                    print("   • 24-hour filter may be too restrictive (try disabling)")
                require_patch_15_3 = getattr(self.settings, 'require_patch_15_3', True)
                if require_patch_15_3:
                    print("   • Patch 15.3+ filter may be excluding older matches (try disabling)")
                
                print("\n💡 Suggestions:")
                if use_24h_filter:
                    print("   • Disable '24-Hour Match Filter' in Development Settings")
                if require_patch_15_3:
                    print("   • Set REQUIRE_PATCH_15_3=false in your .env file to include older patches")
                print("   • Try enabling 'Use Cached Data' for development")
                print("   • Check that challenger players have played TFT recently")
                
                # Don't raise an exception immediately, let the workflow continue with empty data
                print("\n⚠️ Continuing analysis with limited data...")
                # Set a flag so downstream components know there's no data
                state["no_match_data"] = True
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
            if state.get("no_match_data"):
                print("No match data available - providing general Set 15 guidance...")
                state["extracted_comps"] = """# Set 15: K.O. Coliseum - General Meta Guide

## Current Meta Compositions (General Guidance)

Since no recent match data was available, here's general guidance for Set 15: K.O. Coliseum:

### Strong Compositions
- **Arcane Domination**: Focus on Jinx and Vi synergies
- **Conqueror/Warband**: Strong frontline with carry potential
- **Family/Multirole**: Flexible compositions with multiple win conditions

### Key Champions to Consider
- **Jinx**: Primary AD carry with strong late-game scaling
- **Vi**: Tank/bruiser with good utility
- **Ekko**: AP carry with mobility
- **Warwick**: Strong early game unit

### Tips
- Power Snax system provides 2 power-ups per game (rounds 1-3 and 3-6)
- 3-star 5-costs have CC immunity and 20 mana regen
- Games typically run longer (40+ rounds)

**Note**: This is general guidance. For current meta analysis, please:
- Disable strict filtering options
- Ensure API connectivity
- Try again when challenger players have recent matches
"""
                return state
            else:
                raise ValueError("No match data to analyze. Cannot proceed without real match data.")
        
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
        
        # Get current patch for validation
        current_patch = getattr(self.settings, 'current_patch', '15.17')
        
        # Get dynamic validation requirements
        validator = await self.validation_manager.get_validator(current_patch)
        if validator:
            validation_prompt = validator.get_validation_prompt()
            print(f"✅ Using dynamic validation for patch {current_patch}")
        else:
            # Fallback to static validation
            validation_prompt = get_set15_validation_prompt()
            print(f"⚠️ Falling back to static validation for patch {current_patch}")
        
        prompt = f"""
        Analyze these TFT Set 15: K.O. Coliseum match results from Patch 15.3+ (released 2025/08/26 onwards).
        
        {validation_prompt}
        
        Set 15 Context:
        - Power Snax system: 2 power-ups per game (rounds 1-3 and 3-6)
        - Current patch: {current_patch}
        - 3-star 5-costs have CC immunity and 20 mana regen
        - Longer games (40+ rounds common)
        - 3 augments per game
        
        Match Data Summary ({len(match_summary)} successful compositions from real matches):
        {match_summary}
        
        For each composition pattern, identify:
        1. SPECIFIC UNIT NAMES (not just trait names) - mention actual champions FROM THE APPROVED LIST ONLY
        2. Primary trait combinations using ONLY Set 15 traits from the approved list
        3. Key carry units with their exact names and optimal itemization
        4. Role-based team structure and positioning
        5. Power Snax optimization opportunities
        6. Placement consistency and win conditions
        
        CRITICAL: Double-check every champion and trait name against the approved lists before including in your response.
        """
        
        messages = [
            {"role": "system", "content": "You are analyzing real TFT Set 15 match data to identify successful team compositions. Focus on practical patterns and meta insights."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            analysis = await self.llm.generate(messages, max_tokens=1500)
            
            # Validate the analysis using dynamic validation
            if validator:
                validation_results = validator.validate_text(analysis)
            else:
                # Fallback to static validation
                validation_results = validate_analysis_text(analysis)
            
            # Check for validation issues (handle both static and dynamic validation formats)
            invalid_champions = validation_results.get("invalid_champions", validation_results.get("hallucinated_champions", []))
            invalid_traits = validation_results.get("invalid_traits", validation_results.get("hallucinated_traits", []))
            
            if invalid_champions or invalid_traits:
                patch_info = validation_results.get("patch_version", current_patch)
                
                print(f"❌ CRITICAL VALIDATION ERROR for {patch_info}: LLM hallucinated invalid content!")
                if invalid_champions:
                    print(f"   - HALLUCINATED CHAMPIONS: {invalid_champions}")
                if invalid_traits:
                    print(f"   - HALLUCINATED TRAITS: {invalid_traits}")
                
                print("🔄 Attempting to re-prompt LLM with stricter validation...")
                
                # Create a stricter re-prompt
                strict_prompt = f"""
                CRITICAL ERROR DETECTED: Your previous response contained hallucinated champions/traits not in Set 15.
                
                INVALID CONTENT DETECTED:
                - Champions NOT in Set 15: {invalid_champions}  
                - Traits NOT in Set 15: {invalid_traits}
                
                {validation_prompt}
                
                STRICT REQUIREMENTS:
                1. ONLY use champions that exist in Set 15 (TFT15_ prefix in API data)
                2. NEVER mention: Cassiopeia, Elise, LeBlanc, Vladimir (these are Set 14 champions)
                3. NEVER mention: Black Rose (this is a Set 14 trait)
                4. If you're unsure about a champion/trait, DO NOT include it
                5. Focus on the actual match data provided: {match_summary}
                
                Please provide a corrected analysis using ONLY validated Set 15 content.
                """
                
                try:
                    corrected_analysis = await self.llm.generate([
                        {"role": "system", "content": "You are analyzing TFT Set 15 match data. You must NEVER hallucinate champions or traits that don't exist in Set 15. When in doubt, omit the content."},
                        {"role": "user", "content": strict_prompt}
                    ], max_tokens=1500)
                    
                    # Validate again
                    corrected_validation = validate_analysis_text(corrected_analysis)
                    corrected_invalid_champions = corrected_validation.get("hallucinated_champions", [])
                    corrected_invalid_traits = corrected_validation.get("hallucinated_traits", [])
                    
                    if corrected_invalid_champions or corrected_invalid_traits:
                        print("❌ Re-prompt failed - still contains hallucinated content:")
                        print(f"   - Champions: {corrected_invalid_champions}")
                        print(f"   - Traits: {corrected_invalid_traits}")
                        
                        analysis = f"""🚨 **ANALYSIS ERROR: LLM HALLUCINATION DETECTED** 🚨

The AI model generated content containing champions/traits that don't exist in TFT Set 15: K.O. Coliseum (Patch 15.3+).

**HALLUCINATED CONTENT DETECTED:**
- Invalid Champions: {invalid_champions + corrected_invalid_champions}
- Invalid Traits: {invalid_traits + corrected_invalid_traits}

**ACTUAL SET 15 MATCH DATA SUMMARY:**
{match_summary}

❌ **This analysis is unreliable and should not be used for gameplay decisions.**

Please check the validation system or try again with fresh data."""
                    else:
                        print("✅ Re-prompt successful - hallucinated content corrected")
                        analysis = f"""✅ **CORRECTED ANALYSIS** (Original contained hallucinated content)

{corrected_analysis}

*Note: This analysis was corrected after the AI initially hallucinated Set 14 champions/traits.*"""
                
                except Exception as re_prompt_error:
                    print(f"❌ Re-prompt failed with error: {re_prompt_error}")
                    analysis = f"""🚨 **CRITICAL ANALYSIS ERROR** 🚨

The AI model hallucinated invalid champions/traits from previous TFT sets:
- Invalid Champions: {invalid_champions}
- Invalid Traits: {invalid_traits}

The data being analyzed is confirmed to be from Set 15, patch 15.3+ matches only.

**REAL MATCH DATA SUMMARY:**
{match_summary}

❌ **This analysis cannot be trusted for gameplay decisions.**"""
            else:
                print("✅ Validation passed: No hallucinated content detected")
            
            state["extracted_comps"] = analysis
            print("Completed composition extraction with validation")
        except Exception as e:
            print(f"Error extracting Set 15 compositions: {e}")
            state["extracted_comps"] = "Error extracting compositions"
        
        return state
    
    async def _analyze_set15_performance(self, state: AnalysisState) -> AnalysisState:
        """Analyze performance patterns"""
        print("Analyzing performance patterns...")
        
        # Handle case with no match data
        if state.get("no_match_data"):
            state["performance_analysis"] = """## Performance Insights (General Guidance)

Without recent match data, here are general performance tips for Set 15:

1. **Champion Synergies**: Focus on building strong trait combinations rather than forcing specific units
2. **Economic Management**: Power Snax timing is crucial - use them strategically in rounds 1-3 and 3-6  
3. **Positioning**: Late game positioning becomes critical with longer games (40+ rounds)

For detailed performance analysis, please ensure recent match data is available."""
            return state
        
        current_patch = getattr(self.settings, 'current_patch', '15.17')
        
        # Get dynamic validation requirements
        validator = await self.validation_manager.get_validator(current_patch)
        if validator:
            validation_prompt = validator.get_validation_prompt()
        else:
            # Fallback to static validation
            validation_prompt = get_set15_validation_prompt()
        
        prompt = f"""
        Based on the Set 15 compositions extracted, analyze performance patterns for patch {current_patch}+:
        
        {validation_prompt}
        
        Composition Analysis: {state["extracted_comps"]}
        
        Performance Questions:
        1. Which SPECIFIC UNITS show the highest carry potential and consistency?
        2. What trait combinations with NAMED CHAMPIONS are most reliable?
        3. How do Power Snax choices on SPECIFIC UNITS affect final placement?
        4. Which NAMED UNITS provide the best frontline/backline balance?
        5. What economic patterns with SPECIFIC CHAMPIONS lead to success?
        
        CRITICAL: Only reference champions and traits from the approved Set 15 lists above.
        """
        
        messages = [
            {"role": "system", "content": "You are analyzing TFT Set 15 performance data to identify success patterns and meta trends."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            performance_analysis = await self.llm.generate(messages, max_tokens=1500)
            
            # Validate using dynamic validation
            if validator:
                validation_results = validator.validate_text(performance_analysis)
            else:
                validation_results = validate_analysis_text(performance_analysis)
            
            invalid_champions = validation_results.get("invalid_champions", validation_results.get("hallucinated_champions", []))
            invalid_traits = validation_results.get("invalid_traits", validation_results.get("hallucinated_traits", []))
            
            if invalid_champions or invalid_traits:
                print("❌ VALIDATION ERROR in performance analysis: Hallucinated content detected!")
                if invalid_champions:
                    print(f"   - HALLUCINATED CHAMPIONS: {invalid_champions}")
                if invalid_traits:
                    print(f"   - HALLUCINATED TRAITS: {invalid_traits}")
                
                performance_analysis = f"""🚨 **PERFORMANCE ANALYSIS ERROR: HALLUCINATED CONTENT DETECTED** 🚨

The AI model generated invalid champions/traits not in Set 15:
- Invalid Champions: {invalid_champions}
- Invalid Traits: {invalid_traits}

❌ **This performance analysis is unreliable and should not be used.**

Original analysis contained hallucinated content from previous TFT sets."""
            else:
                print("✅ Performance analysis validation passed")
            
            state["performance_analysis"] = performance_analysis
            print("Completed performance analysis with validation")
        except Exception as e:
            print(f"Error analyzing Set 15 performance: {e}")
            state["performance_analysis"] = "Error analyzing performance"
        
        return state
    
    async def _synthesize_set15_meta(self, state: AnalysisState) -> AnalysisState:
        """Create meta report"""
        print("Synthesizing meta report...")
        
        # Handle case with no match data
        if state.get("no_match_data"):
            state["final_report"] = f"""# TFT Set 15: K.O. Coliseum - General Meta Guide

⚠️ **Limited Data Analysis**: This report is based on general Set 15 knowledge rather than recent match data.

{state["extracted_comps"]}

{state["performance_analysis"]}

## Recommendations for Better Analysis

To get detailed meta analysis based on current challenger gameplay:

1. **Disable Restrictive Filters**:
   - Uncheck "24-Hour Match Filter" in Development Settings
   - Consider setting `REQUIRE_PATCH_15_3=false` in .env to include more matches

2. **Enable Development Features**:
   - Check "Use Cached Data" to avoid rate limits during testing
   - Try running analysis at different times when players are more active

3. **Check API Status**:
   - Ensure your Riot API key is valid and not expired
   - Development keys expire every 24 hours

## Set 15 Meta Summary (General)

**Current Meta**: Arcane-focused compositions with Jinx/Vi synergies
**Game Length**: Typically 35-45 rounds due to Power Snax system
**Key Mechanics**: 2 Power Snax per game, 3-star 5-costs with CC immunity

---
*This analysis will be more detailed once recent match data is available.*"""
            return state
        
        current_patch = getattr(self.settings, 'current_patch', '15.17')
        
        # Get dynamic validation requirements
        validator = await self.validation_manager.get_validator(current_patch)
        if validator:
            validation_prompt = validator.get_validation_prompt()
        else:
            # Fallback to static validation
            validation_prompt = get_set15_validation_prompt()
        
        prompt = f"""
        Create a TFT Set 15 meta guide based on the analysis for patch {current_patch}+:

        {validation_prompt}

        Performance Analysis: {state["performance_analysis"]}
        Composition Analysis: {state["extracted_comps"]}
        
        Create sections for:
        
        ## PATCH {current_patch}+ META TIER LIST
        Rank the strongest compositions with SPECIFIC UNIT NAMES and brief descriptions
        
        ## POWER SNAX GUIDE
        Optimal SPECIFIC CHAMPIONS and timing for power-ups
        
        ## POSITIONING STRATEGIES
        Role-based positioning with NAMED UNITS for maximum effectiveness
        
        ## CLIMBING RECOMMENDATIONS
        Specific advice with CHAMPION NAMES for ranking up in current meta
        
        CRITICAL: Every champion and trait mentioned must be from the approved Set 15 lists above.
        """
        
        messages = [
            {"role": "system", "content": "You are creating a strategic TFT Set 15 guide. Focus on actionable advice for the current meta."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            meta_report = await self.llm.generate(messages, max_tokens=2000)
            
            # Validate using dynamic validation
            if validator:
                validation_results = validator.validate_text(meta_report)
            else:
                validation_results = validate_analysis_text(meta_report)
            
            invalid_champions = validation_results.get("invalid_champions", validation_results.get("hallucinated_champions", []))
            invalid_traits = validation_results.get("invalid_traits", validation_results.get("hallucinated_traits", []))
            
            if invalid_champions or invalid_traits:
                patch_info = validation_results.get("patch_version", current_patch)
                set_info = validation_results.get("set_info", f"Set {getattr(self.settings, 'current_tft_set', 15)}")
                
                print("❌ CRITICAL ERROR in final meta report: Hallucinated content detected!")
                if invalid_champions:
                    print(f"   - HALLUCINATED CHAMPIONS: {invalid_champions}")
                if invalid_traits:
                    print(f"   - HALLUCINATED TRAITS: {invalid_traits}")
                
                # Replace report with error message
                meta_report = f"""🚨 **CRITICAL META REPORT ERROR: HALLUCINATED CONTENT DETECTED** 🚨

The AI model generated champions/traits that don't exist in Set 15: K.O. Coliseum (Patch 15.3+):

**HALLUCINATED CONTENT:**
- Invalid Champions: {invalid_champions}  
- Invalid Traits: {invalid_traits}

❌ **This meta report is completely unreliable and should NOT be used for gameplay decisions.**

**IMPORTANT:** The underlying match data is confirmed to be from Set 15, patch 15.3+ only. The AI model is incorrectly hallucinating content from previous sets.

Please check the validation system or request a new analysis."""
            else:
                print("✅ Final meta report validation passed")
                patch_info = validation_results.get("patch_version", current_patch)
                set_info = validation_results.get("set_info", f"Set {getattr(self.settings, 'current_tft_set', 15)}")
                # Add validation confirmation
                validation_notice = f"✅ **Validated Content**: All champions and traits in this analysis have been verified against {patch_info} ({set_info}).\n\n---\n\n"
                meta_report = validation_notice + meta_report
            
            state["final_report"] = meta_report
            print("Completed meta synthesis with validation")
        except Exception as e:
            print(f"Error synthesizing Set 15 meta: {e}")
            state["final_report"] = "Error creating meta report"
        
        return state