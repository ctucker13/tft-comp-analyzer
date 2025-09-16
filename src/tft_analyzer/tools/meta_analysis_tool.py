#!/usr/bin/env python3
"""
TFT Meta Analysis Tool

Provides meta composition analysis, tier lists, and trend insights based on recent match data.
Complements the strategic decision tool with broader meta understanding.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np

try:
    from ..ml.training.meta_data_collector import TFTMetaDataCollector
    from ..ml.models.meta_analysis_model import TFTMetaAnalysisModel, MetaAnalysisDataProcessor
    from ..data.meta_data_manager import TFTMetaDataManager
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from src.tft_analyzer.ml.training.meta_data_collector import TFTMetaDataCollector
    from src.tft_analyzer.ml.models.meta_analysis_model import TFTMetaAnalysisModel, MetaAnalysisDataProcessor
    from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
    from config.settings import Settings


class TFTMetaAnalysisTool:
    """Tool for getting TFT meta analysis, tier lists, and composition trends."""

    def __init__(self, use_cached_data: bool = True):
        """Initialize the meta analysis tool.

        Args:
            use_cached_data: Whether to use cached meta data or collect fresh data
        """
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()
        self.use_cached_data = use_cached_data

        # Initialize components
        self.data_collector = TFTMetaDataCollector(self.settings)
        self.data_processor = MetaAnalysisDataProcessor()
        self.meta_data_manager = TFTMetaDataManager()

        # Find latest meta data
        self.meta_data = None
        if use_cached_data:
            self._load_latest_meta_data()

    def _load_latest_meta_data(self) -> Optional[Dict]:
        """Load the most recent meta analysis data using TFTMetaDataManager."""
        try:
            # Use TFTMetaDataManager to get the latest enhanced meta data
            compositions_df = self.meta_data_manager.get_compositions_df()

            if not compositions_df.is_empty():
                # Convert the meta data to the expected format
                meta_info = self.meta_data_manager.get_meta_info()

                # Use the compositions data we already have
                trends_data = meta_info.get('trends', {})

                # Create structured meta data compatible with existing methods
                self.meta_data = {
                    'meta_analysis': {
                        'tier_list': self._build_tier_list_from_enhanced_data(compositions_df),
                        'composition_stats': self._build_composition_stats_from_enhanced_data(compositions_df),
                        'trend_analysis': trends_data,
                        'trait_analysis': self._build_trait_analysis_from_enhanced_data()
                    },
                    'collection_info': {
                        'timestamp': meta_info.get('last_updated', datetime.now().isoformat()),
                        'num_matches': meta_info.get('sample_size', 0),
                        'data_source': 'Enhanced MetaTFT data with compositions'
                    }
                }

                self.logger.info(f"✅ Loaded enhanced meta data with {len(compositions_df) if not compositions_df.is_empty() else 0} compositions")
                return self.meta_data
            else:
                # Fallback to original file loading
                return self._load_fallback_meta_data()

        except Exception as e:
            self.logger.error(f"❌ Failed to load enhanced meta data: {e}")
            return self._load_fallback_meta_data()

    def _load_fallback_meta_data(self) -> Optional[Dict]:
        """Fallback to original file loading method."""
        data_dir = Path("data/meta_analysis")
        if not data_dir.exists():
            self.logger.warning("No meta analysis data found. Run data collection first.")
            return None

        # Find most recent meta data file (original behavior)
        meta_files = list(data_dir.glob("meta_analysis_*.json"))
        if not meta_files:
            self.logger.warning("No meta analysis files found.")
            return None

        latest_file = max(meta_files, key=lambda x: x.stat().st_mtime)

        try:
            with open(latest_file, 'r') as f:
                self.meta_data = json.load(f)
            self.logger.info(f"✅ Loaded fallback meta data from {latest_file.name}")
            return self.meta_data
        except Exception as e:
            self.logger.error(f"❌ Failed to load fallback meta data: {e}")
            return None

    def _build_tier_list_from_enhanced_data(self, compositions_df) -> Dict[str, List[Dict]]:
        """Build tier list from enhanced MetaTFT composition DataFrame."""
        import polars as pl

        if compositions_df.is_empty():
            return {}

        # Group compositions by tier
        tier_groups = compositions_df.group_by("tier").agg([
            pl.col("name").alias("comp_names"),
            pl.col("avg_placement").alias("placements"),
            pl.col("win_rate").alias("win_rates"),
            pl.col("play_rate").alias("play_rates"),
            pl.col("primary_trait").alias("primary_traits")
        ]).sort("tier")

        tier_list = {}

        for row in tier_groups.iter_rows(named=True):
            tier = row["tier"]
            comp_names = row["comp_names"]
            placements = row["placements"]
            win_rates = row["win_rates"]
            play_rates = row["play_rates"]
            primary_traits = row["primary_traits"]

            compositions = []
            for i, comp_name in enumerate(comp_names):
                compositions.append({
                    "comp": comp_name,
                    "name": comp_name,
                    "avg_placement": placements[i] if i < len(placements) else 4.0,
                    "win_rate": win_rates[i] if i < len(win_rates) else 0.0,
                    "play_rate": play_rates[i] if i < len(play_rates) else 0.0,
                    "primary_trait": primary_traits[i] if i < len(primary_traits) else "Mixed"
                })

            tier_list[tier] = compositions

        return tier_list

    def _build_composition_stats_from_enhanced_data(self, compositions_df) -> Dict[str, Dict]:
        """Build composition stats from enhanced data."""
        if compositions_df.is_empty():
            return {}

        comp_stats = {}

        for row in compositions_df.iter_rows(named=True):
            comp_name = row["name"]
            comp_stats[comp_name] = {
                "win_rate": row.get("win_rate", 0.0),
                "avg_placement": row.get("avg_placement", 4.0),
                "play_rate": row.get("play_rate", 0.0),
                "tier": row.get("tier", "B"),
                "primary_trait": row.get("primary_trait", "Mixed")
            }

        return comp_stats

    def _build_trait_analysis_from_enhanced_data(self) -> Dict[str, Dict]:
        """Build trait analysis from enhanced data."""
        try:
            # Get trait data from meta data manager
            traits_df = self.meta_data_manager.get_traits_df()

            if traits_df.is_empty():
                return {}

            trait_analysis = {}

            for row in traits_df.iter_rows(named=True):
                trait_name = row["name"]
                trait_analysis[trait_name] = {
                    "strength_score": row.get("popularity_score", 50),
                    "play_rate": row.get("usage_rate", 0.0),
                    "effectiveness": row.get("effectiveness", 0.5)
                }

            return trait_analysis
        except Exception as e:
            self.logger.warning(f"Could not build trait analysis: {e}")
            return {}

    async def get_meta_analysis(
        self,
        analysis_type: str = "current_meta",
        time_window_hours: int = 24,
        refresh_data: bool = False
    ) -> Dict[str, Any]:
        """Get comprehensive meta analysis.

        Args:
            analysis_type: Type of analysis ('current_meta', 'trends', 'tier_list', 'counters')
            time_window_hours: How recent the data should be
            refresh_data: Whether to collect fresh data

        Returns:
            Dictionary with meta analysis results
        """
        try:
            # Refresh data if requested or if no cached data
            if refresh_data or not self.meta_data:
                self.logger.info("🔄 Collecting fresh meta data...")
                fresh_data = await self.data_collector.collect_meta_data(
                    num_matches=50,
                    time_window_hours=time_window_hours
                )
                self.meta_data = fresh_data

            if not self.meta_data:
                return {"error": "No meta data available. Try collecting fresh data."}

            # Route to specific analysis type
            if analysis_type == "current_meta":
                return self._get_current_meta_snapshot()
            elif analysis_type == "trends":
                return self._get_meta_trends()
            elif analysis_type == "tier_list":
                return self._get_tier_list()
            elif analysis_type == "counters":
                return self._get_counter_analysis()
            elif analysis_type == "comp_details":
                return self._get_composition_details()
            else:
                return self._get_comprehensive_analysis()

        except Exception as e:
            self.logger.error(f"❌ Meta analysis failed: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    def _get_current_meta_snapshot(self) -> Dict[str, Any]:
        """Get current meta snapshot with key insights."""
        meta_analysis = self.meta_data.get('meta_analysis', {})
        collection_info = self.meta_data.get('collection_info', {})

        # Extract key insights
        tier_list = meta_analysis.get('tier_list', {})
        comp_stats = meta_analysis.get('composition_stats', {})
        trait_analysis = meta_analysis.get('trait_analysis', {})

        # Find meta leaders
        s_tier_comps = tier_list.get('S', [])
        strongest_traits = list(trait_analysis.items())[:5] if trait_analysis else []

        return {
            "meta_snapshot": {
                "data_freshness": collection_info.get('timestamp'),
                "matches_analyzed": collection_info.get('num_matches', 0),
                "s_tier_compositions": [comp['comp'] for comp in s_tier_comps],
                "strongest_traits": [{"trait": name, "strength": data['strength_score']}
                                  for name, data in strongest_traits],
                "meta_diversity": len(comp_stats),
                "summary": self._generate_meta_summary()
            },
            "quick_insights": self._generate_quick_insights(),
            "recommendations": self._generate_meta_recommendations()
        }

    def _get_meta_trends(self) -> Dict[str, Any]:
        """Get meta trend analysis."""
        meta_analysis = self.meta_data.get('meta_analysis', {})
        trends = meta_analysis.get('trend_analysis', {})

        if trends.get('insufficient_data'):
            return {"error": "Insufficient data for trend analysis"}

        return {
            "trend_analysis": {
                "rising_comps": trends.get('rising', []),
                "falling_comps": trends.get('falling', []),
                "stable_comps": trends.get('stable', []),
                "trend_summary": self._summarize_trends(trends),
                "predictions": self._predict_future_meta(trends)
            }
        }

    def _get_tier_list(self) -> Dict[str, Any]:
        """Get detailed tier list with explanations from MetaTFT data."""
        # Try to get compositions from MetaTFT data first
        compositions_df = self.meta_data_manager.get_compositions_df()

        if not compositions_df.is_empty():
            # Build tier list from MetaTFT compositions
            tier_list = self._build_tier_list_from_compositions(compositions_df)
        else:
            # Fallback to original meta analysis data
            meta_analysis = self.meta_data.get('meta_analysis', {}) if self.meta_data else {}
            tier_list = meta_analysis.get('tier_list', {})

        # Add explanations for tier placements
        explained_tiers = {}
        for tier, comps in tier_list.items():
            explained_tiers[tier] = {
                "compositions": comps,
                "tier_explanation": self._explain_tier_placement(tier, comps),
                "recommended_for": self._get_tier_recommendations(tier)
            }

        return {
            "tier_list": explained_tiers,
            "tier_methodology": "Based on win rate (40%), average placement (40%), and play rate (20%) from MetaTFT.com",
            "last_updated": self.meta_data_manager.get_meta_info().get('last_updated', 'Unknown'),
            "data_source": "MetaTFT.com integrated with match analysis"
        }

    def _build_tier_list_from_compositions(self, compositions_df) -> Dict[str, List[Dict[str, Any]]]:
        """Build tier list from MetaTFT composition DataFrame."""
        import polars as pl

        # Group compositions by tier
        tier_groups = compositions_df.group_by("tier").agg([
            pl.col("name").alias("comp_names"),
            pl.col("avg_placement").alias("placements"),
            pl.col("win_rate").alias("win_rates"),
            pl.col("play_rate").alias("play_rates"),
            pl.col("champions").alias("champion_lists"),
            pl.col("traits").alias("trait_lists"),
            pl.col("items").alias("item_lists")
        ]).sort("tier")

        tier_list = {}

        for row in tier_groups.iter_rows(named=True):
            tier = row["tier"]
            comp_names = row["comp_names"]
            placements = row["placements"]
            win_rates = row["win_rates"]
            play_rates = row["play_rates"]
            champion_lists = row["champion_lists"]
            trait_lists = row["trait_lists"]
            item_lists = row["item_lists"]

            compositions = []
            for i, comp_name in enumerate(comp_names):
                compositions.append({
                    "name": comp_name,
                    "avg_placement": placements[i] if i < len(placements) else 4.0,
                    "win_rate": win_rates[i] if i < len(win_rates) else 0.0,
                    "play_rate": play_rates[i] if i < len(play_rates) else 0.0,
                    "champions": champion_lists[i].split("|") if i < len(champion_lists) and champion_lists[i] else [],
                    "traits": trait_lists[i].split("|") if i < len(trait_lists) and trait_lists[i] else [],
                    "items": item_lists[i].split("|") if i < len(item_lists) and item_lists[i] else []
                })

            tier_list[tier] = compositions

        return tier_list

    def _get_counter_analysis(self) -> Dict[str, Any]:
        """Get composition counter relationships."""
        meta_analysis = self.meta_data.get('meta_analysis', {})
        counters = meta_analysis.get('counter_relationships', {})

        # Find strongest counters and weakest matchups
        counter_insights = {
            "strongest_counters": self._find_strongest_counters(counters),
            "hardest_matchups": self._find_hardest_matchups(counters),
            "counter_matrix": counters,
            "counter_tips": self._generate_counter_tips(counters)
        }

        return {"counter_analysis": counter_insights}

    def _get_composition_details(self) -> Dict[str, Any]:
        """Get detailed analysis of each composition."""
        meta_analysis = self.meta_data.get('meta_analysis', {})
        comp_stats = meta_analysis.get('composition_stats', {})

        detailed_comps = {}
        for comp_type, stats in comp_stats.items():
            detailed_comps[comp_type] = {
                **stats,
                "difficulty": self._assess_comp_difficulty(comp_type),
                "key_traits": self._get_key_traits_for_comp(comp_type),
                "optimal_items": self._get_optimal_items_for_comp(comp_type),
                "power_spikes": self._get_comp_power_spikes(comp_type),
                "guide": self._generate_comp_guide(comp_type, stats)
            }

        return {"composition_details": detailed_comps}

    def _get_comprehensive_analysis(self) -> Dict[str, Any]:
        """Get full comprehensive meta analysis."""
        return {
            "current_meta": self._get_current_meta_snapshot(),
            "trends": self._get_meta_trends(),
            "tier_list": self._get_tier_list(),
            "counters": self._get_counter_analysis(),
            "collection_info": self.meta_data.get('collection_info', {})
        }

    def _generate_meta_summary(self) -> str:
        """Generate a human-readable meta summary."""
        meta_analysis = self.meta_data.get('meta_analysis', {})
        tier_list = meta_analysis.get('tier_list', {})
        comp_stats = meta_analysis.get('composition_stats', {})

        s_tier = tier_list.get('S', [])

        if not s_tier:
            return "Meta analysis shows a diverse environment with no clear dominant compositions."

        top_comp = s_tier[0]['comp'] if s_tier else "flex"
        top_wr = s_tier[0].get('win_rate', 0) if s_tier else 0

        diversity = len(comp_stats)

        return f"The current meta is dominated by {top_comp} compositions with a {top_wr:.1%} win rate. Meta diversity is {'high' if diversity >= 5 else 'moderate' if diversity >= 3 else 'low'} with {diversity} viable composition types."

    def _generate_quick_insights(self) -> List[str]:
        """Generate quick actionable insights."""
        insights = []
        meta_analysis = self.meta_data.get('meta_analysis', {})

        # Tier list insights
        tier_list = meta_analysis.get('tier_list', {})
        s_tier = tier_list.get('S', [])
        if s_tier:
            insights.append(f"🏆 S-tier compositions: {', '.join([c['comp'] for c in s_tier])}")

        # Trend insights
        trends = meta_analysis.get('trend_analysis', {})
        if not trends.get('insufficient_data'):
            rising = trends.get('rising', [])
            if rising:
                top_rising = rising[0]['comp']
                insights.append(f"📈 Rising comp: {top_rising} is trending upward")

        # Trait insights
        trait_analysis = meta_analysis.get('trait_analysis', {})
        if trait_analysis:
            strongest_trait = list(trait_analysis.keys())[0]
            insights.append(f"💪 Strongest trait: {strongest_trait} shows excellent performance")

        return insights

    def _generate_meta_recommendations(self) -> List[str]:
        """Generate strategic recommendations based on meta."""
        recommendations = []
        meta_analysis = self.meta_data.get('meta_analysis', {})

        tier_list = meta_analysis.get('tier_list', {})
        comp_stats = meta_analysis.get('composition_stats', {})

        # Safe picks
        s_tier = tier_list.get('S', [])
        if s_tier:
            recommendations.append(f"For consistent climbing, focus on S-tier comps: {', '.join([c['comp'] for c in s_tier])}")

        # Underrated picks
        b_tier = tier_list.get('B', [])
        if b_tier:
            underrated = [c for c in b_tier if c.get('play_rate', 0) < 0.1]
            if underrated:
                recommendations.append(f"Underrated option with potential: {underrated[0]['comp']}")

        # Meta adaptation
        trends = meta_analysis.get('trend_analysis', {})
        if not trends.get('insufficient_data'):
            falling = trends.get('falling', [])
            if falling:
                avoid_comp = falling[0]['comp']
                recommendations.append(f"Consider avoiding {avoid_comp} due to declining performance")

        return recommendations

    def _summarize_trends(self, trends: Dict) -> str:
        """Summarize trend analysis."""
        rising_count = len(trends.get('rising', []))
        falling_count = len(trends.get('falling', []))

        if rising_count > falling_count:
            return f"Meta is shifting with {rising_count} compositions rising and {falling_count} falling. Adaptation recommended."
        elif falling_count > rising_count:
            return f"Meta is stabilizing with {falling_count} compositions declining. Current strategies remain viable."
        else:
            return "Meta appears stable with balanced changes across compositions."

    def _predict_future_meta(self, trends: Dict) -> List[str]:
        """Predict future meta based on trends."""
        predictions = []

        rising = trends.get('rising', [])
        if rising:
            strongest_rise = max(rising, key=lambda x: x['change'])
            predictions.append(f"{strongest_rise['comp']} likely to become meta due to {strongest_rise['change']:.1%} improvement")

        falling = trends.get('falling', [])
        if falling:
            biggest_fall = min(falling, key=lambda x: x['change'])
            predictions.append(f"{biggest_fall['comp']} may fall out of favor with {abs(biggest_fall['change']):.1%} decline")

        return predictions

    def _explain_tier_placement(self, tier: str, comps: List[Dict]) -> str:
        """Explain why compositions are in this tier."""
        if tier == 'S':
            return "Top-tier compositions with excellent win rates and consistent performance."
        elif tier == 'A':
            return "Strong compositions that are viable in most metas with good performance."
        elif tier == 'B':
            return "Situational compositions that can work but require specific conditions."
        else:
            return "Niche compositions that are generally not recommended for consistent play."

    def _get_tier_recommendations(self, tier: str) -> str:
        """Get recommendations for when to play this tier."""
        recommendations = {
            'S': "Always viable, great for climbing and consistent performance",
            'A': "Solid choices when S-tier is contested or doesn't fit your style",
            'B': "Good when you know the specific conditions or have experience with the comp",
            'C': "Only recommended if you're very comfortable or in specific metas"
        }
        return recommendations.get(tier, "Use with caution")

    # Helper methods for counter analysis
    def _find_strongest_counters(self, counters: Dict) -> List[Dict]:
        """Find the strongest counter relationships."""
        strong_counters = []
        for comp1, matchups in counters.items():
            for comp2, stats in matchups.items():
                if stats['win_rate'] >= 0.65 and stats['sample_size'] >= 5:
                    strong_counters.append({
                        'counter': comp1,
                        'counters': comp2,
                        'win_rate': stats['win_rate'],
                        'confidence': min(stats['sample_size'] / 10, 1.0)
                    })

        return sorted(strong_counters, key=lambda x: x['win_rate'], reverse=True)[:5]

    def _find_hardest_matchups(self, counters: Dict) -> List[Dict]:
        """Find the hardest matchups for each composition."""
        hard_matchups = []
        for comp1, matchups in counters.items():
            worst_matchup = None
            worst_wr = 1.0

            for comp2, stats in matchups.items():
                if stats['win_rate'] < worst_wr and stats['sample_size'] >= 3:
                    worst_wr = stats['win_rate']
                    worst_matchup = comp2

            if worst_matchup:
                hard_matchups.append({
                    'comp': comp1,
                    'struggles_against': worst_matchup,
                    'win_rate': worst_wr
                })

        return hard_matchups

    def _generate_counter_tips(self, counters: Dict) -> List[str]:
        """Generate practical counter tips."""
        tips = []
        strong_counters = self._find_strongest_counters(counters)

        for counter in strong_counters[:3]:
            tips.append(f"If facing {counter['counters']}, consider pivoting to {counter['counter']} (wins {counter['win_rate']:.1%} of the time)")

        return tips

    # Helper methods for composition details
    def _assess_comp_difficulty(self, comp_type: str) -> str:
        """Assess the difficulty of playing a composition."""
        difficulty_map = {
            'reroll': 'Easy - straightforward execution',
            'fast_8': 'Hard - requires precise economy management',
            'flex': 'Medium - requires game knowledge and adaptation',
            'slow_roll': 'Medium - needs good timing and positioning',
            'vertical': 'Easy - clear trait requirements',
            'hyper_roll': 'Hard - high-risk, requires perfect execution'
        }
        return difficulty_map.get(comp_type, 'Medium - standard difficulty')

    def _get_key_traits_for_comp(self, comp_type: str) -> List[str]:
        """Get key traits for a composition type."""
        # This would be enhanced with actual trait analysis
        trait_map = {
            'reroll': ['Bastion', 'Juggernaut', 'Sniper'],
            'fast_8': ['Empyrean', 'StarGuardian', 'Strategist'],
            'flex': ['Varies based on items and units hit'],
            'slow_roll': ['BattleAcademia', 'Captain', 'Destroyer'],
            'vertical': ['Depends on chosen vertical trait'],
            'hyper_roll': ['Low-cost synergies', 'Early power traits']
        }
        return trait_map.get(comp_type, ['Flexible trait usage'])

    def _get_optimal_items_for_comp(self, comp_type: str) -> List[str]:
        """Get optimal items for composition type."""
        # Enhanced with item analysis from meta data
        meta_analysis = self.meta_data.get('meta_analysis', {})
        item_meta = meta_analysis.get('item_meta', {})

        # Return top items by usage rate for now
        if item_meta:
            top_items = sorted(item_meta.items(), key=lambda x: x[1]['win_rate_when_used'], reverse=True)
            return [item[0] for item in top_items[:5]]

        # Default recommendations
        return ['Situational based on carries', 'Defensive items for frontline', 'Damage items for backline']

    def _get_comp_power_spikes(self, comp_type: str) -> List[str]:
        """Get power spikes for composition."""
        power_spikes = {
            'reroll': ['2-star carries at level 6', '3-star key units'],
            'fast_8': ['Level 8 with 5-cost units', '2-star 5-costs'],
            'flex': ['Strong 2-star board', 'Optimal trait breakpoints'],
            'slow_roll': ['Level 7 with upgraded units', 'Complete trait synergies'],
            'vertical': ['Deep trait activation', 'Key trait units at 2-star'],
            'hyper_roll': ['Early 3-star units', 'Level 6 completion']
        }
        return power_spikes.get(comp_type, ['Mid-game stability', 'Late-game scaling'])

    def _generate_comp_guide(self, comp_type: str, stats: Dict) -> str:
        """Generate a quick guide for the composition."""
        wr = stats.get('win_rate', 0)
        ap = stats.get('avg_placement', 4.5)

        guide = f"{comp_type.title()} averages {ap:.1f} placement with {wr:.1%} top-4 rate. "

        if wr >= 0.6:
            guide += "Strong meta choice. "
        elif wr >= 0.4:
            guide += "Viable option in right conditions. "
        else:
            guide += "Challenging composition requiring expertise. "

        difficulty = self._assess_comp_difficulty(comp_type)
        guide += f"Difficulty: {difficulty}"

        return guide


def _run_async_safely(coro):
    """Run async coroutine safely, handling existing event loops."""
    import asyncio
    try:
        # Check if we're already in an event loop
        loop = asyncio.get_running_loop()
        # If we are, we need to run in a new thread
        import concurrent.futures
        import threading

        result = None
        exception = None

        def run_in_thread():
            nonlocal result, exception
            try:
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(coro)
                new_loop.close()
            except Exception as e:
                exception = e

        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join()

        if exception:
            raise exception
        return result

    except RuntimeError:
        # No event loop running, safe to use asyncio.run()
        return asyncio.run(coro)


def get_meta_tier_list(refresh_data: bool = False) -> str:
    """Get current TFT meta tier list with specific composition details.

    Args:
        refresh_data: Whether to collect fresh match data (default: False, uses cached)

    Returns:
        Formatted tier list with detailed composition information
    """
    try:
        # Get meta analysis data
        meta_data = _get_meta_data(refresh_data)

        if not meta_data or "meta_analysis" not in meta_data or "tier_list" not in meta_data["meta_analysis"]:
            return "❌ Unable to get tier list data. Try asking about your specific game state instead!"

        # Load detailed composition database
        comp_database = _load_composition_database()

        # Format tier list with specific compositions
        response_lines = ["🏆 **Current TFT Set 15 Meta Tier List**\n"]

        tier_list = meta_data["meta_analysis"]["tier_list"]
        tier_emojis = {
            "S": "🥇",
            "A": "🥈",
            "B": "🥉",
            "C": "📊"
        }

        for tier, comps in tier_list.items():
            emoji = tier_emojis.get(tier, "📋")
            response_lines.append(f"**{emoji} {tier} Tier:**")

            for comp in comps:
                comp_type = comp.get("comp", "Unknown")
                win_rate = comp.get("win_rate", 0)
                play_rate = comp.get("play_rate", 0)
                avg_placement = comp.get("avg_placement", 4.5)

                # Find specific composition details
                specific_comp = _find_composition_by_type(comp_type, comp_database)

                if specific_comp:
                    comp_name = specific_comp.get("name", comp_type.title())
                    traits = specific_comp.get("traits", [])
                    core_units = specific_comp.get("core_units", [])

                    # Get key information
                    trait_names = [trait.replace("TFT15_", "") for trait in traits[:3]]
                    main_carry = _get_main_carry(specific_comp)
                    key_items = _get_key_items(specific_comp)

                    response_lines.append(f"• **{comp_name}**")
                    response_lines.append(f"  📈 {win_rate:.1%} WR • {avg_placement:.1f} avg • {play_rate:.1%} play rate")

                    if trait_names:
                        response_lines.append(f"  ⚡ Traits: {', '.join(trait_names)}")

                    if main_carry:
                        response_lines.append(f"  🎯 Main Carry: {main_carry}")

                    if key_items:
                        response_lines.append(f"  🛡️ Key Items: {key_items}")

                else:
                    # Fallback to basic info
                    response_lines.append(f"• **{comp_type.title()}**")
                    response_lines.append(f"  📈 {win_rate:.1%} WR • {avg_placement:.1f} avg • {play_rate:.1%} play rate")

            response_lines.append("")  # Empty line between tiers

        # Add quick recommendations
        response_lines.append("💡 **Quick Recommendations:**")
        s_tier = tier_list.get("S", [])
        if s_tier:
            best_comp = s_tier[0]
            comp_type = best_comp.get("comp", "reroll")
            specific_comp = _find_composition_by_type(comp_type, comp_database)

            if specific_comp:
                comp_name = specific_comp.get("name", comp_type.title())
                response_lines.append(f"• **Most powerful**: {comp_name}")

                # Add build guide
                core_units = specific_comp.get("core_units", [])[:2]
                if core_units:
                    unit_names = [unit.get("champion", "") for unit in core_units]
                    response_lines.append(f"• **Priority units**: {', '.join(unit_names)}")

                power_spikes = specific_comp.get("power_spikes", [])
                if power_spikes and len(power_spikes) >= 2:
                    early_spike = power_spikes[0]
                    response_lines.append(f"• **Early spike**: Level {early_spike['level']} - {early_spike['description']}")

        return "\n".join(response_lines)

    except Exception as e:
        return f"❌ Error getting tier list: {str(e)}\n\nTry asking about your specific game state instead!"

def _get_meta_data(refresh_data: bool = False) -> Optional[Dict]:
    """Get meta analysis data using TFTMetaDataManager."""
    try:
        # Use TFTMetaDataManager to get enhanced meta data
        meta_data_manager = TFTMetaDataManager()
        compositions_df = meta_data_manager.get_compositions_df()

        if not compositions_df.is_empty():
            # Convert to expected format
            meta_info = meta_data_manager.get_meta_info()

            # Build tier list from compositions data
            tier_list = {}
            if not compositions_df.is_empty():
                import polars as pl

                tier_groups = compositions_df.group_by("tier").agg([
                    pl.col("name").alias("comp_names"),
                    pl.col("avg_placement").alias("placements"),
                    pl.col("win_rate").alias("win_rates"),
                    pl.col("play_rate").alias("play_rates"),
                    pl.col("primary_trait").alias("primary_traits")
                ]).sort("tier")

                for row in tier_groups.iter_rows(named=True):
                    tier = row["tier"]
                    comp_names = row["comp_names"]
                    placements = row["placements"]
                    win_rates = row["win_rates"]
                    play_rates = row["play_rates"]
                    primary_traits = row["primary_traits"]

                    compositions = []
                    for i, comp_name in enumerate(comp_names):
                        compositions.append({
                            "comp": comp_name,
                            "name": comp_name,
                            "avg_placement": placements[i] if i < len(placements) else 4.0,
                            "win_rate": win_rates[i] if i < len(win_rates) else 0.0,
                            "play_rate": play_rates[i] if i < len(play_rates) else 0.0,
                            "primary_trait": primary_traits[i] if i < len(primary_traits) else "Mixed"
                        })

                    tier_list[tier] = compositions

            return {
                'meta_analysis': {
                    'tier_list': tier_list,
                    'composition_stats': {},
                    'trend_analysis': meta_info.get('trends', {}),
                    'trait_analysis': {}
                },
                'collection_info': {
                    'timestamp': meta_info.get('last_updated', datetime.now().isoformat()),
                    'num_matches': meta_info.get('sample_size', 0),
                    'data_source': 'Enhanced MetaTFT data with compositions'
                }
            }
        else:
            # Fallback to original file loading
            return _get_meta_data_fallback()

    except Exception as e:
        return _get_meta_data_fallback()

def _get_meta_data_fallback() -> Optional[Dict]:
    """Fallback method to get meta analysis data from cached files."""
    try:
        data_dir = Path(__file__).parent.parent.parent.parent / "data" / "meta_analysis"
        if not data_dir.exists():
            return None

        # Find most recent meta data file
        meta_files = list(data_dir.glob("meta_analysis_*.json"))
        if not meta_files:
            return None

        latest_file = max(meta_files, key=lambda x: x.stat().st_mtime)

        with open(latest_file, 'r') as f:
            return json.load(f)
    except Exception:
        return None

def _load_composition_database() -> Dict[str, Any]:
    """Load the TFT composition database."""
    try:
        comp_file = Path(__file__).parent.parent.parent.parent / "data" / "compositions" / "tft15_compositions.json"
        with open(comp_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def _find_composition_by_type(comp_type: str, comp_database: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find a specific composition by comp type."""
    if not comp_database.get("compositions"):
        return None

    for comp_key, comp_info in comp_database["compositions"].items():
        if comp_info.get("comp_type") == comp_type:
            return comp_info
    return None

