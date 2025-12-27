"""
Battlecard data model

Enhanced with:
- Multi-tenancy support (tenant_id)
- Full version history
- Human-in-the-loop review workflow
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from src.models.base import Base, TimestampMixin


class Battlecard(Base, TimestampMixin):
    """
    Battlecard entity.
    
    Represents a competitive battlecard with all sections.
    Supports versioning and multi-tenancy.
    """
    __tablename__ = "battlecards"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Reference
    competitor_id = Column(Integer, nullable=False, index=True)
    
    # Metadata
    title = Column(String(255), nullable=False)
    overview = Column(Text)
    
    # Battlecard sections (stored as JSON for flexibility)
    strengths = Column(JSON, default=[])  # List of strength points
    weaknesses = Column(JSON, default=[])  # List of weakness points
    objection_handling = Column(JSON, default=[])  # List of objection/response pairs
    kill_points = Column(JSON, default=[])  # Key winning arguments
    
    # Pricing comparison
    pricing_comparison = Column(JSON, default={})
    
    # Features comparison
    features_comparison = Column(JSON, default={})
    
    # Target personas
    target_personas = Column(JSON, default=[])
    
    # Win/Loss data
    win_rate = Column(JSON, default={})
    
    # Talk tracks
    talk_tracks = Column(JSON, default=[])
    
    # Differentiation
    key_differentiators = Column(JSON, default=[])
    
    # Integration status
    notion_page_id = Column(String(255))
    notion_url = Column(String(500))
    salesforce_record_id = Column(String(255))
    
    # Status
    is_published = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=True)
    
    # Version control
    version = Column(Integer, default=1)
    
    # AI generation metadata
    ai_confidence = Column(Float, default=0.0)  # Overall AI confidence
    ai_generated_at = Column(String(50))  # Last AI generation timestamp
    last_human_review_at = Column(String(50))  # Last human review
    
    # Review workflow
    review_status = Column(String(50), default="pending")  # pending, approved, rejected
    reviewed_by = Column(Integer)  # User ID of reviewer
    review_notes = Column(Text)
    
    def __repr__(self):
        return f"<Battlecard(id={self.id}, competitor_id={self.competitor_id}, v{self.version})>"
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "competitor_id": self.competitor_id,
            "title": self.title,
            "overview": self.overview,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "objection_handling": self.objection_handling,
            "kill_points": self.kill_points,
            "pricing_comparison": self.pricing_comparison,
            "features_comparison": self.features_comparison,
            "target_personas": self.target_personas,
            "key_differentiators": self.key_differentiators,
            "talk_tracks": self.talk_tracks,
            "version": self.version,
            "is_published": self.is_published,
            "review_status": self.review_status,
            "ai_confidence": self.ai_confidence,
            "notion_url": self.notion_url,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None
        }
    
    def needs_review(self) -> bool:
        """Check if battlecard needs human review"""
        if self.review_status == "approved":
            return False
        if self.ai_confidence and self.ai_confidence < 0.7:
            return True
        if not self.last_human_review_at:
            return True
        return self.review_status == "pending"


class BattlecardVersion(Base, TimestampMixin):
    """
    Battlecard version history.
    
    Immutable record of battlecard versions for:
    - Rollback capability
    - Audit trail
    - A/B testing content
    """
    __tablename__ = "battlecard_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Reference
    battlecard_id = Column(Integer, nullable=False, index=True)
    version = Column(Integer, nullable=False)
    
    # Full content snapshot
    content = Column(JSON, nullable=False)
    
    # Metadata
    change_summary = Column(Text)
    changed_by = Column(Integer)  # User ID
    change_source = Column(String(50))  # ai, manual, import
    
    # AI metadata
    ai_confidence = Column(Float)
    prompt_version = Column(String(50))  # Version of prompt used
    
    def __repr__(self):
        return f"<BattlecardVersion(battlecard={self.battlecard_id}, v{self.version})>"


class BattlecardSection(Base, TimestampMixin):
    """
    Individual battlecard section for granular updates.
    
    Allows updating sections independently without full battlecard regeneration.
    """
    __tablename__ = "battlecard_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Multi-tenancy
    tenant_id = Column(Integer, nullable=True, index=True)
    
    # Reference
    battlecard_id = Column(Integer, nullable=False, index=True)
    
    # Section metadata
    section_type = Column(String(50), nullable=False, index=True)  # strengths, weaknesses, etc.
    title = Column(String(255))
    
    # Content
    content = Column(JSON, nullable=False)
    
    # Ordering
    display_order = Column(Integer, default=0)
    
    # AI metadata
    ai_generated = Column(Boolean, default=True)
    ai_confidence = Column(Float, default=0.0)
    
    # Review status
    is_approved = Column(Boolean, default=False)
    approved_by = Column(Integer)
    
    def __repr__(self):
        return f"<BattlecardSection(battlecard={self.battlecard_id}, type='{self.section_type}')>"
