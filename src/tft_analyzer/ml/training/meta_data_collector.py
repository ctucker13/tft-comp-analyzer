#!/usr/bin/env python3
"""
TFT Meta Analysis Data Collector

Collects and processes match data specifically for meta composition analysis.
Focuses on composition trends, win rates, and meta patterns across multiple matches.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

try:
    from ...data.riot_api import RiotTFTAPI
    from ...config.settings import Settings
    from ..data.schemas import CompType
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from src.tft_analyzer.data.riot_api import RiotTFTAPI
    from config.settings import Settings
    from src.tft_analyzer.ml.data.schemas import CompType


class TFTMetaDataCollector:
    """Collects and processes match data for meta analysis."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.riot_client = RiotTFTAPI(settings.riot_api_key, settings.riot_region, use_cache=True)
        self.logger = logging.getLogger(__name__)

        # Data storage
        self.data_dir = Path("data/meta_analysis")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Composition classification helpers
        self.comp_classifiers = self._setup_comp_classifiers()

    def _setup_comp_classifiers(self) -> Dict[str, Dict]:
        """Setup heuristics for classifying compositions."""
        return {
            'reroll': {
                'max_level': 7,
                'min_3star_units': 1,
                'typical_traits': ['TFT15_Bastion', 'TFT15_Juggernaut', 'TFT15_Sniper']
            },
            'fast_8': {
                'min_level': 8,
                'max_3star_units': 0,
                'focus_5cost': True,
                'typical_traits': ['TFT15_Empyrean', 'TFT15_StarGuardian']
            },
            'flex': {
                'varied_traits': True,
                'adaptive_units': True
            },
            'slow_roll': {
                'level_range': (6, 7),
                'economic_focus': True,
                'gradual_improvement': True
            },
            'vertical': {
                'deep_traits': True,
                'min_trait_depth': 6
            },
            'hyper_roll': {
                'max_level': 5,
                'aggressive_rolling': True,
                'early_3stars': True
            }
        }

    async def collect_meta_data(
        self,
        num_matches: int = 100,
        tiers: List[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Collect comprehensive meta data from recent matches.

        Args:
            num_matches: Number of matches to analyze
            tiers: Player tiers to focus on (default: ['CHALLENGER', 'GRANDMASTER', 'MASTER'])
            time_window_hours: How recent matches should be (default: 24 hours)

        Returns:
            Dictionary containing meta analysis data
        """
        if tiers is None:
            tiers = ['CHALLENGER', 'GRANDMASTER', 'MASTER']

        self.logger.info(f"🔍 Starting meta analysis data collection: {num_matches} matches")

        try:
            # Get high-tier players
            players = await self._get_meta_players(tiers)
            self.logger.info(f"Found {len(players)} high-tier players")

            # Collect matches with composition analysis
            matches_data = await self._collect_matches_with_meta_info(players, num_matches, time_window_hours)

            # Process matches for meta insights
            meta_analysis = self._analyze_meta_patterns(matches_data)

            # Save data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"meta_analysis_{len(matches_data)}matches_{timestamp}.json"
            filepath = self.data_dir / filename

            output_data = {
                'meta_analysis': meta_analysis,
                'raw_matches': matches_data,
                'collection_info': {
                    'timestamp': timestamp,
                    'num_matches': len(matches_data),
                    'tiers': tiers,
                    'time_window_hours': time_window_hours
                }
            }

            with open(filepath, 'w') as f:
                json.dump(output_data, f, indent=2, default=str)

            self.logger.info(f"✅ Meta data saved to {filepath}")
            return output_data

        except Exception as e:
            self.logger.error(f"❌ Meta data collection failed: {e}")
            raise

    async def _get_meta_players(self, tiers: List[str]) -> List[Dict[str, str]]:
        """Get players from specified tiers for meta analysis."""
        players = []

        for tier in tiers:
            try:
                if tier.upper() == 'CHALLENGER':
                    tier_players = await self.riot_client.get_challenger_players()
                elif tier.upper() == 'GRANDMASTER':
                    tier_players = await self.riot_client.get_grandmaster_players()
                elif tier.upper() == 'MASTER':
                    tier_players = await self.riot_client.get_master_players()
                else:
                    continue

                # Add tier info to each player
                for player in tier_players:
                    player['tier'] = tier.upper()
                    players.append(player)

                await asyncio.sleep(1)  # Rate limit

            except Exception as e:
                self.logger.warning(f"Failed to get {tier} players: {e}")

        return players

    async def _collect_matches_with_meta_info(
        self,
        players: List[Dict],
        target_matches: int,
        time_window_hours: int
    ) -> List[Dict]:
        """Collect matches with detailed composition information."""
        matches_data = []
        processed_match_ids = set()

        cutoff_time = datetime.now() - timedelta(hours=time_window_hours)

        for player in players[:min(len(players), target_matches // 5)]:  # Limit players to get diverse matches
            try:
                puuid = player['puuid']
                matches = await self.riot_client.get_match_history(puuid, count=20)

                for match_id in matches:
                    if match_id in processed_match_ids:
                        continue

                    if len(matches_data) >= target_matches:
                        break

                    # Get detailed match info
                    match_details = await self.riot_client.get_match_details(match_id)

                    if not self._is_valid_meta_match(match_details, cutoff_time):
                        continue

                    # Process match for meta analysis
                    meta_match_data = self._process_match_for_meta(match_details)
                    matches_data.append(meta_match_data)
                    processed_match_ids.add(match_id)

                    self.logger.info(f"Processed match {len(matches_data)}/{target_matches}")

                    await asyncio.sleep(1)  # Rate limit

                if len(matches_data) >= target_matches:
                    break

            except Exception as e:
                self.logger.warning(f"Failed to process player {player.get('summonerName', 'unknown')}: {e}")

        return matches_data

    def _is_valid_meta_match(self, match_details: Dict, cutoff_time: datetime) -> bool:
        """Check if match is valid for meta analysis."""
        info = match_details.get('info', {})

        # Check patch version
        game_version = info.get('game_version', '')
        if not game_version.startswith('15.'):  # Set 15 only
            return False

        # Check time
        game_datetime = datetime.fromtimestamp(info.get('game_datetime', 0) / 1000)
        if game_datetime < cutoff_time:
            return False

        # Check match quality
        participants = info.get('participants', [])
        if len(participants) != 8:  # Standard TFT match
            return False

        return True

    def _process_match_for_meta(self, match_details: Dict) -> Dict:
        """Process single match for meta analysis."""
        info = match_details.get('info', {})
        participants = info.get('participants', [])

        match_meta = {
            'match_id': match_details.get('metadata', {}).get('match_id'),
            'game_datetime': info.get('game_datetime'),
            'game_length': info.get('game_length'),
            'patch_version': info.get('game_version'),
            'participants': []
        }

        for participant in participants:
            participant_meta = {
                'placement': participant.get('placement'),
                'level': participant.get('level'),
                'total_damage_to_players': participant.get('total_damage_to_players'),
                'comp_analysis': self._analyze_participant_composition(participant),
                'board_state': self._extract_board_composition(participant),
                'trait_summary': self._summarize_traits(participant),
                'item_analysis': self._analyze_items(participant),
                'economic_metrics': self._extract_economic_metrics(participant)
            }
            match_meta['participants'].append(participant_meta)

        return match_meta

    def _analyze_participant_composition(self, participant: Dict) -> Dict:
        """Classify and analyze participant's composition."""
        level = participant.get('level', 1)
        units = participant.get('units', [])
        traits = participant.get('traits', [])

        # Count unit tiers
        tier_counts = Counter(unit.get('tier', 1) for unit in units)
        three_star_units = tier_counts.get(3, 0)

        # Analyze traits
        active_traits = [t for t in traits if t.get('tier_current', 0) > 0]
        max_trait_depth = max((t.get('num_units', 0) for t in active_traits), default=0)

        # Classify composition
        comp_type = self._classify_composition(level, three_star_units, active_traits, max_trait_depth)

        return {
            'comp_type': comp_type,
            'level': level,
            'num_units': len(units),
            'three_star_count': three_star_units,
            'active_traits_count': len(active_traits),
            'max_trait_depth': max_trait_depth,
            'board_power_estimate': self._estimate_board_power(units, active_traits)
        }

    def _classify_composition(
        self,
        level: int,
        three_star_units: int,
        active_traits: List[Dict],
        max_trait_depth: int
    ) -> str:
        """Classify composition type based on characteristics."""

        # Reroll indicators
        if level <= 7 and three_star_units >= 1:
            return 'reroll'

        # Fast 8 indicators
        if level >= 8 and three_star_units == 0:
            five_cost_focus = any(
                unit_cost >= 5 for trait in active_traits
                for unit_cost in [5]  # Simplified - would need unit cost lookup
            )
            if five_cost_focus:
                return 'fast_8'

        # Hyper roll indicators
        if level <= 5 and three_star_units >= 1:
            return 'hyper_roll'

        # Vertical indicators
        if max_trait_depth >= 6:
            return 'vertical'

        # Slow roll indicators
        if 6 <= level <= 7 and len(active_traits) <= 4:
            return 'slow_roll'

        # Default to flex
        return 'flex'

    def _extract_board_composition(self, participant: Dict) -> Dict:
        """Extract detailed board composition."""
        units = participant.get('units', [])

        composition = {
            'unit_distribution': {},
            'cost_distribution': defaultdict(int),
            'carry_units': [],
            'support_units': []
        }

        for unit in units:
            unit_id = unit.get('character_id', '')
            tier = unit.get('tier', 1)
            cost = self._get_unit_cost(unit_id)  # Would need unit cost database

            composition['unit_distribution'][unit_id] = {
                'tier': tier,
                'cost': cost,
                'items': unit.get('itemNames', [])
            }

            composition['cost_distribution'][cost] += 1

            # Classify as carry or support based on items and tier
            if tier >= 2 or len(unit.get('itemNames', [])) >= 2:
                composition['carry_units'].append(unit_id)
            else:
                composition['support_units'].append(unit_id)

        return composition

    def _summarize_traits(self, participant: Dict) -> Dict:
        """Summarize trait activations and synergies."""
        traits = participant.get('traits', [])

        summary = {
            'active_traits': {},
            'trait_coverage': 0,
            'synergy_score': 0
        }

        for trait in traits:
            if trait.get('tier_current', 0) > 0:
                trait_name = trait.get('name', '')
                summary['active_traits'][trait_name] = {
                    'tier': trait.get('tier_current'),
                    'units': trait.get('num_units', 0)
                }

        summary['trait_coverage'] = len(summary['active_traits'])
        summary['synergy_score'] = sum(
            t['tier'] * t['units'] for t in summary['active_traits'].values()
        )

        return summary

    def _analyze_items(self, participant: Dict) -> Dict:
        """Analyze item usage and optimization."""
        units = participant.get('units', [])

        analysis = {
            'total_items': 0,
            'item_efficiency': 0,
            'carry_items': [],
            'item_distribution': defaultdict(int)
        }

        for unit in units:
            items = unit.get('itemNames', [])
            analysis['total_items'] += len(items)

            for item in items:
                analysis['item_distribution'][item] += 1

                # Track items on likely carries (2+ star units or 3+ items)
                if unit.get('tier', 1) >= 2 or len(items) >= 3:
                    analysis['carry_items'].append({
                        'unit': unit.get('character_id'),
                        'item': item
                    })

        # Calculate efficiency (items per unit, capped at reasonable levels)
        num_units = max(len(units), 1)
        analysis['item_efficiency'] = min(analysis['total_items'] / num_units, 3.0)

        return analysis

    def _extract_economic_metrics(self, participant: Dict) -> Dict:
        """Extract economic performance metrics."""
        return {
            'final_level': participant.get('level', 1),
            'gold_left': participant.get('gold_left', 0),
            'last_round': participant.get('last_round', 0),
            'total_damage_dealt': participant.get('total_damage_to_players', 0),
            'damage_per_round': participant.get('total_damage_to_players', 0) / max(participant.get('last_round', 1), 1)
        }

    def _estimate_board_power(self, units: List[Dict], traits: List[Dict]) -> float:
        """Estimate overall board power."""
        unit_power = sum(
            unit.get('tier', 1) * self._get_unit_cost(unit.get('character_id', ''))
            for unit in units
        )

        trait_power = sum(
            trait.get('tier_current', 0) * trait.get('num_units', 0)
            for trait in traits if trait.get('tier_current', 0) > 0
        )

        return unit_power + trait_power * 0.5

    def _get_unit_cost(self, unit_id: str) -> int:
        """Get unit cost (would need actual unit database)."""
        # Simplified cost estimation based on unit name patterns
        if 'TFT15_' in unit_id:
            # This would be replaced with actual unit cost database
            return 3  # Default to 3-cost
        return 1

    def _analyze_meta_patterns(self, matches_data: List[Dict]) -> Dict:
        """Analyze meta patterns from collected matches."""
        analysis = {
            'composition_stats': self._analyze_composition_performance(matches_data),
            'trait_analysis': self._analyze_trait_strength(matches_data),
            'item_meta': self._analyze_item_usage(matches_data),
            'tier_list': self._generate_tier_list(matches_data),
            'trend_analysis': self._analyze_trends(matches_data),
            'counter_relationships': self._analyze_counters(matches_data)
        }

        return analysis

    def _analyze_composition_performance(self, matches_data: List[Dict]) -> Dict:
        """Analyze performance of different composition types."""
        comp_stats = defaultdict(lambda: {'games': 0, 'total_placement': 0, 'wins': 0})

        for match in matches_data:
            for participant in match['participants']:
                comp_type = participant['comp_analysis']['comp_type']
                placement = participant['placement']

                comp_stats[comp_type]['games'] += 1
                comp_stats[comp_type]['total_placement'] += placement

                if placement <= 4:  # Top 4 = win in TFT
                    comp_stats[comp_type]['wins'] += 1

        # Calculate averages
        results = {}
        for comp_type, stats in comp_stats.items():
            if stats['games'] > 0:
                results[comp_type] = {
                    'play_rate': stats['games'] / len(matches_data),
                    'avg_placement': stats['total_placement'] / stats['games'],
                    'win_rate': stats['wins'] / stats['games'],
                    'sample_size': stats['games']
                }

        return results

    def _analyze_trait_strength(self, matches_data: List[Dict]) -> Dict:
        """Analyze trait performance and strength."""
        trait_performance = defaultdict(lambda: {'appearances': 0, 'total_placement': 0, 'wins': 0})

        for match in matches_data:
            for participant in match['participants']:
                active_traits = participant['trait_summary']['active_traits']
                placement = participant['placement']

                for trait_name in active_traits:
                    trait_performance[trait_name]['appearances'] += 1
                    trait_performance[trait_name]['total_placement'] += placement

                    if placement <= 4:
                        trait_performance[trait_name]['wins'] += 1

        # Calculate trait strength scores
        results = {}
        for trait_name, stats in trait_performance.items():
            if stats['appearances'] >= 5:  # Minimum sample size
                results[trait_name] = {
                    'usage_rate': stats['appearances'] / len(matches_data),
                    'avg_placement': stats['total_placement'] / stats['appearances'],
                    'win_rate': stats['wins'] / stats['appearances'],
                    'strength_score': (8.5 - (stats['total_placement'] / stats['appearances'])) * (stats['wins'] / stats['appearances'])
                }

        return dict(sorted(results.items(), key=lambda x: x[1]['strength_score'], reverse=True))

    def _analyze_item_usage(self, matches_data: List[Dict]) -> Dict:
        """Analyze item usage patterns and effectiveness."""
        item_stats = defaultdict(lambda: {'usage': 0, 'total_placement': 0, 'wins': 0})

        for match in matches_data:
            for participant in match['participants']:
                items_used = participant['item_analysis']['item_distribution']
                placement = participant['placement']

                for item_name, count in items_used.items():
                    item_stats[item_name]['usage'] += count
                    item_stats[item_name]['total_placement'] += placement * count

                    if placement <= 4:
                        item_stats[item_name]['wins'] += count

        # Calculate item effectiveness
        results = {}
        for item_name, stats in item_stats.items():
            if stats['usage'] >= 3:  # Minimum usage
                results[item_name] = {
                    'usage_count': stats['usage'],
                    'avg_placement_when_used': stats['total_placement'] / stats['usage'],
                    'win_rate_when_used': stats['wins'] / stats['usage']
                }

        return dict(sorted(results.items(), key=lambda x: x[1]['win_rate_when_used'], reverse=True))

    def _generate_tier_list(self, matches_data: List[Dict]) -> Dict:
        """Generate meta tier list based on performance data."""
        comp_performance = self._analyze_composition_performance(matches_data)

        # Sort compositions by combined score
        tier_scores = []
        for comp_type, stats in comp_performance.items():
            if stats['sample_size'] >= 3:  # Minimum games
                # Combined score: win rate (40%) + average placement (40%) + play rate (20%)
                placement_score = (8.5 - stats['avg_placement']) / 7.5  # Normalize to 0-1
                combined_score = (
                    0.4 * stats['win_rate'] +
                    0.4 * placement_score +
                    0.2 * min(stats['play_rate'] * 10, 1.0)  # Cap play rate influence
                )
                tier_scores.append((comp_type, combined_score, stats))

        tier_scores.sort(key=lambda x: x[1], reverse=True)

        # Assign tiers
        num_comps = len(tier_scores)
        tier_list = {'S': [], 'A': [], 'B': [], 'C': []}

        for i, (comp_type, score, stats) in enumerate(tier_scores):
            comp_info = {
                'comp': comp_type,
                'score': score,
                'win_rate': stats['win_rate'],
                'avg_placement': stats['avg_placement'],
                'play_rate': stats['play_rate']
            }

            if i < num_comps * 0.2:  # Top 20%
                tier_list['S'].append(comp_info)
            elif i < num_comps * 0.5:  # Top 50%
                tier_list['A'].append(comp_info)
            elif i < num_comps * 0.8:  # Top 80%
                tier_list['B'].append(comp_info)
            else:
                tier_list['C'].append(comp_info)

        return tier_list

    def _analyze_trends(self, matches_data: List[Dict]) -> Dict:
        """Analyze trending patterns in the meta."""
        if len(matches_data) < 10:
            return {'insufficient_data': True}

        # Sort matches by time
        sorted_matches = sorted(matches_data, key=lambda x: x['game_datetime'])

        # Split into early and recent periods
        split_point = len(sorted_matches) // 2
        early_matches = sorted_matches[:split_point]
        recent_matches = sorted_matches[split_point:]

        early_stats = self._analyze_composition_performance(early_matches)
        recent_stats = self._analyze_composition_performance(recent_matches)

        trends = {
            'rising': [],
            'falling': [],
            'stable': []
        }

        for comp_type in set(early_stats.keys()) | set(recent_stats.keys()):
            early_wr = early_stats.get(comp_type, {}).get('win_rate', 0)
            recent_wr = recent_stats.get(comp_type, {}).get('win_rate', 0)

            change = recent_wr - early_wr

            trend_info = {
                'comp': comp_type,
                'change': change,
                'early_wr': early_wr,
                'recent_wr': recent_wr
            }

            if change > 0.05:  # 5% increase
                trends['rising'].append(trend_info)
            elif change < -0.05:  # 5% decrease
                trends['falling'].append(trend_info)
            else:
                trends['stable'].append(trend_info)

        return trends

    def _analyze_counters(self, matches_data: List[Dict]) -> Dict:
        """Analyze composition counter relationships."""
        matchups = defaultdict(lambda: defaultdict(lambda: {'games': 0, 'wins': 0}))

        for match in matches_data:
            participants = match['participants']

            # Analyze pairwise matchups
            for i, p1 in enumerate(participants):
                for j, p2 in enumerate(participants):
                    if i >= j:  # Avoid duplicates and self-comparison
                        continue

                    comp1 = p1['comp_analysis']['comp_type']
                    comp2 = p2['comp_analysis']['comp_type']

                    matchups[comp1][comp2]['games'] += 1
                    matchups[comp2][comp1]['games'] += 1

                    # Determine winner (better placement)
                    if p1['placement'] < p2['placement']:
                        matchups[comp1][comp2]['wins'] += 1
                    else:
                        matchups[comp2][comp1]['wins'] += 1

        # Calculate win rates
        counter_matrix = {}
        for comp1 in matchups:
            counter_matrix[comp1] = {}
            for comp2 in matchups[comp1]:
                stats = matchups[comp1][comp2]
                if stats['games'] >= 3:  # Minimum sample size
                    counter_matrix[comp1][comp2] = {
                        'win_rate': stats['wins'] / stats['games'],
                        'sample_size': stats['games']
                    }

        return counter_matrix


if __name__ == "__main__":
    import asyncio
    from config.settings import Settings

    async def test_meta_collector():
        settings = Settings()
        collector = TFTMetaDataCollector(settings)

        # Test with small sample
        data = await collector.collect_meta_data(num_matches=10)
        print(f"Collected meta data: {len(data['raw_matches'])} matches")

        # Print some insights
        if 'tier_list' in data['meta_analysis']:
            print("\nGenerated Tier List:")
            for tier, comps in data['meta_analysis']['tier_list'].items():
                print(f"{tier} Tier: {[c['comp'] for c in comps]}")

    asyncio.run(test_meta_collector())