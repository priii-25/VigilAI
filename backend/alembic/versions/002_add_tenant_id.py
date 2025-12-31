"""Add tenant_id columns for multi-tenancy

Revision ID: 002_add_tenant_id
Revises: a90d2357a441
Create Date: 2025-12-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers
revision = '002_add_tenant_id'
down_revision = 'a90d2357a441'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if table exists"""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """Check if column exists in table"""
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # Create tenants table if not exists
    if not table_exists('tenants'):
        op.create_table(
            'tenants',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('slug', sa.String(length=100), nullable=False),
            sa.Column('admin_email', sa.String(length=255), nullable=True),
            sa.Column('settings', sa.JSON(), nullable=True),
            sa.Column('features', sa.JSON(), nullable=True),
            sa.Column('max_competitors', sa.Integer(), default=50),
            sa.Column('max_users', sa.Integer(), default=10),
            sa.Column('max_scrapes_per_day', sa.Integer(), default=100),
            sa.Column('plan', sa.String(length=50), default='free'),
            sa.Column('is_active', sa.Boolean(), default=True),
            sa.Column('api_key', sa.String(length=255), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tenants_slug', 'tenants', ['slug'], unique=True)
        op.create_index('ix_tenants_api_key', 'tenants', ['api_key'], unique=True)
    
    # Create tenant_settings table if not exists
    if not table_exists('tenant_settings'):
        op.create_table(
            'tenant_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.Text(), nullable=True),
            sa.Column('value_type', sa.String(length=20), default='string'),
            sa.Column('is_encrypted', sa.Boolean(), default=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_tenant_settings_tenant_id', 'tenant_settings', ['tenant_id'])
    
    # Add tenant_id to competitors table if not exists
    if table_exists('competitors') and not column_exists('competitors', 'tenant_id'):
        op.add_column('competitors', sa.Column('tenant_id', sa.Integer(), nullable=True))
        op.create_index('ix_competitors_tenant_id', 'competitors', ['tenant_id'])
    
    # Create competitor_updates table if not exists
    if not table_exists('competitor_updates'):
        op.create_table(
            'competitor_updates',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=True),
            sa.Column('competitor_id', sa.Integer(), nullable=False),
            sa.Column('update_type', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=True),
            sa.Column('title', sa.String(length=500), nullable=False),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('impact_score', sa.Integer(), nullable=True),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('confidence', sa.Float(), nullable=True),
            sa.Column('source_url', sa.String(length=1000), nullable=True),
            sa.Column('raw_data', sa.JSON(), nullable=True),
            sa.Column('content_hash', sa.String(length=64), nullable=True),
            sa.Column('previous_hash', sa.String(length=64), nullable=True),
            sa.Column('is_processed', sa.Boolean(), default=False),
            sa.Column('is_verified', sa.Boolean(), default=False),
            sa.Column('is_noise', sa.Boolean(), default=False),
            sa.Column('idempotency_key', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ondelete='CASCADE')
        )
        op.create_index('ix_competitor_updates_tenant_id', 'competitor_updates', ['tenant_id'])
        op.create_index('ix_competitor_updates_competitor_id', 'competitor_updates', ['competitor_id'])
        op.create_index('ix_competitor_updates_update_type', 'competitor_updates', ['update_type'])
    else:
        # Add tenant_id column if table exists but column doesn't
        if table_exists('competitor_updates') and not column_exists('competitor_updates', 'tenant_id'):
            op.add_column('competitor_updates', sa.Column('tenant_id', sa.Integer(), nullable=True))
            op.create_index('ix_competitor_updates_tenant_id', 'competitor_updates', ['tenant_id'])
    
    # Create battlecards table if not exists  
    if not table_exists('battlecards'):
        op.create_table(
            'battlecards',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tenant_id', sa.Integer(), nullable=True),
            sa.Column('competitor_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('overview', sa.Text(), nullable=True),
            sa.Column('strengths', sa.JSON(), nullable=True),
            sa.Column('weaknesses', sa.JSON(), nullable=True),
            sa.Column('objection_handling', sa.JSON(), nullable=True),
            sa.Column('kill_points', sa.JSON(), nullable=True),
            sa.Column('pricing_comparison', sa.JSON(), nullable=True),
            sa.Column('features_comparison', sa.JSON(), nullable=True),
            sa.Column('target_personas', sa.JSON(), nullable=True),
            sa.Column('win_rate', sa.Float(), nullable=True),
            sa.Column('talk_tracks', sa.JSON(), nullable=True),
            sa.Column('key_differentiators', sa.JSON(), nullable=True),
            sa.Column('notion_page_id', sa.String(length=100), nullable=True),
            sa.Column('notion_url', sa.String(length=500), nullable=True),
            sa.Column('salesforce_record_id', sa.String(length=100), nullable=True),
            sa.Column('is_published', sa.Boolean(), default=False),
            sa.Column('is_draft', sa.Boolean(), default=True),
            sa.Column('version', sa.Integer(), default=1),
            sa.Column('ai_confidence', sa.Float(), nullable=True),
            sa.Column('ai_generated_at', sa.DateTime(), nullable=True),
            sa.Column('last_human_review_at', sa.DateTime(), nullable=True),
            sa.Column('review_status', sa.String(length=20), nullable=True),
            sa.Column('reviewed_by', sa.Integer(), nullable=True),
            sa.Column('review_notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ondelete='CASCADE')
        )
        op.create_index('ix_battlecards_tenant_id', 'battlecards', ['tenant_id'])
        op.create_index('ix_battlecards_competitor_id', 'battlecards', ['competitor_id'])
    else:
        # Add tenant_id column if table exists but column doesn't
        if table_exists('battlecards') and not column_exists('battlecards', 'tenant_id'):
            op.add_column('battlecards', sa.Column('tenant_id', sa.Integer(), nullable=True))
            op.create_index('ix_battlecards_tenant_id', 'battlecards', ['tenant_id'])


def downgrade() -> None:
    if table_exists('battlecards'):
        op.drop_table('battlecards')
    if table_exists('competitor_updates'):
        op.drop_table('competitor_updates')
    if column_exists('competitors', 'tenant_id'):
        op.drop_index('ix_competitors_tenant_id', table_name='competitors')
        op.drop_column('competitors', 'tenant_id')
    if table_exists('tenant_settings'):
        op.drop_table('tenant_settings')
    if table_exists('tenants'):
        op.drop_table('tenants')
