"""
Competitor data model
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, JSON
from src.models.base import Base, TimestampMixin


class Competitor(Base, TimestampMixin):
    """Competitor entity"""
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    industry = Column(String(100))
    is_active = Column(Boolean, default=True)
    pricing_url = Column(String(500))
    
    careers_url = Column(String(500))
    blog_url = Column(String(500))
    
    # Additional data
    extra_data = Column(JSON, default={})
    
    def __repr__(self):
        return f"<Competitor(id={self.id}, name='{self.name}')>"


class CompetitorUpdate(Base, TimestampMixin):
    """Competitor update/change tracking"""
    __tablename__ = "competitor_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, nullable=False, index=True)
    
    # Update details
    update_type = Column(String(50), nullable=False)  # pricing, feature, hiring, news
    category = Column(String(50))  # strategy, pricing, feature_release, leadership
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    
    # Impact
    impact_score = Column(Float, default=0.0)  # 0-10 scale
    severity = Column(String(20))  # low, medium, high, critical
    
    # Source data
    source_url = Column(String(1000))
    raw_data = Column(JSON)
    
    # Processing
    is_processed = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<CompetitorUpdate(id={self.id}, type='{self.update_type}')>"
