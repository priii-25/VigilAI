"""
Tenant model for multi-tenancy support

Enables row-level data isolation with tenant_id column across all models.
Supports multiple isolation approaches:
- Row-level isolation (current)
- Schema-per-tenant (future)
- DB-per-tenant (future)
"""
from sqlalchemy import Column, Integer, String, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from src.models.base import Base, TimestampMixin


class Tenant(Base, TimestampMixin):
    """
    Tenant/Organization entity.
    
    Each tenant has isolated data and configuration.
    """
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    
    # Contact
    admin_email = Column(String(255))
    
    # Settings
    settings = Column(JSON, default={})
    
    # Feature flags
    features = Column(JSON, default={
        "battlecards_enabled": True,
        "ai_analysis_enabled": True,
        "slack_integration": False,
        "notion_integration": False,
        "salesforce_integration": False
    })
    
    # Limits
    max_competitors = Column(Integer, default=50)
    max_users = Column(Integer, default=10)
    max_scrapes_per_day = Column(Integer, default=100)
    
    # Subscription
    plan = Column(String(50), default="free")  # free, pro, enterprise
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # API Keys (encrypted in production)
    api_key = Column(String(255), unique=True, index=True)
    
    def __repr__(self):
        return f"<Tenant(id={self.id}, slug='{self.slug}')>"
    
    def has_feature(self, feature_name: str) -> bool:
        """Check if tenant has a specific feature enabled"""
        return self.features.get(feature_name, False)
    
    def get_setting(self, key: str, default=None):
        """Get a tenant setting"""
        return self.settings.get(key, default)


class TenantMixin:
    """
    Mixin to add tenant_id to models for multi-tenancy.
    
    Usage:
        class Competitor(Base, TimestampMixin, TenantMixin):
            ...
    """
    tenant_id = Column(Integer, nullable=True, index=True)  # nullable for migration
    
    @classmethod
    def filter_by_tenant(cls, query, tenant_id: int):
        """Filter query by tenant"""
        return query.filter(cls.tenant_id == tenant_id)


class TenantSettings(Base, TimestampMixin):
    """
    Extended tenant settings for complex configurations.
    """
    __tablename__ = "tenant_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, nullable=False, index=True)
    
    # Category
    category = Column(String(50), nullable=False)  # integrations, notifications, ai, etc.
    
    # Key-value settings
    key = Column(String(100), nullable=False)
    value = Column(Text)
    value_type = Column(String(20), default="string")  # string, json, int, bool
    
    # Encryption flag
    is_encrypted = Column(Boolean, default=False)
    
    def get_typed_value(self):
        """Get value with proper type conversion"""
        if self.value_type == "json":
            import json
            return json.loads(self.value)
        elif self.value_type == "int":
            return int(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        return self.value


# Helper functions for tenant context
def get_tenant_filter(tenant_id: int):
    """Get SQLAlchemy filter for tenant isolation"""
    if tenant_id is None:
        return True  # No filter if no tenant context
    return lambda model: model.tenant_id == tenant_id
