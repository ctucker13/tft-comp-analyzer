"""Database API endpoints for champions and traits."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.tft_analyzer.data.riot_official_units_with_traits import riot_official_db_with_traits as riot_db
from src.tft_analyzer.data.meta_data_manager import TFTMetaDataManager
from ..models import ChampionInfo, ChampionFilter

router = APIRouter()


@router.get("/champions", response_model=List[ChampionInfo])
async def get_champions(
    name: Optional[str] = Query(None, description="Filter by champion name"),
    cost: Optional[int] = Query(None, description="Filter by cost (1-5)", ge=1, le=5),
    trait: Optional[str] = Query(None, description="Filter by trait"),
    limit: int = Query(100, description="Limit results", ge=1, le=200)
):
    """
    Get champion information with optional filtering.

    - **name**: Filter by specific champion name
    - **cost**: Filter by cost (1-5)
    - **trait**: Filter by trait name
    - **limit**: Maximum number of results
    """
    try:
        champions = []

        if name:
            # Get specific champion
            info = riot_db.get_unit_info(name)
            if 'error' not in info:
                champions.append(ChampionInfo(
                    name=info['name'],
                    cost=info['cost'],
                    traits=info['traits'],
                    type=info.get('type', 'Champion')
                ))
        elif cost:
            # Get champions by cost
            units = riot_db.get_units_by_cost(cost)
            for unit in units[:limit]:
                info = riot_db.get_unit_info(unit.name)
                champions.append(ChampionInfo(
                    name=info['name'],
                    cost=info['cost'],
                    traits=info['traits'],
                    type=info.get('type', 'Champion')
                ))
        elif trait:
            # Get champions by trait
            units = riot_db.get_units_by_trait(trait)
            for unit in units[:limit]:
                info = riot_db.get_unit_info(unit.name)
                champions.append(ChampionInfo(
                    name=info['name'],
                    cost=info['cost'],
                    traits=info['traits'],
                    type=info.get('type', 'Champion')
                ))
        else:
            # Get all champions (limited)
            for name in riot_db.unit_names[:limit]:
                info = riot_db.get_unit_info(name)
                champions.append(ChampionInfo(
                    name=info['name'],
                    cost=info['cost'],
                    traits=info['traits'],
                    type=info.get('type', 'Champion')
                ))

        return champions

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get champions: {str(e)}")


@router.get("/champions/{champion_name}", response_model=ChampionInfo)
async def get_champion_details(champion_name: str):
    """Get detailed information about a specific champion."""
    try:
        info = riot_db.get_unit_info(champion_name)
        if 'error' in info:
            raise HTTPException(status_code=404, detail=f"Champion '{champion_name}' not found")

        return ChampionInfo(
            name=info['name'],
            cost=info['cost'],
            traits=info['traits'],
            type=info.get('type', 'Champion')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get champion details: {str(e)}")


@router.get("/traits")
async def get_traits():
    """Get all traits with champion counts."""
    try:
        trait_distribution = riot_db.get_trait_distribution()

        traits = []
        for trait_name, count in sorted(trait_distribution.items(), key=lambda x: x[1], reverse=True):
            trait_champions = riot_db.get_units_by_trait(trait_name)
            champion_names = [unit.name for unit in trait_champions]

            traits.append({
                "name": trait_name,
                "champion_count": count,
                "champions": champion_names
            })

        return {
            "traits": traits,
            "total_traits": len(trait_distribution)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get traits: {str(e)}")


@router.get("/traits/{trait_name}")
async def get_trait_details(trait_name: str):
    """Get detailed information about a specific trait."""
    try:
        trait_champions = riot_db.get_units_by_trait(trait_name)

        if not trait_champions:
            raise HTTPException(status_code=404, detail=f"Trait '{trait_name}' not found")

        champions = []
        for unit in trait_champions:
            info = riot_db.get_unit_info(unit.name)
            champions.append({
                "name": info['name'],
                "cost": info['cost'],
                "all_traits": info['traits']
            })

        return {
            "trait_name": trait_name,
            "champion_count": len(champions),
            "champions": champions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trait details: {str(e)}")


@router.get("/search")
async def search_database(
    query: str = Query(..., description="Search query", min_length=1),
    type_filter: str = Query("all", description="Search type (champions/traits/all)"),
    limit: int = Query(20, description="Limit results", ge=1, le=100)
):
    """
    Search champions and traits by name.

    - **query**: Search term
    - **type_filter**: Filter by type (champions/traits/all)
    - **limit**: Maximum number of results
    """
    try:
        results = {
            "champions": [],
            "traits": [],
            "total_results": 0
        }

        query_lower = query.lower()

        if type_filter in ["all", "champions"]:
            # Search champions
            matching_champions = [
                name for name in riot_db.unit_names
                if query_lower in name.lower()
            ][:limit]

            for champ_name in matching_champions:
                info = riot_db.get_unit_info(champ_name)
                results["champions"].append({
                    "name": info['name'],
                    "cost": info['cost'],
                    "traits": info['traits'][:3],  # First 3 traits for summary
                    "type": "champion"
                })

        if type_filter in ["all", "traits"]:
            # Search traits
            trait_distribution = riot_db.get_trait_distribution()
            matching_traits = [
                trait for trait in trait_distribution.keys()
                if query_lower in trait.lower()
            ][:limit]

            for trait_name in matching_traits:
                count = trait_distribution[trait_name]
                results["traits"].append({
                    "name": trait_name,
                    "champion_count": count,
                    "type": "trait"
                })

        results["total_results"] = len(results["champions"]) + len(results["traits"])

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_database_stats():
    """Get database statistics."""
    try:
        cost_distribution = riot_db.get_cost_distribution()
        trait_distribution = riot_db.get_trait_distribution()

        # Calculate stats
        cost_stats = []
        for cost in sorted(cost_distribution.keys()):
            units = riot_db.get_units_by_cost(cost)
            examples = [unit.name for unit in units[:3]]

            cost_stats.append({
                "cost": cost,
                "count": cost_distribution[cost],
                "examples": examples
            })

        return {
            "total_champions": len(riot_db.unit_names),
            "total_traits": len(trait_distribution),
            "cost_distribution": cost_stats,
            "most_common_traits": sorted(
                trait_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            "data_source": "Riot Official API with trait mappings"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get database stats: {str(e)}")