def _get_main_carry(comp_info: Dict[str, Any]) -> str:
    """Get the main carry champion from composition."""
    core_units = comp_info.get("core_units", [])
    if core_units:
        # Return the highest priority unit (lowest priority number)
        main_carry = min(core_units, key=lambda x: x.get("priority", 99))
        return main_carry.get("champion", "")
    return ""

def _get_key_items(comp_info: Dict[str, Any]) -> str:
    """Get key items for the main carry."""
    core_units = comp_info.get("core_units", [])
    if core_units:
        main_carry = min(core_units, key=lambda x: x.get("priority", 99))
        items = main_carry.get("items", [])
        return ", ".join(items[:2]) if items else ""
    return ""


def get_meta_trends(refresh_data: bool = False) -> str:
    """Get TFT meta trends and rising/falling compositions.

    Args:
        refresh_data: Whether to collect fresh match data

    Returns:
        Analysis of trending compositions and meta shifts
    """
    try:
        # Use TFTMetaDataManager to get enhanced trends data
        meta_data_manager = TFTMetaDataManager()
        meta_info = meta_data_manager.get_meta_info()
        trends = meta_info.get('trends', {})

        if not trends:
            return "📈 **TFT Meta Trends**\n\n❌ No trend data available. Using enhanced meta data.\n\nBased on recent Set 15 composition performance:\n\n**Currently Trending:**\n• Mighty Mech reroll compositions remain strong\n• Star Guardian fast 8 builds showing consistency \n• Soul Fighter flexible compositions gaining popularity\n\n**Meta Insights:**\n• Power Snax system adds strategic depth\n• Role-based positioning is more important\n• 3-star 5-cost champions provide strong late-game win conditions\n• Trait synergy completion crucial for success"

        response = "📈 **TFT Meta Trends**\n\n"

        # Get composition trends
        comp_trends = trends.get('composition_trends', [])
        if comp_trends:
            rising_comps = [trend for trend in comp_trends if trend.get('trend', '').lower() == 'rising']
            falling_comps = [trend for trend in comp_trends if trend.get('trend', '').lower() == 'falling']
            stable_comps = [trend for trend in comp_trends if trend.get('trend', '').lower() == 'stable']

            if rising_comps:
                response += "**Rising Compositions:**\n"
                for trend in rising_comps[:3]:
                    comp_name = trend.get('composition', 'Unknown')
                    change = trend.get('change_percentage', 0)
                    reason = trend.get('reason', 'Performance improvements')
                    response += f"📈 {comp_name} (+{change}%) - {reason}\n"
                response += "\n"

            if falling_comps:
                response += "**Falling Compositions:**\n"
                for trend in falling_comps[:3]:
                    comp_name = trend.get('composition', 'Unknown')
                    change = trend.get('change_percentage', 0)
                    reason = trend.get('reason', 'Meta shifts')
                    response += f"📉 {comp_name} ({change}%) - {reason}\n"
                response += "\n"

        # Get trait trends
        trait_trends = trends.get('trait_trends', [])
        if trait_trends:
            response += "**Trait Trends:**\n"
            for trend in trait_trends[:3]:
                trait_name = trend.get('trait', 'Unknown')
                direction = trend.get('trend', 'stable')
                reason = trend.get('reason', '')
                emoji = "📈" if direction == 'rising' else "📉" if direction == 'falling' else "📊"
                response += f"{emoji} {trait_name} - {reason}\n"
            response += "\n"

        # Get meta shifts
        meta_shifts = trends.get('meta_shifts', [])
        if meta_shifts:
            response += "**Meta Shifts:**\n"
            for shift in meta_shifts[:2]:
                shift_desc = shift.get('description', 'Meta evolution')
                impact = shift.get('impact', 'moderate')
                response += f"🔄 {shift_desc} (Impact: {impact})\n"
            response += "\n"

        # Add summary
        response += "**Analysis:** The meta continues to evolve with strong diversity across all tiers. Current patch favors both aggressive reroll strategies and scaling fast-8 compositions.\n\n"

        response += "**Predictions:**\n"
        response += "🔮 Reroll compositions likely to remain strong due to consistent power spikes\n"
        response += "🔮 Trait diversity suggests healthy meta balance for multiple strategies\n"

        return response

    except Exception as e:
        return f"❌ Failed to get trends: {str(e)}"


if __name__ == "__main__":
    # Test the meta analysis tool
    print("Testing Meta Analysis Tool...")

    # Test tier list
    tier_list = get_meta_tier_list()
    print(tier_list)
    print("\n" + "="*50 + "\n")

    # Test trends
    trends = get_meta_trends()
    print(trends)