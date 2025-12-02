"""
Log anomaly and incident models
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, JSON, DateTime
from datetime import datetime
from src.models.base import Base, TimestampMixin


class LogAnomaly(Base, TimestampMixin):
    """Log anomaly detection results"""
    __tablename__ = "log_anomalies"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Log details
    log_source = Column(String(100), nullable=False)  # scraper, api, system
    log_level = Column(String(20))  # info, warning, error, critical
    log_message = Column(Text, nullable=False)
    log_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Anomaly detection
    anomaly_score = Column(Float, nullable=False)  # 0-1 scale
    is_anomaly = Column(Boolean, default=False)
    anomaly_type = Column(String(50))  # pattern, frequency, semantic
    
    # Context
    related_logs = Column(JSON, default=[])
    log_sequence = Column(JSON, default=[])
    
    # Root cause analysis
    rca_summary = Column(Text)
    suggested_action = Column(Text)
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolution_notes = Column(Text)
    
    def __repr__(self):
        return f"<LogAnomaly(id={self.id}, score={self.anomaly_score})>"


class Incident(Base, TimestampMixin):
    """System incident tracking"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Incident details
    title = Column(String(255), nullable=False)
    description = Column(Text)
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    status = Column(String(20), default="open")  # open, investigating, resolved, closed
    
    # Related anomalies
    anomaly_ids = Column(JSON, default=[])
    
    # Root cause
    root_cause = Column(Text)
    affected_components = Column(JSON, default=[])
    
    # Resolution
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(100))
    
    # External ticket
    jira_ticket_id = Column(String(50))
    servicenow_ticket_id = Column(String(50))
    
    def __repr__(self):
        return f"<Incident(id={self.id}, severity='{self.severity}', status='{self.status}')>"
