"""add api keys table for multi tenant access

Revision ID: 50f4486b4091
Revises: 491f84d4f7ce
Create Date: 2025-06-15 10:22:34.033721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '50f4486b4091'
down_revision: Union[str, None] = '491f84d4f7ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('key', sa.String(64), nullable=False, unique=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        
        # Usage limits
        sa.Column('max_patients_per_request', sa.Integer(), nullable=False, server_default=sa.text('1000')),
        sa.Column('max_requests_per_day', sa.Integer(), nullable=True),
        sa.Column('max_requests_per_minute', sa.Integer(), nullable=False, server_default=sa.text('60')),
        sa.Column('max_requests_per_hour', sa.Integer(), nullable=False, server_default=sa.text('1000')),
        
        # Usage tracking
        sa.Column('total_requests', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_patients_generated', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('daily_requests', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_reset_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'")),
        
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for performance
    op.create_index('ix_api_keys_key', 'api_keys', ['key'], unique=True)
    op.create_index('ix_api_keys_active', 'api_keys', ['is_active'])
    op.create_index('ix_api_keys_email', 'api_keys', ['email'])
    op.create_index('ix_api_keys_created_at', 'api_keys', ['created_at'])
    op.create_index('ix_api_keys_last_used_at', 'api_keys', ['last_used_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index('ix_api_keys_last_used_at', table_name='api_keys')
    op.drop_index('ix_api_keys_created_at', table_name='api_keys')
    op.drop_index('ix_api_keys_email', table_name='api_keys')
    op.drop_index('ix_api_keys_active', table_name='api_keys')
    op.drop_index('ix_api_keys_key', table_name='api_keys')
    
    # Drop table
    op.drop_table('api_keys')
