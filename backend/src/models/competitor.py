"""
Competitor data model

Enhanced with:
- Multi-tenancy support (tenant_id)
- Content hash for change detection
- Version tracking for immutable history
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base, TimestampMixin


class Competitor(Base, TimestampMixin):
    """
    Competitor entity.
    
    Represents a competitor being tracked for competitive intelligence.
    Supports multi-tenancy via tenant_id.
    """
    __tablename__ = "competitors"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy (nullable for backward compatibility during migration)
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    industry = Column(String(100))
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Monitoring URLs
    pricing_url = Column(String(500))
    careers_url = Column(String(500))
    blog_url = Column(String(500))
    docs_url = Column(String(500))
    
    # Social media
    linkedin_url = Column(String(500))
    twitter_handle = Column(String(100))
    
    # Scraping metadata
    last_scraped_at = Column(String(50))  # ISO timestamp
    scrape_frequency_hours = Column(Integer, default=24)
    
    # Content hashes for change detection
    pricing_content_hash = Column(String(64))
    careers_content_hash = Column(String(64))
    blog_content_hash = Column(String(64))
    
    # Additional data
    extra_data = Column(JSON, default={})
    
    # Tags for categorization
    tags = Column(JSON, default=[])
    
    def __repr__(self):
        return f"<Competitor(id={self.id}, name='{self.name}', tenant={self.tenant_id})>"
    
    def needs_scrape(self, hours_threshold: int = None) -> bool:
        """Check if competitor needs to be scraped based on frequency"""
        if not self.last_scraped_at:
            return True
        
        from datetime import datetime, timedelta
        threshold = hours_threshold or self.scrape_frequency_hours or 24
        
        try:
            last_scraped = datetime.fromisoformat(self.last_scraped_at)
            return datetime.utcnow() - last_scraped > timedelta(hours=threshold)
        except:
            return True


class CompetitorUpdate(Base, TimestampMixin):
    """
    Competitor update/change tracking.
    
    Immutable record of detected changes - never overwritten.
    Supports temporal data modeling (what changed, when, why).
    """
    __tablename__ = "competitor_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Reference
    competitor_id = Column(Integer, nullable=False, index=True)
    
    # Update details
    update_type = Column(String(50), nullable=False, index=True)  # pricing, feature, hiring, news
    category = Column(String(50), index=True)  # strategy, pricing, feature_release, leadership
    title = Column(String(500), nullable=False)
    summary = Column(Text)
    
    # Impact assessment
    impact_score = Column(Float, default=0.0, index=True)  # 0-10 scale
    severity = Column(String(20), index=True)  # low, medium, high, critical
    confidence = Column(Float, default=1.0)  # AI confidence in the analysis
    
    # Source data (immutable - never overwritten)
    source_url = Column(String(1000))
    raw_data = Column(JSON)
    
    # Change detection
    content_hash = Column(String(64))  # Hash of content for deduplication
    previous_hash = Column(String(64))  # Previous content hash
    
    # Processing status
    is_processed = Column(Boolean, default=False, index=True)
    is_verified = Column(Boolean, default=False)  # Human verification
    is_noise = Column(Boolean, default=False)  # Marked as noise
    
    # Idempotency
    idempotency_key = Column(String(100), unique=True, nullable=True)
    
    def __repr__(self):
        return f"<CompetitorUpdate(id={self.id}, type='{self.update_type}', impact={self.impact_score})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "competitor_id": self.competitor_id,
            "update_type": self.update_type,
            "category": self.category,
            "title": self.title,
            "summary": self.summary,
            "impact_score": self.impact_score,
            "severity": self.severity,
            "source_url": self.source_url,
            "is_verified": self.is_verified,
            "created_at": str(self.created_at) if self.created_at else None
        }


class CompetitorSnapshot(Base, TimestampMixin):
    """
    Point-in-time snapshot of competitor data.
    
    Supports temporal data modeling - stores historical state
    for rollback and audit purposes.
    """
    __tablename__ = "competitor_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Reference
    competitor_id = Column(Integer, nullable=False, index=True)
    
    # Snapshot metadata
    snapshot_type = Column(String(50), nullable=False)  # pricing, full, careers
    version = Column(Integer, default=1)
    
    # Content
    content = Column(JSON, nullable=False)
    content_hash = Column(String(64))
    
    # Source
    source_url = Column(String(1000))
    
    def __repr__(self):
        return f"<CompetitorSnapshot(id={self.id}, competitor={self.competitor_id}, type='{self.snapshot_type}')>"
