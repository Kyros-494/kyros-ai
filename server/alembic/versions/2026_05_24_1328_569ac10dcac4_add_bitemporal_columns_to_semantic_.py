"""add_bitemporal_columns_to_semantic_memories

Revision ID: 569ac10dcac4
Revises: 8c4150020997
Create Date: 2026-05-24 13:28:14.313185+00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '569ac10dcac4'
down_revision: Union[str, None] = '8c4150020997'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('semantic_memories', sa.Column('valid_from', sa.DateTime(), server_default=sa.text('now()'), nullable=False))
    op.add_column('semantic_memories', sa.Column('valid_to', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('semantic_memories', 'valid_to')
    op.drop_column('semantic_memories', 'valid_from')


_ = (revision, down_revision, branch_labels, depends_on)
