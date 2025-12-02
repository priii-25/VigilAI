"""
Battlecard data model
"""
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from src.models.base import Base, TimestampMixin


class Battlecard(Base, TimestampMixin):
    """Battlecard entity"""
    __tablename__ = "battlecards"
    
    id = Column(Integer, primary_key=True, index=True)
    competitor_id = Column(Integer, nullable=False, index=True)
    
    # Battlecard content
    title = Column(String(255), nullable=False)
    overview = Column(Text)
    strengths = Column(JSON, default=[])  # List of strengths
    weaknesses = Column(JSON, default=[])  # List of weaknesses
    objection_handling = Column(JSON, default=[])  # List of objection responses
    kill_points = Column(JSON, default=[])  # Key winning arguments
    
    # Pricing comparison
    pricing_comparison = Column(JSON, default={})
    
    # Features comparison
    features_comparison = Column(JSON, default={})
    
    # Target personas
    target_personas = Column(JSON, default=[])
    
    # Win/Loss data
    win_rate = Column(JSON, default={})
    
    # Notion integration
    notion_page_id = Column(String(255))
    notion_url = Column(String(500))
    
    # Status
    is_published = Column(Boolean, default=False)
    version = Column(Integer, default=1)
    
    def __repr__(self):
        return f"<Battlecard(id={self.id}, competitor_id={self.competitor_id})>"
