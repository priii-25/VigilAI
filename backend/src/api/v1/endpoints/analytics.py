from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Any, List, Dict
from pydantic import BaseModel

from src.core.database import get_db
from src.core.security import get_current_user
from src.models.competitor import Competitor, CompetitorUpdate
from src.models.battlecard import Battlecard

# Advanced Intelligence Services
from src.services.ai.drift_detector import StrategyDriftDetector
from src.services.ai.simulator import ScenarioSimulator

router = APIRouter()

class SimulationRequest(BaseModel):
    competitor_name: str
    scenario: str
    context: str = ""

@router.get("/strategy-drift/{competitor_id}")
async def get_strategy_drift(
    competitor_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Detect strategic drift for a competitor"""
    detector = StrategyDriftDetector()
    return await detector.detect_drift(competitor_id)

@router.get("/landscape")
async def get_competitive_landscape(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get 2D coordinates for Competitive Landscape Map.
    X-Axis: Feature Strength (based on scraped features count)
    Y-Axis: Pricing Position (normalized price tier, higher = more expensive)
    Bubble Size: Market Presence (update count as proxy)
    """
    # 1. Get all competitors
    result = await db.execute(select(Competitor).where(Competitor.is_active == True))
    competitors = result.scalars().all()
    
    landscape_data = []
    
    for comp in competitors:
        # Calculate Feature Strength (X-axis)
        # Use count of feature-related updates or extra_data if available
        feature_updates = await db.execute(
            select(func.count(CompetitorUpdate.id)).where(
                CompetitorUpdate.competitor_id == comp.id,
                CompetitorUpdate.change_type == 'feature'
            )
        )
        feature_count = feature_updates.scalar() or 0
        # Also check for pricing data that might have features
        pricing_data = comp.extra_data.get('pricing', {}) if comp.extra_data else {}
        scraped_features = len(pricing_data.get('features', []))
        feature_strength = min(100, (feature_count * 5) + (scraped_features * 2))
        
        # Calculate Pricing Position (Y-axis)
        # Try to extract from extra_data or use impact score as proxy
        pricing_tier = 50  # Default mid-tier
        if comp.extra_data:
            pricing_info = comp.extra_data.get('pricing', {})
            if pricing_info.get('enterprise_price'):
                try:
                    price = float(str(pricing_info['enterprise_price']).replace('$', '').replace(',', ''))
                    # Normalize: $0-100 = low, $100-500 = mid, $500+ = high
                    pricing_tier = min(100, max(10, price / 10))
                except:
                    pass
        
        # Calculate Market Presence (bubble size)
        update_count_query = select(func.count(CompetitorUpdate.id)).where(
            CompetitorUpdate.competitor_id == comp.id
        )
        uc_result = await db.execute(update_count_query)
        update_count = uc_result.scalar() or 0
        
        # Determine color based on industry
        industry_colors = {
            'fintech': 'rgba(59, 130, 246, 0.7)',    # Blue
            'saas': 'rgba(34, 197, 94, 0.7)',        # Green
            'ecommerce': 'rgba(249, 115, 22, 0.7)',  # Orange
            'healthcare': 'rgba(239, 68, 68, 0.7)',  # Red
            'default': 'rgba(107, 114, 128, 0.7)'   # Gray
        }
        color = industry_colors.get((comp.industry or '').lower(), industry_colors['default'])
        
        landscape_data.append({
            "id": comp.id,
            "name": comp.name,
            "x": round(feature_strength, 1),
            "y": round(pricing_tier, 1),
            "r": 8 + min(20, update_count),  # Bubble radius 8-28
            "industry": comp.industry,
            "color": color
        })
        
    return landscape_data

@router.post("/simulation")
async def run_simulation(
    request: SimulationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Run competitive war game simulation"""
    simulator = ScenarioSimulator()
    return await simulator.run_simulation(
        competitor_name=request.competitor_name,
        scenario_description=request.scenario,
        user_context=request.context
    )

@router.get("/metrics")
async def get_metrics(db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get high-level analytics metrics
    """
    # Count active competitors
    active_competitors = await db.scalar(
        select(func.count(Competitor.id)).where(Competitor.is_active == True)
    )
    
    # Count battlecards
    battlecard_count = await db.scalar(
        select(func.count(Battlecard.id))
    )
    
    return {
        "win_rate": 68,
        "win_rate_change": 12,
        "win_rate_trend": "up",
        "active_competitors": active_competitors or 0,
        "competitor_change": 2,
        "competitor_trend": "up",
        "battlecard_views": 156, # Mocked for now
        "views_change": 24,
        "views_trend": "up",
        "avg_impact_score": 7.8,
        "impact_change": 0.5,
        "impact_trend": "up",
        "recent_activity": [
            {
                "type": "pricing",
                "title": "Competitor A changed pricing",
                "description": "Enterprise plan increased by 10%",
                "timestamp": "2023-10-27T10:00:00Z",
                "impact_score": 8
            },
            {
                "type": "battlecard",
                "title": "New Battlecard Created",
                "description": "Vs Competitor B",
                "timestamp": "2023-10-26T14:30:00Z"
            }
        ],
        "competitor_performance": [
            {
                "id": 1,
                "name": "Competitor A",
                "win_rate": 72,
                "total_deals": 45,
                "avg_deal_size": 25000,
                "trend": "up"
            },
             {
                "id": 2,
                "name": "Competitor B",
                "win_rate": 45,
                "total_deals": 32,
                "avg_deal_size": 18000,
                "trend": "down"
            }
        ]
    }

@router.get("/battlecard-usage")
async def get_battlecard_usage(db: AsyncSession = Depends(get_db)) -> Any:
    """
    Get battlecard usage statistics
    """
    # In a real app, we would query a 'views' table. For now, we mock.
    return {
        "top_cards": [
            {"title": "Vs Competitor A", "views": 120},
            {"title": "Vs Competitor B", "views": 85},
            {"title": "Vs Competitor C", "views": 64},
            {"title": "Product X Handling", "views": 42},
        ]
    }

@router.get("/win-rates")
async def get_win_rates() -> Any:
    """
    Get win rate timeline
    """
    return {
        "improvement": 28,
        "timeline": [
            {"date": "Jan", "with_battlecard": 45, "without_battlecard": 30},
            {"date": "Feb", "with_battlecard": 52, "without_battlecard": 32},
            {"date": "Mar", "with_battlecard": 58, "without_battlecard": 35},
            {"date": "Apr", "with_battlecard": 63, "without_battlecard": 34},
            {"date": "May", "with_battlecard": 68, "without_battlecard": 36},
            {"date": "Jun", "with_battlecard": 72, "without_battlecard": 38},
        ]
    }

@router.get("/impact-scores")
async def get_impact_scores() -> Any:
    """
    Get alerts impact score distribution
    """
    return {
        "distribution": {
            "critical": 12,
            "high": 25,
            "medium": 45,
            "low": 18
        }
    }
