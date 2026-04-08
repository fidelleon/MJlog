"""add cache_entries table

Revision ID: b17d524a4513
Revises: 9898aeb59fcf
Create Date: 2026-04-08 20:03:15.417420

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b17d524a4513'
down_revision: Union[str, Sequence[str], None] = '9898aeb59fcf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'cache_entries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('namespace', sa.String(length=64), nullable=False),
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('namespace', 'key', name='uq_cache_namespace_key'),
    )
    op.create_index(op.f('ix_cache_entries_key'), 'cache_entries', ['key'], unique=False)
    op.create_index(op.f('ix_cache_entries_namespace'), 'cache_entries', ['namespace'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_cache_entries_namespace'), table_name='cache_entries')
    op.drop_index(op.f('ix_cache_entries_key'), table_name='cache_entries')
    op.drop_table('cache_entries')
