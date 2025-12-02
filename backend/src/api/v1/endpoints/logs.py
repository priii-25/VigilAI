"""
Log analysis and anomaly detection endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
from pydantic import BaseModel
from src.core.database import get_db
from src.core.security import get_current_user
from src.models.log_anomaly import LogAnomaly, Incident
from src.services.ai.logbert import LogAnomalyDetector, RootCauseAnalyzer

router = APIRouter()
log_detector = LogAnomalyDetector()
rca_analyzer = RootCauseAnalyzer()


class LogAnalysisRequest(BaseModel):
    logs: List[str]
    source: str = "system"


class AnomalyResponse(BaseModel):
    id: int
    log_message: str
    anomaly_score: float
    is_anomaly: bool
    log_source: str
    
    class Config:
        from_attributes = True


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: str
    status: str
    root_cause: str
    
    class Config:
        from_attributes = True


@router.post("/analyze")
async def analyze_logs(
    request: LogAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Analyze logs for anomalies"""
    # Detect anomalies
    analysis = log_detector.analyze_log_sequence(request.logs)
    
    # Save anomalies to database
    for anomalous_log in analysis['anomalous_logs']:
        log_anomaly = LogAnomaly(
            log_source=request.source,
            log_message=anomalous_log['log_message'],
            anomaly_score=anomalous_log['anomaly_score'],
            is_anomaly=True,
            log_sequence=request.logs
        )
        db.add(log_anomaly)
    
    # If critical, create incident
    if analysis['severity'] in ['critical', 'high']:
        # Perform RCA
        rca_result = await rca_analyzer.analyze_incident(
            analysis['anomalous_logs'],
            {'source': request.source, 'severity': analysis['severity']}
        )
        
        incident = Incident(
            title=f"Anomaly detected in {request.source}",
            description=f"Found {analysis['anomaly_count']} anomalies",
            severity=analysis['severity'],
            status='open',
            root_cause=rca_result.get('root_cause', ''),
            affected_components=rca_result.get('affected_components', [])
        )
        db.add(incident)
    
    await db.commit()
    
    return {
        "analysis": analysis,
        "message": "Log analysis completed"
    }


@router.get("/anomalies", response_model=List[AnomalyResponse])
async def list_anomalies(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List recent anomalies"""
    result = await db.execute(
        select(LogAnomaly)
        .where(LogAnomaly.is_anomaly == True)
        .order_by(desc(LogAnomaly.created_at))
        .limit(limit)
    )
    anomalies = result.scalars().all()
    return anomalies


@router.get("/incidents", response_model=List[IncidentResponse])
async def list_incidents(
    status: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List incidents"""
    query = select(Incident).order_by(desc(Incident.created_at))
    
    if status:
        query = query.where(Incident.status == status)
    
    result = await db.execute(query)
    incidents = result.scalars().all()
    return incidents


@router.post("/incidents/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    resolution: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark incident as resolved"""
    result = await db.execute(select(Incident).where(Incident.id == incident_id))
    incident = result.scalar_one_or_none()
    
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    from datetime import datetime
    incident.status = 'resolved'
    incident.resolution = resolution
    incident.resolved_at = datetime.utcnow()
    incident.resolved_by = current_user.get('sub', 'unknown')
    
    await db.commit()
    
    return {"message": "Incident resolved successfully"}
