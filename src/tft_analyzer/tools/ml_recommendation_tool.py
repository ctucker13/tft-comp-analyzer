#!/usr/bin/env python3
"""
TFT ML Recommendation Tool

Provides a tool call interface for getting ML-based TFT composition recommendations.
Works with cached data and trained models to provide strategic advice.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np

try:
    from ..ml.training.trainer import TFTModelTrainer
    from ..ml.data.schemas import TFTGameState, CompType, ActionType, RiskLevel, GamePhase
    from ...config.settings import Settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
    from src.tft_analyzer.ml.training.trainer import TFTModelTrainer
    from src.tft_analyzer.ml.data.schemas import TFTGameState, CompType, ActionType, RiskLevel, GamePhase
    from config.settings import Settings


class TFTMLRecommendationTool:
    """Tool for getting ML-based TFT recommendations via chat interface."""

    def __init__(self, model_path: Optional[str] = None):
        """Initialize the ML recommendation tool.

        Args:
            model_path: Path to trained model. If None, uses latest model.
        """
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()

        # Initialize trainer for model loading
        self.trainer = TFTModelTrainer(self.settings)

        # Find and load the best available model
        self.model_path = self._find_best_model(model_path)
        self.model = None

        if self.model_path:
            try:
                self.model = self.trainer.load_model(self.model_path)
                self.logger.info(f"✅ Loaded ML model from {self.model_path}")
            except Exception as e:
                self.logger.error(f"❌ Failed to load ML model: {e}")
                self.model = None
        else:
            self.logger.warning("⚠️ No trained model found. Please train a model first.")

    def _find_best_model(self, model_path: Optional[str] = None) -> Optional[str]:
        """Find the best available trained model."""
        if model_path and Path(model_path).exists():
            return model_path

        # Look for models in the models directory
        models_dir = Path("models")
        if not models_dir.exists():
            return None

        # Find all model directories
        model_dirs = [d for d in models_dir.iterdir() if d.is_dir() and d.name.startswith("tft_strategy_")]

        if not model_dirs:
            return None

        # Sort by modification time, newest first
        model_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Find the first valid model (has required files)
        for model_dir in model_dirs:
            if (model_dir / "model_weights.pt").exists() and (model_dir / "config.json").exists():
                return str(model_dir)

        return None

    def is_ready(self) -> bool:
        """Check if the tool is ready to make predictions."""
        return self.model is not None

    def get_recommendation(
        self,
        current_placement: int = 4,
        gold: int = 30,
        health: int = 50,
        level: int = 6,
        round_number: int = 15,
        stage: int = 3,
        traits: Optional[Dict[str, int]] = None,
        units_count: int = 6,
        game_phase: str = "mid"
    ) -> Dict[str, Any]:
        """Get ML-based recommendation for current game state.

        Args:
            current_placement: Current placement in the match (1-8)
            gold: Current gold amount
            health: Current health
            level: Current player level
            round_number: Current round number
            stage: Current stage
            traits: Active traits and their counts
            units_count: Number of units on board
            game_phase: Game phase (early/mid/late)

        Returns:
            Dictionary with recommendations and reasoning
        """
        if not self.is_ready():
            return {
                "error": "ML model not available. Please train a model first.",
                "model_status": "not_loaded"
            }

        try:
            # Create feature vector from input parameters
            features = self._create_feature_vector(
                current_placement=current_placement,
                gold=gold,
                health=health,
                level=level,
                round_number=round_number,
                stage=stage,
                traits=traits or {},
                units_count=units_count
            )

            # Make prediction
            predictions = self._predict(features)

            # Create comprehensive recommendation
            recommendation = {
                "placement_prediction": predictions["placement"],
                "recommended_comp": predictions["comp_type"],
                "risk_assessment": predictions["risk_level"],
                "strategic_advice": self._generate_strategic_advice(predictions, {
                    "gold": gold,
                    "health": health,
                    "level": level,
                    "stage": stage,
                    "placement": current_placement
                }),
                "confidence": self._calculate_confidence(predictions),
                "model_info": {
                    "model_path": str(self.model_path),
                    "timestamp": datetime.now().isoformat()
                }
            }

            return recommendation

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return {
                "error": f"Failed to generate recommendation: {str(e)}",
                "model_status": "error"
            }

    def _create_feature_vector(
        self,
        current_placement: int,
        gold: int,
        health: int,
        level: int,
        round_number: int,
        stage: int,
        traits: Dict[str, int],
        units_count: int
    ) -> np.ndarray:
        """Create feature vector from game state parameters."""

        # Load feature names from model config
        config_path = Path(self.model_path) / "config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)

        feature_names = config['feature_names']
        feature_vector = np.zeros(len(feature_names))

        # Map basic features
        feature_map = {
            'current_placement': current_placement,
            'gold': gold,
            'health': health,
            'level': level,
            'player_level': level,  # Same as level
            'round_number': round_number,
            'stage': stage,
            'units_count': units_count,
            'trait_count': len(traits)
        }

        # Fill in basic features
        for i, feature_name in enumerate(feature_names):
            if feature_name in feature_map:
                feature_vector[i] = feature_map[feature_name]
            elif feature_name.startswith('trait_TFT15_'):
                # Extract trait name and check if it's active
                trait_name = feature_name.replace('trait_TFT15_', '')
                if trait_name in traits:
                    feature_vector[i] = traits[trait_name]
                else:
                    feature_vector[i] = 0

        return feature_vector

    def _predict(self, features: np.ndarray) -> Dict[str, Any]:
        """Make prediction using the loaded model."""
        import torch

        # Convert to tensor
        X_tensor = torch.FloatTensor(features.reshape(1, -1)).to(self.trainer.device)

        # Make prediction
        self.model.eval()
        with torch.no_grad():
            outputs = self.model(X_tensor)

        # Extract predictions
        placement_pred = outputs['value_estimate'].squeeze().cpu().numpy()

        # Handle comp type prediction with clamping
        comp_logits = outputs['comp_logits']
        if 'comp_type' in self.trainer.label_encoders:
            n_classes = len(self.trainer.label_encoders['comp_type'].classes_)
            comp_logits = comp_logits[:, :n_classes]
        comp_type_pred = torch.max(comp_logits, 1)[1].cpu().numpy()

        risk_pred = outputs['pivot_urgency'].squeeze().cpu().numpy()

        # Decode comp type
        comp_type_name = "unknown"
        if 'comp_type' in self.trainer.label_encoders:
            comp_type_name = self.trainer.label_encoders['comp_type'].inverse_transform(comp_type_pred)[0]

        return {
            "placement": float(placement_pred.item() if placement_pred.ndim == 0 else placement_pred[0]),
            "comp_type": comp_type_name,
            "risk_level": float(risk_pred.item() if risk_pred.ndim == 0 else risk_pred[0]),
            "raw_outputs": {
                "action_probs": outputs['action_probs'].cpu().numpy().tolist(),
                "comp_probs": outputs['comp_probs'].cpu().numpy().tolist(),
                "risk_probs": outputs['risk_probs'].cpu().numpy().tolist()
            }
        }

    def _generate_strategic_advice(self, predictions: Dict[str, Any], game_state: Dict[str, Any]) -> List[str]:
        """Generate detailed strategic advice with specific compositions and items."""
        advice = []
        comp_type = predictions["comp_type"]
        placement = predictions["placement"]
        risk_level = predictions["risk_level"]

        # Load composition database
        comp_data = self._load_composition_database()

        # Get specific composition recommendation
        recommended_comp = self._get_recommended_composition(comp_type, game_state, comp_data)

        if recommended_comp:
            advice.extend(self._generate_composition_advice(recommended_comp, game_state, placement, risk_level))
        else:
            # Fallback to general advice
            advice.extend(self._generate_general_advice(predictions, game_state))

        return advice

    def _load_composition_database(self) -> Dict[str, Any]:
        """Load the TFT composition database."""
        try:
            comp_file = Path(__file__).parent.parent.parent.parent / "data" / "compositions" / "tft15_compositions.json"
            with open(comp_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load composition database: {e}")
            return {}

    def _get_recommended_composition(self, comp_type: str, game_state: Dict[str, Any], comp_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get the best composition based on comp type and game state."""
        if not comp_data.get("compositions"):
            return None

        # Filter compositions by type
        matching_comps = []
        for comp_key, comp_info in comp_data["compositions"].items():
            if comp_info.get("comp_type") == comp_type:
                matching_comps.append((comp_key, comp_info))

        if not matching_comps:
            return None

        # For now, return the first matching composition
        # Could be enhanced with more sophisticated selection based on game state
        return matching_comps[0][1]

    def _generate_composition_advice(self, comp_info: Dict[str, Any], game_state: Dict[str, Any], placement: float, risk_level: float) -> List[str]:
        """Generate specific advice for the recommended composition."""
        advice = []

        # Composition introduction
        comp_name = comp_info.get("name", "Unknown Composition")
        tier = comp_info.get("tier", "B")
        advice.append(f"🎯 **Recommended: {comp_name}** (Tier {tier})")

        # Complete unit lineup (all 8 units)
        advice.extend(self._generate_complete_unit_lineup(comp_info))

        # Core items and optimal builds
        advice.extend(self._generate_optimal_items_guide(comp_info))

        # Power Up recommendations
        advice.extend(self._generate_power_up_recommendations(comp_info))

        # Traits
        traits = comp_info.get("traits", [])
        if traits:
            trait_names = [trait.replace("TFT15_", "") for trait in traits]
            advice.append(f"\n⚡ **Key Traits:** {', '.join(trait_names)}")

        # Positioning guide
        advice.extend(self._generate_positioning_guide(comp_info))

        # Power spikes based on current level
        current_level = game_state.get("level", 6)
        power_spikes = comp_info.get("power_spikes", [])
        relevant_spike = None
        for spike in power_spikes:
            if spike.get("level", 0) >= current_level:
                relevant_spike = spike
                break

        if relevant_spike:
            advice.append(f"\n🚀 **Next Power Spike (Level {relevant_spike['level']}):** {relevant_spike['description']}")

        # Situational advice based on game state
        advice.extend(self._generate_situational_advice(comp_info, game_state, placement, risk_level))

        return advice

    def _generate_complete_unit_lineup(self, comp_info: Dict[str, Any]) -> List[str]:
        """Generate complete 8-unit lineup with priorities."""
        advice = []

        core_units = comp_info.get("core_units", [])
        flexible_units = comp_info.get("flexible_units", [])

        if core_units or flexible_units:
            advice.append("\n🛡️ **Complete Unit Lineup (8 units):**")

            # Core units (highest priority)
            unit_count = 0
            for unit in core_units:
                if unit_count >= 8:
                    break
                champion = unit.get("champion", "Unknown")
                cost = unit.get("cost", "?")
                priority = unit.get("priority", 1)
                advice.append(f"• **{champion}** ({cost}⭐) - Priority {priority} [CORE]")
                unit_count += 1

            # Flexible units (lower priority)
            for unit in flexible_units:
                if unit_count >= 8:
                    break
                champion = unit.get("champion", "Unknown")
                cost = unit.get("cost", "?")
                synergy = unit.get("synergy", "Flex")
                advice.append(f"• **{champion}** ({cost}⭐) - {synergy} synergy [FLEX]")
                unit_count += 1

            # Fill remaining slots if needed
            while unit_count < 8:
                advice.append(f"• **[Flex Slot {unit_count + 1}]** - Adapt based on items/augments")
                unit_count += 1

        return advice

    def _generate_optimal_items_guide(self, comp_info: Dict[str, Any]) -> List[str]:
        """Generate detailed optimal items guide for each carry."""
        advice = []
        core_units = comp_info.get("core_units", [])

        if core_units:
            advice.append("\n⚔️ **Optimal Items Guide:**")

            for unit in core_units[:3]:  # Focus on top 3 priority units
                champion = unit.get("champion", "Unknown")
                items = unit.get("items", [])
                priority = unit.get("priority", 1)

                if items:
                    # Core items (first 3)
                    core_items = items[:3] if len(items) >= 3 else items
                    advice.append(f"• **{champion}** (Priority {priority}):")
                    advice.append(f"  - Core Items: {', '.join(core_items)}")

                    # Alternative items if available
                    if len(items) > 3:
                        alt_items = items[3:6]
                        advice.append(f"  - Alternative: {', '.join(alt_items)}")

        # Add item priority system
        comp_data = self._load_composition_database()
        if comp_data.get("items"):
            advice.append("\n💎 **Item Priority System:**")
            items_data = comp_data["items"]
            comp_type = comp_info.get("comp_type", "flex")

            if comp_type == "reroll" and "AD_carries" in items_data:
                core_ad = items_data["AD_carries"].get("core", [])[:3]
                advice.append(f"• **AD Carry Priority:** {', '.join(core_ad)}")
            elif "AP_carries" in items_data:
                core_ap = items_data["AP_carries"].get("core", [])[:3]
                advice.append(f"• **AP Carry Priority:** {', '.join(core_ap)}")

            if "Tanks" in items_data:
                core_tank = items_data["Tanks"].get("core", [])[:3]
                advice.append(f"• **Tank Priority:** {', '.join(core_tank)}")

        return advice

    def _generate_power_up_recommendations(self, comp_info: Dict[str, Any]) -> List[str]:
        """Generate Power Up recommendations for key units."""
        advice = []
        core_units = comp_info.get("core_units", [])

        # Power Up database (based on research)
        power_up_recommendations = {
            # Meta carries
            "Seraphine": ["Mind Battery", "Power Font", "Star Sailor"],
            "Ahri": ["Magic Expert", "Power Font", "Keen Eye"],
            "Gnar": ["Classy", "Attack Expert", "Spirit Sword"],
            "Caitlyn": ["Critical Threat", "Max Speed", "Gather Force"],
            "Sivir": ["Critical Threat", "Classy", "Bludgeoner"],
            "Jayce": ["Thrillseeker", "Unflinching", "Star Student"],
            "Kai'Sa": ["Over 9000", "Bullet Hell", "Max Attack"],
            "Senna": ["Precision", "Shadow Clone", "Efficient"],
            "Ryze": ["Icebender", "Annihilation", "Power Font"],
            "Xayah": ["Fan Service", "Critical Threat", "Classy"],
            "Rakan": ["Fan Service", "Unflinching", "Body Change"],
            "Rammus": ["Rare Treat", "Unstoppable", "Body Change"],
            "Poppy": ["Pure Heart", "Unstoppable", "Adaptive Skin"],
            "Darius": ["Bludgeoner", "Final Boss", "Thrillseeker"],
            "Malzahar": ["Shadow Clone", "Annihilation", "Power Font"],
            "Lulu": ["Rare Treat", "Magic Expert", "Star Sailor"],
            "Kalista": ["Critical Threat", "Max Attack", "Annihilation"],
            "Lucian": ["Magic Expert", "Power Font", "Classy"],
            "Aatrox": ["Adaptive Skin", "Unflinching", "Body Change"],
            "Gangplank": ["Max Attack", "Critical Threat", "Bludgeoner"]
        }

        if core_units:
            advice.append("\n🌟 **Power Up Recommendations:**")

            power_up_found = False
            for unit in core_units[:3]:  # Top 3 priority units
                champion = unit.get("champion", "Unknown")
                if champion in power_up_recommendations:
                    power_ups = power_up_recommendations[champion][:3]  # Top 3 options
                    advice.append(f"• **{champion}**: {', '.join(power_ups)}")
                    power_up_found = True

            if power_up_found:
                advice.append("\n✨ **Power Up Strategy:**")
                advice.append("• Use Power Snax at Stage 1-3 and 3-6")
                advice.append("• Prioritize carries first, then frontline units")
                advice.append("• Over 9000 and Shadow Clone are universally strong")
                advice.append("• Fan Service requires both Xayah and Rakan")

        return advice

    def _generate_positioning_guide(self, comp_info: Dict[str, Any]) -> List[str]:
        """Generate detailed positioning guide."""
        advice = []
        positioning = comp_info.get("positioning", {})

        if positioning:
            advice.append("\n📍 **Positioning Guide:**")

            carry_position = positioning.get("carry_position", "")
            if carry_position:
                advice.append(f"• **Main Carry Position:** {carry_position.replace('_', ' ').title()}")

            frontline = positioning.get("frontline", [])
            backline = positioning.get("backline", [])

            if frontline:
                advice.append(f"• **Frontline:** {', '.join(frontline)}")

            if backline:
                advice.append(f"• **Backline:** {', '.join(backline)}")

            # Add general positioning tips
            advice.append("• **Anti-Assassin:** Corner your main carry")
            advice.append("• **vs AOE:** Spread units apart")
            advice.append("• **vs Single Target:** Clump for healing synergy")

        return advice

    def _generate_situational_advice(self, comp_info: Dict[str, Any], game_state: Dict[str, Any], placement: float, risk_level: float) -> List[str]:
        """Generate situational advice based on current game state."""
        advice = []

        health = game_state.get("health", 50)
        gold = game_state.get("gold", 30)
        level = game_state.get("level", 6)
        comp_type = comp_info.get("comp_type", "flex")

        # Health-based advice
        if health < 30:
            advice.append("\n💔 **Low Health Strategy:**")
            if comp_type == "reroll":
                advice.append("• Roll aggressively for upgrades - don't worry about economy")
                advice.append("• Prioritize immediate board strength over perfect items")
            elif comp_type == "fast_8":
                advice.append("• Consider pivoting to a stronger midgame board")
                advice.append("• May need to slow roll at 7 instead of going fast 8")

        # Economy advice
        if gold > 50:
            advice.append(f"\n💰 **High Economy ({gold} gold):**")
            if comp_type == "reroll":
                advice.append("• Perfect position to roll for 3-stars")
                advice.append("• Can afford to be selective with upgrades")
            elif comp_type == "fast_8":
                advice.append("• Level aggressively to 8 and find your 5-costs")
                advice.append("• Don't get baited into rolling early")

        # Level-specific advice
        if level <= 6 and comp_type == "fast_8":
            advice.append(f"\n⚡ **Fast 8 Path (Level {level}):**")
            advice.append("• Level to 7 next round if healthy")
            advice.append("• Look for strong board but don't commit gold to rolls")
        elif level <= 6 and comp_type == "reroll":
            advice.append(f"\n🔄 **Reroll Path (Level {level}):**")
            advice.append("• This is your rolling level - start looking for upgrades")
            advice.append("• Aim for 3-cost 3-stars or multiple 2-stars")

        # Risk-based advice
        if risk_level > 0.7:
            pivot_options = comp_info.get("pivot_options", [])
            if pivot_options:
                advice.append(f"\n🔄 **High Risk - Pivot Options:** {', '.join(pivot_options)}")

        return advice

    def _generate_general_advice(self, predictions: Dict[str, Any], game_state: Dict[str, Any]) -> List[str]:
        """Generate general advice when specific composition data is unavailable."""
        advice = []

        placement = predictions["placement"]
        comp_type = predictions["comp_type"]
        risk_level = predictions["risk_level"]

        # Placement advice
        if placement < 2:
            advice.append("🏆 You're in a strong position! Focus on optimizing your board.")
        elif placement < 4:
            advice.append("✅ Solid positioning. Look for key upgrades to secure top 4.")
        elif placement < 6:
            advice.append("⚠️ Middle of the pack. Consider pivoting or strengthening your board.")
        else:
            advice.append("🚨 Bottom placement predicted. Urgent action needed!")

        # Comp type advice
        if comp_type == "reroll":
            advice.append("🔄 Reroll strategy recommended. Focus on hitting your key units.")
        elif comp_type == "fast_8":
            advice.append("⚡ Fast 8 strategy suggested. Save gold and level aggressively.")
        elif comp_type == "flex":
            advice.append("🔀 Flexible approach recommended. Adapt based on what you hit.")

        # Risk level advice
        if risk_level > 0.8:
            advice.append("🔥 High risk situation! Consider aggressive plays or major pivot.")
        elif risk_level > 0.5:
            advice.append("⚖️ Moderate risk. Balance economy with board strength.")
        else:
            advice.append("🛡️ Low risk situation. You can afford to be patient.")

        # Context-specific advice
        if game_state["health"] < 30:
            advice.append("💔 Low health! Prioritize immediate board strength over economy.")

        if game_state["gold"] > 50:
            advice.append("💰 High gold! Good position for rolling or leveling.")

        return advice

    def _calculate_confidence(self, predictions: Dict[str, Any]) -> float:
        """Calculate confidence score for the prediction."""
        raw_outputs = predictions.get("raw_outputs", {})

        # Use the maximum probability from each head as confidence indicator
        confidences = []

        if "comp_probs" in raw_outputs:
            comp_confidence = max(raw_outputs["comp_probs"][0])
            confidences.append(comp_confidence)

        if "action_probs" in raw_outputs:
            action_confidence = max(raw_outputs["action_probs"][0])
            confidences.append(action_confidence)

        if confidences:
            return float(np.mean(confidences))
        else:
            return 0.5  # Default moderate confidence


