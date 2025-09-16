"""Machine Learning API endpoints for strategic recommendations."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
from pathlib import Path
import subprocess

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.tools.ml_recommendation_tool import get_tft_recommendation
from ..models import MLRecommendationRequest, MLRecommendationResponse

router = APIRouter()


def get_ml_fallback_recommendation(gold: int, level: int, stage: int, health: int) -> str:
    """Provide rule-based fallback recommendations when ML fails."""
    game_phase = 'early' if stage <= 3 else 'mid' if stage <= 5 else 'late'

    # Rule-based strategic advice
    if game_phase == 'early':
        if gold >= 30:
            return f"**EARLY GAME STRATEGY** (Stage {stage})\n\n• With {gold} gold, you have good economy\n• Consider leveling to {level + 1} to improve board strength\n• Look for strong 2-star units and trait synergies\n• Avoid hard-rolling unless you're very close to 3-starring key units"
        else:
            return f"**EARLY GAME STRATEGY** (Stage {stage})\n\n• Economy is tight with {gold} gold\n• Focus on natural leveling and strongest board\n• Prioritize 2-star units over forcing synergies\n• Save gold when possible to reach key breakpoints"

    elif game_phase == 'mid':
        if health <= 40:
            return f"**MID GAME - DANGER ZONE** (Stage {stage})\n\n• Health critical at {health}! Need immediate board strength\n• Consider rolling down to stabilize if you have {gold} gold\n• Look for key 2-star units and strong items\n• Position defensively against strongest opponents"
        elif gold >= 50:
            return f"**MID GAME - STRONG ECONOMY** (Stage {stage})\n\n• Excellent economy with {gold} gold at level {level}\n• Consider slow-rolling for key upgrades or pushing to level 8\n• Look for 4-cost carries and strong synergies\n• Maintain flexibility - don't force specific compositions"
        else:
            return f"**MID GAME STRATEGY** (Stage {stage})\n\n• Standard mid-game with {gold} gold\n• Balance economy and board strength\n• Level strategically when you find good upgrades\n• Start identifying your end-game composition"

    else:  # late game
        if health <= 30:
            return f"**LATE GAME - ALL IN** (Stage {stage})\n\n• Must commit everything with {health} health!\n• Roll down most of your {gold} gold for immediate upgrades\n• Focus on 3-starring key units or hitting 5-costs\n• Perfect positioning is crucial for survival"
        else:
            return f"**LATE GAME OPTIMIZATION** (Stage {stage})\n\n• Good position with {health} health\n• Use {gold} gold strategically for key upgrades\n• Look for 5-cost units and perfect items\n• Focus on optimal positioning and counter-play"


@router.post("/recommend", response_model=Dict[str, Any])
async def get_ml_recommendation(request: MLRecommendationRequest):
    """
    Get ML-powered strategic recommendations based on current game state.

    - **gold**: Current gold amount (0-100)
    - **level**: Current player level (1-11)
    - **stage**: Current game stage (1-7)
    - **health**: Current health (0-100)
    """
    try:
        # Determine game phase
        game_phase = (
            'early' if request.stage <= 3
            else 'mid' if request.stage <= 5
            else 'late'
        )

        # Always use rule-based fallback for now (ML has data format issues)
        print("Using rule-based ML recommendation (ML model temporarily disabled)")
        recommendation = get_ml_fallback_recommendation(
            request.gold, request.level, request.stage, request.health
        )
        analysis_type = "Rule-based strategic analysis"
        confidence = 0.75

        # Structure the response
        response_data = {
            "recommendation": recommendation,
            "game_state": {
                "gold": request.gold,
                "level": request.level,
                "stage": request.stage,
                "health": request.health,
                "game_phase": game_phase
            },
            "confidence": confidence,
            "analysis_type": analysis_type
        }

        return response_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML recommendation failed: {str(e)}")


@router.post("/train/quick")
async def trigger_quick_training():
    """
    Trigger a quick ML model retrain with recent data.

    This runs the quick retrain script which uses matches from the last 24 hours.
    """
    try:
        # Run the quick retrain script
        result = subprocess.run(
            ["uv", "run", "python", "scripts/quick_retrain.py"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return {
                "status": "success",
                "message": "Quick training completed successfully",
                "output": result.stdout,
                "training_type": "24-hour recent data"
            }
        else:
            return {
                "status": "error",
                "message": "Training failed",
                "error": result.stderr,
                "return_code": result.returncode
            }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Training timeout - process took too long")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training trigger failed: {str(e)}")


@router.get("/model/status")
async def get_model_status():
    """Get current ML model status and information."""
    try:
        # Get model information from the ML components
        from src.tft_analyzer.ml.streaming.streaming_trainer import RealTimeStreamingTrainer

        # Create trainer instance to check status
        trainer = RealTimeStreamingTrainer()

        # Check for existing models
        model_dir = project_root / "models"
        model_files = list(model_dir.glob("*.joblib")) if model_dir.exists() else []

        latest_model = None
        if model_files:
            latest_model = max(model_files, key=lambda x: x.stat().st_mtime)

        return {
            "model_available": len(model_files) > 0,
            "latest_model": latest_model.name if latest_model else None,
            "last_updated": latest_model.stat().st_mtime if latest_model else None,
            "model_count": len(model_files),
            "training_framework": "Streaming ML with 24-hour data",
            "data_source": "Challenger/GM/Master rank matches"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/recommendations/examples")
async def get_recommendation_examples():
    """Get example scenarios for ML recommendations."""
    return {
        "examples": [
            {
                "scenario": "Early Game Economy",
                "parameters": {
                    "gold": 30,
                    "level": 6,
                    "stage": 3,
                    "health": 85
                },
                "description": "Should I roll or level with decent economy?"
            },
            {
                "scenario": "Mid Game Transition",
                "parameters": {
                    "gold": 45,
                    "level": 7,
                    "stage": 4,
                    "health": 70
                },
                "description": "High gold, should I push level 8 or stabilize?"
            },
            {
                "scenario": "Late Game All-In",
                "parameters": {
                    "gold": 25,
                    "level": 8,
                    "stage": 6,
                    "health": 30
                },
                "description": "Low health, need to find upgrades fast"
            },
            {
                "scenario": "Win Streak Power",
                "parameters": {
                    "gold": 60,
                    "level": 7,
                    "stage": 4,
                    "health": 95
                },
                "description": "High health and gold, optimize win streak"
            }
        ]
    }


@router.get("/analysis/game-phases")
async def get_game_phase_info():
    """Get information about different game phases and strategic priorities."""
    return {
        "game_phases": {
            "early": {
                "stages": [1, 2, 3],
                "priorities": [
                    "Build strongest board possible",
                    "Maintain win streak if possible",
                    "Don't over-invest in weak units",
                    "Scout opponent boards"
                ],
                "key_decisions": [
                    "When to level to 4",
                    "When to start rolling",
                    "Economic vs board strength balance"
                ]
            },
            "mid": {
                "stages": [4, 5],
                "priorities": [
                    "Identify composition direction",
                    "Stabilize board strength",
                    "Manage economy for power spikes",
                    "Plan transition path"
                ],
                "key_decisions": [
                    "When to level to 7",
                    "When to pivot compositions",
                    "Rolling vs leveling timing"
                ]
            },
            "late": {
                "stages": [6, 7],
                "priorities": [
                    "Maximize composition power",
                    "Find key upgrades",
                    "Optimize positioning",
                    "Manage health efficiently"
                ],
                "key_decisions": [
                    "When to push level 9",
                    "All-in vs preserve health",
                    "Positioning for specific matchups"
                ]
            }
        }
    }