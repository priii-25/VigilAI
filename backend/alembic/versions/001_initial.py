"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-12-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Competitors table
    op.create_table(
        'competitors',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('pricing_url', sa.String(length=500), nullable=True),
        sa.Column('careers_url', sa.String(length=500), nullable=True),
        sa.Column('blog_url', sa.String(length=500), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitors_name'), 'competitors', ['name'], unique=True)
    op.create_index(op.f('ix_competitors_domain'), 'competitors', ['domain'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_competitors_domain'), table_name='competitors')
    op.drop_index(op.f('ix_competitors_name'), table_name='competitors')
    op.drop_table('competitors')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
