"""
Dashboard and analytics endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.competitor import Competitor, CompetitorUpdate
from src.models.battlecard import Battlecard
from src.models.log_anomaly import LogAnomaly, Incident

router = APIRouter()


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard statistics"""
    
    # Count competitors
    competitors_count = await db.scalar(
        select(func.count(Competitor.id)).where(Competitor.is_active == True)
    )
    
    # Count updates (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    updates_count = await db.scalar(
        select(func.count(CompetitorUpdate.id))
        .where(CompetitorUpdate.created_at >= week_ago)
    )
    
    # Count battlecards
    battlecards_count = await db.scalar(
        select(func.count(Battlecard.id)).where(Battlecard.is_published == True)
    )
    
    # Count open incidents
    incidents_count = await db.scalar(
        select(func.count(Incident.id)).where(Incident.status == 'open')
    )
    
    # Count anomalies (last 24 hours)
    day_ago = datetime.utcnow() - timedelta(days=1)
    anomalies_count = await db.scalar(
        select(func.count(LogAnomaly.id))
        .where(LogAnomaly.is_anomaly == True)
        .where(LogAnomaly.created_at >= day_ago)
    )
    
    return {
        "competitors": competitors_count or 0,
        "recent_updates": updates_count or 0,
        "battlecards": battlecards_count or 0,
        "open_incidents": incidents_count or 0,
        "anomalies_24h": anomalies_count or 0
    }


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recent activity feed"""
    from sqlalchemy import desc
    
    # Get recent competitor updates
    # Get recent competitor updates with competitor details
    result = await db.execute(
        select(CompetitorUpdate, Competitor.name, Competitor.domain)
        .join(Competitor, CompetitorUpdate.competitor_id == Competitor.id)
        .order_by(desc(CompetitorUpdate.created_at))
        .limit(limit)
    )
    rows = result.all()
    
    activity = []
    for update, comp_name, comp_domain in rows:
        activity.append({
            "id": update.id,
            "type": "competitor_update",
            "competitor_name": comp_name,
            "competitor_domain": comp_domain,
            "competitor_id": update.competitor_id,
            "title": update.title,
            "summary": update.summary,
            "impact_score": update.impact_score,
            "category": update.category,
            "timestamp": update.created_at.isoformat()
        })
    
    return sorted(activity, key=lambda x: x['timestamp'], reverse=True)[:limit]
