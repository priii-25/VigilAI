"""Fix missing columns in competitor_updates

Revision ID: 004_fix_missing_columns
Revises: 003_sync_schema
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers
revision = '004_fix_missing_columns'
down_revision = '003_sync_schema'
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
    # Ensure competitor_updates has all required columns
    add_column_if_missing('competitor_updates', sa.Column('content_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('previous_hash', sa.String(64), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('idempotency_key', sa.String(100), unique=True, nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('is_processed', sa.Boolean(), default=False, index=True))
    add_column_if_missing('competitor_updates', sa.Column('is_verified', sa.Boolean(), default=False))
    add_column_if_missing('competitor_updates', sa.Column('is_noise', sa.Boolean(), default=False))
    add_column_if_missing('competitor_updates', sa.Column('raw_data', sa.JSON(), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('source_url', sa.String(1000), nullable=True))
    add_column_if_missing('competitor_updates', sa.Column('confidence', sa.Float(), default=1.0))
    add_column_if_missing('competitor_updates', sa.Column('category', sa.String(50), index=True))

def downgrade() -> None:
    pass
