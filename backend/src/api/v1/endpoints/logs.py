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


@router.get("/analysis")
async def get_log_analysis(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get aggregated log analysis data for the frontend dashboard"""
    from datetime import datetime, timedelta
    
    # Get recent anomalies
    result = await db.execute(
        select(LogAnomaly)
        .where(LogAnomaly.is_anomaly == True)
        .order_by(desc(LogAnomaly.created_at))
        .limit(50)
    )
    anomalies = result.scalars().all()
    
    # Get recent incidents for more context
    incidents_result = await db.execute(
        select(Incident)
        .order_by(desc(Incident.created_at))
        .limit(20)
    )
    incidents = incidents_result.scalars().all()
    
    # Build summary
    total_logs = len(anomalies) * 100  # Estimate based on anomalies
    errors = sum(1 for a in anomalies if a.anomaly_score > 0.8)
    warnings = sum(1 for a in anomalies if 0.5 <= a.anomaly_score <= 0.8)
    
    # Format anomalies for frontend
    formatted_anomalies = []
    for anomaly in anomalies:
        formatted_anomalies.append({
            "anomaly_id": str(anomaly.id),
            "anomaly_type": "log_anomaly",
            "severity": "critical" if anomaly.anomaly_score > 0.9 else "high" if anomaly.anomaly_score > 0.7 else "medium" if anomaly.anomaly_score > 0.5 else "low",
            "description": anomaly.log_message[:200] if anomaly.log_message else "Unknown anomaly",
            "affected_component": anomaly.log_source or "system",
            "detected_at": anomaly.created_at.isoformat() if anomaly.created_at else datetime.utcnow().isoformat(),
            "confidence_score": anomaly.anomaly_score or 0.5,
            "log_entries": anomaly.log_sequence[:5] if anomaly.log_sequence else [],
            "rca": {
                "root_cause": f"Anomaly detected with score {anomaly.anomaly_score:.2f}" if anomaly.anomaly_score else "Analysis pending"
            }
        })
    
    return {
        "total_logs": total_logs,
        "anomalies_detected": len(anomalies),
        "log_summary": {
            "errors": errors,
            "warnings": warnings,
            "info": total_logs - errors - warnings
        },
        "anomalies": formatted_anomalies
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


class ChatRequest(BaseModel):
    message: str
    anomaly_id: str = None


@router.post("/chat")
async def chat_with_anomaly(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """AI-powered chat for root cause analysis"""
    import google.generativeai as genai
    import os
    
    # Get anomaly context if provided
    context = ""
    if request.anomaly_id:
        try:
            anomaly_id = int(request.anomaly_id)
            result = await db.execute(
                select(LogAnomaly).where(LogAnomaly.id == anomaly_id)
            )
            anomaly = result.scalar_one_or_none()
            if anomaly:
                context = f"""
                Anomaly Details:
                - Log Message: {anomaly.log_message}
                - Anomaly Score: {anomaly.anomaly_score}
                - Source: {anomaly.log_source}
                - Log Sequence: {anomaly.log_sequence[:5] if anomaly.log_sequence else 'N/A'}
                """
        except:
            pass
    
    # Use Gemini for response
    try:
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""You are an expert DevOps and SRE assistant specializing in root cause analysis.
        
{context}

User Question: {request.message}

Provide a helpful, concise response about the potential root cause, impact, and recommended remediation steps.
Keep your response focused and actionable."""

        response = model.generate_content(prompt)
        return {"response": response.text}
    except Exception as e:
        return {"response": f"I can help analyze this issue. Based on the available data, this appears to be a system anomaly that may require further investigation. Please check logs and monitoring dashboards for more details. Error: {str(e)}"}


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


class RCAQueryRequest(BaseModel):
    """Request model for interactive RCA query"""
    question: str
    logs: List[str] = []
    incident_id: int = None
    context: dict = {}


class RCAQueryResponse(BaseModel):
    """Response model for RCA query"""
    answer: str
    root_cause: str
    affected_components: List[str]
    recommendations: List[str]
    confidence: float
    sources_analyzed: int


@router.post("/query-rca", response_model=RCAQueryResponse)
async def query_root_cause_analysis(
    request: RCAQueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Interactive AI-powered root cause analysis query.
    
    Allows users to ask natural language questions about logs and incidents
    to understand root causes and get recommendations.
    
    Examples:
    - "Why did the service crash?"
    - "What caused the spike in errors?"
    - "How can we prevent this from happening again?"
    """
    from src.services.ai.processor import AIProcessor
    
    ai_processor = AIProcessor()
    
    # Gather logs for analysis
    logs_to_analyze = request.logs
    
    # If incident_id provided, fetch associated logs
    if request.incident_id:
        result = await db.execute(
            select(LogAnomaly)
            .where(LogAnomaly.incident_id == request.incident_id)
            .order_by(LogAnomaly.created_at)
            .limit(50)
        )
        incident_logs = result.scalars().all()
        logs_to_analyze.extend([l.log_message for l in incident_logs])
    
    if not logs_to_analyze:
        # Fetch recent anomalies if no logs provided
        result = await db.execute(
            select(LogAnomaly)
            .where(LogAnomaly.is_anomaly == True)
            .order_by(desc(LogAnomaly.created_at))
            .limit(20)
        )
        recent_anomalies = result.scalars().all()
        logs_to_analyze = [l.log_message for l in recent_anomalies]
    
    # Build RCA prompt
    logs_text = "\n".join(logs_to_analyze[:30])  # Limit for token management
    
    rca_prompt = f"""You are an expert AIOps engineer performing root cause analysis.

USER QUESTION: {request.question}

RELEVANT LOGS:
{logs_text}

CONTEXT: {request.context}

Analyze these logs and provide:
1. A direct answer to the user's question
2. The likely root cause of any issues
3. Affected components or services
4. Specific recommendations for resolution and prevention

Format your response as JSON with keys:
- answer: Direct answer to the question
- root_cause: Identified root cause
- affected_components: List of affected systems
- recommendations: List of actionable recommendations
- confidence: Float 0-1 indicating confidence in analysis
"""

    try:
        response = await ai_processor._call_gemini(rca_prompt)
        result = ai_processor._parse_json_response(response)
        
        return RCAQueryResponse(
            answer=result.get('answer', 'Analysis complete. See details below.'),
            root_cause=result.get('root_cause', 'Unable to determine root cause from available logs.'),
            affected_components=result.get('affected_components', []),
            recommendations=result.get('recommendations', ['Review logs manually for more details.']),
            confidence=float(result.get('confidence', 0.5)),
            sources_analyzed=len(logs_to_analyze)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RCA analysis failed: {str(e)}")


@router.post("/analyze-ensemble")
async def analyze_logs_ensemble(
    request: LogAnalysisRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze logs using ensemble of LSTM, Autoencoder, and LogBERT models.
    Provides more robust anomaly detection through model voting.
    """
    try:
        from src.services.ai.anomaly_models import EnsembleAnomalyDetector
        
        detector = EnsembleAnomalyDetector(
            use_logbert=True,
            use_lstm=True,
            use_autoencoder=True
        )
        
        results = detector.detect_anomalies(request.logs)
        
        # Save anomalies if critical
        if results.get('is_critical'):
            for idx in results.get('anomalous_indices', []):
                if idx < len(request.logs):
                    log_anomaly = LogAnomaly(
                        log_source=request.source,
                        log_message=request.logs[idx],
                        anomaly_score=results.get('ensemble_score', 0.8),
                        is_anomaly=True,
                        log_sequence=request.logs
                    )
                    db.add(log_anomaly)
            await db.commit()
        
        return {
            "results": results,
            "message": "Ensemble analysis completed"
        }
    except ImportError:
        # Fall back to standard analysis
        analysis = log_detector.analyze_log_sequence(request.logs)
        return {
            "results": analysis,
            "message": "Standard analysis completed (ensemble not available)"
        }