def get_tft_recommendation(
    current_placement: int = 4,
    gold: int = 30,
    health: int = 50,
    level: int = 6,
    round_number: int = 15,
    stage: int = 3,
    traits: Optional[Dict[str, int]] = None,
    units_count: int = 6,
    game_phase: str = "mid"
) -> str:
    """
    Get ML-based TFT composition and strategy recommendation.

    This tool uses a trained ML model to analyze your current TFT game state
    and provide strategic recommendations for optimal play.

    Args:
        current_placement: Your current placement in the match (1-8, default: 4)
        gold: Your current gold amount (default: 30)
        health: Your current health (default: 50)
        level: Your current player level (default: 6)
        round_number: Current round number (default: 15)
        stage: Current stage (default: 3)
        traits: Active traits and their counts as dict (optional)
        units_count: Number of units on your board (default: 6)
        game_phase: Game phase - 'early', 'mid', or 'late' (default: 'mid')

    Returns:
        Detailed recommendation with composition suggestion, risk assessment, and strategic advice
    """

    # Initialize the tool
    tool = TFTMLRecommendationTool()

    if not tool.is_ready():
        return "❌ ML model not available. Please train a model first using the training scripts."

    # Get recommendation
    result = tool.get_recommendation(
        current_placement=current_placement,
        gold=gold,
        health=health,
        level=level,
        round_number=round_number,
        stage=stage,
        traits=traits,
        units_count=units_count,
        game_phase=game_phase
    )

    if "error" in result:
        return f"❌ {result['error']}"

    # Format the response for user
    response = f"""
🎯 **TFT ML Recommendation**

📊 **Predicted Outcome:**
• Placement: {result['placement_prediction']:.1f}
• Recommended Comp: **{result['recommended_comp'].title()}**
• Risk Level: {result['risk_assessment']:.2f} (0=low, 1=high)

🧠 **Strategic Advice:**
{chr(10).join(f"• {advice}" for advice in result['strategic_advice'])}

🎲 **Confidence:** {result['confidence']:.2f}

💡 **Model Info:** {Path(result['model_info']['model_path']).name}
"""

    return response


if __name__ == "__main__":
    # Test the tool
    print("Testing TFT ML Recommendation Tool...")

    # Test with default parameters
    result = get_tft_recommendation()
    print(result)

    # Test with specific game state
    result = get_tft_recommendation(
        current_placement=6,
        gold=15,
        health=25,
        level=7,
        round_number=20,
        stage=4,
        traits={"Reroll": 2, "FastEight": 1},
        units_count=7,
        game_phase="late"
    )
    print(result)