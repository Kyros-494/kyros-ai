"""add_event_time_and_semantic_metadata

Revision ID: 7ef45fdad5be
Revises: 569ac10dcac4
Create Date: 2026-05-24 14:03:50.203827+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ef45fdad5be'
down_revision: Union[str, None] = '569ac10dcac4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from sqlalchemy.dialects import postgresql

def upgrade() -> None:
    # Add event_time to all memory tables
    op.add_column('episodic_memories', sa.Column('event_time', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('semantic_memories', sa.Column('event_time', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('procedural_memories', sa.Column('event_time', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Add metadata to semantic_memories
    op.add_column('semantic_memories', sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default='{}', nullable=False))


def downgrade() -> None:
    op.drop_column('semantic_memories', 'metadata')
    op.drop_column('procedural_memories', 'event_time')
    op.drop_column('semantic_memories', 'event_time')
    op.drop_column('episodic_memories', 'event_time')


_ = (revision, down_revision, branch_labels, depends_on)
