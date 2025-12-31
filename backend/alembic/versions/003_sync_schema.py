"""Add all missing columns to sync schema with models

Revision ID: 003_sync_schema
Revises: 002_add_tenant_id
Create Date: 2025-12-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers
revision = '003_sync_schema'
down_revision = '002_add_tenant_id'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if column exists in table"""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False


def add_column_if_missing(table_name, column):
    """Add column to table if it doesn't exist"""
    if not column_exists(table_name, column.name):
        op.add_column(table_name, column)
        return True
    return False


def upgrade() -> None:
    # =========================================
    # COMPETITORS TABLE - Add missing columns
    # =========================================
    add_column_if_missing('competitors', sa.Column('docs_url', sa.String(500), nullable=True))
    add_column_if_missing('competitors', sa.Column('linkedin_url', sa.String(500), nullable=True))
    add_column_if_missing('competitors', sa.Column('twitter_handle', sa.String(100), nullable=True))
    add_column_if_missing('competitors', sa.Column('last_scraped_at', sa.String(50), nullable=True))
    add_column_if_missing('competitors', sa.Column('scrape_frequency_hours', sa.Integer(), nullable=True, default=24))
    add_column_if_missing('competitors', sa.Column('pricing_content_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitors', sa.Column('careers_content_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitors', sa.Column('blog_content_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitors', sa.Column('extra_data', sa.JSON(), nullable=True))
    add_column_if_missing('competitors', sa.Column('tags', sa.JSON(), nullable=True))
    
    # =========================================
    # COMPETITOR_UPDATES TABLE - Add missing columns
    # =========================================
    add_column_if_missing('competitor_updates', sa.Column('category', sa.String(50), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('confidence', sa.Float(), nullable=True, default=1.0))
    add_column_if_missing('competitor_updates', sa.Column('previous_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('is_verified', sa.Boolean(), nullable=True, default=False))
    add_column_if_missing('competitor_updates', sa.Column('is_noise', sa.Boolean(), nullable=True, default=False))
    
    # =========================================
    # BATTLECARDS TABLE - Add missing columns
    # =========================================
    add_column_if_missing('battlecards', sa.Column('objection_handling', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('pricing_comparison', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('features_comparison', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('target_personas', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('win_rate', sa.Float(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('talk_tracks', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('key_differentiators', sa.JSON(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('salesforce_record_id', sa.String(100), nullable=True))
    add_column_if_missing('battlecards', sa.Column('is_draft', sa.Boolean(), nullable=True, default=True))
    add_column_if_missing('battlecards', sa.Column('version', sa.Integer(), nullable=True, default=1))
    add_column_if_missing('battlecards', sa.Column('ai_confidence', sa.Float(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('ai_generated_at', sa.DateTime(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('last_human_review_at', sa.DateTime(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('review_status', sa.String(20), nullable=True))
    add_column_if_missing('battlecards', sa.Column('reviewed_by', sa.Integer(), nullable=True))
    add_column_if_missing('battlecards', sa.Column('review_notes', sa.Text(), nullable=True))


def downgrade() -> None:
    # Downgrade is complex - would need to drop columns
    # For simplicity, we don't implement full downgrade
    pass
